# Radar de Licitações — Alimentação e Material de Construção

O robô roda sozinho 2 vezes por dia (07h07 e 16h07, horário de Brasília) no GitHub Actions, sem custo. A cada rodada ele:

1. Busca no PNCP as contratações publicadas no último dia em SP e MG (pregão, dispensa, concorrência eletrônica, pregão presencial e credenciamento).
2. Separa o que é **alimentação** e o que é **material de construção** pelas palavras-chave definidas em `radar/config.py`.
3. Descarta o que já encerrou e o que já foi enviado antes.
4. Posta cada oportunidade no canal do Telegram do nicho, com objeto, órgão, cidade, valor, prazo e link do PNCP.

---

## Configuração (uma vez só, cerca de 20 minutos)

### 1. Criar o bot e os canais no Telegram
1. No Telegram, abra o **@BotFather**, mande `/newbot` e escolha um nome (ex.: *Radar Licitações*). Guarde o **token** que ele devolver (algo como `123456:ABC...`).
2. Crie **2 canais**: um de alimentação e um de material de construção. Podem começar privados.
3. Em cada canal, vá em *Administradores → Adicionar* e coloque o seu bot como administrador, com permissão para publicar.
4. Descubra o ID de cada canal:
   - **Canal público:** o ID é o próprio `@nomedocanal`.
   - **Canal privado:** publique qualquer mensagem no canal, abra no navegador `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` e copie o número que começa com `-100...`.

### 2. Subir o código no GitHub
1. Crie uma conta em github.com e um repositório **privado** chamado `radar-licitacoes`.
2. Envie todos os arquivos desta pasta, incluindo a pasta oculta `.github`. Pelo site: *Add file → Upload files* e arraste a pasta inteira.

### 3. Cadastrar os segredos
No repositório, vá em *Settings → Secrets and variables → Actions → New repository secret* e crie:

| Nome | Valor |
|---|---|
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ALIMENTACAO` | ID do canal de alimentação |
| `TELEGRAM_CHAT_CONSTRUCAO` | ID do canal de construção |

### 4. Primeiro teste
Na aba **Actions**, clique em **Radar de Licitações → Run workflow**. Em poucos minutos as licitações devem aparecer nos canais. Daí em diante ele roda sozinho.

---

## Testar no seu PC (opcional)
```bash
pip install -r requirements.txt
python main.py --teste --dias 2           # só mostra na tela, não envia nada
python -m unittest discover -s tests -t . # testes offline
```

## Ajustes comuns (tudo em `radar/config.py`)
- **Mais estados:** mude `UFS = ["SP", "MG"]`. Para o Brasil todo, use `UFS = []`.
- **Licitação que não devia ter entrado:** adicione o termo que causou o erro em `excluir` do nicho.
- **Licitação que faltou:** adicione o termo em `palavras`.
- **Volume no canal:** ajuste `MAX_ENVIOS_POR_NICHO`. O que passar do limite vai num resumo único.

## Próximas fases (monetização)
1. **Validação:** deixar os canais abertos de graça por 2 a 3 semanas e convidar fornecedores da região.
2. **Assinatura:** canal pago via Asaas ou Mercado Pago, com liberação automática por webhook.
3. **Resumo por IA** de cada edital e **páginas SEO** por cidade e segmento para trazer clientes pelo Google.
