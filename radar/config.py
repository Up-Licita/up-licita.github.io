"""
config.py — Configurações do Radar de Licitações.

É AQUI que se ajusta o robô sem mexer no resto do código:
  - abrangência (estados) e modalidades
  - segmentos (palavras-chave) e quais têm canal no Telegram
  - endereço do site
"""

# ---------------------------------------------------------------------------
# SITE
# ---------------------------------------------------------------------------
SITE_NOME = "Radar de Licitações"
SITE_URL = "https://guilhermemoraesss.github.io/radar-licitacoes"  # sem barra no fim
PASTA_SITE = "_site"
MAX_PAGINAS_DETALHE = 50000  # trava de segurança contra site gigante

# ---------------------------------------------------------------------------
# PNCP (Portal Nacional de Contratações Públicas) — API pública de consulta
# ---------------------------------------------------------------------------
PNCP_BASE_URL = "https://pncp.gov.br/api/consulta"

# Contratações com prazo de proposta ABERTO. Exige só "dataFinal" (data-limite
# de encerramento); a modalidade é opcional, mas consultamos uma a uma para
# dividir o volume.
PNCP_ENDPOINT_PROPOSTA = "/v1/contratacoes/proposta"
DIAS_A_FRENTE = 60          # licitações que encerram em até X dias
PNCP_TAMANHO_PAGINA = 50
PNCP_PAUSA_ENTRE_CHAMADAS = 0.25

# Códigos de modalidade da Lei 14.133 (tabela de domínio do PNCP)
MODALIDADES = {
    6: "Pregão eletrônico",
    8: "Dispensa",
    4: "Concorrência eletrônica",
    7: "Pregão presencial",
    12: "Credenciamento",
    5: "Concorrência presencial",
}

# Estados monitorados. Lista VAZIA = Brasil inteiro.
UFS = []

UF_NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia",
    "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe",
    "TO": "Tocantins",
}

