"""Scraping de la pagina de Sunat para enviar una boleta con .json"""
import logging
import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from DataBase.DatabaseManager import DatabaseManager

db = DatabaseManager()

logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def slow_typing(element, text):
    """tipear lento para undected"""
    element.send_keys(text)


def get_client(id_sender):
    """Obtiene los datos del cliente desde DB"""

    sender = db.get_sender_by_id(id_sender)
    logging.info(f"sende: {sender}")
    if sender:
        ruc = sender[2]
        user = sender[3]
        password = sender[4]
        return ruc, user, password


# Función para agregar productos
def agregar_producto(driver, producto, tipo_documento):
    """Agregar un producto al sistema."""
    try:
        logging.info("Agregando Productos")
        descripcion = producto["descripcion"]
        precio_base = producto["precio_base"]
        cantidad = producto["cantidad"]
        unidad_medida = producto["unidad_medida"]
        igv = producto["igv"]

        logging.debug("-" * 30)
        logging.debug(f"Descripción: {descripcion}")
        logging.debug(f"Precio base: {precio_base}")
        logging.debug(f"Cantidad: {cantidad}")
        logging.debug(f"IGV: {igv}")
        logging.debug("-" * 30)

        # Esperar que el overlay desaparezca
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.ID, "waitMessage_underlay"))
        )
        # entrar al agregar producto
        if tipo_documento == "Boleta":
            boton_adicionar = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "boleta.addItemButton"))
            )
        if tipo_documento == "Factura":
            boton_adicionar = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "factura.addItemButton_label"))
            )
        boton_adicionar.click()

        # Seleccionar tipo de ítem
        radio_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='item.subTipoTI01']"))
        )
        radio_button.click()

        # Ingresar cantidad
        campo_cantidad = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='cantidad']"))
        )
        campo_cantidad.clear()
        campo_cantidad.send_keys(str(cantidad))

        # Ingresar unidad de medida
        unidad_medida_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "item.unidadMedida"))
        )
        unidad_medida_input.clear()
        unidad_medida_input.send_keys(unidad_medida)

        # Ingresar descripción
        descripcion_textarea = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "item.descripcion"))
        )
        descripcion_textarea.clear()
        descripcion_textarea.send_keys(descripcion)

        # Ingresar precio base
        precio_unitario_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "item.precioUnitario"))
        )

        precio_unitario_input.clear()

        # hacer 4 ficras para ingresar
        precio_formateado = "{:.4f}".format(
            float(precio_base)
        )  # Convertir a 4 decimales
        precio_unitario_input.send_keys(precio_formateado)

        # verificar el ingresar igv antes ingresar preico base
        if igv == 0:
            logging.debug(f"el producto :{descripcion}  -> no tiene efecto igv")
            # tiene efecto igv
            igv_wait = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "item.subTipoTB01"))
            )
            igv_wait.click()

        boton_aceptar = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "item.botonAceptar_label"))
        )
        boton_aceptar.click()
        logging.info("Producto agregado con éxito")

    except Exception as e:
        logging.error(f"Error al agregar producto: {e}")


# Función para configurar el WebDriver
def configurar_driver():
    """Configurar el WebDriver de Chrome con las opciones adecuadas."""
    logging.info("Configurando Drivers")
    load_dotenv()

    chrome_driver_path = ChromeDriverManager().install()
    service = Service(executable_path=chrome_driver_path)

    # Opciones de Chrome
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--log-level=3")

    lista = ["enable-automation", "enable-logging"]
    chrome_options.add_experimental_option("excludeSwitches", lista)

    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver


# Función para iniciar sesión
def iniciar_sesion(driver, sender_id=1):
    """Iniciar sesión en la página utilizando credenciales de entorno."""
    try:
        logging.info("Iniciando Secion en la Pagina")
        url = os.getenv("URL")
        driver.get(url)

        # Esperar e ingresar credenciales
        ruc_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtRuc"))
        )
        usuario_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtUsuario"))
        )
        contrasena_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtContrasena"))
        )
        iniciar_sesion_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "btnAceptar"))
        )

        # Obtener credenciales
        MY_RUC, MY_USER, MY_PASS = get_client(sender_id)

        # Ingresar credenciales
        slow_typing(ruc_input, MY_RUC)
        slow_typing(usuario_input, MY_USER)
        slow_typing(contrasena_input, MY_PASS)

        # Clic en "Aceptar"
        iniciar_sesion_button.click()
        logging.info("Inicio de sesión exitoso")
    except TimeoutException:
        logging.error("Tiempo de espera excedido durante el inicio de sesión")
    except NoSuchElementException:
        logging.critical("No se encontraron los elementos de inicio de sesión")


