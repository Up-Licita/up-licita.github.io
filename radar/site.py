"""
site.py — Gera o site estático (HTML) com todas as licitações abertas.

Páginas geradas a cada execução, do zero, em config.PASTA_SITE:
  index.html                         página inicial (busca, prazos curtos, segmentos, estados)
  busca.html                         busca com filtros (JavaScript, lê dados/*.json)
  licitacao/<...>.html               uma página por licitação
  estado/<uf>.html, estado/<uf>/<cidade>.html
  segmento/<seg>.html, segmento/<seg>/<uf>.html
  alertas.html, sobre.html, 404.html, sitemap*.xml, robots.txt, dados/*.json

Só usa campos que o PNCP devolve; nada é inventado.
"""

import html
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime

from radar import config, filtro, urls
from radar.formatacao import moeda, data_br

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site_assets")
e = html.escape


# ---------------------------------------------------------------------------
# Preparação dos dados
# ---------------------------------------------------------------------------
def _dt(valor):
    try:
        return datetime.fromisoformat(str(valor)[:19]) if valor else None
    except ValueError:
        return None


def preparar(itens: list[dict], agora: datetime) -> list[dict]:
    """Normaliza as licitações abertas num formato único para o site."""
    regs = []
    for it in itens:
        if not filtro.prazo_aberto(it, agora):
            continue
        un = it.get("unidadeOrgao") or {}
        org = it.get("orgaoEntidade") or {}
        uf = (un.get("ufSigla") or "").upper()
        if uf not in config.UF_NOMES:
            continue
        segs = filtro.classificar(it)
        regs.append({
            "raw": it,
            "url": urls.pagina_licitacao(it),
            "objeto": (it.get("objetoCompra") or "").strip() or "Objeto não informado",
            "orgao": org.get("razaoSocial") or "",
            "unidade": un.get("nomeUnidade") or "",
            "cidade": un.get("municipioNome") or "",
            "uf": uf,
            "segs": segs,
            "seg": segs[0] if segs else "outros",
            "valor": it.get("valorTotalEstimado"),
            "fim": _dt(it.get("dataEncerramentoProposta")),
            "inicio": _dt(it.get("dataAberturaProposta")),
            "modalidade": it.get("modalidadeNome") or "",
        })
    regs.sort(key=lambda r: r["fim"] or datetime.max)
    return regs[: config.MAX_PAGINAS_DETALHE]


def seg_info(seg: str) -> dict:
    return config.SEGMENTOS.get(seg, config.SEGMENTO_OUTROS)


def seg_titulo(seg: str) -> str:
    return seg_info(seg)["titulo"]


def canal_do_segmento(seg: str) -> str | None:
    s = config.SEGMENTOS.get(seg) or {}
    return s.get("chat_padrao")


def canais() -> list[tuple[str, str, str]]:
    """(segmento, título, @canal) de todos os segmentos com canal público."""
    return [(k, v["titulo"], v["chat_padrao"]) for k, v in config.SEGMENTOS.items() if v.get("chat_padrao")]


