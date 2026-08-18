# ─────────────────────────────────────────────────────────────
#  BIBLIOTECA DE CONTEÚDO — pools temáticos por fase da vida
#  de Derick. Cada pool alimenta o motor de anti-repetição e
#  o prompt engine. Estruturado para crescer: adicionar itens
#  aqui não exige tocar no motor_narrativo.py nem no prompt_engine.py.
# ─────────────────────────────────────────────────────────────

# ═════════════════════════════════════════════════════════════
#  FASE 1 — A BASE (CATOLICISMO)
# ═════════════════════════════════════════════════════════════

MANDAMENTOS = [
    {"n": 1, "texto": "Amar a Deus sobre todas as coisas",
     "mal_entendido": "Derick acha que significa amar Deus mais que a família, e sofre com a ideia até a avó explicar que é sobre prioridade de valores, não de afeto."},
    {"n": 2, "texto": "Não tomar o Santo Nome de Deus em vão",
     "mal_entendido": "Ele apanha um sabão da avó por usar o nome de Deus como interjeição de time de futebol perdendo."},
    {"n": 3, "texto": "Guardar domingos e festas de guarda",
     "mal_entendido": "Conflito real: o campeonato de várzea é sempre domingo de manhã, mesmo horário da missa."},
    {"n": 4, "texto": "Honrar pai e mãe",
     "mal_entendido": "Como ele é criado pela avó, ele reinterpreta esse mandamento em cima da própria estrutura familiar."},
    {"n": 5, "texto": "Não matar",
     "mal_entendido": "Confunde com regras esportivas ('matar' a bola no peito no futebol) — vira piada recorrente."},
    {"n": 6, "texto": "Não pecar contra a castidade",
     "mal_entendido": "Explicado de forma vaga e evasiva pela catequista, gera mais dúvida que resposta na pré-adolescência."},
    {"n": 7, "texto": "Não furtar",
     "mal_entendido": "Ele devolve um trocado a mais que recebeu na padaria e sente orgulho genuíno, episódio formador de caráter."},
    {"n": 8, "texto": "Não levantar falso testemunho",
     "mal_entendido": "Dilema real na escola: entregar ou não um colega que colou na prova."},
    {"n": 9, "texto": "Não desejar a mulher do próximo",
     "mal_entendido": "Mandamento que ele só entende de verdade muito mais tarde, na fase adulta."},
    {"n": 10, "texto": "Não cobiçar as coisas alheias",
     "mal_entendido": "O tênis de marca do colega rico da escola vira o símbolo desse mandamento pra ele."},
]

ORACOES_CATOLICAS = [
    {"nome": "Pai Nosso", "contexto": "primeira oração decorada, ensinada pela avó ainda no colo"},
    {"nome": "Ave Maria", "contexto": "decorada errado por anos até a catequista corrigir"},
    {"nome": "Credo", "contexto": "a mais difícil de decorar, cheia de palavras que ele não entende ainda"},
    {"nome": "Salve Rainha", "contexto": "aprendida nas novenas de maio, mês de Maria"},
    {"nome": "Ato de Contrição", "contexto": "decorada às pressas antes da primeira confissão"},
    {"nome": "Terço (Mistérios Gozosos/Dolorosos/Gloriosos)", "contexto": "rezado com a avó todo fim de tarde, ritual quase hipnótico da infância"},
]

SACRAMENTOS_MARCOS = [
    {"id": "batismo", "idade_tipica": 0, "descricao": "narrado por relato da avó, não como lembrança própria"},
    {"id": "primeira_confissao", "idade_tipica": 7, "descricao": "pavor da primeira confissão, medo de esquecer um pecado"},
    {"id": "primeira_comunhao", "idade_tipica": 8, "descricao": "marco emocional forte, roupa branca, festa simples no salão paroquial"},
    {"id": "crisma_concluida", "idade_tipica": 19, "descricao": "conclusão simbólica da infância religiosa — marco de ENCERRAMENTO DA FASE 1"},
]

