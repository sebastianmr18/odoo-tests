import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    yield driver
    driver.quit()


def test_login_credenciales_validas(driver):
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

    # Odoo 19 redirige después del login a /odoo/apps
    wait.until(EC.url_contains("/odoo/apps"))

    assert "/odoo/apps" in driver.current_url
    assert "login" not in driver.current_url.lower()

    driver.save_screenshot("screenshots/CPF-03-login-exitoso.png")

def test_login_credenciales_invalidas(driver):
    wait = WebDriverWait(driver, 30)

    driver.get(f"{ODOO_URL}/web/login")

    usuario = wait.until(
        EC.visibility_of_element_located((By.NAME, "login"))
    )
    usuario.clear()
    usuario.send_keys("usuario_invalido@test.com")

    password = driver.find_element(By.NAME, "password")
    password.clear()
    password.send_keys("clave_incorrecta")

    boton_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    boton_login.click()

    # Debe quedarse en la pantalla de login
    wait.until(EC.url_contains("/web/login"))

    # Buscar mensaje de error
    errores = driver.find_elements(
        By.CSS_SELECTOR,
        ".alert-danger, .text-danger, .o_notification"
    )

    driver.save_screenshot("screenshots/CPF-04-login-invalido.png")

    assert "/web/login" in driver.current_url
    assert len(errores) > 0