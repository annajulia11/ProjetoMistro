import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import EMAIL, SENHA

def iniciar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def fazer_login(driver):
    print("🔐 Fazendo login...")
    driver.get("https://www.compraqui.app/login")
    time.sleep(3)

    try:
        botao_email = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'entrar com e-mail')]"
            ))
        )
        botao_email.click()
        time.sleep(2)
    except:
        print("⚠️  Tentando direto nos campos...")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(SENHA)
    time.sleep(1)

    driver.find_element(By.XPATH,
        "//button[@type='submit' or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'entrar')]"
    ).click()

    WebDriverWait(driver, 15).until(lambda d: "panel" in d.current_url)
    print(f"✅ Login feito. URL: {driver.current_url}")
    return driver

def criar_driver_logado():
    driver = iniciar_driver()
    fazer_login(driver)
    return driver