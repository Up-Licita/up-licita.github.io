"""
filtro.py — Classifica cada licitação em segmentos e filtra prazos.

Regras:
  1. Texto analisado: "objetoCompra" + "informacaoComplementar".
  2. Maiúsculas e acentos são ignorados; palavras-chave casam como PALAVRAS INTEIRAS.
  3. Palavra de exclusão tira a licitação daquele segmento.
  4. Licitações com prazo de proposta encerrado são descartadas.
"""

import re
import unicodedata
from datetime import datetime, timedelta

from radar import config


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto.lower()).strip()


def slug(texto: str, limite: int = 0) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")
    if limite and len(s) > limite:
        s = s[:limite].rsplit("-", 1)[0]
    return s or "x"


def _compilar(termos: list[str]) -> re.Pattern | None:
    termos = [re.escape(normalizar(t)) for t in termos if t.strip()]
    if not termos:
        return None
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(termos) + r")(?![a-z0-9])")


_REGRAS = {
    nome: (_compilar(s["palavras"]), _compilar(s.get("excluir", [])))
    for nome, s in config.SEGMENTOS.items()
}


def texto_da_licitacao(item: dict) -> str:
    return normalizar(f"{item.get('objetoCompra') or ''} {item.get('informacaoComplementar') or ''}")


def _data(valor) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor)[:19])
    except ValueError:
        return None


def prazo_aberto(item: dict, agora: datetime | None = None) -> bool:
    fim = _data(item.get("dataEncerramentoProposta"))
    return fim is None or fim >= (agora or datetime.now())


def publicada_recentemente(item: dict, agora: datetime | None = None) -> bool:
    """True se publicada no PNCP nos últimos DIAS_NOVIDADE dias (ou sem data)."""
    pub = _data(item.get("dataPublicacaoPncp") or item.get("dataInclusao"))
    if pub is None:
        return True
    return pub >= (agora or datetime.now()) - timedelta(days=config.DIAS_NOVIDADE)


def classificar(item: dict) -> list[str]:
    """Segmentos em que a licitação se encaixa, na ordem de prioridade (pode ser vazia)."""
    texto = texto_da_licitacao(item)
    return [nome for nome, (inc, exc) in _REGRAS.items()
            if inc and inc.search(texto) and not (exc and exc.search(texto))]


def separar_por_nicho(itens: list[dict], agora: datetime | None = None) -> dict[str, list[dict]]:
    """Agrupa licitações abertas pelos segmentos que têm canal no Telegram."""
    grupos: dict[str, list[dict]] = {nome: [] for nome in config.NICHOS}
    for item in itens:
        if not prazo_aberto(item, agora):
            continue
        for nome in classificar(item):
            if nome in grupos:
                grupos[nome].append(item)
    for nome in grupos:
        grupos[nome].sort(key=lambda i: str(i.get("dataEncerramentoProposta") or "9999"))
    return grupos
