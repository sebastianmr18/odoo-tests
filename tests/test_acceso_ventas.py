import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def iniciar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def login_odoo(driver):
    wait = WebDriverWait(driver, 30)

    driver.get(f"{ODOO_URL}/web/login")

    usuario = wait.until(
        EC.visibility_of_element_located((By.NAME, "login"))
    )
    usuario.clear()
    usuario.send_keys(ODOO_USER)

    password = driver.find_element(By.NAME, "password")
    password.clear()
    password.send_keys(ODOO_PASSWORD)

    boton_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    boton_login.click()

    wait.until(EC.url_contains("/odoo"))

    return wait


def test_visualizar_modulo_ventas_en_apps():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 30)

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/apps")

        buscador = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input.o_searchview_input, input[type='text']")
            )
        )

        buscador.clear()
        buscador.send_keys("Sales")
        buscador.send_keys(Keys.ENTER)

        # Esperar a que la página actualice los resultados
        wait.until(
            lambda d: "Sales" in d.page_source
            or "Ventas" in d.page_source
            or "Sale" in d.page_source
        )

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-13-visualizar-modulo-ventas.png")
        )

        page_text = driver.page_source

        assert (
            "Sales" in page_text
            or "Ventas" in page_text
            or "Sale" in page_text
        )

    finally:
        driver.quit()