def prazo_texto(fim: datetime | None, agora: datetime) -> tuple[str, str]:
    """Texto curto do prazo e a 'classe' visual (urgente, breve, normal)."""
    if not fim:
        return "Prazo não informado", "normal"
    delta = fim - agora
    dias = delta.days
    if delta.total_seconds() < 86400:
        horas = max(1, int(delta.total_seconds() // 3600))
        return f"Encerra em {horas} h", "urgente"
    if dias == 1:
        return "Encerra amanhã", "urgente"
    if dias <= 5:
        return f"Encerra em {dias} dias", "breve"
    return f"Encerra em {fim.strftime('%d/%m')}", "normal"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def _raiz(caminho: str) -> str:
    return "../" * caminho.count("/")


def _raiz_absoluta() -> str:
    """Caminho do site no servidor, ex.: '/radar-licitacoes/'."""
    from urllib.parse import urlparse
    return (urlparse(config.SITE_URL).path.rstrip("/") or "") + "/"


def layout(caminho: str, titulo: str, descricao: str, corpo: str, migalhas=None,
           noindex: bool = False, raiz: str | None = None) -> str:
    r = raiz if raiz is not None else _raiz(caminho)
    canonical = urls.absoluta(caminho if caminho != "index.html" else "")
    ld = ""
    if migalhas:
        ld_itens = [{"@type": "ListItem", "position": i + 1, "name": nome,
                     "item": urls.absoluta(link) if link else canonical}
                    for i, (nome, link) in enumerate(migalhas)]
        ld = ('<script type="application/ld+json">'
              + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                            "itemListElement": ld_itens}, ensure_ascii=False)
              + "</script>")
        trilha = " <span aria-hidden=\"true\">/</span> ".join(
            f'<a href="{r}{link}">{e(nome)}</a>' if link else f'<span aria-current="page">{e(nome)}</span>'
            for nome, link in migalhas)
        trilha_html = f'<nav class="trilha" aria-label="Você está em">{trilha}</nav>'
    else:
        trilha_html = ""
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    ano = datetime.now().year
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{canonical}">
{robots}
<meta property="og:type" content="website">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="pt_BR">
<meta name="theme-color" content="#1A2A5C">
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}estilo.css">
{ld}
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <div class="envelope topo-linha">
    <a class="marca" href="{r}index.html" aria-label="{e(config.SITE_NOME)}, página inicial">
      <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true"><circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" stroke-width="2.5"/><circle cx="16" cy="16" r="7.5" fill="none" stroke="currentColor" stroke-width="2" opacity=".55"/><path d="M16 16 L27 8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><circle cx="21.5" cy="19.5" r="2.4" fill="#FFE45C"/></svg>
      <span>Radar <b>de Licitações</b></span>
    </a>
    <nav class="menu" aria-label="Principal">
      <a class="menu-secundario" href="{r}busca.html">Buscar</a>
      <a class="menu-secundario" href="{r}index.html#estados">Estados</a>
      <a class="menu-secundario" href="{r}index.html#segmentos">Segmentos</a>
      <a class="menu-alerta" href="{r}alertas.html">Alertas grátis</a>
    </nav>
  </div>
</header>
<main id="conteudo">
{trilha_html}
{corpo}
</main>
<footer class="rodape">
  <div class="envelope rodape-grade">
    <div>
      <p class="rodape-marca">{e(config.SITE_NOME)}</p>
      <p>Licitações públicas abertas em todo o Brasil, organizadas por estado, cidade e segmento. Atualizado todos os dias.</p>
    </div>
    <div>
      <p><a href="{r}alertas.html">Receber alertas no Telegram</a></p>
      <p><a href="{r}busca.html">Buscar licitações</a></p>
      <p><a href="{r}sobre.html">Sobre e fonte dos dados</a></p>
    </div>
    <div>
      <p>Dados públicos do <a href="https://pncp.gov.br" rel="noopener">Portal Nacional de Contratações Públicas (PNCP)</a>. Este site não é um órgão oficial: confira sempre o edital antes de participar.</p>
      <p class="pequeno">© {ano} {e(config.SITE_NOME)}</p>
    </div>
  </div>
</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------------------
def linha(reg: dict, r: str, agora: datetime) -> str:
    texto, classe = prazo_texto(reg["fim"], agora)
    objeto = reg["objeto"]
    if len(objeto) > 220:
        objeto = objeto[:220].rsplit(" ", 1)[0] + "…"
    valor = moeda(reg["valor"])
    valor_html = f'<span class="lin-valor">{e(valor)}</span>' if valor.startswith("R$") else ""
    return f"""<li class="lin">
  <a href="{r}{reg['url']}">
    <span class="lin-prazo prazo-{classe}">{e(texto)}</span>
    <span class="lin-objeto">{e(objeto)}</span>
    <span class="lin-meta"><span>{e(reg['cidade'])}, {reg['uf']}</span><span>{e(seg_titulo(reg['seg']))}</span>{valor_html}</span>
  </a>
</li>"""


