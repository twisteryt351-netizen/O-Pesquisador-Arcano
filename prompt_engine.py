# ─────────────────────────────────────────────────────────────
#  MOTOR DE PROMPTS — monta o prompt de 3 camadas
#  (Diário Pessoal / Estudo Místico / Reflexão + Cultura Pop)
#  específico pra fase atual da vida de Derick.
# ─────────────────────────────────────────────────────────────
import random
from conteudo_fases import *
from motor_narrativo import FASES, registrar_marco

PALAVRAS_MIN = 3400

# ─────────────────────────────────────────────────────────────
#  HELPERS DE SELEÇÃO ANTI-REPETIÇÃO
# ─────────────────────────────────────────────────────────────
def escolher_nao_repetido(pool, temas_recentes, extrator=lambda x: str(x)):
    """Escolhe um item do pool cujo identificador não esteja nos temas
    recentes do estado. Se todos estiverem 'gastos', libera o pool
    inteiro de novo (igual à lógica do pets_diario.py)."""
    disponiveis = [item for item in pool if extrator(item) not in temas_recentes]
    if not disponiveis:
        disponiveis = pool
    return random.choice(disponiveis)


# ─────────────────────────────────────────────────────────────
#  CABEÇALHO COMUM — persona do autor + regras fixas de formato/ética
#  (repetido em TODA fase — é a camada de segurança nº1)
# ─────────────────────────────────────────────────────────────
def cabecalho_persona(estado):
    return f"""
Você é "Twister", autor de um blog-legado no formato de diário místico.
Você escreve em primeira pessoa, na voz de Derick de Souza (geração {estado['geracao']}),
{estado['idade_atual']} anos, em {estado['data_narrativa_atual']}.

Este é um projeto de LEGADO: uma obra de referência que funciona como
curso escrito para futuros magos e sábios, no espírito de "O Alquimista"
e "O Diário de um Mago" de Paulo Coelho, mas com profundidade técnica
real sobre tradições místicas, religiosas e ocultas.

REGRAS FIXAS E INEGOCIÁVEIS DE ÉTICA E CONTEÚDO (nunca quebrar):
- PROIBIDO: sacrifício humano ou animal, uso de sangue em qualquer ritual,
  magia sexual explícita, incentivo a causar dano real a terceiros.
- Feitiços de "ataque" ou proteção são descritos apenas em contexto de
  defesa, nunca como incentivo a agressão não provocada.
- Magia amorosa é sempre enquadrada como atrair o que é recíproco e mudar
  a si mesmo — nunca como forçar a vontade de outra pessoa. Sempre que o
  tema surgir, reforce que o desapego costuma ser o caminho mais sábio.
- Ao citar obras, autores ou tradições reais (grimórios, livros, fundadores
  de ordens), mencione o nome da obra/autor claramente para que o leitor
  possa pesquisar e confirmar por conta própria. NUNCA copie texto extenso
  e literal de nenhuma obra — explique e contextualize com suas próprias
  palavras, como quem já leu e está resumindo/comentando para um aprendiz.

REGRAS DE FORMATO (HTML puro, sem Markdown):
- PROIBIDO usar sintaxe de Markdown em QUALQUER lugar do texto: nada de "##"
  pra subtítulo, nada de "**negrito**", nada de "*itálico*", nada de "> "
  pra citação. Use SOMENTE as tags HTML reais indicadas abaixo. Se você
  escrever "##" em algum ponto, está ERRADO — o subtítulo tem que ser uma
  tag <h2>...</h2> de verdade, sozinha em sua própria linha, sem texto colado.
- TODO parágrafo normal de texto corrido deve vir envolvido em <p> e </p>,
  um parágrafo por bloco. Nunca deixe frases soltas sem tag ao redor.
- Mínimo de {PALAVRAS_MIN} palavras.
- Parágrafo de abertura envolvente, já dentro da cena do dia.
- Estrutura em 3 camadas obrigatórias (dia a dia / estudo místico / reflexão),
  mas os subtítulos <h2> devem ser ESPECÍFICOS do conteúdo de hoje, nunca os
  nomes genéricos das camadas. PROIBIDO usar <h2> como "O dia a dia",
  "Estudo místico do dia", "Reflexão" ou qualquer variação genérica disso —
  são só um guia estrutural interno, não títulos.
  Exemplo do que NÃO fazer: "<h2>O Dia a Dia</h2>", "<h2>Estudo Místico</h2>".
  Exemplo do que fazer: um <h2> específico como "A confissão que eu quase
  esqueci" ou "O 5º Mandamento e a regra do futebol" — títulos que só fariam
  sentido NESTE post, amarrados ao tema/mandamento/obra/prática específica
  que você está tratando hoje.
- Cada subtítulo deve nascer do conteúdo do parágrafo que ele introduz —
  releia o parágrafo antes de escrever o <h2> e garanta que ele descreve
  aquele trecho específico, não a estrutura genérica do post.
- Pelo menos 1 lista <ul> com pontos práticos do ensinamento do dia.
- 2 a 3 <blockquote> com reflexões pessoais de Derick, tom confessional.
- Feche com uma frase-síntese que pareça uma "lição do dia" de curso.
"""


