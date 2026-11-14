"""
estado.py — "Memória" do robô.

Guarda em estado/vistos.json os IDs (numeroControlePNCP) já enviados, com a data
do envio, para nunca mandar a mesma licitação duas vezes. O GitHub Actions salva
esse arquivo de volta no repositório ao fim de cada execução.
"""

import json
import os
from datetime import date, timedelta

from radar import config


def carregar() -> dict[str, str]:
    try:
        with open(config.ARQUIVO_ESTADO, encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def salvar(vistos: dict[str, str]) -> None:
    """Remove registros antigos e grava o arquivo."""
    limite = (date.today() - timedelta(days=config.DIAS_GUARDAR_ESTADO)).isoformat()
    vistos = {k: v for k, v in vistos.items() if v >= limite}
    os.makedirs(os.path.dirname(config.ARQUIVO_ESTADO), exist_ok=True)
    with open(config.ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(vistos, f, ensure_ascii=False, indent=0, sort_keys=True)


def chave(nicho: str, item: dict) -> str:
    """Chave por nicho: a mesma licitação pode ir para os dois canais."""
    return f"{nicho}:{item.get('numeroControlePNCP')}"
