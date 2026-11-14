"""
main.py — Ponto de partida do Radar de Licitações.

Fluxo: coleta licitações abertas no PNCP (Brasil todo)
       -> envia as NOVAS para os canais do Telegram de cada segmento
       -> gera o site com todas as abertas (pasta _site)

Uso:
  python main.py                  # execução completa
  python main.py --teste          # não envia nada ao Telegram (só mostra no terminal)
  python main.py --sem-telegram   # só gera o site
  python main.py --sem-site       # só Telegram
"""

import argparse
import logging
import os
import sys
from datetime import date, datetime

from radar import config, estado, filtro, formatacao, pncp, site, telegram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("radar")


def titulo_nicho(seg: str) -> str:
    s = config.SEGMENTOS[seg]
    return f"{s.get('emoji', '')} {s['titulo']}".strip()


def enviar_telegram(itens: list[dict], teste: bool) -> None:
    agora = datetime.now()
    hoje = date.today().isoformat()
    recentes = [i for i in itens if filtro.publicada_recentemente(i, agora)]
    grupos = filtro.separar_por_nicho(recentes, agora)
    vistos = estado.carregar()
    primeira_vez = not vistos
    token = os.environ.get(config.TELEGRAM_TOKEN_ENV, "")
    if not teste and not token:
        log.error("Segredo %s não configurado: Telegram pulado.", config.TELEGRAM_TOKEN_ENV)
        return

    for seg, lista in grupos.items():
        nicho = config.NICHOS[seg]
        novos = [i for i in lista if estado.chave(seg, i) not in vistos]
        log.info("Segmento %s: %s recentes abertas, %s novas", seg, len(lista), len(novos))
        if not novos:
            continue
        individuais = novos[: config.MAX_ENVIOS_POR_NICHO]
        excedentes = novos[config.MAX_ENVIOS_POR_NICHO:]

        if teste:
            for item in individuais[:5]:
                print("\n" + "=" * 60 + "\n" + formatacao.mensagem(item, titulo_nicho(seg)))
            print(f"... ({len(individuais)} individuais, {len(excedentes)} no resumo)")
            continue

        chat_id = os.environ.get(nicho.get("chat_env", ""), "") or nicho.get("chat_padrao", "")
        if not chat_id:
            continue
        for item in individuais:
            if telegram.enviar(token, chat_id, formatacao.mensagem(item, titulo_nicho(seg))):
                vistos[estado.chave(seg, item)] = hoje
        if excedentes and telegram.enviar(
                token, chat_id, formatacao.resumo_excedente(titulo_nicho(seg), excedentes, seg)):
            for item in excedentes:
                vistos[estado.chave(seg, item)] = hoje

    # Na primeira execução, marca também as abertas antigas como vistas,
    # para o canal não receber uma enxurrada no dia seguinte.
    if primeira_vez and not teste:
        for item in itens:
            for seg in filtro.classificar(item):
                if seg in config.NICHOS:
                    vistos.setdefault(estado.chave(seg, item), hoje)
    if not teste:
        estado.salvar(vistos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Radar de Licitações")
    parser.add_argument("--teste", action="store_true", help="não envia ao Telegram")
    parser.add_argument("--sem-telegram", action="store_true")
    parser.add_argument("--sem-site", action="store_true")
    args = parser.parse_args()

    itens = pncp.buscar_abertas()
    if not itens:
        log.error("Nenhuma licitação coletada (PNCP fora do ar?). Nada foi alterado.")
        return 1

    if not args.sem_telegram:
        enviar_telegram(itens, args.teste)
    if not args.sem_site:
        resultado = site.gerar(itens)
        log.info("Site gerado: %s licitações, %s páginas", resultado["licitacoes"], resultado["paginas"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
