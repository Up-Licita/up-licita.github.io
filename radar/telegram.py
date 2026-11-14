"""
telegram.py — Envio de mensagens pelo bot do Telegram (API oficial, sem bibliotecas extras).
"""

import time
import logging

import requests

from radar import config

log = logging.getLogger("radar.telegram")
LIMITE_CARACTERES = 4096


def enviar(token: str, chat_id: str, texto: str) -> bool:
    """Envia uma mensagem HTML. Respeita o 'retry_after' do Telegram se houver limite."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto[:LIMITE_CARACTERES],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    for tentativa in range(1, 4):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            dados = resp.json() if resp.content else {}
            if resp.status_code == 200 and dados.get("ok"):
                time.sleep(config.TELEGRAM_PAUSA_ENTRE_ENVIOS)
                return True
            if resp.status_code == 429:
                espera = (dados.get("parameters") or {}).get("retry_after", 30)
                log.warning("Limite do Telegram, aguardando %ss", espera)
                time.sleep(espera + 1)
                continue
            log.error("Telegram recusou (%s): %s", resp.status_code, dados.get("description"))
            return False
        except (requests.RequestException, ValueError) as erro:
            log.warning("Falha ao enviar (tentativa %s): %s", tentativa, erro)
            time.sleep(5 * tentativa)
    return False