# ─────────────────────────────────────────────────────────────
#  FASE 1 — CATOLICISMO
# ─────────────────────────────────────────────────────────────
def montar_prompt_fase1(estado):
    mandamento = escolher_nao_repetido(MANDAMENTOS, estado["temas_recentes"], lambda x: f"mandamento_{x['n']}")
    oracao = escolher_nao_repetido(ORACOES_CATOLICAS, estado["temas_recentes"], lambda x: x["nome"])
    vida_avo = escolher_nao_repetido(VIDA_AVO, estado["temas_recentes"])
    vida_escola = escolher_nao_repetido(VIDA_ESCOLA_F1, estado["temas_recentes"])
    angulo = escolher_nao_repetido(ANGULOS_REFLEXAO_F1, estado["temas_recentes"])

    # Verifica se algum marco sacramental bate com a idade atual
    marco_do_dia = None
    for marco in SACRAMENTOS_MARCOS:
        if marco["idade_tipica"] == estado["idade_atual"] and marco["id"] not in estado["marcos_concluidos"]:
            marco_do_dia = marco
            break

    ref_pop = None
    for ref in REFERENCIAS_POP_F1:
        ano_narrativo = int(estado["data_narrativa_atual"][:4])
        if ref["janela_anos"][0] <= ano_narrativo <= ref["janela_anos"][1]:
            ref_pop = ref
            break

    temas_usados = [f"mandamento_{mandamento['n']}", oracao["nome"], vida_avo, vida_escola, angulo]

    bloco_marco = ""
    if marco_do_dia:
        bloco_marco = f"\nMARCO ESPECIAL DE HOJE: narre o sacramento '{marco_do_dia['id']}' — {marco_do_dia['descricao']}.\n"
    bloco_pop = ""
    if ref_pop:
        bloco_pop = f"\nReferência de cultura pop disponível pro contexto (época compatível): {ref_pop['obra']} — {ref_pop['nota']}.\n"

    prompt = cabecalho_persona(estado) + f"""
CONTEXTO DA FASE: Fase 1 — A Base (Catolicismo). Derick tem {estado['idade_atual']} anos,
criado pela avó (beata da igreja do bairro), seguindo catequese aos sábados e missa aos domingos.
{bloco_marco}
CAMADA 1 (dia a dia): narre uma cena envolvendo: "{vida_escola}".
CAMADA 2 (estudo místico/religioso): explique o {mandamento['n']}º Mandamento
("{mandamento['texto']}") através da confusão infantil real de Derick: {mandamento['mal_entendido']}.
Inclua também a oração "{oracao['nome']}" — contexto: {oracao['contexto']}.
CAMADA 3 (reflexão): explore o ângulo "{angulo}". Traga também uma cena com a avó: "{vida_avo}".
{bloco_pop}
Não repita ideias já usadas recentemente (evite duplicar qualquer um destes temas
já trabalhados): {', '.join(estado['temas_recentes'][-10:]) if estado['temas_recentes'] else '(nenhum ainda)'}
"""
    marco_id = marco_do_dia["id"] if marco_do_dia else None
    return prompt, temas_usados, marco_id


