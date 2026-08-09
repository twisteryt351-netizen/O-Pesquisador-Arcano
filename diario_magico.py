import os
import re
import json
import time
import base64
import urllib.parse
import requests
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from motor_narrativo import (
    carregar_estado, salvar_estado, avancar_estado,
    registrar_tema, registrar_titulo, registrar_marco, FASES,
)
from prompt_engine import (
    montar_prompt_diario, montar_prompt_titulo, verificar_filtro_etico,
)

# ─────────────────────────────────────────────────────────────
#  CONFIGURAÇÕES (mesmas variáveis de ambiente do robô de pets,
#  só troca o nome do BLOGGER_ID pra manter blogs separados)
# ─────────────────────────────────────────────────────────────
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
BLOGGER_ID         = os.environ.get("BLOGGER_ID_MAGO")
CLIENT_ID          = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET      = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN      = os.environ.get("BLOGGER_REFRESH_TOKEN")
POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN")
IMGBB_API_KEY      = os.environ.get("IMGBB_API_KEY")

INTERVALO_POLLINATIONS = 6 if POLLINATIONS_TOKEN else 16

for nome, valor in [
    ("GROQ_API_KEY",          GROQ_API_KEY),
    ("BLOGGER_ID_MAGO",       BLOGGER_ID),
    ("BLOGGER_CLIENT_ID",     CLIENT_ID),
    ("BLOGGER_CLIENT_SECRET", CLIENT_SECRET),
    ("BLOGGER_REFRESH_TOKEN", REFRESH_TOKEN),
]:
    if not valor:
        raise ValueError(f"Faltou configurar a variável/segredo: {nome}")

groq_client = Groq(api_key=GROQ_API_KEY)
MODELO_IA   = "llama-3.3-70b-versatile"

ARQUIVO_HISTORICO_TEXTO = "historico_magico.txt"
IMAGEM_PADRAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/News_icon.svg/640px-News_icon.svg.png"

# Moodboard visual por fase (usado nos prompts de imagem)
MOODBOARD_FASE = {
    1: "humble Brazilian Catholic household in the 1990s, warm nostalgic lighting, "
       "grandmother figure, Virgin Mary statue, rosary, soft photorealistic tone",
    2: "eclectic spiritual gathering, diverse religious symbols, warm candlelight, "
       "emotional atmosphere, photorealistic, respectful and dignified tone",
    3: "dark academia occult study, ancient grimoire open on wooden desk, candlelight, "
       "esoteric symbols, mysterious atmosphere, cinematic 8k, no gore, no blood",
    4: "hermetic lodge interior, robed practitioners in respectful ceremonial setting, "
       "warm mystical lighting, Belo Horizonte Brazil urban esoteric temple, tasteful",
    5: "wise elder mystic in quiet contemplative setting, books and candles, serene "
       "atmosphere, mentorship mood, warm cinematic photography",
}


# ─────────────────────────────────────────────────────────────
#  GROQ (texto)
# ─────────────────────────────────────────────────────────────
def pedir_ia_groq(prompt, temperatura=0.78):
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODELO_IA,
        temperature=temperatura,
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────
#  GERAÇÃO DO ARTIGO DO DIA (com filtro ético em código)
# ─────────────────────────────────────────────────────────────
def gerar_artigo_diario(estado, max_tentativas=2):
    prompt, temas_usados, marco_do_dia = montar_prompt_diario(estado)

    for tentativa in range(1, max_tentativas + 1):
        corpo = pedir_ia_groq(prompt, temperatura=0.78)
        violacoes = verificar_filtro_etico(corpo)
        if not violacoes:
            return corpo, temas_usados, marco_do_dia
        print(f"  ⚠️  Filtro ético bloqueou tentativa {tentativa}: {violacoes}")
        prompt += (
            f"\n\nATENÇÃO: a versão anterior violou as regras éticas "
            f"(mencionou: {', '.join(violacoes)}). Reescreva SEM nenhuma "
            f"menção a isso, mantendo a qualidade e o tamanho do texto."
        )

    raise ValueError(
        "Não foi possível gerar um artigo dentro das regras éticas "
        f"após {max_tentativas} tentativas. Abortando publicação de hoje."
    )


