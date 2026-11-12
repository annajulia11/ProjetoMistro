import re
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def buscar_pedidos_aceitos(driver):
    driver.get("https://www.compraqui.app/panel/orders?page=1&status=accepted")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='order-card-root']"))
        )
        time.sleep(2)
    except:
        print("⚠️  Nenhum pedido aceito no momento")
        return []

    cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='order-card-root']")
    print(f"📦 {len(cards)} pedido(s) aceito(s) encontrado(s)")
    return cards

def buscar_pedidos_cancelados(driver):
    try:
        driver.get("https://www.compraqui.app/panel/orders")
        time.sleep(2)

        botao_cancelado = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                "//*[contains(text(), 'Cancelado')]"
            ))
        )
        botao_cancelado.click()
        time.sleep(4)  # espera carregar apenas os cancelados

    except Exception as e:
        print(f"⚠️  Erro ao acessar cancelados: {e}")
        return []

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='order-card-root']"))
        )
        time.sleep(2)
    except:
        print("📭 Nenhum pedido cancelado hoje")
        return []

    cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='order-card-root']")
    hoje = datetime.now().strftime("%d/%m/%Y")

    cancelados = []
    for card in cards:
        texto = card.text.strip()

        # Só considera cancelados de hoje
        if hoje not in texto:
            continue

        numero = re.search(r"#(\d+)\s", texto)
        if numero:
            cancelados.append(numero.group(1))

    if cancelados:
        print(f"❌ {len(cancelados)} pedido(s) cancelado(s) hoje: {cancelados}")

    return cancelados

def extrair_dados_card(card):
    texto = card.text.strip()
    print(f"\n📋 Texto bruto:\n{texto}\n")

    numero = re.search(r"#(\d+)\s", texto)
    numero = numero.group(1) if numero else ""

    valor_match = re.search(r"R\$\s?([\d.,]+)", texto)
    valor_str = valor_match.group(1).replace(".", "").replace(",", ".") if valor_match else "0"
    valor = float(valor_str)

    cliente = re.search(r"R\$\s?[\d.,]+\s+(.+?)\s+#\d+\b", texto)
    cliente = cliente.group(1).strip() if cliente else ""

    pagamento = ""
    for p in ["Pix", "Dinheiro", "C. Crédito", "C. Débito", "Crédito", "Débito", "Cartão"]:
        if p in texto:
            pagamento = p
            break

    tipo = ""
    if "Retirada" in texto:
        tipo = "Retirada"
    elif "Entrega" in texto:
        tipo = "Entrega"

    print(f"🚚 Tipo: {tipo}")

    return {
        "numero":    numero,
        "cliente":   cliente,
        "pagamento": pagamento,
        "valor":     valor,
        "tipo":      tipo,
        "data":      datetime.now().strftime("%d/%m/%Y"),
    }

def extrair_produtos_do_modal(driver, numero_pedido, tipo):
    try:
        driver.find_element(By.XPATH, f"//p[contains(text(), '#{numero_pedido}')]").click()
    except Exception as e:
        print(f"⚠️  Não conseguiu clicar no pedido #{numero_pedido}: {e}")
        return "", "Retirada" if tipo == "Retirada" else 0, 0

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Produtos')]"))
        )
    except:
        print("⚠️  Modal não abriu")
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        return "", "Retirada" if tipo == "Retirada" else 0, 0

    time.sleep(4)

    try:
        modal = driver.find_element(By.XPATH,
            "//*[contains(text(), 'Produtos')]/ancestor::*[contains(@class,'MuiDialog') or contains(@class,'MuiPaper')][1]"
        )
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)
    except:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    time.sleep(3)

    produtos = []
    try:
        linhas = driver.find_elements(By.XPATH,
            "//*[contains(text(), 'Produtos')]/following::table//tr[td]"
        )
        if not linhas:
            linhas = driver.find_elements(By.XPATH, "//tr[contains(., 'X') and td]")

        for linha in linhas:
            celulas = linha.find_elements(By.TAG_NAME, "td")
            if len(celulas) >= 2:
                nome = celulas[0].text.strip()
                qtd  = celulas[1].text.strip()
                if nome and nome.lower() not in ["item", "qtd", "uni", "sub", "total"]:
                    produtos.append(f"{qtd} {nome}")
    except Exception as e:
        print(f"⚠️  Erro ao ler produtos: {e}")

    troco = 0
    try:
        texto_troco = driver.find_element(By.XPATH, "//*[contains(text(), 'Troco')]").text.strip()
        match_troco = re.search(r"=\s*R\$\s?([\d.,]+)", texto_troco)
        if match_troco:
            troco = float(match_troco.group(1).replace(".", "").replace(",", "."))
            print(f"💵 Troco: R$ {troco}")
    except:
        troco = 0

    if tipo == "Retirada":
        taxa = "Retirada"
        print("🏪 Retirada")
    else:
        taxa = 0
        try:
            resumo = driver.find_element(By.XPATH,
                "//p[text()='Subtotal' or text()='subtotal']/ancestor::*[3]"
            )
            texto_resumo = resumo.text
            print(f"📄 Resumo:\n{texto_resumo}")

            # Divide o resumo em linhas e busca "Entrega" seguido de R$ na linha seguinte
            linhas_resumo = texto_resumo.split("\n")
            for i, linha in enumerate(linhas_resumo):
                if linha.strip() == "Entrega" and i + 1 < len(linhas_resumo):
                    proxima = linhas_resumo[i + 1].strip()
                    match = re.search(r"R\$\s?([\d.,]+)", proxima)
                    if match:
                        taxa = float(match.group(1).replace(".", "").replace(",", "."))
                        print(f"🚗 Taxa: R$ {taxa}")
                        break

        except Exception as e:
            print(f"⚠️  Erro ao ler taxa: {e}")

    print(f"💸 Taxa final: {taxa} | 💵 Troco final: {troco}")

    try:
        driver.find_element(By.XPATH, "//button[.//*[@data-testid='CloseIcon']]").click()
    except:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(1)

    return ", ".join(produtos) if produtos else "", taxa, troco