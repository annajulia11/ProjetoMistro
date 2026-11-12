import time
from datetime import datetime
from config import INTERVALO_SEGUNDOS, RENOVAR_A_CADA
from driver import criar_driver_logado
from scraping import buscar_pedidos_aceitos, buscar_pedidos_cancelados, extrair_dados_card, extrair_produtos_do_modal
from sheets import conectar_planilha, salvar_na_planilha, remover_pedido_planilha

print("🚀 Iniciando sistema de monitoramento CompreAqui...")

aba_compre_aqui = conectar_planilha()
driver = criar_driver_logado()

pedidos_ja_registrados = set()
pedidos_cancelados     = set()
ciclo = 0

print(f"🔄 Monitorando pedidos aceitos a cada {INTERVALO_SEGUNDOS} segundos...")

while True:
    try:
        ciclo += 1
        if ciclo >= RENOVAR_A_CADA:
            print("♻️  Renovando sessão preventivamente...")
            try:
                driver.quit()
            except:
                pass
            time.sleep(3)
            driver = criar_driver_logado()
            ciclo = 0

        # ── Pedidos aceitos ──────────────────────────────────────
        cards = buscar_pedidos_aceitos(driver)

        for card in cards:
            try:
                dados = extrair_dados_card(card)
                identificador = f"{dados['numero']}_{dados['data']}"

                if not dados["numero"]:
                    continue

                # Não re-registra pedidos já cancelados
                if identificador in pedidos_cancelados:
                    continue

                if identificador in pedidos_ja_registrados:
                    print(f"⏭️  Pedido #{dados['numero']} já registrado hoje.")
                    continue

                produtos, taxa, troco = extrair_produtos_do_modal(
                    driver, dados["numero"], dados["tipo"]
                )
                salvar_na_planilha(dados, produtos, taxa, troco, aba_compre_aqui)
                pedidos_ja_registrados.add(identificador)

            except Exception as e:
                print(f"⚠️  Erro ao processar card: {e}")

        # ── Pedidos cancelados ───────────────────────────────────
        cancelados = buscar_pedidos_cancelados(driver)

        for numero in cancelados:
            identificador = f"{numero}_{datetime.now().strftime('%d/%m/%Y')}"
            if identificador in pedidos_ja_registrados:
                remover_pedido_planilha(numero, aba_compre_aqui)
                pedidos_ja_registrados.discard(identificador)
                pedidos_cancelados.add(identificador)
                print(f"🚫 Pedido #{numero} marcado como cancelado")

        time.sleep(INTERVALO_SEGUNDOS)

    except Exception as e:
        print(f"❌ Erro no loop: {e}")
        print("🔄 Reiniciando em 10 segundos...")
        try:
            driver.quit()
        except:
            pass
        time.sleep(10)
        try:
            driver = criar_driver_logado()
            ciclo = 0
        except Exception as e2:
            print(f"❌ Falha ao reiniciar: {e2}")
            time.sleep(30)