def emitir_boleta(driver, data):
    """Función para emitir una boleta a través de la interfaz web."""
    try:
        logging.info("emitiendo boleta")
        logging.info(f"data recibida en emitir boleta: {data}")
        data_cliente = data["cliente"]
        # datos de cliente
        fecha = data["fecha"]
        cliente = data_cliente["nombre"]
        dni = data_cliente["dni"]

        # Buscar "BOLETA" en el campo de búsqueda
        campo_busqueda = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtBusca"))
        )
        campo_busqueda.send_keys("BOLETA")

        # Hacer clic en "Emitir Boleta de Venta"
        emitir_boleta_driver = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Emitir Boleta de Venta')]")
            )
        )
        emitir_boleta_driver.click()

        # Cambiar al iframe de emisión de boleta
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "iframeApplication"))
        )

        # Ingresar los datos requeridos
        input_tipo_documento = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "inicio.tipoDocumento"))
        )
        input_tipo_documento.clear()

        if dni is not None:
            logging.info("Emitiendo con dni ")
            input_tipo_documento.send_keys("DOC. NACIONAL DE IDENTIDAD")
            input_tipo_documento.send_keys(Keys.RETURN)

            input_nro_dni = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "inicio.numeroDocumento"))
            )
            input_nro_dni.send_keys(dni)
            # sacar el foco
            input_nro_dni.send_keys(Keys.TAB)

            WebDriverWait(driver, 20).until(
                lambda d: d.find_element(By.ID, "inicio.razonSocial")
                .get_attribute("value")
                .strip()
                != ""
            )

            razon_social = driver.find_element(
                By.ID, "inicio.razonSocial"
            ).get_attribute("value")

            logging.info("Razon social detectado", razon_social)
        else:
            logging.info("Emitiendo sin documento ")
            input_tipo_documento.send_keys("SIN DOCUMENTO")
            input_tipo_documento.send_keys(Keys.RETURN)

            input_razon_social = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "inicio.razonSocial"))
            )
            input_razon_social.send_keys(cliente)

        time.sleep(1)

        # continuar con el proceso de ingreso
        boton_continuar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "inicio.botonGrabarDocumento_label"))
        )
        boton_continuar.click()
        logging.info("Datos de cliente ingresados correctamente")

        input_fecha = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "boleta.fechaEmision"))
        )
        input_fecha.clear()
        input_fecha.send_keys(fecha)

        for producto in data["productos"]:
            agregar_producto(driver, producto, tipo_documento="Boleta")
        total = data["resumen"]["total"]
        succes = validate_importe_all(driver, total)
        if not succes:
            return None

        logging.info("boleta emitido correctamente")
    except TimeoutException:
        logging.error("Tiempo de espera excedido durante la emisión de la boleta")
    except NoSuchElementException:
        logging.critical(
            "No se encontraron los elementos necesarios para la emisión de la boleta"
        )