def lista(regs: list[dict], r: str, agora: datetime, limite: int | None = None) -> str:
    if not regs:
        return '<p class="vazio">Nenhuma licitação aberta aqui agora. Novas oportunidades entram todos os dias; ative os alertas para ser avisado.</p>'
    mostrar = regs[:limite] if limite else regs
    return '<ol class="lista">' + "\n".join(linha(x, r, agora) for x in mostrar) + "</ol>"


def bloco_alerta(r: str, seg: str | None = None) -> str:
    canal = canal_do_segmento(seg) if seg else None
    if canal:
        nome = canal.lstrip("@")
        return f"""<aside class="alerta">
  <div>
    <h2>Receba licitações de {e(seg_titulo(seg).lower())} no celular</h2>
    <p>Todo dia, assim que são publicadas, direto no Telegram. Grátis, sem cadastro.</p>
  </div>
  <a class="botao botao-amarelo" href="https://t.me/{e(nome)}" rel="noopener">Entrar no canal {e(canal)}</a>
</aside>"""
    botoes = "".join(
        f'<a class="botao botao-amarelo" href="https://t.me/{e(c.lstrip("@"))}" rel="noopener">{e(t)}</a>'
        for _, t, c in canais())
    return f"""<aside class="alerta">
  <div>
    <h2>Receba novas licitações no celular</h2>
    <p>Alertas diários e gratuitos no Telegram, separados por segmento.</p>
  </div>
  <div class="alerta-botoes">{botoes}<a class="botao botao-contorno" href="{r}alertas.html">Ver todos os canais</a></div>
</aside>"""


def chips(pares: list[tuple[str, str, int]], r: str) -> str:
    """pares = (rótulo, link, quantidade)"""
    return '<ul class="chips">' + "".join(
        f'<li><a href="{r}{link}">{e(rot)} <span>{qtd}</span></a></li>' for rot, link, qtd in pares
    ) + "</ul>"


