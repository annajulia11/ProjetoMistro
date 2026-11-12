import os
import time
from pathlib import Path
import requests
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# As credenciais ficam no arquivo .env na raiz do projeto (não vai pro GitHub).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ══════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════

PLANILHA_ID        = os.getenv("PLANILHA_ID")
CREDENCIAIS_JSON   = os.getenv("GOOGLE_CREDENCIAIS", "credenciais.json")

IF_CLIENT_ID       = os.getenv("IFOOD_CLIENT_ID")
IF_CLIENT_SECRET   = os.getenv("IFOOD_CLIENT_SECRET")
IF_MERCHANT_ID     = os.getenv("IFOOD_MERCHANT_ID")
IF_BASE_URL        = os.getenv("IFOOD_BASE_URL", "https://merchant-api.ifood.com.br")
INTERVALO_SEGUNDOS = 10

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ══════════════════════════════════════════════════════════════════
# GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════

def conectar_aba_ifood():
    creds = Credentials.from_service_account_file(CREDENCIAIS_JSON, scopes=SCOPES)
    client = gspread.authorize(creds)
    planilha = client.open_by_key(PLANILHA_ID)
    return planilha.worksheet("ifood")

def salvar_na_planilha(dados, aba):
    valor = dados["valor"]
    pag   = dados["pagamento"]

    debito   = valor if pag in ["Débito", "C. Débito"]   else 0
    credito  = valor if pag in ["Crédito", "C. Crédito"] else 0
    pix      = valor if pag == "Pix"                      else 0
    dinheiro = valor if pag == "Dinheiro"                 else 0
    app      = dados["app"] if dados["app"] > 0 else (valor if pag == "APP" else 0)

    linha = [
        dados["numero"],
        dados["cliente"],
        dados["produtos"],
        debito,
        credito,
        pix,
        dinheiro,
        dados["troco"],
        app,
        dados["taxa"],
        "",
        dados["data"],
    ]

    col_a = aba.col_values(1)
    proxima_linha = len(col_a) + 1
    aba.update(range_name=f"A{proxima_linha}", values=[linha], value_input_option='USER_ENTERED')
    print(f"✅ Salvo na linha {proxima_linha}: {linha}")

# ══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO IFOOD
# ══════════════════════════════════════════════════════════════════

_token        = None
_token_expiry = 0

def obter_token():
    global _token, _token_expiry

    if _token and time.time() < _token_expiry - 60:
        return _token

    print("🔑 Obtendo token...", end=" ", flush=True)

    try:
        response = requests.post(
            f"{IF_BASE_URL}/authentication/v1.0/oauth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grantType":    "client_credentials",
                "clientId":     IF_CLIENT_ID,
                "clientSecret": IF_CLIENT_SECRET,
            },
            timeout=10
        )
    except requests.exceptions.Timeout:
        print("❌ Timeout")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Sem conexão: {e}")
        return None

    if response.status_code != 200:
        print(f"❌ Erro {response.status_code}")
        return None

    dados = response.json()
    _token        = dados["accessToken"]
    _token_expiry = time.time() + dados.get("expiresIn", 21600)
    print(f"✅ próxima renovação em {round(dados.get('expiresIn', 21600) / 3600, 1)}h")
    return _token

def headers():
    return {
        "Authorization": f"Bearer {obter_token()}",
        "Content-Type":  "application/json",
    }

# ══════════════════════════════════════════════════════════════════
# API IFOOD
# ══════════════════════════════════════════════════════════════════

def buscar_eventos():
    try:
        response = requests.get(
            f"{IF_BASE_URL}/order/v1.0/events:polling",
            headers=headers(),
            params={"merchantId": IF_MERCHANT_ID},
            timeout=10
        )
    except requests.exceptions.Timeout:
        print("⚠️  Timeout no polling")
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"⚠️  Sem conexão: {e}")
        return []

    if response.status_code == 204:
        return []
    if response.status_code != 200:
        print(f"❌ Erro polling: {response.status_code} — {response.text}")
        return []

    return response.json()

def confirmar_evento(evento_id):
    try:
        response = requests.post(
            f"{IF_BASE_URL}/order/v1.0/events/acknowledgment",
            headers=headers(),
            json=[{"id": evento_id}],
            timeout=10
        )
        if response.status_code not in [200, 202]:
            print(f"⚠️  Erro ao confirmar evento: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Erro ao confirmar evento: {e}")

def confirmar_pedido(order_id):
    try:
        response = requests.post(
            f"{IF_BASE_URL}/order/v1.0/orders/{order_id}/confirm",
            headers=headers(),
            timeout=10
        )
        print(f"   ✅ Pedido confirmado: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Erro ao confirmar pedido: {e}")

