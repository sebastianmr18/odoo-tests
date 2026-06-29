import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".o_form_view, .o_list_view, .o_action_manager")) > 0
    )


def obtener_campo_nombre_producto(driver):
    """
    Busca el campo de nombre del producto con varios selectores,
    porque Odoo puede renderizarlo como input, textarea o widget.
    """

    script = """
    const selectors = [
        "input[name='name']",
        "textarea[name='name']",
        ".o_field_widget[name='name'] input",
        ".o_field_widget[name='name'] textarea",
        "div[name='name'] input",
        "div[name='name'] textarea",
        "input[placeholder*='Product']",
        "input[placeholder*='Producto']",
        "textarea[placeholder*='Product']",
        "textarea[placeholder*='Producto']",
        ".o_form_view input.o_input",
        ".o_form_view textarea.o_input",
        ".o_form_view input",
        ".o_form_view textarea"
    ];

    for (const selector of selectors) {
        const elementos = Array.from(document.querySelectorAll(selector));

        for (const el of elementos) {
            const visible = el.offsetParent !== null;
            const editable = !el.disabled && !el.readOnly;

            if (visible && editable) {
                el.scrollIntoView({block: "center"});
                return el;
            }
        }
    }

    return null;
    """

    return driver.execute_script(script)


def guardar_registro(driver):
    wait = WebDriverWait(driver, 40)

    boton_guardar = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.o_form_button_save, button[aria-label='Save manually']")
        )
    )

    boton_guardar.click()

    # Esperar a que Odoo quite el estado de formulario modificado
    wait.until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".o_form_dirty")) == 0
    )

    time.sleep(2)


def test_crear_producto_datos_validos():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    nombre_producto = f"Producto prueba Selenium {int(time.time())}"

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/action-433/new")

        esperar_carga_odoo(driver)

        campo_nombre = wait.until(
            EC.element_to_be_clickable((By.ID, "name_0"))
        )
        campo_nombre.click()
        campo_nombre.send_keys(Keys.CONTROL, "a")
        campo_nombre.send_keys(nombre_producto)

        campo_precio = wait.until(
            EC.element_to_be_clickable((By.ID, "list_price_0"))
        )
        campo_precio.click()
        campo_precio.send_keys(Keys.CONTROL, "a")
        campo_precio.send_keys("25000")

        campo_cantidad = wait.until(
            EC.element_to_be_clickable((By.ID, "qty_available_2"))
        )
        campo_cantidad.click()
        campo_cantidad.send_keys(Keys.CONTROL, "a")
        campo_cantidad.send_keys("10")

        guardar_registro(driver)

        campo_nombre_guardado = wait.until(
            EC.presence_of_element_located((By.ID, "name_0"))
        )

        valor_guardado = campo_nombre_guardado.get_attribute("value")

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-05-crear-producto-valido.png")
        )

        assert valor_guardado == nombre_producto
        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()


def test_crear_producto_sin_nombre():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/action-433/new")

        esperar_carga_odoo(driver)

        # Confirmar que el campo nombre existe, pero dejarlo vacío
        campo_nombre = wait.until(
            EC.element_to_be_clickable((By.ID, "name_0"))
        )
        campo_nombre.click()
        campo_nombre.send_keys(Keys.CONTROL, "a")
        campo_nombre.send_keys(Keys.BACKSPACE)

        # Ingresar precio para que el único error sea el nombre vacío
        campo_precio = wait.until(
            EC.element_to_be_clickable((By.ID, "list_price_0"))
        )
        campo_precio.click()
        campo_precio.send_keys(Keys.CONTROL, "a")
        campo_precio.send_keys("25000")

        # Intentar guardar
        boton_guardar = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.o_form_button_save, button[aria-label='Save manually']")
            )
        )
        boton_guardar.click()

        # Esperar que Odoo marque el campo Product como inválido
        wait.until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR,
                    "label[for='name_0'].o_field_invalid, div[name='name'].o_field_invalid"
                )
            ) > 0
        )

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-06-crear-producto-sin-nombre.png")
        )

        errores_nombre = driver.find_elements(
            By.CSS_SELECTOR,
            "label[for='name_0'].o_field_invalid, div[name='name'].o_field_invalid"
        )

        assert len(errores_nombre) > 0
        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()


