"""
formatacao.py — Textos usados no Telegram e no site (moeda, datas, mensagens).
Usa somente campos devolvidos pelo PNCP; vazio vira "não informado".
"""

import html
from datetime import datetime

from radar import urls


def _txt(valor) -> str:
    return html.escape(str(valor)) if valor not in (None, "") else "não informado"


def moeda(valor) -> str:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "não informado"
    if v <= 0:
        return "sigiloso / não informado"
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(valor, com_hora: bool = True) -> str:
    if not valor:
        return "não informado"
    try:
        d = datetime.fromisoformat(str(valor)[:19])
        return d.strftime("%d/%m/%Y %H:%M" if com_hora else "%d/%m/%Y")
    except ValueError:
        return _txt(valor)


def link_pncp(item: dict) -> str | None:
    return urls.link_pncp(item)


def mensagem(item: dict, titulo_nicho: str) -> str:
    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    objeto = (item.get("objetoCompra") or "").strip()
    if len(objeto) > 600:
        objeto = objeto[:600].rsplit(" ", 1)[0] + "…"
    local = " / ".join(x for x in [unidade.get("municipioNome"), unidade.get("ufSigla")] if x)

    linhas = [
        f"<b>{html.escape(titulo_nicho)}</b> | {_txt(item.get('modalidadeNome'))}",
        "",
        f"📄 <b>Objeto:</b> {_txt(objeto)}",
        f"🏛 <b>Órgão:</b> {_txt(orgao.get('razaoSocial'))}",
        f"📍 <b>Local:</b> {_txt(local)}",
        f"💰 <b>Valor estimado:</b> {moeda(item.get('valorTotalEstimado'))}",
        f"🟢 <b>Abertura propostas:</b> {data_br(item.get('dataAberturaProposta'))}",
        f"⏰ <b>Encerramento:</b> {data_br(item.get('dataEncerramentoProposta'))}",
    ]
    links = [f'<a href="{urls.absoluta(urls.pagina_licitacao(item))}">Detalhes</a>']
    if link_pncp(item):
        links.append(f'<a href="{link_pncp(item)}">Edital no PNCP</a>')
    if item.get("linkSistemaOrigem"):
        links.append(f'<a href="{html.escape(item["linkSistemaOrigem"])}">Sistema de origem</a>')
    linhas += ["", "🔗 " + " | ".join(links)]
    return "\n".join(linhas)


def resumo_excedente(titulo_nicho: str, restantes: list[dict], seg: str | None = None) -> str:
    linhas = [f"<b>{html.escape(titulo_nicho)}</b>: mais {len(restantes)} oportunidades novas", ""]
    for item in restantes[:25]:
        un = item.get("unidadeOrgao") or {}
        objeto = (item.get("objetoCompra") or "")[:90]
        rotulo = html.escape(f"{un.get('municipioNome', '')}/{un.get('ufSigla', '')}: {objeto}")
        linhas.append(f'• <a href="{urls.absoluta(urls.pagina_licitacao(item))}">{rotulo}</a>')
    if len(restantes) > 25:
        linhas.append(f"… e outras {len(restantes) - 25}.")
    if seg:
        linhas += ["", f'👉 <a href="{urls.absoluta(urls.pagina_segmento(seg))}">Ver todas no site</a>']
    return "\n".join(linhas)