EVENTOS_LITURGICOS = [
    "Missa dominical comum, com a rotina de sempre",
    "Quaresma e o desafio pessoal de abrir mão de algo",
    "Semana Santa — Quinta-feira Santa, Sexta da Paixão, Páscoa",
    "Festa Junina da paróquia, arraiá com quermesse",
    "Novena de Natal e a Missa do Galo",
    "Mês de Maria (maio) com suas novenas diárias",
    "Corpus Christi e o tapete de serragem colorida na rua",
    "Festa do padroeiro do bairro",
]

FIGURAS_RELIGIOSAS_F1 = [
    "Nossa Senhora Aparecida", "Santa Terezinha do Menino Jesus",
    "Santo Antônio (o casamenteiro)", "São Jorge (ainda sem a camada sincrética que ele só vai entender na Fase 2)",
    "São Miguel Arcanjo (citado de leve na infância, vai retornar com força na Fase 5)",
]

VIDA_AVO = [
    "A avó reza o terço durante o jogo do Brasil e pede silêncio total na sala",
    "A avó benze a casa com um raminho de arruda e reza baixinho contra o 'olho gordo'",
    "A avó guarda uma imagem de santo debaixo do colchão de Derick 'pra proteção'",
    "A avó conta uma história de aparição/milagre que ela jura ter presenciado",
    "A avó ensina uma simpatia caseira 'não é bruxaria, é bênção', gerando confusão categorial que só faz sentido pra Derick anos depois",
    "A avó reclama de vizinha que 'anda com gente de macumba', plantando o primeiro preconceito que ele vai desconstruir na vida adulta",
]

VIDA_ESCOLA_F1 = [
    "Prova de matemática difícil e a pressão de tirar nota boa",
    "Primeira paixonite de sala de aula, bilhetinho, coração na primeira página do caderno",
    "Briga boba com o melhor amigo por causa de figurinha/bafo/campeonato de bolinha de gude",
    "Professora dura que humilha aluno na frente da turma",
    "Trabalho em grupo em que ele carrega o grupo inteiro sozinho",
    "Descoberta de um desenho/anime novo que vira obsessão da turma inteira",
]

REFERENCIAS_POP_F1 = [
    {"obra": "Cavaleiros do Zodíaco (Saint Seiya)", "janela_anos": (1994, 1996),
     "nota": "primeiro contato com a ideia de signos, constelações e 'armaduras' — sem entender ainda o simbolismo, só a emoção"},
    {"obra": "Desenhos de sábado de manhã em geral", "janela_anos": (1992, 1998), "nota": "pano de fundo cultural da infância"},
    {"obra": "Rádio AM da avó com programa de novena", "janela_anos": (1985, 2004), "nota": "trilha sonora doméstica constante"},
]

ANGULOS_REFLEXAO_F1 = [
    "Dúvida ingênua: 'Deus me vê o tempo todo mesmo escondido no banheiro?'",
    "Comparação entre o que a catequista ensina e o que ele vê os adultos realmente fazerem",
    "Pequena crise de consciência depois de mentir e não contar na confissão",
    "A sensação estranha e nova de rezar sozinho, sem ninguém mandar",
    "Percepção infantil de que a igreja tem 'gente boa fingindo' e 'gente boa de verdade' — e ele tenta entender a diferença",
]


# ═════════════════════════════════════════════════════════════
#  FASE 2 — O LUTO E A BUSCA (PLURALIDADE RELIGIOSA)
# ═════════════════════════════════════════════════════════════

LUTO_AVO_ETAPAS = [
    "O período final da doença da avó, e a impotência de vê-la fraquejar",
    "O dia da morte — narrado com delicadeza, sem melodrama gratuito",
    "O velório e o choque de ver a comunidade da igreja toda reunida",
    "As primeiras semanas sem ela, a casa estranhamente silenciosa sem o terço das 18h",
    "Encontrar objetos dela meses depois (terço, novena, caderno de receita) e o luto que volta em onda",
    "A primeira vez que ele reza sozinho depois da morte dela, e percebe que não sabe mais em que acredita",
]

