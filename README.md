# Radar de Licitações

Robô que roda sozinho 2x por dia (06h37 e 15h37, horário de Brasília) no GitHub Actions:

1. Coleta no PNCP **todas as licitações com proposta aberta no Brasil** (pregão, dispensa, concorrência, credenciamento).
2. Classifica cada uma em segmentos (alimentação, material de construção, obras, saúde, limpeza, tecnologia, veículos etc.) — palavras-chave em `radar/config.py`.
3. Envia as **novas** para os canais do Telegram dos segmentos que têm canal (@uplicita_alimentos e @up_licita_construcao).
4. Gera e publica o **site** com todas as abertas: página por licitação, por estado, por cidade e por segmento, busca, sitemap para o Google.

Site: https://guilhermemoraesss.github.io/radar-licitacoes

## Configuração única
- Segredo `TELEGRAM_BOT_TOKEN` em Settings → Secrets and variables → Actions.
- Settings → Pages → Source: **GitHub Actions**.

## Rodar localmente
```bash
pip install -r requirements.txt
python main.py --teste            # não envia ao Telegram; gera o site em _site/
python -m unittest discover -s tests -t .
```

## Ajustes comuns (`radar/config.py`)
- Novo segmento: adicione em `SEGMENTOS`. Para ter canal, informe `chat_padrao` (ex.: "@meucanal") e coloque o bot como admin do canal.
- Falso positivo: adicione o termo em `excluir` do segmento.
- Limitar estados: `UFS = ["SP", "MG"]`.
