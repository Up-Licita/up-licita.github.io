"""
formatacao.py — Monta o texto (HTML do Telegram) de cada licitação.

Usa somente campos devolvidos pelo PNCP; se algum vier vazio, mostra "não informado".
"""

import html
from datetime import datetime


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


def data_br(valor) -> str:
    if not valor:
        return "não informado"
    try:
        return datetime.fromisoformat(str(valor)[:19]).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return _txt(valor)


def link_pncp(item: dict) -> str | None:
    """Página pública do edital no PNCP: /app/editais/{cnpj}/{ano}/{sequencial}."""
    orgao = item.get("orgaoEntidade") or {}
    cnpj, ano, seq = orgao.get("cnpj"), item.get("anoCompra"), item.get("sequencialCompra")
    if cnpj and ano and seq:
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    return None


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
    links = []
    if link_pncp(item):
        links.append(f'<a href="{link_pncp(item)}">Ver no PNCP</a>')
    if item.get("linkSistemaOrigem"):
        links.append(f'<a href="{html.escape(item["linkSistemaOrigem"])}">Sistema de origem</a>')
    if links:
        linhas += ["", "🔗 " + " | ".join(links)]
    return "\n".join(linhas)


def resumo_excedente(titulo_nicho: str, restantes: list[dict]) -> str:
    """Mensagem curta listando o que passou do limite de envios individuais."""
    linhas = [f"<b>{html.escape(titulo_nicho)}</b> — mais {len(restantes)} oportunidades hoje:", ""]
    for item in restantes[:30]:
        un = item.get("unidadeOrgao") or {}
        objeto = (item.get("objetoCompra") or "")[:90]
        url = link_pncp(item)
        rotulo = html.escape(f"{un.get('municipioNome', '')}/{un.get('ufSigla', '')} — {objeto}")
        linhas.append(f'• <a href="{url}">{rotulo}</a>' if url else f"• {rotulo}")
    if len(restantes) > 30:
        linhas.append(f"… e outras {len(restantes) - 30}.")
    return "\n".join(linhas)
