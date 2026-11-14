"""
config.py — Configurações do Radar de Licitações.

É AQUI que você ajusta o robô sem mexer no resto do código:
  - quais estados (UF) monitorar
  - quais modalidades de contratação buscar
  - palavras-chave de cada nicho (e palavras que excluem falsos positivos)
  - limites de envio para o Telegram
"""

# ---------------------------------------------------------------------------
# PNCP (Portal Nacional de Contratações Públicas) — API pública de consulta
# ---------------------------------------------------------------------------
PNCP_BASE_URL = "https://pncp.gov.br/api/consulta"

# Endpoint de contratações publicadas. A API EXIGE dataInicial, dataFinal
# e codigoModalidadeContratacao — por isso consultamos modalidade por modalidade.
PNCP_ENDPOINT_PUBLICACAO = "/v1/contratacoes/publicacao"

# Itens por página (50 é o máximo aceito com segurança neste endpoint).
PNCP_TAMANHO_PAGINA = 50

# Pausa entre chamadas, para não sobrecarregar o portal (segundos).
PNCP_PAUSA_ENTRE_CHAMADAS = 0.4

# Códigos de modalidade da Lei 14.133 (tabela de domínio do PNCP):
#   4 = Concorrência eletrônica   6 = Pregão eletrônico   7 = Pregão presencial
#   8 = Dispensa de licitação    12 = Credenciamento (inclui chamadas públicas)
MODALIDADES = {
    6: "Pregão eletrônico",
    8: "Dispensa",
    4: "Concorrência eletrônica",
    7: "Pregão presencial",
    12: "Credenciamento",
}

# Estados monitorados. Deixe a lista VAZIA [] para monitorar o Brasil inteiro.
UFS = ["SP", "MG"]

# ---------------------------------------------------------------------------
# NICHOS — cada nicho vai para um canal próprio do Telegram.
#   palavras  -> basta UMA aparecer no objeto da licitação para entrar
#   excluir   -> se UMA aparecer, a licitação é descartada (falso positivo)
#   chat_env  -> nome do "segredo" (variável de ambiente) com o ID do canal
# A comparação ignora maiúsculas e acentos ("Gêneros" == "generos").
# ---------------------------------------------------------------------------
NICHOS = {
    "alimentacao": {
        "titulo": "🍎 Alimentação",
        "chat_env": "TELEGRAM_CHAT_ALIMENTACAO",
        "chat_padrao": "@uplicita_alimentos",  # canal público (usado se o segredo estiver vazio)
        "palavras": [
            "genero alimenticio", "generos alimenticios", "alimentacao escolar",
            "merenda", "pnae", "agricultura familiar", "hortifruti",
            "hortifrutigranjeiro", "frutas", "verduras", "legumes",
            "carne", "carnes", "frango", "pescado", "embutidos", "frios",
            "pao", "paes", "panificacao", "leite", "laticinio", "laticinios",
            "cafe", "acucar", "arroz", "feijao", "cesta basica", "cestas basicas",
            "refeicao", "refeicoes", "marmitex", "marmita", "quentinha",
            "lanche", "lanches", "coffee break", "alimentos", "alimenticio",
            "agua mineral", "estivas",
        ],
        "excluir": [
            "racao", "veterinari", "fonte de alimentacao", "alimentacao eletrica",
            "cabo de alimentacao", "nobreak", "alimentacao de dados",
            "cafeteira",
        ],
    },
    "construcao": {
        "titulo": "🧱 Material de Construção",
        "chat_env": "TELEGRAM_CHAT_CONSTRUCAO",
        "chat_padrao": "@up_licita_construcao",  # canal público (usado se o segredo estiver vazio)
        "palavras": [
            "material de construcao", "materiais de construcao",
            "material hidraulico", "materiais hidraulicos",
            "material eletrico", "materiais eletricos",
            "cimento", "areia", "brita", "pedra britada", "pedrisco",
            "tijolo", "tijolos", "bloco de concreto", "blocos de concreto",
            "bloco ceramico", "argamassa", "vergalhao", "vergalhoes",
            "ferragens", "ferragem", "tinta", "tintas", "madeira", "madeiras",
            "telha", "telhas", "tubos e conexoes", "tubo pvc", "tubos pvc",
            "piso", "pisos", "revestimento ceramico", "porcelanato",
            "concreto usinado", "massa asfaltica", "cbuq", "artefatos de cimento",
            "artefatos de concreto", "manilha", "manilhas", "bloquete",
            "paver", "pavers", "meio-fio", "cal hidratada", "esquadrias",
        ],
        "excluir": [
            "toner", "cartucho", "impressora", "tinta para carimbo",
            "execucao de obra", "execucao da obra", "piso salarial",
            "madeira apreendida",
        ],
    },
}

# ---------------------------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------------------------
TELEGRAM_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"

# Telegram limita ~20 mensagens/minuto no mesmo canal -> 3,1 s entre envios.
TELEGRAM_PAUSA_ENTRE_ENVIOS = 3.1

# Máximo de licitações enviadas individualmente por nicho em cada execução.
# O que passar disso vai num resumo final (evita "spam" no canal).
MAX_ENVIOS_POR_NICHO = 40

# ---------------------------------------------------------------------------
# ESTADO (memória do robô, para não repetir licitação já enviada)
# ---------------------------------------------------------------------------
ARQUIVO_ESTADO = "estado/vistos.json"
DIAS_GUARDAR_ESTADO = 45  # IDs mais antigos que isso são apagados