def gerar_titulo(estado, temas_usados):
    resumo = ", ".join(str(t) for t in temas_usados)
    prompt = montar_prompt_titulo(estado, resumo)
    return pedir_ia_groq(prompt, temperatura=0.85).replace('"', '').strip()


# ─────────────────────────────────────────────────────────────
#  TAGS / MARCADORES (Blogger "labels")
#  O Blogger tem um campo próprio pra isso na API — não adianta
#  só pedir pra IA "incluir tags" dentro do texto, tem que extrair
#  numa lista e mandar no campo "labels" do post.
# ─────────────────────────────────────────────────────────────
MAX_TAGS = 8

def gerar_tags(estado, temas_usados, titulo):
    fase_nome = FASES[estado["fase"]]["nome"]
    resumo = ", ".join(str(t) for t in temas_usados)
    prompt = f"""
Gere de 5 a {MAX_TAGS} marcadores/tags (labels) para um post de blog em português do Brasil.

Título do post: "{titulo}"
Fase da vida do personagem: {fase_nome}
Temas do dia: {resumo}

Regras:
- Tags curtas (1 a 3 palavras cada), sem "#", sem numeração.
- Misture tags específicas do tema do dia com tags amplas do nicho
  (ex: "diário místico", "ocultismo", "desenvolvimento espiritual"),
  pra ajudar tanto na navegação do blog quanto em SEO.
- Não repita o título literalmente como tag.

Retorne APENAS um array JSON válido de strings, nada mais.
Exemplo: ["tag um", "tag dois", "tag tres"]
"""
    raw = pedir_ia_groq(prompt, temperatura=0.5)
    match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if match:
        try:
            tags = json.loads(match.group())
            if isinstance(tags, list):
                tags_limpas = [str(t).strip() for t in tags if str(t).strip()]
                return tags_limpas[:MAX_TAGS]
        except Exception:
            pass
    # fallback simples se a IA não retornar JSON válido
    linhas = [l.strip(" -\"'") for l in raw.split(",") if l.strip()]
    return linhas[:MAX_TAGS] if linhas else [fase_nome]


# ─────────────────────────────────────────────────────────────
#  PROMPTS DE IMAGEM
# ─────────────────────────────────────────────────────────────
def gerar_prompts_imagens(estado, titulo, num_imagens=3):
    moodboard = MOODBOARD_FASE[estado["fase"]]
    prompt = f"""
You are an art director for a mystical, literary diary-blog with a warm, respectful,
non-graphic tone (no gore, no blood, no explicit content).

Life phase mood: {moodboard}
Article title: "{titulo}"

Create exactly {num_imagens} image concepts:
- Image 1 (COVER): eye-catching but tasteful thumbnail-style image matching the mood above.
  Cinematic lighting, photorealistic or painterly, 8k quality, no text or watermarks.
- Remaining images: conceptual/emotional scenes that illustrate DIFFERENT, DISTINCT specific
  moments described in the article, matching the same mood and phase. Each one must depict a
  clearly different scene from the others (no two images of "the same moment").

For EACH image, provide:
- "prompt": one vivid descriptive paragraph in ENGLISH for the image generator. No text, logos
  or words inside images. No gore, no blood, no explicit/sexual content.
- "legenda": a short caption in BRAZILIAN PORTUGUESE (under 12 words) describing what the image
  shows, written like a photo caption a reader would see under the image — not a repeat of the
  article title.

Return ONLY a valid JSON array of {num_imagens} objects, nothing else.
Example: [{{"prompt": "...", "legenda": "..."}}, {{"prompt": "...", "legenda": "..."}}]
"""
    raw = pedir_ia_groq(prompt, temperatura=0.6)
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            itens = json.loads(match.group())
            if isinstance(itens, list) and all(isinstance(i, dict) for i in itens):
                resultado = [
                    {"prompt": str(i.get("prompt", "")).strip(),
                     "legenda": str(i.get("legenda", "")).strip()}
                    for i in itens[:num_imagens]
                ]
                if all(r["prompt"] for r in resultado):
                    return resultado
        except Exception:
            pass
    # fallback: sem legenda estruturada, usa o moodboard puro
    return [{"prompt": f"{moodboard}, 8k photorealistic, scene {i+1}", "legenda": ""}
            for i in range(num_imagens)]