# ---------------------------------------------------------------------------
# SEGMENTOS
#   A ordem importa: o PRIMEIRO segmento que casar vira o segmento "principal"
#   da licitação no site. (No Telegram, ela vai para todos os canais que casarem.)
#   palavras -> basta UMA aparecer no objeto   |   excluir -> descarta
#   chat_padrao -> canal do Telegram (só segmentos com canal recebem alertas)
#   A comparação ignora maiúsculas e acentos e usa palavras inteiras.
# ---------------------------------------------------------------------------
SEGMENTOS = {
    "alimentacao": {
        "titulo": "Alimentação",
        "emoji": "🍎",
        "chat_env": "TELEGRAM_CHAT_ALIMENTACAO",
        "chat_padrao": "@uplicita_alimentos",
        "palavras": [
            "genero alimenticio", "generos alimenticios", "alimentacao escolar",
            "merenda", "pnae", "agricultura familiar", "hortifruti",
            "hortifrutigranjeiro", "hortifrutigranjeiros", "frutas", "verduras",
            "legumes", "carne", "carnes", "frango", "pescado", "embutidos", "frios",
            "pao", "paes", "panificacao", "leite", "laticinio", "laticinios",
            "cafe", "acucar", "arroz", "feijao", "cesta basica", "cestas basicas",
            "refeicao", "refeicoes", "marmitex", "marmita", "quentinha",
            "lanche", "lanches", "coffee break", "alimentos", "alimenticio",
            "alimenticios", "agua mineral", "estivas",
        ],
        "excluir": [
            "racao", "veterinari", "fonte de alimentacao", "alimentacao eletrica",
            "cabo de alimentacao", "nobreak", "alimentacao de dados", "cafeteira",
        ],
    },
    "material-de-construcao": {
        "titulo": "Material de construção",
        "emoji": "🧱",
        "chat_env": "TELEGRAM_CHAT_CONSTRUCAO",
        "chat_padrao": "@up_licita_construcao",
        "palavras": [
            "material de construcao", "materiais de construcao",
            "material hidraulico", "materiais hidraulicos",
            "material eletrico", "materiais eletricos",
            "cimento", "areia", "brita", "pedra britada", "pedrisco",
            "tijolo", "tijolos", "bloco de concreto", "blocos de concreto",
            "bloco ceramico", "argamassa", "vergalhao", "vergalhoes",
            "ferragens", "ferragem", "tinta", "tintas", "madeira", "madeiras",
            "telha", "telhas", "tubos e conexoes", "tubo pvc", "tubos pvc",
            "revestimento ceramico", "porcelanato", "concreto usinado",
            "massa asfaltica", "cbuq", "artefatos de cimento", "artefatos de concreto",
            "manilha", "manilhas", "bloquete", "paver", "pavers", "meio-fio",
            "cal hidratada", "esquadrias",
        ],
        "excluir": [
            "toner", "cartucho", "impressora", "tinta para carimbo",
            "execucao de obra", "execucao da obra", "piso salarial",
            "madeira apreendida",
        ],
    },
    "obras-e-engenharia": {
        "titulo": "Obras e engenharia", "emoji": "🏗️",
        "palavras": [
            "execucao de obra", "execucao da obra", "execucao de obras", "reforma",
            "reformas", "ampliacao", "pavimentacao", "recapeamento", "construcao de",
            "servicos de engenharia", "servico de engenharia", "drenagem",
            "terraplenagem", "obra de", "obras de",
        ],
        "excluir": ["reforma de estofados"],
    },
    "saude": {
        "titulo": "Saúde e hospitalar", "emoji": "🩺",
        "palavras": [
            "medicamento", "medicamentos", "material medico", "materiais medicos",
            "medico hospitalar", "medico-hospitalar", "hospitalar", "hospitalares",
            "odontologico", "odontologicos", "insumos de saude", "laboratorial",
            "laboratoriais", "exames", "farmaceutico", "farmacia", "seringas",
            "luvas de procedimento", "equipamentos medicos", "ortese", "proteses",
        ],
        "excluir": ["veterinari"],
    },
    "limpeza-e-higiene": {
        "titulo": "Limpeza e higiene", "emoji": "🧽",
        "palavras": [
            "material de limpeza", "materiais de limpeza", "produtos de limpeza",
            "higiene", "higienizacao", "saneantes", "papel higienico", "papel toalha",
            "detergente", "desinfetante", "sabonete", "alcool em gel", "sacos de lixo",
            "saco de lixo", "limpeza e conservacao", "servicos de limpeza",
        ],
        "excluir": ["limpeza de fossa", "limpeza urbana"],
    },
    "tecnologia": {
        "titulo": "Tecnologia e informática", "emoji": "💻",
        "palavras": [
            "computador", "computadores", "notebook", "notebooks", "informatica",
            "software", "softwares", "licenca de uso", "licencas", "impressora",
            "impressoras", "toner", "cartucho", "cartuchos", "servidor", "servidores",
            "rede logica", "switch", "nobreak", "tablet", "tablets", "monitor",
            "monitores", "sistema de gestao", "solucao tecnologica", "internet",
            "link de dados", "telefonia",
        ],
        "excluir": [],
    },
    "veiculos-e-combustivel": {
        "titulo": "Veículos e combustível", "emoji": "🚗",
        "palavras": [
            "veiculo", "veiculos", "ambulancia", "ambulancias", "onibus", "caminhao",
            "caminhoes", "motocicleta", "pneu", "pneus", "pecas automotivas",
            "autopecas", "combustivel", "combustiveis", "gasolina", "diesel", "etanol",
            "lubrificantes", "manutencao veicular", "manutencao preventiva e corretiva de veiculos",
            "locacao de veiculos", "frota",
        ],
        "excluir": [],
    },
    "escritorio-e-escolar": {
        "titulo": "Escritório e material escolar", "emoji": "✏️",
        "palavras": [
            "material de expediente", "materiais de expediente", "papelaria",
            "material escolar", "materiais escolares", "kit escolar", "kits escolares",
            "papel a4", "papel sulfite", "material de escritorio",
            "material pedagogico", "materiais pedagogicos", "livros", "livro didatico",
        ],
        "excluir": [],
    },
    "moveis-e-eletro": {
        "titulo": "Móveis e eletrodomésticos", "emoji": "🪑",
        "palavras": [
            "mobiliario", "moveis", "cadeira", "cadeiras", "mesa", "mesas",
            "armario", "armarios", "estante", "estantes", "eletrodomestico",
            "eletrodomesticos", "ar condicionado", "ar-condicionado", "condicionadores de ar",
            "geladeira", "refrigerador", "freezer", "fogao", "bebedouro", "bebedouros",
            "ventilador", "ventiladores", "eletroeletronicos",
        ],
        "excluir": [],
    },
    "uniformes-e-epi": {
        "titulo": "Uniformes e EPIs", "emoji": "🦺",
        "palavras": [
            "uniforme", "uniformes", "fardamento", "fardamentos", "vestuario",
            "camiseta", "camisetas", "calcado", "calcados", "botina", "botinas",
            "epi", "epis", "equipamento de protecao individual",
            "equipamentos de protecao individual", "enxoval", "roupas",
        ],
        "excluir": [],
    },
    "servicos-e-eventos": {
        "titulo": "Serviços e eventos", "emoji": "🎪",
        "palavras": [
            "evento", "eventos", "locacao de", "transporte escolar", "vigilancia",
            "seguranca patrimonial", "grafica", "graficos", "impressos", "buffet",
            "sonorizacao", "palco", "tendas", "show", "shows", "consultoria",
            "assessoria", "treinamento", "capacitacao", "publicidade", "manutencao",
        ],
        "excluir": [],
    },
    "agro-e-meio-ambiente": {
        "titulo": "Agro e meio ambiente", "emoji": "🌱",
        "palavras": [
            "sementes", "mudas", "adubo", "adubos", "fertilizante", "fertilizantes",
            "calcario", "insumos agricolas", "racao", "defensivos", "maquinas agricolas",
            "trator", "tratores", "roçada", "rocada", "jardinagem", "paisagismo",
            "coleta de lixo", "residuos solidos", "aterro",
        ],
        "excluir": [],
    },
}

SEGMENTO_OUTROS = {"titulo": "Outros", "emoji": "📋"}

# Segmentos que têm canal no Telegram (recebem alertas)
NICHOS = {k: v for k, v in SEGMENTOS.items() if v.get("chat_padrao") or v.get("chat_env")}

# ---------------------------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------------------------
TELEGRAM_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_PAUSA_ENTRE_ENVIOS = 3.1   # ~20 mensagens/min no mesmo canal
MAX_ENVIOS_POR_NICHO = 30           # posts individuais por execução; o resto vai num resumo
DIAS_NOVIDADE = 3                   # só alerta licitações publicadas nos últimos X dias

# ---------------------------------------------------------------------------
# ESTADO (memória do robô)
# ---------------------------------------------------------------------------
ARQUIVO_ESTADO = "estado/vistos.json"
DIAS_GUARDAR_ESTADO = 45
