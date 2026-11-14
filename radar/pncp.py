"""
pncp.py — Coleta de licitações na API pública do PNCP.

Usa o endpoint /v1/contratacoes/proposta, que devolve as contratações com prazo
de recebimento de propostas ABERTO (parâmetro obrigatório: dataFinal).
- Consulta modalidade por modalidade (e por UF, se houver UFs configuradas).
- Percorre todas as páginas.
- Trata internet instável, timeout, resposta vazia (HTTP 204) e JSON inválido.
"""

import time
import logging
from datetime import date, timedelta

import requests

from radar import config

log = logging.getLogger("radar.pncp")

TENTATIVAS = 4
TIMEOUT = 60  # segundos


def _get_com_retentativa(url: str, params: dict) -> dict | None:
    """GET com novas tentativas. Retorna o JSON (dict) ou None se vazio/falhou."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT,
                                headers={"accept": "application/json"})
            if resp.status_code == 204:
                return None
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    log.warning("JSON inválido (tentativa %s) params=%s", tentativa, params)
            elif resp.status_code in (429, 500, 502, 503, 504):
                log.warning("PNCP respondeu %s (tentativa %s)", resp.status_code, tentativa)
            else:
                log.error("PNCP respondeu %s: %s", resp.status_code, resp.text[:300])
                return None
        except requests.RequestException as erro:
            log.warning("Falha de conexão (tentativa %s): %s", tentativa, erro)
        time.sleep(3 * tentativa)
    log.error("Desisti após %s tentativas. params=%s", TENTATIVAS, params)
    return None


def buscar_abertas(hoje: date | None = None) -> list[dict]:
    """
    Todas as contratações com proposta aberta que encerram nos próximos
    config.DIAS_A_FRENTE dias. Cada item é o dicionário original do PNCP.
    """
    hoje = hoje or date.today()
    url = config.PNCP_BASE_URL + config.PNCP_ENDPOINT_PROPOSTA
    data_final = (hoje + timedelta(days=config.DIAS_A_FRENTE)).strftime("%Y%m%d")
    ufs = config.UFS or [None]
    resultado: dict[str, dict] = {}

    for codigo, nome in config.MODALIDADES.items():
        for uf in ufs:
            pagina = 1
            while True:
                params = {
                    "dataFinal": data_final,
                    "codigoModalidadeContratacao": codigo,
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
                if pagina == 1 or pagina % 20 == 0 or pagina >= total_paginas:
                    log.info("%s | %s | página %s/%s", nome, uf or "BR", pagina, total_paginas)
                if pagina >= total_paginas or not itens:
                    break
                pagina += 1

    log.info("Total coletado (sem duplicatas): %s", len(resultado))
    return list(resultado.values())
