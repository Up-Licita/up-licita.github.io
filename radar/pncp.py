"""
pncp.py — Coleta de licitações na API pública do PNCP.

- Consulta o endpoint /v1/contratacoes/publicacao por modalidade e por UF.
- Percorre todas as páginas.
- Trata erros de internet, timeout, respostas vazias (HTTP 204) e JSON inválido,
  tentando de novo algumas vezes antes de desistir daquela consulta.
"""

import time
import logging
from datetime import date

import requests

from radar import config

log = logging.getLogger("radar.pncp")

TENTATIVAS = 4
TIMEOUT = 40  # segundos


def _get_com_retentativa(url: str, params: dict) -> dict | None:
    """Faz GET com novas tentativas. Retorna o JSON (dict) ou None se vazio/falhou."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT,
                                headers={"accept": "application/json"})
            if resp.status_code == 204:          # sem resultados
                return None
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    log.warning("JSON inválido (tentativa %s) params=%s", tentativa, params)
            elif resp.status_code in (429, 500, 502, 503, 504):
                log.warning("PNCP respondeu %s (tentativa %s)", resp.status_code, tentativa)
            else:
                # Erro de parâmetro (400/422 etc.) — não adianta repetir.
                log.error("PNCP respondeu %s: %s", resp.status_code, resp.text[:300])
                return None
        except requests.RequestException as erro:
            log.warning("Falha de conexão (tentativa %s): %s", tentativa, erro)
        time.sleep(2 * tentativa)  # espera crescente: 2s, 4s, 6s...
    log.error("Desisti após %s tentativas. params=%s", TENTATIVAS, params)
    return None


def buscar_publicadas(data_inicial: date, data_final: date) -> list[dict]:
    """
    Retorna todas as contratações publicadas no período, nas modalidades e UFs
    configuradas. Cada item é o dicionário original devolvido pelo PNCP.
    """
    url = config.PNCP_BASE_URL + config.PNCP_ENDPOINT_PUBLICACAO
    ufs = config.UFS or [None]  # None = sem filtro de UF (Brasil todo)
    resultado: dict[str, dict] = {}  # chave = numeroControlePNCP (evita duplicar)

    for codigo_modalidade, nome_modalidade in config.MODALIDADES.items():
        for uf in ufs:
            pagina = 1
            while True:
                params = {
                    "dataInicial": data_inicial.strftime("%Y%m%d"),
                    "dataFinal": data_final.strftime("%Y%m%d"),
                    "codigoModalidadeContratacao": codigo_modalidade,
                    "pagina": pagina,
                    "tamanhoPagina": config.PNCP_TAMANHO_PAGINA,
                }
                if uf:
                    params["uf"] = uf

                dados = _get_com_retentativa(url, params)
                time.sleep(config.PNCP_PAUSA_ENTRE_CHAMADAS)
                if not dados:
                    break

                itens = dados.get("data") or []
                for item in itens:
                    chave = item.get("numeroControlePNCP")
                    if chave:
                        resultado[chave] = item

                total_paginas = dados.get("totalPaginas") or 1
                log.info("%s | %s | página %s/%s | %s itens",
                         nome_modalidade, uf or "BR", pagina, total_paginas, len(itens))
                if pagina >= total_paginas or not itens:
                    break
                pagina += 1

    log.info("Total coletado (sem duplicatas): %s", len(resultado))
    return list(resultado.values())
