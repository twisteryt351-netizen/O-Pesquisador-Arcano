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
    montar_prompt_diario, montar_prompt_titulo, verificar_filtro_etico, PALAVRAS_MIN,
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
MODELO_IA   = "openai/gpt-oss-120b"

def _mascarar(valor):
    if not valor:
        return "❌ NÃO configurado"
    return f"✅ configurado ({len(valor)} caracteres, começa com '{valor[:4]}...')"

print(f"🔑 POLLINATIONS_TOKEN: {_mascarar(POLLINATIONS_TOKEN)}")
print(f"🔑 IMGBB_API_KEY:      {_mascarar(IMGBB_API_KEY)}")

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
def pedir_ia_groq(prompt, temperatura=0.78, max_tokens=5500, tentativas=3):
    kwargs = {
        "messages": [{"role": "user", "content": prompt}],
        "model": MODELO_IA,
        "temperature": temperatura,
        "max_tokens": max_tokens,
    }
    for tentativa in range(1, tentativas + 1):
        try:
            response = groq_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e)
            eh_rate_limit = "rate_limit_exceeded" in msg or "429" in msg or "413" in msg or "tokens per minute" in msg
            if eh_rate_limit and tentativa < tentativas:
                espera = 65  # a janela de TPM da Groq reseta por minuto
                print(f"⚠️ Limite de tokens/min da Groq atingido (tentativa {tentativa}/{tentativas}). "
                      f"Aguardando {espera}s pra janela resetar... ({msg[:150]})")
                time.sleep(espera)
            else:
                raise


# ─────────────────────────────────────────────────────────────
#  GERAÇÃO DO ARTIGO DO DIA (com filtro ético em código)
# ─────────────────────────────────────────────────────────────
TAGS_BLOCO_PRONTAS = ("<h2", "<h3", "<blockquote", "<div", "<p", "<table", "<ul", "<ol", "<li")


def normalizar_para_html(texto):
    """Rede de segurança contra a IA usar Markdown (## título, **negrito**,
    > citação) em vez de HTML puro, e contra parágrafos separados só por
    linha em branco — que o navegador/Blogger colapsa em espaço único,
    virando uma parede de texto só com '##' aparecendo literalmente."""
    texto = texto.strip().replace("\r\n", "\n").replace("\r", "\n")
    blocos = re.split(r'\n\s*\n', texto)

    html_blocos = []
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
        if bloco.lower().startswith(TAGS_BLOCO_PRONTAS):
            html_blocos.append(bloco)
            continue

        m = re.match(r'^#{1,3}\s*(.+)$', bloco, flags=re.DOTALL)
        if m:
            resto = m.group(1).strip()
            corte = re.search(r'[.!?]\s+[A-ZÀ-Ú]', resto)
            if corte and corte.start() < 100:
                titulo_bloco = resto[:corte.start() + 1].strip()
                resto_paragrafo = resto[corte.start() + 1:].strip()
            elif len(resto) > 90:
                palavras = resto.split()
                titulo_bloco = " ".join(palavras[:12])
                resto_paragrafo = " ".join(palavras[12:])
            else:
                titulo_bloco, resto_paragrafo = resto, ""
            html_blocos.append(f"<h2>{titulo_bloco}</h2>")
            if resto_paragrafo:
                resto_paragrafo = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', resto_paragrafo)
                html_blocos.append(f"<p>{resto_paragrafo}</p>")
            continue

        if bloco.startswith(">"):
            citado = re.sub(r'^>\s?', '', bloco, flags=re.MULTILINE).strip().replace("\n", "<br>")
            html_blocos.append(f"<blockquote>{citado}</blockquote>")
            continue

        if re.match(r'^[-*]\s+', bloco, flags=re.MULTILINE):
            # lista estilo Markdown ("- item" ou "* item")
            itens = re.findall(r'^[-*]\s+(.+)$', bloco, flags=re.MULTILINE)
            if itens:
                lis = "".join(f"<li>{it.strip()}</li>" for it in itens)
                html_blocos.append(f"<ul>{lis}</ul>")
                continue

        paragrafo = bloco.replace("\n", "<br>")
        paragrafo = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', paragrafo)
        paragrafo = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', paragrafo)
        html_blocos.append(f"<p>{paragrafo}</p>")

    return "\n".join(html_blocos)


def contar_palavras_html(texto_html):
    texto_puro = re.sub(r'<[^>]+>', ' ', texto_html)
    return len(re.findall(r"[A-Za-zÀ-ÿ]+(?:['’-][A-Za-zÀ-ÿ]+)*", texto_puro))


