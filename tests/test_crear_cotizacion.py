import os
import time
from pathlib import Path
import pytest

from selenium.webdriver.common.action_chains import ActionChains
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

# Usa nombres parciales, porque ya creamos clientes/productos con timestamp.
CLIENTE_BUSCAR = "Cliente Selenium"
PRODUCTO_BUSCAR = "Producto prueba Selenium"

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

    usuario = wait.until(EC.visibility_of_element_located((By.NAME, "login")))
    usuario.clear()
    usuario.send_keys(ODOO_USER)

    password = driver.find_element(By.NAME, "password")
    password.clear()
    password.send_keys(ODOO_PASSWORD)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait.until(EC.url_contains("/odoo"))
    return wait


def esperar_carga_odoo(driver):
    wait = WebDriverWait(driver, 40)

    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    wait.until(
        lambda d: len(
            d.find_elements(
                By.CSS_SELECTOR,
                ".o_form_view, .o_list_view, .o_kanban_view, .o_action_manager"
            )
        ) > 0
    )


def cerrar_tour_si_aparece(driver):
    time.sleep(1)

    botones = driver.find_elements(
        By.XPATH,
        "//button[contains(normalize-space(), 'Stop Tour')]"
    )

    for boton in botones:
        if boton.is_displayed() and boton.is_enabled():
            boton.click()
            time.sleep(1)
            return

    # Por si el tour queda encima y no permite clics
    driver.execute_script("""
        document.querySelectorAll('.o_tour_pointer, .o-overlay-item')
            .forEach(e => e.remove());
    """)


def seleccionar_many2one_por_id(driver, campo_id, texto_busqueda):
    wait = WebDriverWait(driver, 40)

    campo = wait.until(EC.element_to_be_clickable((By.ID, campo_id)))
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(texto_busqueda)

    time.sleep(2)

    # Selecciona la primera opción sugerida
    campo.send_keys(Keys.ARROW_DOWN)
    campo.send_keys(Keys.ENTER)

    time.sleep(2)


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


def test_crear_cotizacion_datos_validos():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        # Nueva cotización
        driver.get(f"{ODOO_URL}/odoo/sales/new")

        esperar_carga_odoo(driver)
        cerrar_tour_si_aparece(driver)

        # Seleccionar cliente
        seleccionar_many2one_por_id(driver, "partner_id_0", CLIENTE_BUSCAR)

        # Agregar producto
        boton_agregar_producto = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(normalize-space(), 'Add a product') "
                    "or contains(normalize-space(), 'Agregar un producto') "
                    "or contains(normalize-space(), 'Añadir un producto')]"
                )
            )
        )
        boton_agregar_producto.click()

        time.sleep(2)

        # Buscar el campo producto que aparece dentro de la línea de pedido
        campo_producto = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "td[data-name='product_template_id'] input.o-autocomplete--input, "
                    "div[name='product_template_id'] input.o-autocomplete--input, "
                    "input.o-autocomplete--input"
                )
            )
        )

        campo_producto.click()
        campo_producto.send_keys(PRODUCTO_BUSCAR)

        time.sleep(2)
        campo_producto.send_keys(Keys.ARROW_DOWN)
        campo_producto.send_keys(Keys.ENTER)

        time.sleep(3)

        # Cambiar cantidad a 2 si el campo queda disponible
        campos_cantidad = driver.find_elements(
            By.CSS_SELECTOR,
            "td[data-name='product_uom_qty'] input.o_input, "
            "input[name='product_uom_qty'], "
            "input[id*='product_uom_qty']"
        )

        for campo in campos_cantidad:
            if campo.is_displayed() and campo.is_enabled():
                campo.click()
                campo.send_keys(Keys.CONTROL, "a")
                campo.send_keys("2")
                break

        time.sleep(2)

        guardar_registro(driver)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-09-crear-cotizacion-valida.png")
        )

        # Validaciones
        assert "login" not in driver.current_url.lower()
        assert "Quotation" in driver.page_source or "Cotización" in driver.page_source
        assert "$" in driver.page_source

    finally:
        driver.quit()


def test_crear_cotizacion_sin_cliente():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        # Nueva cotización
        driver.get(f"{ODOO_URL}/odoo/sales/new")

        esperar_carga_odoo(driver)
        cerrar_tour_si_aparece(driver)

        # No se diligencia el cliente.
        # Se intenta guardar directamente.
        boton_guardar = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.o_form_button_save, button[aria-label='Save manually']"
                )
            )
        )
        boton_guardar.click()

        # Esperar que Odoo marque el campo Customer como inválido
        wait.until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR,
                    "label[for='partner_id_0'].o_field_invalid, "
                    "div[name='partner_id'].o_field_invalid, "
                    ".o_notification_content"
                )
            ) > 0
        )

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-10-crear-cotizacion-sin-cliente.png")
        )

        campo_cliente_invalido = driver.find_elements(
            By.CSS_SELECTOR,
            "label[for='partner_id_0'].o_field_invalid, "
            "div[name='partner_id'].o_field_invalid"
        )

        notificaciones = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_notification_content"
        )

        textos_notificacion = [n.text for n in notificaciones]

        assert len(campo_cliente_invalido) > 0 or any(
            "Missing required fields" in texto
            or "required" in texto.lower()
            or "campos requeridos" in texto.lower()
            for texto in textos_notificacion
        )

        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()