def numero(n: int) -> str:
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
def pagina_detalhe(reg: dict, relacionadas: list[dict], agora: datetime) -> str:
    caminho = reg["url"]
    r = _raiz(caminho)
    it = reg["raw"]
    texto, classe = prazo_texto(reg["fim"], agora)
    titulo_curto = reg["objeto"][:90].rsplit(" ", 1)[0] if len(reg["objeto"]) > 90 else reg["objeto"]
    titulo = f"{titulo_curto} | {reg['cidade']}-{reg['uf']} | Licitação"
    descricao = (f"Licitação aberta em {reg['cidade']} ({reg['uf']}): {reg['objeto'][:120]}. "
                 f"Valor estimado {moeda(reg['valor'])}. Prazo até {data_br(it.get('dataEncerramentoProposta'), False)}.")
    pncp = urls.link_pncp(it)
    origem = it.get("linkSistemaOrigem")
    botoes = ""
    if pncp:
        botoes += f'<a class="botao botao-tinta" href="{e(pncp)}" rel="noopener nofollow">Abrir edital no PNCP</a>'
    if origem:
        botoes += f'<a class="botao botao-contorno" href="{e(origem)}" rel="noopener nofollow">Sistema onde a disputa acontece</a>'

    fatos = [
        ("Órgão", reg["orgao"]),
        ("Unidade compradora", reg["unidade"]),
        ("Local", f"{reg['cidade']}, {config.UF_NOMES.get(reg['uf'], reg['uf'])}"),
        ("Modalidade", reg["modalidade"]),
        ("Valor estimado", moeda(reg["valor"])),
        ("Recebe propostas a partir de", data_br(it.get("dataAberturaProposta"))),
        ("Encerramento das propostas", data_br(it.get("dataEncerramentoProposta"))),
        ("Situação", it.get("situacaoCompraNome") or ""),
        ("Número da compra", f"{it.get('numeroCompra') or ''}/{it.get('anoCompra') or ''}".strip("/")),
        ("Controle PNCP", it.get("numeroControlePNCP") or ""),
    ]
    dl = "".join(f"<div><dt>{e(k)}</dt><dd>{e(str(v))}</dd></div>" for k, v in fatos if v and v != "/")
    compl = (it.get("informacaoComplementar") or "").strip()
    compl_html = f'<section class="secao"><h2>Informações complementares</h2><p class="texto-livre">{e(compl[:2000])}</p></section>' if compl else ""

    rel_html = ""
    if relacionadas:
        rel_html = (f'<section class="secao"><h2>Outras licitações abertas em {e(reg["cidade"])}</h2>'
                    + lista(relacionadas, r, agora)
                    + f'<p><a class="link-forte" href="{r}{urls.pagina_cidade(reg["uf"], reg["cidade"])}">Ver todas em {e(reg["cidade"])}</a></p></section>')

    corpo = f"""<article class="envelope detalhe">
  <p class="detalhe-prazo"><mark class="prazo-{classe}">{e(texto)}</mark></p>
  <h1 class="detalhe-titulo">{e(reg['objeto'])}</h1>
  <p class="detalhe-sub"><a href="{r}{urls.pagina_segmento(reg['seg'])}">{e(seg_titulo(reg['seg']))}</a> em <a href="{r}{urls.pagina_cidade(reg['uf'], reg['cidade'])}">{e(reg['cidade'])}, {reg['uf']}</a></p>
  <div class="detalhe-acoes">{botoes}</div>
  <dl class="fatos">{dl}</dl>
  {compl_html}
  {bloco_alerta(r, reg['seg'])}
  {rel_html}
</article>"""
    migalhas = [("Início", "index.html"),
                (config.UF_NOMES[reg["uf"]], urls.pagina_estado(reg["uf"])),
                (reg["cidade"], urls.pagina_cidade(reg["uf"], reg["cidade"])),
                ("Licitação", None)]
    return layout(caminho, titulo, descricao, corpo, migalhas)


def pagina_lista(caminho: str, h1: str, intro: str, regs: list[dict], agora: datetime,
                 titulo: str, descricao: str, migalhas, extra_html: str = "",
                 seg: str | None = None, limite: int = 400) -> str:
    r = _raiz(caminho)
    mais = ""
    if len(regs) > limite:
        mais = f'<p class="nota">Mostrando as {limite} que encerram primeiro, de {numero(len(regs))}. Use a <a href="{r}busca.html">busca</a> para filtrar.</p>'
    corpo = f"""<div class="envelope">
  <header class="cabeca-lista">
    <h1>{e(h1)}</h1>
    <p>{intro}</p>
  </header>
  {extra_html}
  {lista(regs, r, agora, limite)}
  {mais}
  {bloco_alerta(r, seg)}
</div>"""
    return layout(caminho, titulo, descricao, corpo, migalhas)


