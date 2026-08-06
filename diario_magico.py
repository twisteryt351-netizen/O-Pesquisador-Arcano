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
#  PROMPTS DE IMAGEM
# ─────────────────────────────────────────────────────────────
def gerar_prompts_imagens(estado, titulo, num_imagens=3):
    moodboard = MOODBOARD_FASE[estado["fase"]]
    prompt = f"""
You are an art director for a mystical, literary diary-blog with a warm, respectful,
non-graphic tone (no gore, no blood, no explicit content).

Life phase mood: {moodboard}
Article title: "{titulo}"

Create exactly {num_imagens} image generation prompt(s) in English:
- Prompt 1 (COVER): eye-catching but tasteful thumbnail-style image matching the mood above.
  Cinematic lighting, photorealistic or painterly, 8k quality, no text or watermarks.
- Remaining prompts: conceptual/emotional scenes that illustrate specific moments described
  in the article, matching the same mood and phase.

Rules for ALL prompts:
- One vivid descriptive paragraph each, no numbering or labels.
- No text, logos or words inside images. No gore, no blood, no explicit/sexual content.
- Warm, respectful, cinematic tone throughout.

Return ONLY a valid JSON array of {num_imagens} strings, nothing else.
Example: ["prompt one", "prompt two", "prompt three"]
"""
    raw = pedir_ia_groq(prompt, temperatura=0.6)
    match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if match:
        try:
            prompts = json.loads(match.group())
            if isinstance(prompts, list):
                return [str(p).strip() for p in prompts[:num_imagens]]
        except Exception:
            pass
    linhas = [l.strip().strip('"').strip("'") for l in raw.split('\n') if l.strip()]
    return linhas[:num_imagens] if linhas else [f"{moodboard}, 8k photorealistic"]


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


def html_imagem_blogger(src, alt_title, height=360, width=640):
    return (
        '<table align="center" cellpadding="0" cellspacing="0" '
        'class="tr-caption-container" '
        'style="margin-left:auto;margin-right:auto;margin-bottom:24px;">'
        '<tbody><tr><td style="text-align:center;">'
        f'<img alt="{alt_title}" border="0" height="{height}" src="{src}" '
        f'title="{alt_title}" width="{width}" '
        'style="max-width:100%;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.12);" />'
        '</td></tr></tbody></table><br />'
    )


def obter_imagens_html(prompts, titulo, palavra_fallback):
    imagens_html = []
    openverse_cache = None
    for i, prompt_img in enumerate(prompts):
        src = None
        try:
            print(f"  🖼️  [{i+1}/{len(prompts)}] Gerando via Pollinations.ai...")
            b64 = gerar_imagem_worker_b64(prompt_img, ratio="16:9")
            try:
                src = hospedar_imgbb(b64, nome=f"mago_{titulo[:40].replace(' ','_')}_{i+1}")
            except Exception as e_imgbb:
                print(f"  ⚠️  ImgBB falhou ({e_imgbb}). Usando data URI...")
                src = f"data:image/png;base64,{b64}"
        except Exception as e_ia:
            print(f"  ⚠️  Pollinations.ai falhou ({e_ia}). Buscando no Openverse...")
            if openverse_cache is None:
                openverse_cache = buscar_imagens_openverse(palavra_fallback, quantidade=len(prompts))
            src = openverse_cache[i % len(openverse_cache)]
        altura = 420 if i == 0 else 300
        imagens_html.append(html_imagem_blogger(src, titulo, height=altura))
        if i < len(prompts) - 1:
            time.sleep(INTERVALO_POLLINATIONS)
    return imagens_html


# ─────────────────────────────────────────────────────────────
#  MONTAGEM DO HTML FINAL
# ─────────────────────────────────────────────────────────────
def montar_html(corpo_artigo, imagens_html, estado):
    html_corpo = corpo_artigo
    for idx in range(1, len(imagens_html)):
        marcador = f"<!--IMG_{idx + 1}-->"
        if marcador in html_corpo:
            html_corpo = html_corpo.replace(marcador, imagens_html[idx], 1)
        else:
            html_corpo += imagens_html[idx]

    rodape = (
        '<p style="font-size:12px;color:#999;font-style:italic;margin-top:24px;">'
        f'📖 Diário Mágico — Geração {estado["geracao"]} — '
        f'{FASES[estado["fase"]]["nome"]} — {estado["data_narrativa_atual"]}. '
        'Conteúdo ficcional/educativo sobre tradições místicas e religiosas, '
        'com fins de reflexão e estudo. Não substitui orientação religiosa, '
        'psicológica ou médica profissional.</p>'
    )
    return f"{imagens_html[0]}{html_corpo}{rodape}"


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


def publicar_no_blogger(titulo, conteudo):
    creds = obter_credenciais()
    blogger = build("blogger", "v3", credentials=creds)
    corpo = {"kind": "blogger#post", "title": titulo, "content": conteudo}
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

    print("🖊️  Gerando prompts de imagem...")
    prompts_imagem = gerar_prompts_imagens(estado, titulo, num_imagens=3)

    print("🖼️  Obtendo imagens...")
    imagens_html = obter_imagens_html(
        prompts_imagem, titulo, MOODBOARD_FASE[estado["fase"]].split(",")[0]
    )

    html_final = montar_html(corpo, imagens_html, estado)
    publicar_no_blogger(titulo, html_final)

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