# ─────────────────────────────────────────────────────────────
#  GERAÇÃO DE IMAGEM — Pollinations.ai (b64) — igual ao pets_diario.py
# ─────────────────────────────────────────────────────────────
DIMENSOES_RATIO = {"16:9": (1280, 720), "1:1": (1024, 1024), "9:16": (720, 1280)}


def gerar_imagem_worker_b64(prompt_img, ratio="16:9"):
    largura, altura = DIMENSOES_RATIO.get(ratio, (1280, 720))
    prompt_codificado = urllib.parse.quote(prompt_img)
    url = f"https://image.pollinations.ai/prompt/{prompt_codificado}"
    params = {
        "width": largura, "height": altura, "model": "flux",
        "seed": __import__("random").randint(1, 999999), "nologo": "true",
    }
    headers = {}
    if POLLINATIONS_TOKEN:
        headers["Authorization"] = f"Bearer {POLLINATIONS_TOKEN}"
    resp = requests.get(url, params=params, headers=headers, timeout=120)
    resp.raise_for_status()
    if "image" not in resp.headers.get("Content-Type", ""):
        raise ValueError("Resposta não parece ser uma imagem.")
    b64 = base64.b64encode(resp.content).decode("utf-8")
    if not b64:
        raise ValueError("Pollinations.ai retornou imagem vazia.")
    return b64


def hospedar_imgbb(b64_data, nome="mago_img"):
    if not IMGBB_API_KEY:
        raise ValueError("IMGBB_API_KEY não configurada.")
    resp = requests.post(
        "https://api.imgbb.com/1/image",
        data={"key": IMGBB_API_KEY, "image": b64_data, "name": nome[:100]},
        timeout=60,
    )
    resp.raise_for_status()
    resultado = resp.json()
    if not resultado.get("success"):
        raise ValueError(f"ImgBB recusou o upload: {resultado}")
    return resultado["data"]["url"]


def verificar_url_imagem(url, tentativas=5, espera_segundos=2):
    """Confirma que a URL da imagem já está de fato acessível antes de
    usar no post. O ImgBB (e às vezes o Pollinations) podem levar alguns
    segundos pra propagar no CDN deles — sem essa checagem, o post é
    publicado com um link que ainda dá 404/timeout, e só passa a
    funcionar quando o Blogger recarrega o conteúdo depois (ex: ao
    clicar em 'Atualizar')."""
    for tentativa in range(1, tentativas + 1):
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                return True
            # alguns hosts não respondem bem a HEAD, tenta GET como fallback
            if resp.status_code in (403, 405):
                resp = requests.get(url, timeout=10, stream=True)
                if resp.status_code == 200:
                    return True
        except requests.RequestException:
            pass
        if tentativa < tentativas:
            time.sleep(espera_segundos)
    return False


def buscar_imagens_openverse(palavra_chave, quantidade=3):
    try:
        resposta = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": palavra_chave, "license_type": "commercial",
                    "page_size": max(quantidade, 5), "mature": "false"},
            headers={"User-Agent": "RoboMago/1.0"}, timeout=15,
        )
        resultados = resposta.json().get("results", [])
        urls = [r["url"] for r in resultados[:quantidade]]
        return urls if urls else [IMAGEM_PADRAO]
    except Exception as e:
        print(f"⚠️ Erro Openverse: {e}")
        return [IMAGEM_PADRAO]


