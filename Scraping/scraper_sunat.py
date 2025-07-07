import os
import time
from datetime import datetime

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

import logging

logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)  # Crea la carpeta si no existe

log_file = os.path.join(log_dir, f"sunat_{datetime.today().date()}.log")

# Configura logging
logging.basicConfig(
    filename=log_file,
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def slow_typing(element, text, delay=0.1):
    # for char in text:
    #     element.send_keys(char)
    #     time.sleep(delay)
    element.send_keys(text)


def get_client(id):
    """Obtiene los datos del cliente desde DB"""
    sender = db.get_sender_by_id(id)

    logging.info(f"sende: {sender}")
    if sender:
        ruc = sender[2]
        user = sender[3]
        password = sender[4]
        return ruc, user, password
    else:
        return None, None, None


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
            print("el producto no tiene efecto igv")
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
def configurar_driver(headless=True):
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
        slow_typing(ruc_input, MY_RUC, delay=0.2)
        slow_typing(usuario_input, MY_USER, delay=0.15)
        slow_typing(contrasena_input, MY_PASS, delay=0.1)

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
        fecha = data_cliente["fecha"]
        cliente = data_cliente["nombre"]
        dni = data_cliente["dni"]

        # Buscar "BOLETA" en el campo de búsqueda
        campo_busqueda = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtBusca"))
        )
        campo_busqueda.send_keys("BOLETA")

        # Hacer clic en "Emitir Boleta de Venta"
        emitir_boleta = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Emitir Boleta de Venta')]")
            )
        )
        emitir_boleta.click()

        # Cambiar al iframe de emisión de boleta
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "iframeApplication"))
        )

        # Ingresar los datos requeridos
        input_tipo_documento = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "inicio.tipoDocumento"))
        )
        input_tipo_documento.clear()

        if dni != "":
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

        input_fecha = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "boleta.fechaEmision"))
        )
        input_fecha.clear()
        input_fecha.send_keys(fecha)

        for producto in data["productos"]:
            agregar_producto(driver, producto, tipo_documento="Boleta")
        total = data["resumen"]["total"]
        validate_importe_all(driver, total)

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
        fecha = data_cliente["fecha"]
        # cliente = data_cliente["cliente"] # no es necesario
        # dni = data_cliente["dni"]   # no es necesario
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

        print(f"Razón Social detectada: {razon_social}")

        time.sleep(1)

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

        # Ingresar la fecha de emisión
        input_fecha = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "factura.fechaEmision"))
        )
        input_fecha.clear()
        input_fecha.send_keys(fecha)

        # Agregar productos
        for producto in data["productos"]:
            agregar_producto(driver, producto, tipo_documento="Factura")
        print("Productos agregados correctamente.")

        # Validar importe total TODO: Revisar si es necesario
        total = data["resumen"]["total"]
        validate_importe_all(driver, total)

    except TimeoutException:
        logging.error("Tiempo de espera excedido durante la emisión de la factura")
    except NoSuchElementException:
        logging.critical(
            "No se encontraron los elementos necesarios para la emisión de la factura"
        )
    except Exception as e:
        logging.critical(f"Error inesperado: {e}")


def send_billing_sunat(data, sender_id=1):
    """Envía la boleta a la SUNAT utilizando un navegador automatizado."""
    logging.info("Iniciando proceso de emisión en SUNAT...")
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
        driver = configurar_driver()  # Configurar e iniciar el driver
        iniciar_sesion(driver, sender_id)  # Iniciar sesión
        if data["tipo_documento"] == "BOLETA":
            emitir_boleta(driver, data)
        if data["tipo_documento"] == "FACTURA":
            emitir_factura(driver, data)

        logging.info(f"{data['tipo_documento']}enviado correctamente a sunat")
        # Tiempo para revisión manual si es necesario
        logging.debug(
            "Manteniendo navegador abierto por 900 segundos para revisión manual..."
        )
        time.sleep(900)

    except Exception as e:
        logging.error(
            f"Ocurrió un error durante el proceso de facturación en SUNAT: {e}"
        )
    finally:
        logging.info("[INFO] Finalizando proceso de emisión en SUNAT.")
        driver.quit()


def validate_importe_all(driver, total):
    """
    Validates that the total value in the input box matches the expected total.

    :param driver: WebDriver instance
    :param total: Expected total as a string
    :return: True if the value matches the expected total, False otherwise
    """
    try:
        input_total = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "boleta.totalGeneral2"))
        )
        actual_value = int(input_total.get_attribute("value"))

        # Compara el valor obtenido con el valor esperado
        if float(actual_value) == float(total):
            logging.info("El valor de la caja coincide con el total esperado.")
            return True
        else:
            logging.error(
                f"El valor de la caja ({actual_value}) no coincide con el total esperado ({total})."
            )
            return False

    except Exception as e:
        logging.critical(f"Error al validar el valor: {e}")
        return False


# Ejecutar el de prueba
if __name__ == "__main__":
    data = {
        "cliente": {
            "nombre": "TONFAY COMPANY",
            "dni": "75276980",
            "ruc": "",
            "fecha": "03/07/2025",
        },
        "productos": [
            {
                "cantidad": 2.0,
                "descripcion": "",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 32.0,
                "Igv": 0,
                "Total IGV": 0.0,
                "precio_total": 64.0,
            },
            {
                "cantidad": 1.0,
                "descripcion": "",
                "unidad_medida": "KILOGRAMO",
                "precio_base": 36.0,
                "Igv": 0,
                "Total IGV": 0.0,
                "precio_total": 36.0,
            },
        ],
        "resumen": {
            "serie": "B05-18",
            "numero": "18",
            "igv_total": 0.0,
            "total": 100.0,
        },
        "id_cliente": None,
        "id_remitente": 5,
        "tipo_documento": "BOLETA",
    }

    send_billing_sunat(data, sender_id=2)