RELACIONAMENTOS_F2 = [
    {"nome": "Fernanda", "religiao_introduzida": "Evangélico (Assembleia de Deus)",
     "contexto": "colega de trabalho no primeiro emprego, o convida pro culto de jovens"},
    {"nome": "Camila", "religiao_introduzida": "Evangélico (Igreja Lagoinha)",
     "contexto": "conhecida numa festa, estilo de culto mais contemporâneo e musical o surpreende"},
    {"nome": "Ana Paula", "religiao_introduzida": "Umbanda",
     "contexto": "vizinha nova que o convida pra um terreiro, ele vai com o preconceito da avó na cabeça e sai de lá confuso"},
    {"nome": "Priscila", "religiao_introduzida": "Kardecismo (Espiritismo)",
     "contexto": "conhece num centro espírita que ela frequenta, se impressiona com a passe e a doutrina da reencarnação"},
    {"nome": "Bianca", "religiao_introduzida": "Budismo",
     "contexto": "professora de ioga que pratica budismo tibetano, ele experimenta meditação pela primeira vez"},
    {"nome": "Sarah", "religiao_introduzida": "Judaísmo",
     "contexto": "colega de faculdade/curso, ele é convidado a um Shabat em família"},
    {"nome": "Yasmin", "religiao_introduzida": "Islamismo",
     "contexto": "conhecida por app/amigos em comum, aprende sobre as 5 orações diárias e o Ramadã"},
    {"nome": "Verônica", "religiao_introduzida": "Adventismo",
     "contexto": "colega que guarda o sábado, ele aprende a diferença entre adventismo e outras vertentes protestantes"},
    {"nome": "Marina (reencontro)", "religiao_introduzida": "Candomblé/Quimbanda",
     "contexto": "reencontra uma amiga de infância que hoje é filha de santo, e ele revisita seu próprio preconceito herdado"},
]

RELIGIOES_PERFIS = {
    "evangelico_variantes": [
        "Assembleia de Deus (tradicional, culto extenso, ênfase em dons do Espírito)",
        "Igreja Lagoinha (contemporânea, música de louvor estilo banda, público jovem)",
        "Deus é Amor (rigor comportamental forte, estética mais sóbria)",
        "Batista (ênfase no estudo bíblico sistemático)",
        "Presbiteriana (mais litúrgica, tradição reformada, calvinismo)",
    ],
    "umbanda": "religião afro-brasileira sincrética, giras, orixás, entidades (caboclos, pretos-velhos, exus de linha), pontos cantados",
    "quimbanda": "vertente distinta da umbanda, culto aos exus e pombagiras com abordagem própria",
    "candomble": "religião de matriz africana, culto aos orixás, terreiros, iniciação (feitura de santo)",
    "kardecismo": "doutrina espírita codificada por Allan Kardec, reencarnação, mediunidade, 'O Livro dos Espíritos'",
    "budismo": "as Quatro Nobres Verdades, meditação (zazen/vipassana), impermanência, desapego",
    "adventismo": "guarda do sábado, ênfase escatológica, saúde e estilo de vida",
    "vudu": "religião afro-caribenha (raízes haitianas/oeste-africanas), loas, sincretismo com catolicismo",
    "islamismo": "os 5 pilares, orações diárias (salat), Ramadã, o Alcorão",
    "judaismo": "Torá, Shabat, festas (Pessach, Yom Kipur), tradição rabínica",
}

ANGULOS_REFLEXAO_F2 = [
    "Choque cultural real na primeira visita a um culto/terreiro/centro diferente",
    "Comparação honesta entre o que essa religião promete e o que o catolicismo prometia",
    "A sensação (ou ausência dela) de algo 'sobrenatural' acontecendo no ritual",
    "Culpa residual católica por estar 'traindo' a fé da avó",
    "Percepção de que cada religião resolve uma dor específica que ele carrega",
    "O relacionamento esfria ou termina, e a pergunta que fica: 'era fé ou era ela que eu buscava?'",
]


# ═════════════════════════════════════════════════════════════
#  FASE 3 — O DESPERTAR (OCULTISMO BRUTO)
# ═════════════════════════════════════════════════════════════