def pagina_inicial(regs: list[dict], por_uf, por_seg, agora: datetime) -> str:
    r = ""
    total = numero(len(regs))
    opcoes_uf = "".join(f'<option value="{uf}">{e(nome)}</option>' for uf, nome in sorted(config.UF_NOMES.items(), key=lambda x: x[1]))
    opcoes_seg = "".join(f'<option value="{k}">{e(v["titulo"])}</option>' for k, v in config.SEGMENTOS.items())
    seg_pares = [(f'{seg_info(s)["emoji"]} {seg_titulo(s)}', urls.pagina_segmento(s), len(por_seg[s]))
                 for s in list(config.SEGMENTOS) + ["outros"] if por_seg.get(s)]
    uf_pares = [(config.UF_NOMES[uf], urls.pagina_estado(uf), len(por_uf[uf]))
                for uf in sorted(por_uf, key=lambda u: config.UF_NOMES[u])]
    urgentes = [x for x in regs if x["fim"] and (x["fim"] - agora).days < 3]
    corpo = f"""<section class="heroi">
  <div class="envelope">
    <h1>Licitações abertas agora, em todo o Brasil.</h1>
    <p class="heroi-sub">Hoje são <strong>{total}</strong> oportunidades com prazo aberto para fornecer a prefeituras, estados e órgãos federais. Encontre as da sua cidade e do seu ramo.</p>
    <form class="busca" action="busca.html" method="get" role="search">
      <label class="busca-campo">
        <span class="sr">O que você vende?</span>
        <input type="search" name="q" placeholder="O que você vende? Ex.: cimento" autocomplete="off">
      </label>
      <label><span class="sr">Estado</span>
        <select name="uf"><option value="">Todos os estados</option>{opcoes_uf}</select>
      </label>
      <label><span class="sr">Segmento</span>
        <select name="seg"><option value="">Todos os segmentos</option>{opcoes_seg}</select>
      </label>
      <button class="botao botao-amarelo" type="submit">Buscar licitações</button>
    </form>
    <p class="heroi-nota">Atualizado em {agora.strftime('%d/%m/%Y às %H:%M')} com dados do PNCP.</p>
  </div>
</section>
<div class="envelope">
  <section class="secao">
    <h2>Encerram nos próximos 3 dias</h2>
    <p class="secao-sub">Ainda dá tempo de enviar proposta.</p>
    {lista(urgentes, r, agora, 15)}
    <p><a class="link-forte" href="busca.html">Ver todas as licitações abertas</a></p>
  </section>
  <section class="secao" id="segmentos">
    <h2>Por segmento</h2>
    {chips(seg_pares, r)}
  </section>
  <section class="secao" id="estados">
    <h2>Por estado</h2>
    {chips(uf_pares, r)}
  </section>
  {bloco_alerta(r)}
  <section class="secao como">
    <h2>Como funciona</h2>
    <ol class="passos">
      <li><strong>Encontre</strong> a licitação pelo que você vende, pela cidade ou pelo estado.</li>
      <li><strong>Abra o edital</strong> no portal oficial e confira as exigências.</li>
      <li><strong>Envie sua proposta</strong> no sistema indicado antes do prazo.</li>
    </ol>
  </section>
</div>"""
    titulo = f"Licitações abertas hoje no Brasil: {total} oportunidades | {config.SITE_NOME}"
    descricao = f"{total} licitações públicas com prazo aberto em todo o Brasil. Busque por cidade, estado ou segmento e receba alertas grátis no Telegram."
    return layout("index.html", titulo, descricao, corpo)


def pagina_busca() -> str:
    opcoes_uf = "".join(f'<option value="{uf}">{e(nome)}</option>' for uf, nome in sorted(config.UF_NOMES.items(), key=lambda x: x[1]))
    opcoes_seg = "".join(f'<option value="{k}">{e(v["titulo"])}</option>' for k, v in config.SEGMENTOS.items())
    corpo = f"""<div class="envelope">
  <header class="cabeca-lista"><h1>Buscar licitações abertas</h1>
  <p>Digite o que você vende e escolha o estado. A lista mostra primeiro as que encerram antes.</p></header>
  <form class="busca busca-pagina" id="form-busca" role="search">
    <label class="busca-campo"><span class="sr">O que você vende?</span>
      <input type="search" name="q" id="q" placeholder="Ex.: cimento, merenda, pneu" autocomplete="off"></label>
    <label><span class="sr">Estado</span><select name="uf" id="uf"><option value="">Todos os estados</option>{opcoes_uf}</select></label>
    <label><span class="sr">Segmento</span><select name="seg" id="seg"><option value="">Todos os segmentos</option>{opcoes_seg}<option value="outros">Outros</option></select></label>
    <button class="botao botao-amarelo" type="submit">Buscar</button>
  </form>
  <p class="nota" id="status" role="status" aria-live="polite">Carregando licitações…</p>
  <ol class="lista" id="resultados"></ol>
  {bloco_alerta("")}
</div>
<script src="busca.js" defer></script>"""
    return layout("busca.html", f"Buscar licitações abertas | {config.SITE_NOME}",
                  "Busque licitações públicas abertas por produto, estado e segmento.", corpo,
                  [("Início", "index.html"), ("Buscar", None)])