def emitir_factura(driver, data):
    """Función para emitir una factura a través de la interfaz web."""
    try:
        logging.info("emitiendo Factura")
        # datos de cliente
        data_cliente = data["cliente"]
        fecha = data["fecha"]
        ruc = data_cliente["ruc"]

        # Buscar "factura" en el campo de búsqueda
        campo_busqueda = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtBusca"))
        )
        campo_busqueda.send_keys("factura")

        # Hacer clic en "Emitir Factura"
        emitir_boleta = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='nivel4_11_5_3_1_1']/span/span")
            )
        )
        emitir_boleta.click()

        # Esperar a que el iframe esté disponible y cambiar a él (descomentado si es necesario)
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "iframeApplication"))
        )

        logging.debug("Ingresando datos de la factura...")
        logging.debug(f"RUC: {ruc}")
        logging.debug(f"Type: {type(ruc)}")

        # Ingresar el RUC
        input_ruc = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "inicio.numeroDocumento"))
        )
        input_ruc.send_keys(ruc)
        # tab para sacar el foco
        input_ruc.send_keys(Keys.TAB)
        # Esperar a que el campo de razón social se llene automáticamente
        WebDriverWait(driver, 20).until(
            lambda d: d.find_element(By.ID, "inicio.razonSocial")
            .get_attribute("value")
            .strip()
            != ""
        )
        razon_social = driver.find_element(By.ID, "inicio.razonSocial").get_attribute(
            "value"
        )

        logging.info(f"Razón Social detectada: {razon_social}")

        # Seleccionar la dirección (ID corregido)
        add_direccion = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "inicio.subTipoEstEmi00"))
        )
        add_direccion.click()

        # Presionar botón de continuar
        boton_continuar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "inicio.botonGrabarDocumento_label"))
        )
        boton_continuar.click()

        logging.info("Datos de cliente ingresados correctamente")
        # Ingresar la fecha de emisión
        input_fecha = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "factura.fechaEmision"))
        )
        input_fecha.clear()
        input_fecha.send_keys(fecha)

        # Agregar productos
        for producto in data["productos"]:
            agregar_producto(driver, producto, tipo_documento="Factura")
        logging.info("Productos agregados correctamente.")

        # Validar importe total TODO: Revisar si es necesario
        total = data["resumen"]["total"]
        succes = validate_importe_all(driver, total)
        if not succes:
            return None

    except TimeoutException:
        logging.error("Tiempo de espera excedido durante la emisión de la factura")
    except NoSuchElementException:
        logging.critical(
            "No se encontraron los elementos necesarios para la emisión de la factura"
        )
    except Exception as e:
        logging.critical(f"Error inesperado: {e}")


def send_billing_sunat(data):
    """Envía la boleta a la SUNAT utilizando un navegador automatizado."""
    logging.info("Iniciando proceso de emisión en SUNAT...")
    sender_id = data.get("id_remitente", None)
    if sender_id is None:
        logging.critical("No se ha proporcionado un ID de remitente.")
        return
    logging.info(f"Datos cargados correctamente: {data}")
    if "productos" not in data or len(data["productos"]) == 0:
        logging.critical(
            "[ERROR] La boleta no contiene productos. No se puede enviar a SUNAT."
        )
        return

    cliente = data.get("cliente", {})
    resumen = data.get("resumen", {})

    logging.info(f"   - Cliente: {cliente.get('nombre', 'N/A')}")
    logging.info(f"   - DNI: {cliente.get('dni', 'N/A')}")
    logging.info(f"   - RUC: {cliente.get('ruc', 'N/A')}")
    logging.info(f"   - Total: S/ {resumen.get('total', 0):.2f}")

    try:
        driver = configurar_driver(headless=False)  # Configurar e iniciar el driver
        iniciar_sesion(driver, sender_id)  # Iniciar sesión
        if data["tipo_documento"] == "BOLETA":
            emitir_boleta(driver, data)
        if data["tipo_documento"] == "FACTURA":
            emitir_factura(driver, data)

        logging.info(f"{data['tipo_documento']} enviado correctamente a sunat")
        # Tiempo para revisión manual si es necesario
        logging.debug(
            "Manteniendo navegador abierto por 900 segundos para revisión manual..."
        )
        time.sleep(900)
    except Exception as e:
        logging.error(
            f"Ocurrió un error durante el proceso de facturación en SUNAT: {e}"
        )
        logging.info("-----Corrigiendo Manualmente-------------")
        time.sleep(900)
    finally:
        logging.info("Finalizando proceso de emisión en SUNAT.")
        driver.quit()


def validate_importe_all(driver, total):
    """validar importe del scraping con total de data"""
    try:
        time.sleep(1)
        input_total = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "boleta.totalGeneral"))
        )

        actual_value = float(input_total.get_attribute("value").replace("S/ ", ""))

        if abs(actual_value - float(total)) < 0.001:
            logging.info(f"Importe correcto: {actual_value} ≈ {total}")
            return True
        else:
            logging.warning(f"Importe distinto: {actual_value} vs {total}")
            return False

    except Exception as e:
        logging.critical(f"Error al validar el valor: {e}")