def html_imagem_blogger(src, alt_title, legenda="", height=360, width=640):
    legenda_html = ""
    if legenda:
        legenda_html = (
            f'<div style="font-size:13px;color:#777;font-style:italic;'
            f'text-align:center;margin-top:6px;margin-bottom:20px;">{legenda}</div>'
        )
    return (
        '<table align="center" cellpadding="0" cellspacing="0" '
        'class="tr-caption-container" '
        'style="margin-left:auto;margin-right:auto;margin-bottom:8px;">'
        '<tbody><tr><td style="text-align:center;">'
        f'<img alt="{legenda or alt_title}" border="0" height="{height}" src="{src}" '
        f'title="{legenda or alt_title}" width="{width}" '
        'style="max-width:100%;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.12);" />'
        '</td></tr></tbody></table>'
        f'{legenda_html}'
    )


def obter_imagens_html(itens_imagem, titulo, palavra_fallback):
    """itens_imagem: lista de dicts {'prompt':..., 'legenda':...}"""
    imagens_html = []
    openverse_cache = None
    for i, item in enumerate(itens_imagem):
        prompt_img = item["prompt"]
        legenda = item.get("legenda", "")
        src = None
        try:
            print(f"  🖼️  [{i+1}/{len(itens_imagem)}] Gerando via Pollinations.ai...")
            b64 = gerar_imagem_worker_b64(prompt_img, ratio="16:9")
            try:
                url_imgbb = hospedar_imgbb(b64, nome=f"mago_{titulo[:40].replace(' ','_')}_{i+1}")
                print(f"  ⏳ Confirmando que a URL do ImgBB já está acessível...")
                if verificar_url_imagem(url_imgbb):
                    src = url_imgbb
                    print(f"  ✅ URL confirmada: {url_imgbb}")
                else:
                    raise ValueError("URL do ImgBB não respondeu 200 depois de várias tentativas.")
            except Exception as e_imgbb:
                print(f"  ⚠️  ImgBB falhou/não propagou ({e_imgbb}). Usando data URI...")
                src = f"data:image/png;base64,{b64}"
        except Exception as e_ia:
            print(f"  ⚠️  Pollinations.ai falhou ({e_ia}). Buscando no Openverse...")
            if openverse_cache is None:
                openverse_cache = buscar_imagens_openverse(palavra_fallback, quantidade=len(itens_imagem))
            src = openverse_cache[i % len(openverse_cache)]
        altura = 420 if i == 0 else 300
        imagens_html.append(html_imagem_blogger(src, titulo, legenda=legenda, height=altura))
        if i < len(itens_imagem) - 1:
            time.sleep(INTERVALO_POLLINATIONS)
    return imagens_html


