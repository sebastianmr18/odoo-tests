import os
from pathlib import Path

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

SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def iniciar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


@pytest.mark.parametrize(
    "usuario, password, nombre_evidencia",
    [
        ("", "", "CPF-15-login-usuario-vacio-password-vacio.png"),
        (ODOO_USER, "", "CPF-15-login-usuario-valido-password-vacio.png"),
        ("", ODOO_PASSWORD, "CPF-15-login-usuario-vacio-password-valido.png"),
        ("usuario_invalido@test.com", "clave_incorrecta", "CPF-15-login-usuario-password-invalidos.png"),
    ]
)
def test_login_tabla_decision_combinaciones_invalidas(usuario, password, nombre_evidencia):
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(f"{ODOO_URL}/web/login")

        campo_usuario = wait.until(
            EC.visibility_of_element_located((By.NAME, "login"))
        )
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)

        campo_password = driver.find_element(By.NAME, "password")
        campo_password.clear()
        campo_password.send_keys(password)

        boton_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        boton_login.click()

        # Si el navegador bloquea por campo requerido, seguimos en login.
        # Si Odoo procesa credenciales inválidas, también debe quedarse en login.
        wait.until(
            lambda d: "/web/login" in d.current_url
            or "login" in d.current_url.lower()
        )

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / nombre_evidencia)
        )

        assert "login" in driver.current_url.lower()
        assert "/odoo/apps" not in driver.current_url

    finally:
        driver.quit()