# ─────────────────────────────────────────────────────────────
#  FASE 2 — BUSCA / PLURALIDADE RELIGIOSA
# ─────────────────────────────────────────────────────────────
def montar_prompt_fase2(estado):
    if estado["idade_atual"] <= 21 and "luto_avo_concluido" not in estado["marcos_concluidos"]:
        etapa_luto = escolher_nao_repetido(LUTO_AVO_ETAPAS, estado["temas_recentes"])
        angulo = escolher_nao_repetido(ANGULOS_REFLEXAO_F2, estado["temas_recentes"])
        temas_usados = [etapa_luto, angulo]
        prompt = cabecalho_persona(estado) + f"""
CONTEXTO DA FASE: Fase 2 — O Luto e a Busca. Derick tem {estado['idade_atual']} anos.
Este é um momento do LUTO pela avó, ainda sem entrar nas outras religiões.

CAMADA 1 (dia a dia): narre a etapa: "{etapa_luto}".
CAMADA 2 (estudo místico): reflita sobre o que o catolicismo ensinou a Derick sobre morte,
céu e ressurreição, e como isso conforta (ou não) agora que é real e não teórico.
CAMADA 3 (reflexão): explore o ângulo "{angulo}".

Não repita: {', '.join(estado['temas_recentes'][-10:]) if estado['temas_recentes'] else '(nenhum ainda)'}
"""
        return prompt, temas_usados, "luto_avo_concluido" if estado["idade_atual"] >= 21 else None

    relacao = escolher_nao_repetido(RELACIONAMENTOS_F2, [r["nome"] for r in estado.get("relacoes", [])])
    angulo = escolher_nao_repetido(ANGULOS_REFLEXAO_F2, estado["temas_recentes"])
    temas_usados = [relacao["nome"], angulo]

    fase_cfg = FASES[2]
    marco_do_dia = None
    if (estado["idade_atual"] >= fase_cfg["idade_fim"]
            and "decepcao_religiosa_total" not in estado["marcos_concluidos"]):
        marco_do_dia = "decepcao_religiosa_total"

    prompt = cabecalho_persona(estado) + f"""
CONTEXTO DA FASE: Fase 2 — O Luto e a Busca. Derick tem {estado['idade_atual']} anos,
e está numa fase de explorar religiões diferentes através de relacionamentos.
{"NARRE TAMBÉM: Derick sente que já passou por religiões suficientes e começa a se decepcionar com todas elas, fechando esse ciclo de busca externa." if marco_do_dia else ""}
CAMADA 1 (dia a dia): narre o relacionamento com "{relacao['nome']}" — contexto: {relacao['contexto']}.
CAMADA 2 (estudo místico/religioso): explique com profundidade e respeito a religião
"{relacao['religiao_introduzida']}" que essa pessoa apresenta a ele. Traga elementos reais
e verificáveis da tradição (não invente doutrina).
CAMADA 3 (reflexão): explore o ângulo "{angulo}", sempre comparando com a base católica
da infância dele.

Não repita: {', '.join(estado['temas_recentes'][-10:]) if estado['temas_recentes'] else '(nenhum ainda)'}
"""
    return prompt, temas_usados, marco_do_dia