def pagina_alertas() -> str:
    itens = "".join(
        f'<li><span class="canal-emoji" aria-hidden="true">{seg_info(s)["emoji"]}</span><div><h2>{e(t)}</h2>'
        f'<p>Novas licitações de {e(t.lower())} em todo o Brasil, todos os dias.</p></div>'
        f'<a class="botao botao-amarelo" href="https://t.me/{e(c.lstrip("@"))}" rel="noopener">Entrar em {e(c)}</a></li>'
        for s, t, c in canais())
    corpo = f"""<div class="envelope estreito">
  <header class="cabeca-lista"><h1>Alertas grátis no Telegram</h1>
  <p>Escolha o canal do seu ramo. Você recebe cada licitação nova com objeto, órgão, cidade, valor, prazo e link do edital. Sem cadastro e sem custo: para sair, é só deixar o canal.</p></header>
  <ul class="canais">{itens}</ul>
  <p class="nota">Novos segmentos chegam em breve. As licitações dos demais ramos já estão no site, na <a href="busca.html">busca</a>.</p>
</div>"""
    return layout("alertas.html", f"Alertas de licitação grátis no Telegram | {config.SITE_NOME}",
                  "Receba licitações novas do seu segmento todos os dias no Telegram, de graça.", corpo,
                  [("Início", "index.html"), ("Alertas", None)])


def pagina_sobre() -> str:
    corpo = """<div class="envelope estreito texto">
  <h1>Sobre o Radar de Licitações</h1>
  <p>O Radar reúne, todos os dias, as licitações públicas com prazo de proposta aberto publicadas no Portal Nacional de Contratações Públicas (PNCP), o portal oficial criado pela Lei 14.133/2021.</p>
  <p>Organizamos essas oportunidades por estado, cidade e segmento para que pequenos e médios fornecedores encontrem rapidamente o que podem vender ao governo.</p>
  <h2>De onde vêm os dados</h2>
  <p>Todos os dados vêm da API pública de consultas do PNCP. Não alteramos as informações oficiais; apenas organizamos. Em caso de divergência, vale o que está no edital e no portal oficial.</p>
  <h2>Isto não é um órgão público</h2>
  <p>Este é um serviço independente de informação. Antes de participar, leia o edital completo no link oficial de cada licitação.</p>
</div>"""
    return layout("sobre.html", f"Sobre e fonte dos dados | {config.SITE_NOME}",
                  "Como o Radar de Licitações reúne as licitações abertas do PNCP.", corpo,
                  [("Início", "index.html"), ("Sobre", None)])


def pagina_404() -> str:
    corpo = """<div class="envelope estreito texto">
  <h1>Esta licitação não está mais aqui</h1>
  <p>O prazo dela provavelmente encerrou e ela saiu do site. As oportunidades abertas continuam na busca.</p>
  <p><a class="botao botao-amarelo" href="RAIZbusca.html">Buscar licitações abertas</a></p>
</div>""".replace("RAIZ", _raiz_absoluta())
    return layout("404.html", f"Página não encontrada | {config.SITE_NOME}", "Página não encontrada.", corpo,
                  noindex=True, raiz=_raiz_absoluta())


