import gspread
from google.oauth2.service_account import Credentials
from config import PLANILHA_ID, CREDENCIAIS_JSON

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def conectar_planilha():
    creds = Credentials.from_service_account_file(CREDENCIAIS_JSON, scopes=SCOPES)
    client = gspread.authorize(creds)
    planilha = client.open_by_key(PLANILHA_ID)
    return planilha.worksheet("CompreAqui")

def salvar_na_planilha(dados, produtos, taxa, troco, aba):
    valor = dados["valor"]
    pag   = dados["pagamento"]

    debito   = valor if pag in ["Débito", "C. Débito"]   else 0
    credito  = valor if pag in ["Crédito", "C. Crédito"] else 0
    pix      = valor if pag == "Pix"                      else 0
    dinheiro = valor if pag == "Dinheiro"                 else 0

    linha = [
        dados["numero"],
        dados["cliente"],
        produtos,
        debito,
        credito,
        pix,
        dinheiro,
        troco,
        0,
        taxa,
        "",
        dados["data"],
    ]

    todos_valores = aba.get_all_values()
    proxima_linha = len(todos_valores) + 1
    aba.update(range_name=f"A{proxima_linha}", values=[linha], value_input_option='USER_ENTERED')
    print(f"✅ Salvo na linha {proxima_linha}: {linha}")

def remover_pedido_planilha(numero_pedido, aba):
    try:
        todos = aba.get_all_values()

        for i, linha in enumerate(todos):
            if linha and str(linha[0]).strip().lstrip("0") == str(numero_pedido).strip().lstrip("0"):
                numero_linha = i + 1
                aba.delete_rows(numero_linha)
                print(f"🗑️  Pedido #{numero_pedido} removido da linha {numero_linha}")
                return True

        print(f"⚠️  Pedido #{numero_pedido} não encontrado na planilha")
        return False

    except Exception as e:
        print(f"⚠️  Erro ao remover pedido #{numero_pedido}: {e}")
        return False