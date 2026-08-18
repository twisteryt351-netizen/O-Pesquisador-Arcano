# ─────────────────────────────────────────────────────────────
#  MOTOR NARRATIVO — Diário Mágico de Derick de Souza
#  Substitui a lógica de "sorteio aleatório de bicho" por um
#  motor de progressão cronológica com estado persistente.
# ─────────────────────────────────────────────────────────────
import json
import os
import random
from datetime import date

ARQUIVO_ESTADO = "estado_mago.json"

# ─────────────────────────────────────────────────────────────
#  1. CONFIGURAÇÃO DAS FASES
#  Cada fase tem: faixa etária, ano-base de nascimento (1985),
#  e "brackets" de densidade narrativa (idade_min, idade_max,
#  salto_min_dias, salto_max_dias). O motor escolhe o salto
#  dentro do bracket correspondente à idade atual do personagem.
# ─────────────────────────────────────────────────────────────
ANO_NASCIMENTO = 1985
MES_NASCIMENTO = 2

# ─────────────────────────────────────────────────────────────
#  DIAL DE DENSIDADE NARRATIVA
#  Multiplica todos os saltos de dias. >1.0 = saltos MENORES =
#  MAIS posts = narrativa mais lenta/detalhada (mais "anos de
#  conteúdo diário"). <1.0 = o contrário.
#  1.0 ≈ 943 posts / ~2,6 anos publicando p/ a 1ª geração inteira.
#  2.5 ≈ ritmo bem mais denso, próximo dos "6 anos" cogitados.
#  Como o projeto prioriza PROFUNDIDADE e é um curso embutido no
#  diário (não uma corrida pra terminar), o padrão fica em 2.2 —
#  ritmo lento o bastante pra cada assunto (ex: cada mandamento,
#  cada religião visitada, cada grimório) render vários posts
#  seguidos em vez de ser mencionado e abandonado.
# ─────────────────────────────────────────────────────────────
DENSIDADE_GLOBAL = 2.2

FASES = {
    1: {
        "nome": "A Base — Catolicismo",
        "idade_inicio": 6,
        "idade_fim": 19,          # transição ocorre ao completar a Crisma, aos 19
        "marco_encerramento": "crisma_concluida",
        "brackets": [
            # (idade_min, idade_max, salto_min_dias, salto_max_dias)
            (0, 6,   90, 150),   # infância resumida — poucos posts
            (7, 12,  20, 40),    # catequese, 1ª comunhão — ritmo médio
            (13, 19, 8, 18),     # escola, paixonites, crisma — pico de detalhe
        ],
        "posts_estimados": 260,
    },
    2: {
        "nome": "O Luto e a Busca — Pluralidade Religiosa",
        "idade_inicio": 19,
        "idade_fim": 30,
        "marco_encerramento": "decepcao_religiosa_total",
        "brackets": [
            (19, 21, 5, 15),     # luto da avó, período mais intenso
            (22, 27, 8, 25),     # relacionamentos e religiões, ritmo médio
            (28, 30, 15, 40),    # desgaste final, ritmo acelera
        ],
        "posts_estimados": 180,
    },
    3: {
        "nome": "O Despertar — Ocultismo Bruto",
        "idade_inicio": 30,
        "idade_fim": 38,
        "marco_encerramento": "decide_buscar_ordem",
        "brackets": [
            (30, 38, 5, 20),
        ],
        "posts_estimados": 180,
    },
    4: {
        "nome": "A Ordem — Hermetismo Estruturado",
        "idade_inicio": 38,
        "idade_fim": 40,
        "marco_encerramento": "formatura_mago_hermetista",
        "brackets": [
            (38, 40, 5, 15),
        ],
        "posts_estimados": 60,
    },
    5: {
        "nome": "A Sabedoria e o Legado — O Sábio",
        "idade_inicio": 40,
        "idade_fim": None,        # fase aberta, sem idade limite
        "marco_encerramento": "discipulo_formado",
        "brackets": [
            (40, 999, 7, 90),
        ],
        "posts_estimados": None,  # indefinido
    },
}

# ─────────────────────────────────────────────────────────────
#  2. ESTADO INICIAL
# ─────────────────────────────────────────────────────────────
def estado_padrao():
    return {
        "personagem": "Derick de Souza",
        "autor_persona": "Twister",
        "geracao": 1,                     # 1 = Derick; 2 = discípulo; etc.
        "fase": 1,
        "dia_na_fase": 0,
        "post_numero_total": 0,
        "data_nascimento": f"{ANO_NASCIMENTO}-{MES_NASCIMENTO:02d}-01",
        "idade_atual": 0,
        "data_narrativa_atual": f"{ANO_NASCIMENTO}-{MES_NASCIMENTO:02d}-01",
        "marcos_concluidos": [],           # ex: "primeira_comunhao", "crisma_concluida"
        "relacoes": [],                    # nomes/contextos de pessoas importantes
        "religioes_exploradas": [],        # fase 2
        "obras_estudadas": [],             # livros/grimórios já citados (fase 3+)
        "poderes_dominados": [],           # orações, feitiços, técnicas já ensinadas
        "temas_recentes": [],              # anti-repetição de situações (janela deslizante)
        "titulos_recentes": [],            # anti-repetição de títulos SEO
        "ordem_iniciatica": None,          # preenchido na fase 4
        "discipulo_atual": None,           # preenchido no fim da fase 5
        "encerrado": False,
    }