# ─────────────────────────────────────────────────────────────
#  MONTAGEM DO HTML FINAL
# ─────────────────────────────────────────────────────────────
def montar_html(corpo_artigo, imagens_html, estado):
    capa = imagens_html[0]
    extras = imagens_html[1:]

    if not extras:
        corpo_final = corpo_artigo
    else:
        # Acha onde cada <h2> começa no texto — cada seção do artigo
        # (dia a dia / estudo místico / reflexão) começa com um <h2>.
        posicoes_h2 = [m.start() for m in re.finditer(r'<h2\b', corpo_artigo, flags=re.IGNORECASE)]

        if not posicoes_h2:
            # não achou nenhum <h2> pra ancorar — melhor colocar as imagens
            # no fim do que quebrar a formatação tentando adivinhar posição
            corpo_final = corpo_artigo + "".join(extras)
        else:
            # pula a 1ª seção (que já vem logo depois da capa) e espalha
            # as imagens restantes pelas seções seguintes
            alvos = posicoes_h2[1:] if len(posicoes_h2) > 1 else posicoes_h2
            passo = max(1, len(alvos) // len(extras))
            posicoes_escolhidas = [alvos[min(i * passo, len(alvos) - 1)] for i in range(len(extras))]

            # insere de trás pra frente, senão os índices calculados
            # ficam inválidos assim que a 1ª inserção desloca o texto
            corpo_final = corpo_artigo
            for pos, img in sorted(zip(posicoes_escolhidas, extras), key=lambda par: -par[0]):
                corpo_final = corpo_final[:pos] + img + corpo_final[pos:]

    rodape = (
        '<p style="font-size:12px;color:#999;font-style:italic;margin-top:24px;">'
        f'📖 Diário Mágico — Geração {estado["geracao"]} — '
        f'{FASES[estado["fase"]]["nome"]} — {estado["data_narrativa_atual"]}. '
        'Conteúdo ficcional/educativo sobre tradições místicas e religiosas, '
        'com fins de reflexão e estudo. Não substitui orientação religiosa, '
        'psicológica ou médica profissional.</p>'
    )
    return f"{capa}{corpo_final}{rodape}"


# ─────────────────────────────────────────────────────────────
#  BLOGGER
# ─────────────────────────────────────────────────────────────
def obter_credenciais():
    creds = Credentials(
        token=None, refresh_token=REFRESH_TOKEN, client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET, token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds


def publicar_no_blogger(titulo, conteudo, tags=None):
    creds = obter_credenciais()
    blogger = build("blogger", "v3", credentials=creds)
    corpo = {"kind": "blogger#post", "title": titulo, "content": conteudo}
    if tags:
        corpo["labels"] = tags
    res = blogger.posts().insert(blogId=BLOGGER_ID, body=corpo).execute()
    print(f"🔮 Postado: '{titulo}' -> {res.get('url')}")


def registrar_historico_texto(estado, titulo):
    with open(ARQUIVO_HISTORICO_TEXTO, "a", encoding="utf-8") as f:
        f.write(
            f"[Ger.{estado['geracao']} | Fase {estado['fase']} | "
            f"{estado['idade_atual']}a | {estado['data_narrativa_atual']}] {titulo}\n"
        )


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔮 Gerando entrada do Diário Mágico de hoje...")

    estado = carregar_estado()
    print(f"📍 Geração {estado['geracao']} | Fase {estado['fase']} "
          f"({FASES[estado['fase']]['nome']}) | {estado['idade_atual']} anos | "
          f"{estado['data_narrativa_atual']}")

    print("📖 Escrevendo entrada do diário...")
    corpo, temas_usados, marco_do_dia = gerar_artigo_diario(estado)

    print("📝 Gerando título...")
    titulo = gerar_titulo(estado, temas_usados)
    print(f"✏️  Título: {titulo}")

    print("🏷️  Gerando tags/marcadores...")
    tags = gerar_tags(estado, temas_usados, titulo)
    print(f"🏷️  Tags: {tags}")

    print("🖊️  Gerando prompts de imagem...")
    prompts_imagem = gerar_prompts_imagens(estado, titulo, num_imagens=3)

    print("🖼️  Obtendo imagens...")
    imagens_html = obter_imagens_html(
        prompts_imagem, titulo, MOODBOARD_FASE[estado["fase"]].split(",")[0]
    )

    html_final = montar_html(corpo, imagens_html, estado)
    publicar_no_blogger(titulo, html_final, tags=tags)

    # Atualiza estado: registra temas/título/marco e avança o tempo narrativo
    for tema in temas_usados:
        registrar_tema(estado, tema)
    registrar_titulo(estado, titulo)
    if marco_do_dia:
        registrar_marco(estado, marco_do_dia)

    # Registra a obra/prática estudada em pools próprios de continuidade
    if estado["fase"] == 3 and temas_usados:
        estado["obras_estudadas"].append(temas_usados[0])
        estado["obras_estudadas"] = estado["obras_estudadas"][-15:]
    if estado["fase"] == 5 and temas_usados:
        estado["poderes_dominados"].append(temas_usados[0])
        estado["poderes_dominados"] = estado["poderes_dominados"][-15:]
    if estado["fase"] == 2 and temas_usados:
        nomes_relacoes = [r["nome"] for r in estado.get("relacoes", [])]
        if temas_usados[0] not in nomes_relacoes:
            estado["relacoes"].append({"nome": temas_usados[0]})
            estado["relacoes"] = estado["relacoes"][-12:]

    registrar_historico_texto(estado, titulo)
    estado = avancar_estado(estado)
    salvar_estado(estado)

    print(f"✅ Concluído! Próxima entrada: {estado['data_narrativa_atual']} "
          f"({estado['idade_atual']} anos, Fase {estado['fase']})")
