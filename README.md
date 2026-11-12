# Mistrô Massas — Automação de pedidos de delivery

Automação que registra sozinha, numa planilha do Google Sheets, os pedidos de delivery do restaurante **Mistrô Massas** que chegam pelo **CompreAqui** e pelo **iFood**. Assim ninguém precisa copiar pedido por pedido à mão.

## Como funciona

| Plataforma | Como os pedidos são lidos | Aba da planilha | Frequência |
|---|---|---|---|
| CompreAqui | Selenium entra no painel do restaurante, lê os pedidos aceitos e abre cada um para pegar os itens, taxa e troco | `CompreAqui` | a cada 30 s |
| iFood | API oficial do iFood (Merchant API, OAuth 2.0) — busca eventos de pedido confirmado e os detalhes de cada pedido | `ifood` | a cada 10 s |

Pedidos cancelados no CompreAqui são detectados e removidos da planilha.

Colunas registradas: ID_Pedido, Nome do cliente, Produto, Débito, Crédito, PIX, Dinheiro, Troco, APP, Taxa, Entregador (preenchido à mão) e Data.

## Estrutura

```
├── compraqui/
│   ├── config.py        # Lê as configurações do .env
│   ├── driver.py        # Abre o Chrome e faz login no painel
│   ├── scraping.py      # Lê pedidos aceitos, cancelados e os itens de cada pedido
│   ├── sheets.py        # Grava e remove pedidos na planilha
│   └── main.py          # Loop principal
├── ifood/
│   └── ifood.py         # Autenticação, polling de eventos e gravação na planilha
├── ferramentas/
│   └── teste_planilha.py  # Insere uma linha de exemplo para testar a conexão
├── .env.example         # Modelo das variáveis de ambiente
└── requirements.txt
```

## Configuração

1. Instale as dependências (Python 3.10+ e Google Chrome):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copie o modelo de configuração e preencha com os dados reais:
   ```bash
   cp .env.example .env
   ```
3. Coloque o arquivo `credenciais.json` da conta de serviço do Google dentro da pasta de cada integração (`compraqui/` e `ifood/`) e compartilhe a planilha com o e-mail dessa conta de serviço.

> O `.env` e o `credenciais.json` estão no `.gitignore` e nunca devem ser enviados ao GitHub.

## Como rodar

```bash
# CompreAqui
cd compraqui
python main.py

# iFood (em outro terminal)
cd ifood
python ifood.py
```

## Tecnologias

Python · Selenium · webdriver-manager · gspread · Google Sheets API · iFood Merchant API · requests