def carregar_estado():
    if not os.path.exists(ARQUIVO_ESTADO):
        estado = estado_padrao()
        salvar_estado(estado)
        return estado
    with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────
#  3. MOTOR DE AVANÇO TEMPORAL
# ─────────────────────────────────────────────────────────────
def _bracket_atual(fase_cfg, idade):
    for idade_min, idade_max, salto_min, salto_max in fase_cfg["brackets"]:
        if idade_min <= idade <= idade_max:
            return salto_min, salto_max
    # fallback: último bracket
    _, _, salto_min, salto_max = fase_cfg["brackets"][-1]
    return salto_min, salto_max


def calcular_salto_dias(estado):
    """Sorteia quantos dias narrativos avançam neste post,
    respeitando a densidade da fase/idade atual."""
    fase_cfg = FASES[estado["fase"]]
    salto_min, salto_max = _bracket_atual(fase_cfg, estado["idade_atual"])
    salto_min = max(1, round(salto_min / DENSIDADE_GLOBAL))
    salto_max = max(salto_min, round(salto_max / DENSIDADE_GLOBAL))
    return random.randint(salto_min, salto_max)


def avancar_data(data_str, dias):
    d = date.fromisoformat(data_str)
    novo = date.fromordinal(d.toordinal() + dias)
    return novo.isoformat()


def calcular_idade(data_nascimento_str, data_atual_str):
    nasc = date.fromisoformat(data_nascimento_str)
    atual = date.fromisoformat(data_atual_str)
    idade = atual.year - nasc.year - (
        (atual.month, atual.day) < (nasc.month, nasc.day)
    )
    return idade


def verificar_transicao_fase(estado):
    """
    Retorna True se a fase deve avançar. A transição NÃO é só por
    idade — precisa que o marco de encerramento tenha sido marcado
    em `marcos_concluidos` (isso é setado pelo gerador de conteúdo
    quando o post do dia narra o evento culminante daquela fase).
    """
    fase_cfg = FASES[estado["fase"]]
    marco = fase_cfg["marco_encerramento"]
    idade_fim = fase_cfg["idade_fim"]

    idade_ok = (idade_fim is None) or (estado["idade_atual"] >= idade_fim)
    marco_ok = marco in estado["marcos_concluidos"]

    return idade_ok and marco_ok


def avancar_estado(estado):
    """Chamado ao FINAL de cada execução (depois de publicar o post)."""
    dias = calcular_salto_dias(estado)
    estado["data_narrativa_atual"] = avancar_data(estado["data_narrativa_atual"], dias)
    estado["idade_atual"] = calcular_idade(
        estado["data_nascimento"], estado["data_narrativa_atual"]
    )
    estado["dia_na_fase"] += 1
    estado["post_numero_total"] += 1

    if verificar_transicao_fase(estado):
        proxima_fase = estado["fase"] + 1
        if proxima_fase in FASES:
            print(f"🌗 Transição de fase: {FASES[estado['fase']]['nome']} → {FASES[proxima_fase]['nome']}")
            estado["fase"] = proxima_fase
            estado["dia_na_fase"] = 0
        else:
            # Fim da Fase 5 (Sábio) — ciclo se reinicia com o discípulo
            print("🔁 Ciclo completo! Iniciando nova geração pelo olhar do discípulo.")
            estado["geracao"] += 1
            estado["fase"] = 1
            estado["dia_na_fase"] = 0
            estado["marcos_concluidos"] = []
            estado["poderes_dominados"] = []  # discípulo recomeça o aprendizado
            # data de nascimento do discípulo fica a cargo da camada de prompt
            # (o mestre Derick pode reaparecer como personagem coadjuvante)

    return estado


# ─────────────────────────────────────────────────────────────
#  4. ANTI-REPETIÇÃO (janela deslizante, igual ao pets_diario.py)
# ─────────────────────────────────────────────────────────────
JANELA_TEMAS = 25
JANELA_TITULOS = 30


def registrar_tema(estado, tema):
    estado["temas_recentes"].append(tema)
    estado["temas_recentes"] = estado["temas_recentes"][-JANELA_TEMAS:]


def registrar_titulo(estado, titulo):
    estado["titulos_recentes"].append(titulo)
    estado["titulos_recentes"] = estado["titulos_recentes"][-JANELA_TITULOS:]


def registrar_marco(estado, marco):
    if marco not in estado["marcos_concluidos"]:
        estado["marcos_concluidos"].append(marco)
