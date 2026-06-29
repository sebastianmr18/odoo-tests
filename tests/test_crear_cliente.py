import os
import time
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


def esperar_carga_odoo(driver):
    wait = WebDriverWait(driver, 40)

    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    wait.until(
        lambda d: len(
            d.find_elements(
                By.CSS_SELECTOR,
                ".o_form_view, .o_list_view, .o_kanban_view, .o_action_manager"
            )
        ) > 0
    )


def escribir_campo(campo, valor):
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(valor)


def guardar_registro(driver):
    wait = WebDriverWait(driver, 40)

    boton_guardar = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.o_form_button_save, button[aria-label='Save manually']")
        )
    )

    boton_guardar.click()

    wait.until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".o_form_dirty")) == 0
    )

    time.sleep(2)


def test_crear_cliente_datos_validos():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    timestamp = int(time.time())
    nombre_cliente = f"Cliente Selenium {timestamp}"
    correo_cliente = f"cliente{timestamp}@test.com"
    telefono_cliente = "3001234567"

    try:
        login_odoo(driver)

        # Ruta directa al formulario nuevo de contactos
        driver.get(f"{ODOO_URL}/odoo/contacts/new")

        esperar_carga_odoo(driver)

        campo_nombre = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[name='name'] input.o-autocomplete--input")
            )
        )
        escribir_campo(campo_nombre, nombre_cliente)

        campo_email = wait.until(
            EC.element_to_be_clickable((By.ID, "email_0"))
        )
        escribir_campo(campo_email, correo_cliente)

        campo_telefono = wait.until(
            EC.element_to_be_clickable((By.ID, "phone_0"))
        )
        escribir_campo(campo_telefono, telefono_cliente)

        campo_direccion = wait.until(
            EC.element_to_be_clickable((By.ID, "street_0"))
        )
        escribir_campo(campo_direccion, "Calle 10 # 20-30")

        campo_ciudad = wait.until(
            EC.element_to_be_clickable((By.ID, "city_0"))
        )
        escribir_campo(campo_ciudad, "Cali")

        guardar_registro(driver)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-07-crear-cliente-valido.png")
        )

        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()



def test_crear_cliente_sin_nombre():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    timestamp = int(time.time())
    correo_cliente = f"cliente_sin_nombre{timestamp}@test.com"
    telefono_cliente = "3009876543"

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/contacts/new")

        esperar_carga_odoo(driver)

        # Dejar el nombre vacío
        campo_nombre = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[name='name'] input.o-autocomplete--input")
            )
        )
        campo_nombre.click()
        campo_nombre.send_keys(Keys.CONTROL, "a")
        campo_nombre.send_keys(Keys.BACKSPACE)

        # Llenar otros campos válidos para que el error sea solo por el nombre
        campo_email = wait.until(
            EC.element_to_be_clickable((By.ID, "email_0"))
        )
        escribir_campo(campo_email, correo_cliente)

        campo_telefono = wait.until(
            EC.element_to_be_clickable((By.ID, "phone_0"))
        )
        escribir_campo(campo_telefono, telefono_cliente)

        # Intentar guardar
        boton_guardar = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.o_form_button_save, button[aria-label='Save manually']"
                )
            )
        )
        boton_guardar.click()

        # Esperar que Odoo marque el campo como inválido o muestre notificación
        wait.until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR,
                    "div[name='name'].o_field_invalid, .o_notification_content"
                )
            ) > 0
        )

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-08-crear-cliente-sin-nombre.png")
        )

        campo_invalido = driver.find_elements(
            By.CSS_SELECTOR,
            "div[name='name'].o_field_invalid"
        )

        notificaciones = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_notification_content"
        )

        textos_notificacion = [n.text for n in notificaciones]

        assert len(campo_invalido) > 0 or any(
            "Missing required fields" in texto
            or "campos requeridos" in texto.lower()
            or "required" in texto.lower()
            for texto in textos_notificacion
        )

        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()