def buscar_detalhes_pedido(order_id):
    try:
        response = requests.get(
            f"{IF_BASE_URL}/order/v1.0/orders/{order_id}",
            headers=headers(),
            timeout=10
        )
    except requests.exceptions.Timeout:
        print("❌ Timeout ao buscar pedido")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Sem conexão: {e}")
        return None

    if response.status_code != 200:
        print(f"❌ Erro ao buscar pedido: {response.status_code}")
        return None

    return response.json()

# ══════════════════════════════════════════════════════════════════
# EXTRAÇÃO DE DADOS DO PEDIDO
# ══════════════════════════════════════════════════════════════════

def extrair_dados_pedido(pedido):
    try:
        numero  = pedido.get("displayId", pedido.get("id", ""))
        cliente = pedido.get("customer", {}).get("name", "")
        total   = pedido.get("total", {}).get("orderAmount", 0)
        taxa    = pedido.get("total", {}).get("deliveryFee", 0)
        data    = datetime.now().strftime("%d/%m/%Y")

        tipo_entrega = pedido.get("delivery", {}).get("deliveryBy", "")
        if tipo_entrega == "IFOOD":
            tipo = "Entrega iFood"
        elif tipo_entrega == "MERCHANT":
            tipo = "Entrega própria"
        else:
            tipo = pedido.get("orderType", "")
            if tipo == "TAKEOUT":
                tipo = "Retirada"
                taxa = "Retirada"

        itens = pedido.get("items", [])
        produtos_lista = []
        for item in itens:
            nome = item.get("name", "")
            qtd  = item.get("quantity", 1)
            produtos_lista.append(f"{qtd}x {nome}")
        produtos = ", ".join(produtos_lista)

        pagamentos = pedido.get("payments", {}).get("methods", [])
        pagamento  = ""
        troco      = 0
        app        = 0

        for pag in pagamentos:
            metodo    = pag.get("method", "").upper()
            tipo_pag  = pag.get("type", "").upper()
            valor_pag = pag.get("value", 0)

            if tipo_pag in ["ONLINE", "PREPAID"] or "ONLINE" in metodo or "DIGITAL" in metodo:
                app += valor_pag
                pagamento = "APP"
            elif "PIX" in metodo:
                pagamento = "Pix"
            elif "CREDIT" in metodo:
                pagamento = "Crédito"
            elif "DEBIT" in metodo:
                pagamento = "Débito"
            elif "CASH" in metodo or "DINHEIRO" in metodo:
                pagamento = "Dinheiro"
                troco_bruto = pag.get("changeFor", 0)
                if troco_bruto > 0:
                    troco = round(troco_bruto - total, 2)
                    if troco < 0:
                        troco = 0

        print(f"   📋 #{numero} | {cliente} | {pagamento} | R${total} | taxa:{taxa}")

        return {
            "numero":    numero,
            "cliente":   cliente,
            "produtos":  produtos,
            "tipo":      tipo,
            "pagamento": pagamento,
            "valor":     total,
            "taxa":      taxa,
            "troco":     troco,
            "app":       app,
            "data":      data,
        }

    except Exception as e:
        print(f"⚠️  Erro ao extrair dados: {e}")
        return None

# ══════════════════════════════════════════════════════════════════
# LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════════

print("🚀 Iniciando monitoramento iFood...")
aba_ifood = conectar_aba_ifood()
pedidos_ja_registrados = set()
print(f"🔄 Monitorando a cada {INTERVALO_SEGUNDOS}s...")

while True:
    try:
        eventos = buscar_eventos()

        if eventos:
            print(f"📬 {len(eventos)} evento(s) recebido(s)")

        for evento in eventos:
            evento_id = evento.get("id")
            order_id  = evento.get("orderId")
            full_code = evento.get("fullCode", "")

            print(f"\n→ {full_code} | {order_id}")
            confirmar_evento(evento_id)

            # Em teste: confirma automaticamente
            # Em produção: remova esse bloco
            if full_code == "PLACED":
                confirmar_pedido(order_id)
                continue

            if full_code != "CONFIRMED":
                continue

            if order_id in pedidos_ja_registrados:
                print("⏭️  Já registrado")
                continue

            pedido = buscar_detalhes_pedido(order_id)
            if not pedido:
                continue

            dados = extrair_dados_pedido(pedido)
            if not dados:
                continue

            salvar_na_planilha(dados, aba_ifood)
            pedidos_ja_registrados.add(order_id)

        time.sleep(INTERVALO_SEGUNDOS)

    except Exception as e:
        print(f"❌ {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)