OBRAS_OCULTAS = [
    {"titulo": "Livro de São Cipriano", "nota": "grimório de tradição popular ibérica/brasileira, sincretismo entre catolicismo popular e magia; ponto de entrada natural pra quem vem de formação católica"},
    {"titulo": "Ars Goetia (parte da Lemegeton / Chave Menor de Salomão)", "nota": "catálogo dos 72 espíritos, selos e hierarquias — tratado com respeito histórico, sem incentivar evocação real de entidades hostis"},
    {"titulo": "Grimório Verum", "nota": "grimório francês do séc. XVIII, lista de espíritos e pactos — abordado como objeto de estudo histórico"},
    {"titulo": "As Clavículas de Salomão", "nota": "um dos grimórios mais influentes da tradição salomônica"},
    {"titulo": "Tábua de Esmeralda (atribuída a Hermes Trismegisto)", "nota": "'Assim como é em cima, é embaixo' — texto fundacional do hermetismo"},
    {"titulo": "O Testamento de Salomão", "nota": "texto pseudoepígrafo antigo, relação de Salomão com demônios subjugados"},
    {"titulo": "Helena Blavatsky — Ísis sem Véu / A Doutrina Secreta", "nota": "fundadora da Teosofia, síntese entre esoterismo ocidental e filosofias orientais"},
    {"titulo": "Samuel Liddell MacGregor Mathers", "nota": "fundador da Ordem Hermética da Aurora Dourada (Golden Dawn), tradutor de grimórios"},
    {"titulo": "Samuel Aun Weor", "nota": "fundador do movimento gnóstico moderno latino-americano"},
    {"titulo": "Aleister Crowley — Magick in Theory and Practice / Liber AL vel Legis", "nota": "figura controversa, fundador da Thelema — tratado criticamente, sem endosso das partes mais transgressoras de sua biografia"},
    {"titulo": "O Livro Sagrado da Magia de Abramelin", "nota": "método de longa purificação e contato com o 'Anjo Guardião' — citado como referência histórica, sem instrução literal de ritual completo"},
    {"titulo": "Tratados de Demonologia (tradição salomônica e renascentista)", "nota": "estudo classificatório, não invocação prática"},
    {"titulo": "Angelologia (hierarquias angélicas, Pseudo-Dionísio)", "nota": "coros angélicos, futura ponte pro Ritual de São Miguel na Fase 5"},
    {"titulo": "Tradição dos Jinns (folclore e teologia islâmica)", "nota": "paralelo cultural que Derick estuda por curiosidade comparada, sem apropriação rasa"},
]

PRATICAS_F3 = [
    "Simpatia popular caseira (ex: para atrair prosperidade, para 'limpar' energia da casa)",
    "Defumação com ervas (arruda, alecrim, sálvia) — ritual de limpeza energética",
    "Banho de ervas ritualístico",
    "Primeira tentativa de meditação com foco em visualização",
    "Experimento de sensibilização com vela e respiração (sem invocação de entidade)",
    "Tentativa de leitura de tarot com baralho comum de cartas (baralho cigano)",
    "Diário de sonhos como ferramenta de autoconhecimento simbólico",
]

RESULTADOS_EXPERIMENTOS = [
    "deu certo de um jeito que ele não sabe explicar racionalmente",
    "não deu em nada, e ele questiona se fez algo errado ou se é tudo sugestão",
    "sentiu algo físico (arrepio, frio na sala, sensação de presença) que o assustou",
    "percebeu uma coincidência forte demais pra ignorar, mas nem por isso vira crente cego",
    "terminou frustrado e mais cético do que quando começou",
]

ANGULOS_REFLEXAO_F3 = [
    "A tensão entre ceticismo racional e a vontade de acreditar",
    "Comparação entre o que os livros prometem e o que ele de fato sente/vive",
    "A solidão de estudar sem mestre, sem ordem, só com livros e fóruns/internet",
    "Primeira vez que ele entende magia como PSICOLOGIA aplicada, não como 'mundo paralelo'",
    "O medo real de estar mexendo com algo que ele não entende direito",
]