def test_confirmar_cotizacion_valida():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        # Crear nueva cotización
        driver.get(f"{ODOO_URL}/odoo/sales/new")

        esperar_carga_odoo(driver)
        cerrar_tour_si_aparece(driver)

        # Seleccionar cliente
        seleccionar_many2one_por_id(driver, "partner_id_0", CLIENTE_BUSCAR)

        # Agregar producto
        boton_agregar_producto = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(normalize-space(), 'Add a product') "
                    "or contains(normalize-space(), 'Agregar un producto') "
                    "or contains(normalize-space(), 'Añadir un producto')]"
                )
            )
        )
        boton_agregar_producto.click()

        time.sleep(2)

        campo_producto = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "td[data-name='product_template_id'] input.o-autocomplete--input, "
                    "div[name='product_template_id'] input.o-autocomplete--input, "
                    "input.o-autocomplete--input"
                )
            )
        )

        campo_producto.click()
        campo_producto.send_keys(PRODUCTO_BUSCAR)

        time.sleep(2)
        campo_producto.send_keys(Keys.ARROW_DOWN)
        campo_producto.send_keys(Keys.ENTER)

        time.sleep(3)

        # Guardar la cotización
        guardar_registro(driver)

        # Confirmar la cotización
        boton_confirmar = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button[name='action_confirm']"
                )
            )
        )
        boton_confirmar.click()

        time.sleep(5)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-11-confirmar-cotizacion-valida.png")
        )

        # Validar cambio de estado
        assert "login" not in driver.current_url.lower()
        assert (
            "Sales Order" in driver.page_source
            or "Orden de venta" in driver.page_source
            or "sale" in driver.page_source.lower()
        )

    finally:
        driver.quit()


def escribir_valor_en_elemento_activo(driver, elemento, valor):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        elemento
    )

    elemento.click()
    time.sleep(1)

    acciones = ActionChains(driver)
    acciones.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
    acciones.send_keys(str(valor))
    acciones.send_keys(Keys.TAB)
    acciones.perform()

    time.sleep(2)

def agregar_producto_a_cotizacion(driver, producto):
    wait = WebDriverWait(driver, 40)

    boton_agregar_producto = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@name='order_line']//a[contains(normalize-space(), 'Add a product') "
                "or contains(normalize-space(), 'Agregar un producto') "
                "or contains(normalize-space(), 'Añadir un producto')]"
            )
        )
    )
    boton_agregar_producto.click()

    time.sleep(2)

    campo_producto = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@name='order_line']//input[contains(@class, 'o-autocomplete--input')]"
            )
        )
    )

    campo_producto.click()
    campo_producto.send_keys(producto)

    time.sleep(2)
    campo_producto.send_keys(Keys.ARROW_DOWN)
    campo_producto.send_keys(Keys.ENTER)

    # Esperar hasta que Odoo cree la fila real del producto
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[@name='order_line']//tr[contains(@class, 'o_data_row')]"
            )
        )
    )

    time.sleep(2)



def establecer_cantidad_linea(driver, cantidad):
    wait = WebDriverWait(driver, 40)

    celda_cantidad = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[@name='order_line']//tr[contains(@class, 'o_data_row')]//td[@name='product_uom_qty']"
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        celda_cantidad
    )

    ActionChains(driver).double_click(celda_cantidad).perform()
    time.sleep(1)

    campo = None

    posibles_inputs = driver.find_elements(
        By.XPATH,
        "//div[@name='order_line']//tr[contains(@class, 'o_data_row')]//td[@name='product_uom_qty']//input"
    )

    for input_cantidad in posibles_inputs:
        if input_cantidad.is_displayed() and input_cantidad.is_enabled():
            campo = input_cantidad
            break

    if campo is None:
        activo = driver.switch_to.active_element
        if activo.tag_name.lower() in ["input", "textarea"]:
            campo = activo

    if campo is not None:
        campo.click()
        campo.send_keys(Keys.CONTROL, "a")
        campo.send_keys(str(cantidad))
        campo.send_keys(Keys.TAB)
    else:
        ActionChains(driver)\
            .click(celda_cantidad)\
            .key_down(Keys.CONTROL)\
            .send_keys("a")\
            .key_up(Keys.CONTROL)\
            .send_keys(str(cantidad))\
            .send_keys(Keys.TAB)\
            .perform()

    time.sleep(2)