def test_buscar_producto_existente():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    producto_buscar = "Producto prueba Selenium"

    try:
        login_odoo(driver)

        # Entrar directamente al listado/acción de productos
        driver.get(f"{ODOO_URL}/odoo/action-433")

        esperar_carga_odoo(driver)

        time.sleep(3)

        # Intentar abrir/focalizar el buscador de Odoo
        posibles_buscadores = [
            "input.o_searchview_input",
            ".o_searchview input",
            ".o_cp_searchview input",
            "input[placeholder*='Search']",
            "input[placeholder*='Buscar']",
            "input[type='search']",
            "input[type='text']",
        ]

        campo_busqueda = None

        for selector in posibles_buscadores:
            campos = driver.find_elements(By.CSS_SELECTOR, selector)

            for campo in campos:
                if campo.is_displayed() and campo.is_enabled():
                    campo_busqueda = campo
                    break

            if campo_busqueda is not None:
                break

        # Si no aparece el input, intentar activar el área de búsqueda
        if campo_busqueda is None:
            contenedores_busqueda = driver.find_elements(
                By.CSS_SELECTOR,
                ".o_searchview, .o_cp_searchview, .o_control_panel"
            )

            for contenedor in contenedores_busqueda:
                if contenedor.is_displayed():
                    contenedor.click()
                    time.sleep(1)
                    break

            for selector in posibles_buscadores:
                campos = driver.find_elements(By.CSS_SELECTOR, selector)

                for campo in campos:
                    if campo.is_displayed() and campo.is_enabled():
                        campo_busqueda = campo
                        break

                if campo_busqueda is not None:
                    break

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-17-debug-productos.png")
        )

        assert campo_busqueda is not None, "No se encontró el campo de búsqueda de productos"

        campo_busqueda.click()
        campo_busqueda.send_keys(Keys.CONTROL, "a")
        campo_busqueda.send_keys(producto_buscar)
        campo_busqueda.send_keys(Keys.ENTER)

        time.sleep(4)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-17-buscar-producto-existente.png")
        )

        assert producto_buscar in driver.page_source
        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()


def test_buscar_producto_inexistente():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    producto_inexistente = f"Producto inexistente Selenium {int(time.time())}"

    try:
        login_odoo(driver)

        # Entrar directamente al listado/acción de productos
        driver.get(f"{ODOO_URL}/odoo/action-433")

        esperar_carga_odoo(driver)

        time.sleep(3)

        posibles_buscadores = [
            "input.o_searchview_input",
            ".o_searchview input",
            ".o_cp_searchview input",
            "input[placeholder*='Search']",
            "input[placeholder*='Buscar']",
            "input[type='search']",
            "input[type='text']",
        ]

        campo_busqueda = None

        for selector in posibles_buscadores:
            campos = driver.find_elements(By.CSS_SELECTOR, selector)

            for campo in campos:
                if campo.is_displayed() and campo.is_enabled():
                    campo_busqueda = campo
                    break

            if campo_busqueda is not None:
                break

        if campo_busqueda is None:
            contenedores_busqueda = driver.find_elements(
                By.CSS_SELECTOR,
                ".o_searchview, .o_cp_searchview, .o_control_panel"
            )

            for contenedor in contenedores_busqueda:
                if contenedor.is_displayed():
                    contenedor.click()
                    time.sleep(1)
                    break

            for selector in posibles_buscadores:
                campos = driver.find_elements(By.CSS_SELECTOR, selector)

                for campo in campos:
                    if campo.is_displayed() and campo.is_enabled():
                        campo_busqueda = campo
                        break

                if campo_busqueda is not None:
                    break

        assert campo_busqueda is not None, "No se encontró el campo de búsqueda de productos"

        campo_busqueda.click()
        campo_busqueda.send_keys(Keys.CONTROL, "a")
        campo_busqueda.send_keys(producto_inexistente)
        campo_busqueda.send_keys(Keys.ENTER)

        time.sleep(4)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-18-buscar-producto-inexistente.png")
        )

        mensaje_sin_resultados = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_view_nocontent"
        )

        tarjetas_producto = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_kanban_record:not(.o_kanban_ghost)"
        )

        assert len(mensaje_sin_resultados) > 0 or "No product found" in driver.page_source
        assert len(tarjetas_producto) == 0
        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()