# ═════════════════════════════════════════════════════════════
#  FASE 4 — A ORDEM (HERMETISMO ESTRUTURADO)
# ═════════════════════════════════════════════════════════════

ORDEM_INFO = {
    "nome": "Nosso Templo BH",
    "bairro": "Glória, Belo Horizonte",
    "fundador_referencia": "Nino Denani Grão Mago mestre do fogo, um mago conhecido da cena de ocultismo no YouTube/internet, Fundador do nosso templo SP (Matriz)",
    "ano_abertura_filial": 2024,
}

PERSONAGENS_ORDEM = [
    {"nome": "Regulus", "papel": "mago do Caos, referência técnica em Goétia"},
    {"nome": "Frater A", "papel": "figura descontraida e enigmática, fala muito mas ensina muito nas entrelinhas"},
    {"nome": "Pracy", "papel": "Mestre Maga, forte em alquimia prática, professora de tarot, uma das fundadoras do Nosso templo SP (matriz)"},
    {"nome": "O Mago do Escritório", "papel": "apelido carinhoso de um colega que concilia magia com vida corporativa, um dos fundadores do nosso templo BH"},
    {"nome": "A Maga Sofia", "papel": "referência em astrologia e tarologa, uma das fundadoras do nosso templo BH"},
    {"nome": "O Mago Xamã Wesley", "papel": "traz influência de xamanismo e práticas de vivencias/jornada"},
    {"nome": "O Mago Nórdico Walter", "papel": "especialista em assunça arquetipica e tradição nórdica, colega de turma"},
    {"nome": "A Maga Rafa", "papel": "colega manipulção energetica, fogo azul, colega de turma"},
    {"nome": "O Rafa Zen", "papel": "famoso mago do caos, aparece nas resenhas do nosso templo BH"},
]

CURRICULO_ORDEM = [
    "Fundamentos do Hermetismo (os 7 princípios herméticos / Cybalion)",
    "Cabala prática (Árvore da Vida, sephirot)",
    "Alquimia (simbólica, como processo de transformação interior)",
    "Tarot como sistema simbólico completo",
    "Hermetismo pratico e no dia a dia",
    "meditação sobre os quatros elementos"
    "Manipulação energética",
    "Assunção Arquetipa (Assunção forma Deus)",
    "Abertura do ciruculo sagrado",
    "Meditação da vela",
    "meditação do palácio astral(como construir um palácio astral)",
    "Astrologia aplicada à prática mágica",
    "Ritual cerimonial (estrutura, ferramentas, elementos)",
    "Ética mágica — o tema mais debatido em sala",
    "Meditação e desenvolvimento da vontade",
    "Visão remota",
    "Percepção sensorial",
    "Sagrado Anjo Guardião, Abramelin",
    "os segredos da iniciação",
    "Formação de um Mago",
]

MARCOS_ORDEM = [
    "workshop_inicial", "matricula_curso", "primeiro_ritual_em_grupo",
    "prova_intermediaria", "formatura_mago_hermetista",
]

ANGULOS_REFLEXAO_F4 = [
    "A alegria genuína de finalmente ter pares que entendem do que ele fala",
    "O choque de descobrir que magia estruturada é mais disciplina que mistério",
    "Debate ético em sala sobre até onde vai a responsabilidade do mago",
    "A diferença entre o que ele aprendeu sozinho (Fase 3) e o que a Ordem corrige/refina",
    "Amizades reais nascendo dentro da Ordem — sensação de comunidade que faltava desde a igreja da infância",
]


# ═════════════════════════════════════════════════════════════
#  FASE 5 — A SABEDORIA E O LEGADO (O SÁBIO)
# ═════════════════════════════════════════════════════════════

