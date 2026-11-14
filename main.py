"""
main.py — Ponto de partida do Radar de Licitações.

Fluxo: coleta no PNCP -> filtra por nicho -> descarta já enviadas -> envia ao Telegram
       -> grava a memória (estado/vistos.json).

Uso:
  python main.py                 # execução normal (usa os segredos do Telegram)
  python main.py --teste         # NÃO envia nada: só mostra no terminal o que enviaria
  python main.py --dias 3        # busca publicações dos últimos 3 dias (padrão: 1)
"""

import argparse
import logging
import os
import sys
from datetime import date, timedelta

from radar import config, estado, filtro, formatacao, pncp, telegram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("radar")


def main() -> int:
    parser = argparse.ArgumentParser(description="Radar de Licitações")
    parser.add_argument("--teste", action="store_true", help="não envia ao Telegram")
    parser.add_argument("--dias", type=int, default=1, help="dias para trás a consultar")
    args = parser.parse_args()

    hoje = date.today()
    itens = pncp.buscar_publicadas(hoje - timedelta(days=args.dias), hoje)
    grupos = filtro.separar_por_nicho(itens)
    vistos = estado.carregar()
    token = os.environ.get(config.TELEGRAM_TOKEN_ENV, "")

    if not args.teste and not token:
        log.error("Segredo %s não configurado. Use --teste para rodar sem Telegram.",
                  config.TELEGRAM_TOKEN_ENV)
        return 1

    for nome, lista in grupos.items():
        nicho = config.NICHOS[nome]
        novos = [i for i in lista if estado.chave(nome, i) not in vistos]
        log.info("Nicho %s: %s abertas, %s novas", nome, len(lista), len(novos))
        if not novos:
            continue

        individuais = novos[: config.MAX_ENVIOS_POR_NICHO]
        excedentes = novos[config.MAX_ENVIOS_POR_NICHO:]

        if args.teste:
            for item in individuais:
                print("\n" + "=" * 60 + "\n" + formatacao.mensagem(item, nicho["titulo"]))
            if excedentes:
                print("\n" + formatacao.resumo_excedente(nicho["titulo"], excedentes))
            continue

        chat_id = os.environ.get(nicho["chat_env"], "") or nicho.get("chat_padrao", "")
        if not chat_id:
            log.warning("Segredo %s vazio — nicho %s pulado.", nicho["chat_env"], nome)
            continue

        for item in individuais:
            if telegram.enviar(token, chat_id, formatacao.mensagem(item, nicho["titulo"])):
                vistos[estado.chave(nome, item)] = hoje.isoformat()
        if excedentes and telegram.enviar(
                token, chat_id, formatacao.resumo_excedente(nicho["titulo"], excedentes)):
            for item in excedentes:
                vistos[estado.chave(nome, item)] = hoje.isoformat()

    if not args.teste:
        estado.salvar(vistos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