def gerar_artigo_diario(estado, max_tentativas=2):
    prompt, temas_usados, marco_do_dia = montar_prompt_diario(estado)

    for tentativa in range(1, max_tentativas + 1):
        corpo = pedir_ia_groq(prompt, temperatura=0.78)
        violacoes = verificar_filtro_etico(corpo)
        if not violacoes:
            corpo = normalizar_para_html(corpo)
            # Se saiu curto (a Groq às vezes encerra antes do pedido),
            # pede uma continuação real em vez de publicar algo raso.
            if contar_palavras_html(corpo) < int(PALAVRAS_MIN * 0.8):
                palavras_atuais = contar_palavras_html(corpo)
                print(f"  ✏️  Artigo curto ({palavras_atuais} palavras, meta {PALAVRAS_MIN}) "
                      f"— pedindo continuação...")
                # manda só o FINAL do que já foi escrito (não o texto
                # inteiro) — evita estourar o limite de tokens de entrada
                contexto_final = corpo[-2000:]
                prompt_continuar = f"""
O texto abaixo terminou curto demais (menos de {PALAVRAS_MIN} palavras).
Abaixo está o TRECHO FINAL do que já foi escrito (não é o texto inteiro, só
o final, pra você saber onde parou). Continue EXATAMENTE de onde esse
trecho termina, mesma voz em primeira pessoa de Derick, mesmo tom e formato
HTML (pode abrir novos <h2> se fizer sentido). NÃO repita nada, não recomece
— só continue e aprofunde até fechar bem o dia.

TRECHO FINAL DO QUE JÁ FOI ESCRITO:
[...continua de: ]
{contexto_final}
"""
                continuacao = pedir_ia_groq(prompt_continuar, temperatura=0.78)
                corpo = corpo + "\n" + normalizar_para_html(continuacao)
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


def gerar_imagem_worker_b64(prompt_img, ratio="16:9", tentativas=3):
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

    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=120)
            if resp.status_code != 200:
                trecho = resp.text[:200].replace("\n", " ")
                raise ValueError(f"HTTP {resp.status_code} — resposta: {trecho!r}")
            if "image" not in resp.headers.get("Content-Type", ""):
                trecho = resp.text[:200].replace("\n", " ")
                raise ValueError(f"Resposta não é imagem (Content-Type: {resp.headers.get('Content-Type')}) — corpo: {trecho!r}")
            b64 = base64.b64encode(resp.content).decode("utf-8")
            if not b64:
                raise ValueError("Pollinations.ai retornou imagem vazia.")
            return b64
        except Exception as e:
            ultimo_erro = e
            if tentativa < tentativas:
                espera = 5 * tentativa
                print(f"  ⚠️  Pollinations.ai falhou (tentativa {tentativa}/{tentativas}): {e}. "
                      f"Tentando de novo em {espera}s...")
                time.sleep(espera)
                params["seed"] = __import__("random").randint(1, 999999)
    raise ultimo_erro


def hospedar_imgbb(b64_data, nome="mago_img"):
    if not IMGBB_API_KEY:
        raise ValueError("IMGBB_API_KEY não configurada.")
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
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
                # NUNCA usa data URI aqui: o Blogger não gera miniatura nem
                # sempre renderiza base64 embutido de primeira, o que causava
                # o "só aparece depois de abrir e atualizar". Sempre cai pra
                # uma URL externa real (Openverse) em vez disso.
                print(f"  ⚠️  ImgBB falhou/não propagou ({e_imgbb}). Buscando no Openverse...")
                if openverse_cache is None:
                    openverse_cache = buscar_imagens_openverse(palavra_fallback, quantidade=len(itens_imagem))
                src = openverse_cache[i % len(openverse_cache)]
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
            # as imagens restantes do MEIO ao FIM das seções seguintes
            # (usa a primeira e a última âncora disponível como extremos,
            # em vez de sempre cair em posições vizinhas no meio do texto)
            alvos = posicoes_h2[1:] if len(posicoes_h2) > 1 else posicoes_h2
            if len(extras) == 1:
                indices = [len(alvos) // 2]
            else:
                indices = [round(i * (len(alvos) - 1) / (len(extras) - 1)) for i in range(len(extras))]
            posicoes_escolhidas = sorted({alvos[i] for i in indices})
            livres = [a for a in alvos if a not in posicoes_escolhidas]
            while len(posicoes_escolhidas) < len(extras) and livres:
                posicoes_escolhidas.append(livres.pop(0))
            posicoes_escolhidas = sorted(posicoes_escolhidas)[:len(extras)]

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
    post_id = res.get("id")
    print(f"🔮 Postado: '{titulo}' -> {res.get('url')}")

    # Automatiza o "abrir e atualizar" manual: o Blogger às vezes só
    # (re)processa miniaturas/imagens externas quando o post é resalvo.
    if post_id:
        try:
            time.sleep(5)
            blogger.posts().update(blogId=BLOGGER_ID, postId=post_id, body=corpo).execute()
            print("  🔄 Re-save automático aplicado (equivalente a abrir e atualizar).")
        except Exception as e_update:
            print(f"  ⚠️  Re-save automático falhou (post já está publicado normalmente): {e_update}")


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