# ─────────────────────────────────────────────────────────────
#  FASE 3 — OCULTISMO BRUTO
# ─────────────────────────────────────────────────────────────
def montar_prompt_fase3(estado):
    obra = escolher_nao_repetido(OBRAS_OCULTAS, estado["obras_estudadas"], lambda x: x["titulo"])
    pratica = escolher_nao_repetido(PRATICAS_F3, estado["temas_recentes"])
    resultado = random.choice(RESULTADOS_EXPERIMENTOS)
    angulo = escolher_nao_repetido(ANGULOS_REFLEXAO_F3, estado["temas_recentes"])

    temas_usados = [obra["titulo"], pratica, angulo]

    fase_cfg = FASES[3]
    marco_do_dia = None
    if (estado["idade_atual"] >= fase_cfg["idade_fim"]
            and "decide_buscar_ordem" not in estado["marcos_concluidos"]):
        marco_do_dia = "decide_buscar_ordem"

    bloco_marco = ("\nNARRE TAMBÉM: Derick sente que precisa validar seu conhecimento "
                   "com uma ordem iniciática de verdade, e começa a pesquisar Rosa-Cruz, "
                   "maçonaria, e outras ordens até ouvir falar de uma que abriu filial "
                   "perto dele.\n") if marco_do_dia else ""

    prompt = cabecalho_persona(estado) + f"""
CONTEXTO DA FASE: Fase 3 — O Despertar (Ocultismo Bruto). Derick tem {estado['idade_atual']} anos,
estudando sozinho, sem mestre nem ordem, movido por decepção com religiões organizadas.
{bloco_marco}
CAMADA 1 (dia a dia): narre Derick tentando encaixar seus estudos na rotina normal da vida adulta
(trabalho, contas, solidão do estudo autodidata).
CAMADA 2 (estudo místico — o núcleo técnico do dia): apresente a obra "{obra['titulo']}".
Contexto pra você usar como base: {obra['nota']}. Explique com profundidade real o que é essa obra,
sua origem histórica, e o que Derick aprendeu dela — SEMPRE em palavras próprias, nunca copiando
texto original literalmente. Descreva também a prática "{pratica}" que ele tentou.
CAMADA 3 (reflexão): o experimento de hoje {resultado}. Explore o ângulo "{angulo}".

Não repita obras/práticas recentes: {', '.join(estado['obras_estudadas'][-10:]) if estado['obras_estudadas'] else '(nenhuma ainda)'}
"""
    return prompt, temas_usados, marco_do_dia


# ─────────────────────────────────────────────────────────────
#  FASE 4 — A ORDEM
# ─────────────────────────────────────────────────────────────
def montar_prompt_fase4(estado):
    materia = escolher_nao_repetido(CURRICULO_ORDEM, estado["temas_recentes"])
    personagem = random.choice(PERSONAGENS_ORDEM)
    angulo = escolher_nao_repetido(ANGULOS_REFLEXAO_F4, estado["temas_recentes"])

    # marco de matrícula/formatura conforme avanço dentro da fase
    marco_do_dia = None
    if estado["dia_na_fase"] == 0:
        marco_do_dia = "workshop_inicial"
    elif estado["dia_na_fase"] == 3:
        marco_do_dia = "matricula_curso"
    fase_cfg = FASES[4]
    # formatura perto do fim da fase (heurística: quando idade bate no teto)
    if estado["idade_atual"] >= fase_cfg["idade_fim"] and "formatura_mago_hermetista" not in estado["marcos_concluidos"]:
        marco_do_dia = "formatura_mago_hermetista"

    temas_usados = [materia, angulo]

    bloco_marco = f"\nMARCO ESPECIAL DE HOJE: narre o evento '{marco_do_dia}' na Ordem.\n" if marco_do_dia else ""

    prompt = cabecalho_persona(estado) + f"""
CONTEXTO DA FASE: Fase 4 — A Ordem (Hermetismo Estruturado). Derick tem {estado['idade_atual']} anos,
estudando na Ordem "{ORDEM_INFO['nome']}", no bairro {ORDEM_INFO['bairro']}.
{bloco_marco}
CAMADA 1 (dia a dia): narre uma interação com o colega de Ordem "{personagem['nome']}"
({personagem['papel']}).
CAMADA 2 (estudo místico — aula da Ordem): explique com profundidade a matéria do currículo:
"{materia}".
CAMADA 3 (reflexão): explore o ângulo "{angulo}".

Não repita: {', '.join(estado['temas_recentes'][-10:]) if estado['temas_recentes'] else '(nenhum ainda)'}
"""
    return prompt, temas_usados, marco_do_dia


