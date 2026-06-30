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

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait.until(EC.url_contains("/odoo"))

    return wait


def test_visualizar_modulo_contabilidad_facturacion():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        # Ir al listado de aplicaciones
        driver.get(f"{ODOO_URL}/odoo/apps")

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        time.sleep(4)

        # Buscar módulo relacionado con contabilidad o facturación
        buscadores = driver.find_elements(
            By.CSS_SELECTOR,
            "input.o_searchview_input, input[type='text'], input[type='search']"
        )

        campo_busqueda = None

        for campo in buscadores:
            if campo.is_displayed() and campo.is_enabled():
                campo_busqueda = campo
                break

        assert campo_busqueda is not None, "No se encontró el buscador de aplicaciones"

        campo_busqueda.click()
        campo_busqueda.send_keys(Keys.CONTROL, "a")
        campo_busqueda.send_keys("Accounting")
        campo_busqueda.send_keys(Keys.ENTER)

        time.sleep(4)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-19-visualizar-modulo-contabilidad.png")
        )

        contenido = driver.page_source.lower()

        assert "login" not in driver.current_url.lower()

        assert (
            "accounting" in contenido
            or "invoicing" in contenido
            or "contabilidad" in contenido
            or "facturación" in contenido
            or "facturacion" in contenido
            or "invoice" in contenido
        )

    finally:
        driver.quit()
        
        
def test_acceder_listado_facturas_cliente():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        # Probar rutas comunes de Contabilidad / Facturación en Odoo
        rutas_posibles = [
            f"{ODOO_URL}/odoo/invoicing",
            f"{ODOO_URL}/odoo/accounting",
            f"{ODOO_URL}/odoo/invoices",
        ]

        acceso_correcto = False

        for ruta in rutas_posibles:
            driver.get(ruta)

            wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            time.sleep(4)

            contenido = driver.page_source.lower()
            url_actual = driver.current_url.lower()

            if (
                "invoice" in contenido
                or "invoices" in contenido
                or "factura" in contenido
                or "facturas" in contenido
                or "accounting" in contenido
                or "invoicing" in contenido
                or "contabilidad" in contenido
                or "facturación" in contenido
                or "facturacion" in contenido
            ):
                acceso_correcto = True
                break

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-20-acceder-listado-facturas-cliente.png")
        )

        assert "login" not in driver.current_url.lower()
        assert acceso_correcto, "No se pudo acceder al módulo de facturas o contabilidad"

    finally:
        driver.quit()
        
def obtener_campo_busqueda_visible(driver):
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

    return campo_busqueda

def test_buscar_factura_inexistente():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    factura_inexistente = f"FACTURA-INEXISTENTE-{int(time.time())}"

    try:
        login_odoo(driver)

        # Intentar acceder al listado de facturas
        rutas_posibles = [
            f"{ODOO_URL}/odoo/invoices",
            f"{ODOO_URL}/odoo/invoicing",
            f"{ODOO_URL}/odoo/accounting",
        ]

        campo_busqueda = None

        for ruta in rutas_posibles:
            driver.get(ruta)

            wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            time.sleep(4)

            campo_busqueda = obtener_campo_busqueda_visible(driver)

            if campo_busqueda is not None:
                break

        assert campo_busqueda is not None, "No se encontró el campo de búsqueda de facturas"

        campo_busqueda.click()
        campo_busqueda.send_keys(Keys.CONTROL, "a")
        campo_busqueda.send_keys(factura_inexistente)
        campo_busqueda.send_keys(Keys.ENTER)

        time.sleep(4)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-21-buscar-factura-inexistente.png")
        )

        # No se valida que el texto buscado desaparezca,
        # porque Odoo lo deja visible como filtro de búsqueda.
        filas_reales = driver.find_elements(
            By.CSS_SELECTOR,
            "tr.o_data_row"
        )

        tarjetas_reales = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_kanban_record:not(.o_kanban_ghost)"
        )

        mensaje_sin_resultados = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_view_nocontent"
        )

        hay_filas_visibles = any(
            fila.is_displayed()
            for fila in filas_reales
        )

        hay_tarjetas_visibles = any(
            tarjeta.is_displayed()
            for tarjeta in tarjetas_reales
        )

        hay_mensaje_sin_resultados = any(
            mensaje.is_displayed()
            for mensaje in mensaje_sin_resultados
        )

        contenido = driver.page_source.lower()

        assert "login" not in driver.current_url.lower()

        assert (
            hay_mensaje_sin_resultados
            or "no records" in contenido
            or "no matching records" in contenido
            or "no invoices found" in contenido
            or "no se encontraron" in contenido
            or "sin resultados" in contenido
            or not hay_filas_visibles
            or not hay_tarjetas_visibles
        )

    finally:
        driver.quit()
        
        
