import os
from pathlib import Path

from dotenv import load_dotenv

# As credenciais ficam no arquivo .env na raiz do projeto (não vai pro GitHub).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

EMAIL              = os.getenv("COMPRAQUI_EMAIL")
SENHA              = os.getenv("COMPRAQUI_SENHA")
PLANILHA_ID        = os.getenv("PLANILHA_ID")
CREDENCIAIS_JSON   = os.getenv("GOOGLE_CREDENCIAIS", "credenciais.json")
INTERVALO_SEGUNDOS = 30
RENOVAR_A_CADA     = 20