# ---------------------------------------------------------------------------
# Gravação
# ---------------------------------------------------------------------------
def _gravar(base: str, caminho: str, conteudo: str) -> None:
    destino = os.path.join(base, caminho)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(conteudo)


def gerar(itens: list[dict], agora: datetime | None = None, pasta: str | None = None) -> dict:
    agora = agora or datetime.now()
    base = pasta or config.PASTA_SITE
    shutil.rmtree(base, ignore_errors=True)
    os.makedirs(base)
    for nome in os.listdir(ASSETS):
        shutil.copy(os.path.join(ASSETS, nome), base)
    open(os.path.join(base, ".nojekyll"), "w").close()

    regs = preparar(itens, agora)
    por_uf, por_cidade, por_seg, por_seg_uf = (defaultdict(list) for _ in range(4))
    for x in regs:
        por_uf[x["uf"]].append(x)
        por_cidade[(x["uf"], x["cidade"])].append(x)
        por_seg[x["seg"]].append(x)
        por_seg_uf[(x["seg"], x["uf"])].append(x)

    paginas = ["", "busca.html", "alertas.html", "sobre.html"]

    # Detalhes
    for x in regs:
        rel = [y for y in por_cidade[(x["uf"], x["cidade"])] if y is not x][:6]
        _gravar(base, x["url"], pagina_detalhe(x, rel, agora))
        paginas.append(x["url"])

    # Estados
    for uf, lst in por_uf.items():
        nome = config.UF_NOMES[uf]
        cidades = sorted(((c, len(v)) for (u, c), v in por_cidade.items() if u == uf), key=lambda t: -t[1])
        extra = ('<section class="secao"><h2>Cidades</h2>'
                 + chips([(c, urls.pagina_cidade(uf, c), n) for c, n in cidades], "../") + "</section>"
                 + '<section class="secao"><h2>Segmentos</h2>'
                 + chips([(seg_titulo(s), urls.pagina_segmento_uf(s, uf), len(por_seg_uf[(s, uf)]))
                          for s in list(config.SEGMENTOS) + ["outros"] if por_seg_uf.get((s, uf))], "../")
                 + '</section><h2 class="titulo-lista">Encerram primeiro</h2>')
        cam = urls.pagina_estado(uf)
        _gravar(base, cam, pagina_lista(
            cam, f"Licitações abertas em {nome}",
            f"{numero(len(lst))} oportunidades com prazo aberto em {len(cidades)} cidades de {e(nome)}.",
            lst, agora, f"Licitações abertas em {nome} ({uf}) hoje | {config.SITE_NOME}",
            f"{numero(len(lst))} licitações abertas em {nome}. Veja por cidade e segmento, com prazos e valores.",
            [("Início", "index.html"), (nome, None)], extra, limite=200))
        paginas.append(cam)

    # Cidades
    for (uf, cidade), lst in por_cidade.items():
        cam = urls.pagina_cidade(uf, cidade)
        nome_uf = config.UF_NOMES[uf]
        _gravar(base, cam, pagina_lista(
            cam, f"Licitações abertas em {cidade} ({uf})",
            f"{numero(len(lst))} {'oportunidade' if len(lst) == 1 else 'oportunidades'} com prazo aberto em {e(cidade)}, {e(nome_uf)}.",
            lst, agora, f"Licitações em {cidade} - {uf}: {len(lst)} abertas | {config.SITE_NOME}",
            f"Licitações abertas da prefeitura e órgãos públicos de {cidade} ({uf}): objeto, valor e prazo de cada uma.",
            [("Início", "index.html"), (nome_uf, urls.pagina_estado(uf)), (cidade, None)]))
        paginas.append(cam)

    # Segmentos
    for seg, lst in por_seg.items():
        cam = urls.pagina_segmento(seg)
        t = seg_titulo(seg)
        ufs = sorted(((u, len(v)) for (s, u), v in por_seg_uf.items() if s == seg), key=lambda p: config.UF_NOMES[p[0]])
        extra = ('<section class="secao"><h2>Por estado</h2>'
                 + chips([(config.UF_NOMES[u], urls.pagina_segmento_uf(seg, u), n) for u, n in ufs], "../")
                 + '</section><h2 class="titulo-lista">Encerram primeiro</h2>')
        _gravar(base, cam, pagina_lista(
            cam, f"Licitações de {t.lower()}",
            f"{numero(len(lst))} licitações abertas de {e(t.lower())} em todo o Brasil.",
            lst, agora, f"Licitações de {t.lower()} abertas hoje | {config.SITE_NOME}",
            f"{numero(len(lst))} licitações de {t.lower()} com prazo aberto no Brasil. Filtre por estado e receba alertas.",
            [("Início", "index.html"), (t, None)], extra, seg=seg, limite=300))
        paginas.append(cam)
    for (seg, uf), lst in por_seg_uf.items():
        cam = urls.pagina_segmento_uf(seg, uf)
        t, nome_uf = seg_titulo(seg), config.UF_NOMES[uf]
        _gravar(base, cam, pagina_lista(
            cam, f"Licitações de {t.lower()} em {nome_uf}",
            f"{numero(len(lst))} licitações abertas de {e(t.lower())} em {e(nome_uf)}.",
            lst, agora, f"Licitações de {t.lower()} em {nome_uf} ({uf}) | {config.SITE_NOME}",
            f"Licitações abertas de {t.lower()} em {nome_uf}: prazos, valores e cidades.",
            [("Início", "index.html"), (t, urls.pagina_segmento(seg)), (nome_uf, None)], seg=seg))
        paginas.append(cam)

    # Páginas fixas
    _gravar(base, "index.html", pagina_inicial(regs, por_uf, por_seg, agora))
    _gravar(base, "busca.html", pagina_busca())
    _gravar(base, "alertas.html", pagina_alertas())
    _gravar(base, "sobre.html", pagina_sobre())
    _gravar(base, "404.html", pagina_404())

    # Dados da busca: um arquivo por UF, em formato compacto
    segs_lista = list(config.SEGMENTOS) + ["outros"]
    meta = {"atualizado": agora.isoformat(timespec="minutes"),
            "segmentos": {s: seg_titulo(s) for s in segs_lista},
            "ufs": {uf: len(v) for uf, v in por_uf.items()}}
    _gravar(base, "dados/meta.json", json.dumps(meta, ensure_ascii=False))
    for uf, lst in por_uf.items():
        linhas = [[x["url"], x["objeto"][:200], x["cidade"], x["seg"],
                   x["valor"] if isinstance(x["valor"], (int, float)) else None,
                   x["fim"].isoformat(timespec="minutes") if x["fim"] else None] for x in lst]
        _gravar(base, f"dados/{uf.lower()}.json", json.dumps(linhas, ensure_ascii=False, separators=(",", ":")))

    # Sitemaps (máx. 45 mil URLs por arquivo) + robots
    hoje = agora.strftime("%Y-%m-%d")
    blocos = [paginas[i:i + 45000] for i in range(0, len(paginas), 45000)]
    for n, bloco in enumerate(blocos, 1):
        corpo = "".join(f"<url><loc>{e(urls.absoluta(p))}</loc><lastmod>{hoje}</lastmod></url>" for p in bloco)
        _gravar(base, f"sitemap-{n}.xml",
                f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{corpo}</urlset>')
    indice = "".join(f"<sitemap><loc>{urls.absoluta(f'sitemap-{n}.xml')}</loc><lastmod>{hoje}</lastmod></sitemap>"
                     for n in range(1, len(blocos) + 1))
    _gravar(base, "sitemap.xml",
            f'<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{indice}</sitemapindex>')
    _gravar(base, "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {urls.absoluta('sitemap.xml')}\n")

    return {"licitacoes": len(regs), "paginas": len(paginas)}
