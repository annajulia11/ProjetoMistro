# Teste rápido: insere uma linha de exemplo nas abas CompreAqui e ifood
# para conferir se a conexão com a planilha está funcionando.
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

#defina as permissões necessárias para acessar a planilha e o Google Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets", # Permissão para acessar e editar planilhas
    "https://www.googleapis.com/auth/drive" # Permissão para acessar arquivos no Google Drive
]

#autentica usando o arquivo de credenciais e as permissões definidas
creds = Credentials.from_service_account_file(os.getenv("GOOGLE_CREDENCIAIS", "credenciais.json"), scopes=SCOPES)
client = gspread.authorize(creds)

#abre a planilha usando a chave da URL
planilha = client.open_by_key(os.getenv("PLANILHA_ID"))
aba = planilha.sheet1

#Seleciona a aba
aba_compre_aqui = planilha.worksheet("CompreAqui")
aba_ifood = planilha.worksheet("ifood")

data_hoje = datetime.now().strftime("%d/%m/%Y")

# Exemplo inserindo na aba Compre Aqui
aba_compre_aqui.append_row([
    "001",          # ID_Pedido
    "Maria Silva",  # Nome do cliente
    "Macarrão ao molho branco",  # Pedido
    "0",            # Débito
    45.00,        # Crédito
    "0",            # pix
    "0",            # Dinheiro
    "0",            # Troco
    "0",            # APP
    3.00,           # Taxa
    "João",          # Entregador
    data_hoje       # Data
])

# Exemplo inserindo na aba iFood
aba_ifood.append_row([
    "001",          # ID_Pedido
    "Carlos Lima",  # Nome do cliente
    "Macarrão",  # Pedido
    "0",            # Débito
    "0",            # Crédito
    "0",            # pix
    "0",            # Dinheiro
    "0",            # Troco
    32.00,        # APP
    5.00,           # Taxa
    "Pedro",         # Entregador
    data_hoje       # Data
])

print("Pedidos inseridos com sucesso!")