# Ejecutar el de prueba
if __name__ == "__main__":
    # BOLETA - SIN DNI
    test_sin_dni = {
        "cliente": {"nombre": "CLIENTE SIN DOCUMENTO", "dni": "", "ruc": ""},
        "productos": [
            {
                "cantidad": 3.0,
                "descripcion": "HARINA DE TRIGO",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 2.5,
                "igv": 0.0,
                "igv_total": 0.0,
                "precio_total": 7.5,
            }
        ],
        "resumen": {"serie": "B05-19", "numero": "19", "igv_total": 0.0, "total": 7.5},
        "fecha": "09/07/2025",
        "id_cliente": None,
        "id_remitente": 5,
        "tipo_documento": "BOLETA",
    }

    # BOLETA  - CON DNI
    test_con_dni = {
        "cliente": {"nombre": "TONFAY COMPANY", "dni": "10121518", "ruc": ""},
        "productos": [
            {
                "cantidad": 2.0,
                "descripcion": "PRODUCTO 1",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 32.0,
                "igv": 0.0,
                "igv_total": 0.0,
                "precio_total": 64.0,
            },
            {
                "cantidad": 1.0,
                "descripcion": "PRODUCTO 2",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 36.0,
                "igv": 0.0,
                "igv_total": 0.0,
                "precio_total": 36.0,
            },
        ],
        "resumen": {
            "serie": "B05-18",
            "numero": "18",
            "igv_total": 0.0,
            "total": 100.0,
        },
        "fecha": "09/07/2025",
        "id_cliente": None,
        "id_remitente": 5,
        "tipo_documento": "BOLETA",
    }

    # FACTURA - CON RUC
    test_con_ruc = {
        "cliente": {"nombre": "JEFERSSON", "dni": "10267606", "ruc": "12321312r"},
        "productos": [
            {
                "cantidad": 2.0,
                "descripcion": "AVENA ",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 6.0,
                "igv": 0,
                "igv_total": 0.0,
                "precio_total": 12.0,
            },
            {
                "cantidad": 5.0,
                "descripcion": "CANCHA MONTANA",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 4.6,
                "igv": 0,
                "igv_total": 0.0,
                "precio_total": 23.0,
            },
            {
                "cantidad": 4.0,
                "descripcion": "AVP RUMBA",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 4.6,
                "igv": 0,
                "igv_total": 0.0,
                "precio_total": 18.4,
            },
            {
                "cantidad": 2.0,
                "descripcion": "MORON ENT",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 3.8,
                "igv": 0,
                "igv_total": 0.0,
                "precio_total": 7.6,
            },
            {
                "cantidad": 2.0,
                "descripcion": "PARDINA",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 6.2,
                "igv": 0,
                "igv_total": 0.0,
                "precio_total": 12.4,
            },
        ],
        "resumen": {
            "serie": "F05-24",
            "numero": "24",
            "sub_total": 73.4,
            "igv_total": 0.0,
            "total": 73.4,
        },
        "fecha": "09/07/2025",
        "id_cliente": None,
        "id_remitente": "5",
        "tipo_documento": "FACTURA",
    }

    ##test sende :
    test_sende = {
        "cliente": {"nombre": "TONFAY COMPANY", "dni": None, "ruc": None},
        "productos": [
            {
                "cantidad": 2,
                "descripcion": "GOLARINA GULLITO F+N",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 32.0,
                "igv": 0.0,
                "igv_total": 0.0,
                "precio_total": 64.0,
            },
            {
                "cantidad": 1,
                "descripcion": "GOLATINA ZONTA GUIN",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 36.0,
                "igv": 0.0,
                "igv_total": 0.0,
                "precio_total": 36.0,
            },
        ],
        "resumen": {
            "serie": "F03-01",
            "numero": "01",
            "sub_total": 100.0,
            "igv_total": 0.0,
            "total": 100.0,
        },
        "fecha": "22/07/2025",
        "id_remitente": "2",
        "id_cliente": "None",
        "tipo_documento": "BOLETA",
    }

    send_billing_sunat(test_sende)
