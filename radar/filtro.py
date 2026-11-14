"""
filtro.py — Decide em qual nicho cada licitação se encaixa.

Regras:
  1. O texto analisado é o "objetoCompra" + "informacaoComplementar".
  2. Maiúsculas e acentos são ignorados.
  3. As palavras-chave são comparadas como PALAVRAS INTEIRAS
     ("pao" casa com "pão francês", mas não com "papão" ou "padrão").
  4. Se aparecer uma palavra de exclusão, a licitação sai daquele nicho.
  5. Licitações cujo prazo de proposta já encerrou são descartadas.
"""

import re
import unicodedata
from datetime import datetime

from radar import config


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, espaços simples."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto.lower()).strip()


def _compilar(termos: list[str]) -> re.Pattern | None:
    """Gera uma regex única de palavras inteiras a partir da lista de termos."""
    termos = [re.escape(normalizar(t)) for t in termos if t.strip()]
    if not termos:
        return None
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(termos) + r")(?![a-z0-9])")


# Regex pré-compiladas por nicho (feito uma vez só, ao importar o módulo).
_REGRAS = {
    nome: (_compilar(n["palavras"]), _compilar(n.get("excluir", [])))
    for nome, n in config.NICHOS.items()
}


def texto_da_licitacao(item: dict) -> str:
    partes = [item.get("objetoCompra") or "", item.get("informacaoComplementar") or ""]
    return normalizar(" ".join(partes))


def prazo_aberto(item: dict, agora: datetime | None = None) -> bool:
    """True se ainda dá para enviar proposta (ou se o PNCP não informou o prazo)."""
    fim = item.get("dataEncerramentoProposta")
    if not fim:
        return True
    try:
        fim_dt = datetime.fromisoformat(str(fim)[:19])
    except ValueError:
        return True  # data em formato inesperado: melhor mostrar do que perder
    return fim_dt >= (agora or datetime.now())


def classificar(item: dict) -> list[str]:
    """Devolve a lista de nichos em que a licitação se encaixa (pode ser vazia)."""
    texto = texto_da_licitacao(item)
    nichos = []
    for nome, (incluir, excluir) in _REGRAS.items():
        if incluir and incluir.search(texto) and not (excluir and excluir.search(texto)):
            nichos.append(nome)
    return nichos


def separar_por_nicho(itens: list[dict], agora: datetime | None = None) -> dict[str, list[dict]]:
    """Agrupa as licitações abertas por nicho, ordenadas pelo prazo mais próximo."""
    grupos: dict[str, list[dict]] = {nome: [] for nome in config.NICHOS}
    for item in itens:
        if not prazo_aberto(item, agora):
            continue
        for nome in classificar(item):
            grupos[nome].append(item)
    for nome in grupos:
        grupos[nome].sort(key=lambda i: str(i.get("dataEncerramentoProposta") or "9999"))
    return grupos