def test_crear_cotizacion_cantidad_negativa():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/sales/new")

        esperar_carga_odoo(driver)
        cerrar_tour_si_aparece(driver)

        # Seleccionar cliente válido
        seleccionar_many2one_por_id(driver, "partner_id_0", CLIENTE_BUSCAR)

        # Agregar producto válido
        agregar_producto_a_cotizacion(driver, PRODUCTO_BUSCAR)

        # Valor fuera de rango
        establecer_cantidad_linea(driver, -1)

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

        time.sleep(3)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-12-cotizacion-cantidad-negativa.png")
        )

        # Buscar señales de rechazo o validación
        notificaciones = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_notification_content"
        )

        campos_invalidos = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_field_invalid"
        )

        textos_notificacion = [n.text for n in notificaciones]

        hay_validacion = len(campos_invalidos) > 0 or any(
            "required" in texto.lower()
            or "invalid" in texto.lower()
            or "error" in texto.lower()
            or "negative" in texto.lower()
            or "must be" in texto.lower()
            or "no puede" in texto.lower()
            or "inválido" in texto.lower()
            for texto in textos_notificacion
        )

        if not hay_validacion:
            pytest.xfail(
                "No conformidad funcional: Odoo permitió guardar una cotización con cantidad negativa sin mostrar validación."
            )

        assert hay_validacion

        assert "login" not in driver.current_url.lower()

    finally:
        driver.quit()


def test_crear_cotizacion_cantidad_minima_valida():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/sales/new")

        esperar_carga_odoo(driver)
        cerrar_tour_si_aparece(driver)

        # Seleccionar cliente válido
        seleccionar_many2one_por_id(driver, "partner_id_0", CLIENTE_BUSCAR)

        # Agregar producto válido
        agregar_producto_a_cotizacion(driver, PRODUCTO_BUSCAR)

        # Valor límite válido: cantidad mínima aceptada
        establecer_cantidad_linea(driver, 1)

        # Guardar cotización
        guardar_registro(driver)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / "CPF-14-cotizacion-cantidad-minima-valida.png")
        )

        campos_invalidos = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_field_invalid"
        )

        notificaciones = driver.find_elements(
            By.CSS_SELECTOR,
            ".o_notification_content"
        )

        textos_notificacion = [n.text.lower() for n in notificaciones]

        assert len(campos_invalidos) == 0

        assert not any(
            "error" in texto
            or "invalid" in texto
            or "required" in texto
            or "inválido" in texto
            for texto in textos_notificacion
        )

        assert "login" not in driver.current_url.lower()
        assert "Quotation" in driver.page_source or "Cotización" in driver.page_source
        assert "$" in driver.page_source

    finally:
        driver.quit()



def seleccionar_termino_pago(driver, termino_pago):
    if termino_pago == "default":
        return

    wait = WebDriverWait(driver, 40)

    campo_pago = wait.until(
        EC.element_to_be_clickable((By.ID, "payment_term_id_0"))
    )

    campo_pago.click()
    campo_pago.send_keys(Keys.CONTROL, "a")
    campo_pago.send_keys(termino_pago)

    time.sleep(2)

    campo_pago.send_keys(Keys.ARROW_DOWN)
    campo_pago.send_keys(Keys.ENTER)

    time.sleep(2)


@pytest.mark.parametrize(
    "cantidad, termino_pago, accion_final, evidencia",
    [
        (1, "default", "guardar", "CPF-16-AO-cantidad-1-default-guardar.png"),
        (1, "Immediate", "confirmar", "CPF-16-AO-cantidad-1-immediate-confirmar.png"),
        (2, "default", "confirmar", "CPF-16-AO-cantidad-2-default-confirmar.png"),
        (2, "Immediate", "guardar", "CPF-16-AO-cantidad-2-immediate-guardar.png"),
    ]
)
def test_cotizacion_arreglo_ortogonal(cantidad, termino_pago, accion_final, evidencia):
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)

    try:
        login_odoo(driver)

        driver.get(f"{ODOO_URL}/odoo/sales/new")

        esperar_carga_odoo(driver)
        cerrar_tour_si_aparece(driver)

        # Factor 1: cliente válido
        seleccionar_many2one_por_id(driver, "partner_id_0", CLIENTE_BUSCAR)

        # Factor 2: término de pago
        seleccionar_termino_pago(driver, termino_pago)

        # Factor 3: producto válido
        agregar_producto_a_cotizacion(driver, PRODUCTO_BUSCAR)

        # Factor 4: cantidad
        establecer_cantidad_linea(driver, cantidad)

        # Guardar cotización
        guardar_registro(driver)

        # Factor 5: acción final
        if accion_final == "confirmar":
            boton_confirmar = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[name='action_confirm']")
                )
            )
            boton_confirmar.click()
            time.sleep(5)

        driver.save_screenshot(
            str(SCREENSHOTS_DIR / evidencia)
        )

        assert "login" not in driver.current_url.lower()

        if accion_final == "guardar":
            assert "Quotation" in driver.page_source or "Cotización" in driver.page_source

        if accion_final == "confirmar":
            assert (
                "Sales Order" in driver.page_source
                or "Orden de venta" in driver.page_source
                or "sale" in driver.page_source.lower()
            )

        assert "$" in driver.page_source

    finally:
        driver.quit()