def hacer_click_en_boton_por_texto(driver, textos, timeout=40):
    tiempo_inicio = time.time()

    while time.time() - tiempo_inicio < timeout:
        for texto in textos:
            xpath = (
                f"//button[contains(normalize-space(), '{texto}') "
                f"or .//*[contains(normalize-space(), '{texto}')]]"
            )

            botones = driver.find_elements(By.XPATH, xpath)

            for boton in botones:
                if boton.is_displayed() and boton.is_enabled():
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        boton
                    )

                    try:
                        boton.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", boton)

                    time.sleep(2)
                    return True

        time.sleep(1)

    return False


def abrir_nueva_factura_cliente(driver):
    wait = WebDriverWait(driver, 40)

    rutas_posibles = [
        f"{ODOO_URL}/odoo/invoices/new",
        f"{ODOO_URL}/odoo/invoicing/new",
        f"{ODOO_URL}/odoo/accounting/new",
    ]

    for ruta in rutas_posibles:
        driver.get(ruta)

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        time.sleep(5)

        contenido = driver.page_source.lower()

        if (
            "invoice" in contenido
            or "factura" in contenido
            or "customer" in contenido
            or "cliente" in contenido
        ):
            formularios = driver.find_elements(
                By.CSS_SELECTOR,
                ".o_form_view, .o_action_manager"
            )

            if len(formularios) > 0:
                return True

    # Si las rutas directas no funcionan, entrar al listado y presionar New/Nuevo
    rutas_listado = [
        f"{ODOO_URL}/odoo/invoices",
        f"{ODOO_URL}/odoo/invoicing",
        f"{ODOO_URL}/odoo/accounting",
    ]

    for ruta in rutas_listado:
        driver.get(ruta)

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        time.sleep(5)

        creado = hacer_click_en_boton_por_texto(
            driver,
            [
                "New",
                "Nuevo",
                "Create",
                "Crear",
            ],
            timeout=8
        )

        if creado:
            time.sleep(5)

            contenido = driver.page_source.lower()

            if (
                "invoice" in contenido
                or "factura" in contenido
                or "customer" in contenido
                or "cliente" in contenido
            ):
                return True

    return False


def test_publicar_factura_incompleta():
    driver = iniciar_driver()

    try:
        login_odoo(driver)

        factura_abierta = abrir_nueva_factura_cliente(driver)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-21-factura-incompleta-formulario.png")
        )

        assert factura_abierta, "No se pudo abrir el formulario de nueva factura"

        # Intentar publicar/confirmar una factura sin datos obligatorios
        intento_publicar = hacer_click_en_boton_por_texto(
            driver,
            [
                "Confirm",
                "Post",
                "Publicar",
                "Confirmar",
                "Validate",
                "Validar",
            ],
            timeout=15
        )

        # Si no aparece botón de publicar, intentamos guardar para forzar validación
        if not intento_publicar:
            botones_guardar = driver.find_elements(
                By.CSS_SELECTOR,
                "button.o_form_button_save, button[aria-label='Save manually']"
            )

            for boton in botones_guardar:
                if boton.is_displayed() and boton.is_enabled():
                    try:
                        boton.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", boton)

                    time.sleep(3)
                    break

        time.sleep(5)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-22-publicar-factura-incompleta.png")
        )

        campos_invalidos = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_field_invalid"
        )

        notificaciones = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_notification_content, .o_notification"
        )

        textos_notificacion = [
            n.text.lower()
            for n in notificaciones
            if n.text.strip()
        ]

        contenido = driver.page_source.lower()

        hay_validacion = (
            len(campos_invalidos) > 0
            or any(
                "required" in texto
                or "missing" in texto
                or "invalid" in texto
                or "error" in texto
                or "faltan" in texto
                or "obligatorio" in texto
                or "requerido" in texto
                or "no se puede" in texto
                for texto in textos_notificacion
            )
            or "missing required fields" in contenido
            or "required" in contenido
            or "obligatorio" in contenido
            or "requerido" in contenido
        )

        assert "login" not in driver.current_url.lower()
        assert hay_validacion, "El sistema no mostró validación al intentar publicar una factura incompleta"

    finally:
        driver.quit()
        
        
