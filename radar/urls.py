"""
urls.py — Endereços das páginas do site (usados pelo site e pelas mensagens do Telegram).
Todos os caminhos são relativos à raiz do site, sem barra inicial.
"""

from radar import config
from radar.filtro import slug


def _partes(item: dict):
    orgao = item.get("orgaoEntidade") or {}
    return orgao.get("cnpj"), item.get("anoCompra"), item.get("sequencialCompra")


def id_licitacao(item: dict) -> str:
    cnpj, ano, seq = _partes(item)
    if cnpj and ano and seq:
        return f"{cnpj}-{ano}-{seq}"
    return slug(str(item.get("numeroControlePNCP") or "sem-id"))


def pagina_licitacao(item: dict) -> str:
    un = item.get("unidadeOrgao") or {}
    uf = (un.get("ufSigla") or "br").lower()
    cidade = slug(un.get("municipioNome") or "", 30)
    objeto = slug(item.get("objetoCompra") or "", 50)
    return f"licitacao/{uf}-{cidade}-{objeto}-{id_licitacao(item)}.html"


def pagina_estado(uf: str) -> str:
    return f"estado/{uf.lower()}.html"


def pagina_cidade(uf: str, cidade: str) -> str:
    return f"estado/{uf.lower()}/{slug(cidade, 60)}.html"


def pagina_segmento(seg: str) -> str:
    return f"segmento/{seg}.html"


def pagina_segmento_uf(seg: str, uf: str) -> str:
    return f"segmento/{seg}/{uf.lower()}.html"


def absoluta(caminho: str) -> str:
    return f"{config.SITE_URL}/{caminho}"


def link_pncp(item: dict) -> str | None:
    cnpj, ano, seq = _partes(item)
    if cnpj and ano and seq:
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    return None