# ─────────────────────────────────────────────────────────────
#  FASE 5 — O SÁBIO
# ─────────────────────────────────────────────────────────────
def montar_prompt_fase5(estado):
    pratica = escolher_nao_repetido(PRATICAS_AVANCADAS_F5, estado["poderes_dominados"], lambda x: x["nome"])
    etica = random.choice(ETICA_ENSINAMENTOS_F5)

    usar_discipulo = estado["idade_atual"] >= 50
    usar_pop = random.random() < 0.35

    bloco_discipulo = ""
    marco_do_dia = None
    if usar_discipulo:
        etapa = escolher_nao_repetido(BUSCA_DISCIPULO_ETAPAS, estado["temas_recentes"])
        bloco_discipulo = f"\nARCO DO DISCÍPULO: narre a etapa \"{etapa}\" da busca por um sucessor.\n"
        if etapa == BUSCA_DISCIPULO_ETAPAS[-1]:
            marco_do_dia = "discipulo_formado"

    bloco_pop = ""
    if usar_pop:
        ref = random.choice(CULTURA_POP_SIMBOLOGIA_F5)
        bloco_pop = f"\nCAMADA EXTRA (cultura pop): conecte o ensinamento de hoje com \"{ref['obra']}\" — {ref['simbolismo']}.\n"

    temas_usados = [pratica["nome"]]

    prompt = cabecalho_persona(estado) + f"""
CONTEXTO DA FASE: Fase 5 — A Sabedoria e o Legado (O Sábio). Derick tem {estado['idade_atual']} anos,
já reconhecido como Sábio, ensinando e revisitando toda sua trajetória.
{bloco_discipulo}
CAMADA 1 (dia a dia): a rotina madura de Derick como Sábio — orientando pessoas, escrevendo,
revisitando memórias antigas de forma natural.
CAMADA 2 (estudo místico — o ensinamento avançado do dia): explique com profundidade a prática
"{pratica['nome']}". Contexto: {pratica['nota']}.
CAMADA 3 (reflexão ética, sempre presente nesta fase): "{etica}"
{bloco_pop}
Não repita práticas recentes: {', '.join(estado['poderes_dominados'][-10:]) if estado['poderes_dominados'] else '(nenhuma ainda)'}
"""
    return prompt, temas_usados, marco_do_dia


DISPATCH_FASE = {
    1: montar_prompt_fase1,
    2: montar_prompt_fase2,
    3: montar_prompt_fase3,
    4: montar_prompt_fase4,
    5: montar_prompt_fase5,
}


def montar_prompt_diario(estado):
    return DISPATCH_FASE[estado["fase"]](estado)


# ─────────────────────────────────────────────────────────────
#  PROMPT DE TÍTULO (SEO, anti-repetição)
# ─────────────────────────────────────────────────────────────
def montar_prompt_titulo(estado, resumo_tema):
    titulos_recentes = estado["titulos_recentes"][-20:]
    return f"""
Crie um título de blog em português do Brasil, envolvente, otimizado para SEO,
sem aspas, para uma entrada de diário místico sobre: {resumo_tema}.
O tom é confessional e narrativo, como um diário real sendo publicado.
NÃO pode ser parecido com nenhum destes já usados recentemente:
{chr(10).join(titulos_recentes) if titulos_recentes else '(nenhum ainda)'}
Responda apenas o título, texto puro.
"""


# ─────────────────────────────────────────────────────────────
#  FILTRO ÉTICO — camada de segurança em CÓDIGO (não só no prompt)
# ─────────────────────────────────────────────────────────────
def verificar_filtro_etico(texto):
    """Retorna lista de termos proibidos encontrados no texto gerado.
    Lista vazia = passou no filtro."""
    texto_lower = texto.lower()
    encontrados = [termo for termo in TERMOS_PROIBIDOS if termo in texto_lower]
    return encontrados