PRATICAS_AVANCADAS_F5 = [
    {"nome": "Visão Remota", "nota": "técnica de percepção extrassensorial estudada inclusive por programas militares (Stargate Project, domínio público histórico)"},
    {"nome": "Espelho Negro", "nota": "ferramenta de escrying, tradição que remonta a John Dee"},
    {"nome": "Espelho da Alma", "nota": "prática reflexiva de autoconhecimento profundo via meditação especular"},
    {"nome": "Incorporação", "nota": "tratada com respeito e cautela, contextualizada dentro de tradições mediúnicas específicas"},
    {"nome": "Assunção Arquetípica", "nota": "técnica de 'vestir' um arquétipo (deidade/força) pra incorporar suas qualidades simbolicamente"},
    {"nome": "Controle e Manipulação Mental (uso ético)", "nota": "sempre enquadrado como autocontrole e comunicação persuasiva ética — nunca como coerção de terceiros"},
    {"nome": "Fogo Azul", "nota": "prática ritualística de purificação/proteção energética"},
    {"nome": "Fogo Roxo", "nota": "prática associada à transmutação (referência à 'chama violeta' de tradições teosóficas/ascensão)"},
    {"nome": "Ritual de São Miguel Arcanjo", "nota": "oração de proteção católica que ganha camada mágica reinterpretada — fechando o círculo com a Fase 1"},
    {"nome": "Tarot avançado (leituras complexas, cruz celta)", "nota": ""},
    {"nome": "Baralho Cigano avançado", "nota": ""},
]

ETICA_ENSINAMENTOS_F5 = [
    "Feitiço de amor é pra atrair o que é recíproco, nunca pra escravizar a vontade alheia",
    "Magia de defesa se ensina pra proteção, nunca como incentivo a ataque não provocado",
    "Muitas vezes o ato mágico mais poderoso é o desapego, não a manipulação",
    "O verdadeiro poder de um mago está no autocontrole, não no controle dos outros",
    "Todo ensinamento vem com o alerta: liberdade e responsabilidade andam juntas",
]

BUSCA_DISCIPULO_ETAPAS = [
    "Primeiros alunos que aparecem mas não têm o comprometimento certo",
    "Encontros decepcionantes com pessoas atrás de atalho, não de caminho",
    "O primeiro sinal genuíno de potencial em alguém",
    "A decisão de aceitar o discípulo e começar a repassar o legado",
    "As primeiras lições ensinadas, revisitando a própria trajetória através dos olhos de quem ensina",
]

CULTURA_POP_SIMBOLOGIA_F5 = [
    {"obra": "Cavaleiros do Zodíaco", "simbolismo": "as 12 casas zodiacais e as armaduras de ouro como arquétipos planetários; a armadura de Fênix e a ressurreição como analogia pra transmutação alquímica"},
    {"obra": "O Senhor dos Anéis", "simbolismo": "a jornada do herói campbelliana explícita; Gandalf como arquétipo do Mago/Ancião Sábio; o Anel como símbolo do apego e da vontade de poder"},
    {"obra": "A Cabana (William P. Young)", "simbolismo": "reinterpretação simbólica da Trindade e do perdão como processo iniciático de cura"},
    {"obra": "Matrix", "simbolismo": "alegoria gnóstica quase literal — o mundo como véu (Maya) e o despertar (gnose) como libertação"},
    {"obra": "Star Wars", "simbolismo": "dualismo Luz/Sombra, a Força como equivalente pop de um campo energético universal"},
    {"obra": "Harry Potter", "simbolismo": "estrutura de escola iniciática, varinhas como ferramentas de foco de vontade (paralelo com a varinha mágica cerimonial real)"},
]


# ═════════════════════════════════════════════════════════════
#  FILTRO ÉTICO — checagem pós-geração (camada de segurança em código,
#  além da instrução já embutida no prompt)
# ═════════════════════════════════════════════════════════════
TERMOS_PROIBIDOS = [
    "sacrifício animal", "sacrifício de animal", "sacrificar um animal",
    "sacrifício humano", "sacrificar uma pessoa",
    "magia sexual", "rito sexual", "sexo ritual",
    "beber sangue", "oferenda de sangue", "usar sangue do", "corte ritual",
    "fazer mal a", "amaldiçoar uma criança", "magia negra para matar",
]
