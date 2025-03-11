import json
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
from selenium.webdriver.chrome.service import Service


from DataBase.database import get_sender_by_id




def slow_typing(element, text, delay=0.1):
    # for char in text:
    #     element.send_keys(char)
    #     time.sleep(delay)

    element.send_keys(text)



def get_client(id):
    """Obtiene los datos del cliente desde DB"""
    sender=get_sender_by_id(id)

    print("sende:",sender)
    print(get_sender_by_id(id))
    if sender:
        ruc=sender[2]
        user=sender[3]
        password=sender[4]
        return ruc,user,password
    else:
        return None,None,None


# Función para agregar productos
def agregar_producto(driver, producto,tipo_documento):
    """Agregar un producto al sistema."""
    try:
        descripcion=producto["descripcion"]
        precio_base=producto["precio_base"]
        cantidad=producto["cantidad"]
        unidad_medida=producto["unidad_medida"]
        igv=producto["Igv"]

        print("--" * 15)
        print("\ndescripcion:",descripcion)
        print("\nprecio_base:", precio_base)
        print("\ncantidad:", cantidad)
        print("\nigv:", igv)

        print("--" * 15)
        #entrar al agregar producto
        if tipo_documento=="Boleta":
            boton_adicionar = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "boleta.addItemButton"))
            )
        if tipo_documento=="Factura":
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
        print("se puso correctamente la descipcion")
        # Ingresar precio base
        precio_unitario_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "item.precioUnitario"))
        )


        precio_unitario_input.clear()

        # hacer 4 ficras para ingresar
        precio_formateado = "{:.4f}".format(float(precio_base))  # Convertir a 4 decimales
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
        print("Producto agregado con éxito")

    except Exception as e:
        print(f"Error al agregar producto: {e}")


# Función para configurar el WebDriver
def configurar_driver(headless=True):
    """Configurar el WebDriver de Chrome con las opciones adecuadas."""
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

    lista = [
        'enable-automation',
        'enable-logging'
    ]
    chrome_options.add_experimental_option('excludeSwitches', lista)

    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver


# Función para iniciar sesión
def iniciar_sesion(driver,sender_id=1):
    """Iniciar sesión en la página utilizando credenciales de entorno."""
    try:
        url = os.getenv('URL')
        driver.get(url)

        # Esperar e ingresar credenciales
        ruc_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtRuc")))
        usuario_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtUsuario")))
        contrasena_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtContrasena")))
        iniciar_sesion_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "btnAceptar")))

        # Obtener credenciales
        MY_RUC,MY_USER,MY_PASS=get_client(sender_id)


        # Ingresar credenciales
        slow_typing(ruc_input, MY_RUC, delay=0.2)
        slow_typing(usuario_input, MY_USER, delay=0.15)
        slow_typing(contrasena_input, MY_PASS, delay=0.1)

        # Clic en "Aceptar"
        iniciar_sesion_button.click()
        print("Inicio de sesión exitoso")

    except TimeoutException:
        print("Tiempo de espera excedido durante el inicio de sesión")
    except NoSuchElementException:
        print("No se encontraron los elementos de inicio de sesión")


# Función para emitir boleta
# def dowload_send():

#
# # Clic en el botón "Continuar"
#
# boton_continuar = WebDriverWait(driver, 20).until(
#     EC.element_to_be_clickable((By.ID, "boleta.botonGrabarDocumento_label"))
# )
# boton_continuar.click()
#
# boton_continuar = WebDriverWait(driver, 20).until(
#     EC.element_to_be_clickable((By.ID, "docsrel.botonGrabarDocumento_label")))
#
# boton_continuar.click()  # Hacer clic en el botón
#
# print("Boleta emitida con éxito")

def emitir_boleta(driver,data):
    """Función para emitir una boleta a través de la interfaz web."""
    try:
        tipo_venta=data["tipo_venta"]  # Boleta o factura

        fecha=data["fecha"]
        cliente=data["cliente"]
        dni=data["dni"]
        ruc=data["ruc"]

        # Buscar "BOLETA" en el campo de búsqueda
        campo_busqueda = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txtBusca")))
        campo_busqueda.send_keys("BOLETA")

        # Hacer clic en "Emitir Boleta de Venta"
        emitir_boleta = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Emitir Boleta de Venta')]")))
        emitir_boleta.click()
        print("[DEBUG] Emitiendo boleta de venta...")


        # Cambiar al iframe de emisión de boleta
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "iframeApplication")))

        # Ingresar los datos requeridos
        input_tipo_documento = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "inicio.tipoDocumento")))
        input_tipo_documento.clear()

        if dni!="":
            print("el dcoumento es con dni")
            input_tipo_documento.send_keys("DOC. NACIONAL DE IDENTIDAD")
            input_tipo_documento.send_keys(Keys.RETURN)

            input_nro_dni = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "inicio.numeroDocumento")))
            input_nro_dni.send_keys(dni)
            print("se puso correctamente el tipo de documento con DNI:", dni)
            #sacar el foco
            input_nro_dni.send_keys(Keys.TAB)

            input_razon_social=WebDriverWait(driver, 20).until(
                lambda d: d.find_element(By.ID, "inicio.razonSocial").get_attribute("value").strip() != ""
            )
            razon_social = input_razon_social.get_attribute("value")

            print(f"Razón Social detectada: {razon_social}")

        else:
            input_tipo_documento.send_keys("SIN DOCUMENTO")
            input_tipo_documento.send_keys(Keys.RETURN)
            print("se puso correctamente el tipo de documento")

            input_razon_social = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "inicio.razonSocial")))
            input_razon_social.send_keys(cliente)
            print("se puso correctamente la razon social")

        time.sleep(1)


        #continuar con el proceso de ingreso
        boton_continuar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "inicio.botonGrabarDocumento_label")))
        boton_continuar.click()
        print("se puso correctamente el boton continuar")

        #agregar fechar

        """ LA FECHA SOLO DEBE SER OPCIONAL EN CASO (NO HAY SE DEBE PONER LA DE HOY)"""

        date_validated = validate_date(fecha)


        input_fecha = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "boleta.fechaEmision"))
        )
        input_fecha.clear()
        input_fecha.send_keys(date_validated)

        for producto in data["productos"]:
            agregar_producto(driver, producto,tipo_documento="Boleta")
        print("products added correctly :)")
        total=data["total"]
        validate_importe_all(driver,total)


    except TimeoutException:
        print("Tiempo de espera excedido durante la emisión de la boleta")
    except NoSuchElementException:
        print("No se encontraron los elementos necesarios para la emisión de la boleta")



def emitir_factura(driver, data):
    """Función para emitir una factura a través de la interfaz web."""
    try:
        fecha = data.get("fecha", None)  # Usa None si no se proporciona fecha
        cliente = data["cliente"]
        dni = data["dni"]
        ruc = data["ruc"]

        # Buscar "factura" en el campo de búsqueda
        campo_busqueda = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtBusca"))
        )
        campo_busqueda.send_keys("factura")

        # Hacer clic en "Emitir Factura"
        emitir_boleta = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='nivel4_11_5_3_1_1']/span/span"))
        )
        emitir_boleta.click()
        print("[DEBUG] Emitiendo factura de venta...")

        # Esperar a que el iframe esté disponible y cambiar a él (descomentado si es necesario)
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "iframeApplication"))
        )

        # Ingresar el RUC
        input_ruc = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "inicio.numeroDocumento"))
        )
        input_ruc.send_keys(ruc)
        #tab para sacar el foco
        input_ruc.send_keys(Keys.TAB)
        # Esperar a que el campo de razón social se llene automáticamente
        WebDriverWait(driver, 20).until(
            lambda d: d.find_element(By.ID, "inicio.razonSocial").get_attribute("value").strip() != ""
        )
        razon_social = driver.find_element(By.ID, "inicio.razonSocial").get_attribute("value")

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
        print("Se presionó correctamente el botón continuar")

        # Manejo de fecha (si no hay fecha, se usa la de hoy)
        if not fecha:
            fecha = datetime.today().strftime("%d/%m/%Y")

        input_fecha = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "factura.fechaEmision"))
        )
        input_fecha.clear()
        input_fecha.send_keys(fecha)

        # Agregar productos
        for producto in data["productos"]:
            agregar_producto(driver, producto,tipo_documento="Factura")
        print("Productos agregados correctamente.")

        # Validar importe total
        total = data["total"]
        validate_importe_all(driver, total)

    except TimeoutException:
        print("⚠️ Tiempo de espera excedido durante la emisión de la factura")
    except NoSuchElementException:
        print("❌ No se encontraron los elementos necesarios para la emisión de la factura")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")







def send_billing_sunat(data, sender_id=1):
    """Envía la boleta a la SUNAT utilizando un navegador automatizado."""

    print("\n🔹 [DEBUG] Iniciando proceso de emisión en SUNAT...")

    # Validación de datos
    if not data:
        print("[❌ ERROR] No hay datos en `data`. No se puede emitir la boleta.")
        return

    if 'productos' not in data or len(data['productos']) == 0:
        print("[❌ ERROR] La boleta no contiene productos. No se puede enviar a SUNAT.")
        return

    print(f"[INFO] Enviando boleta con los siguientes datos:\n"
          f"    - Remitente ID: {sender_id}\n"
          f"    - Cliente: {data.get('cliente', 'N/A')}\n"
          f"    - DNI: {data.get('dni', 'N/A')}\n"
          f"    - RUC: {data.get('ruc', 'N/A')}\n"
          f"    - Total: S/ {data.get('total', 0):.2f}\n"
          f"    - Cantidad de productos: {len(data.get('productos', []))}")

    try:
        print("[DEBUG] Configurando WebDriver para conexión con SUNAT...")
        driver = configurar_driver()  # Configurar e iniciar el driver
        print("[SUCCESS] WebDriver configurado correctamente.")

        print(f"[DEBUG] Iniciando sesión en SUNAT con remitente ID: {sender_id}...")
        iniciar_sesion(driver, sender_id)  # Iniciar sesión
        print("[SUCCESS] Sesión iniciada correctamente.")

        print("[DEBUG] Enviando SUNAT...")
        if data["tipo_documento"]=="Boleta":
            print("se va a emitir una boleta")
            emitir_boleta(driver, data)
        if data["tipo_documento"]=="Factura":
            print("se va a emitir una factura")
            emitir_factura(driver,data)


        print("✅ [SUCCESS] Boleta enviada correctamente a SUNAT.")

        # Tiempo para revisión manual si es necesario
        print("[DEBUG] Manteniendo navegador abierto por 900 segundos para revisión manual...")
        time.sleep(900)

    except Exception as e:
        print(f"[❌ ERROR] Ocurrió un error durante el proceso de facturación en SUNAT: {e}")
    finally:
        print("[INFO] Finalizando proceso de emisión en SUNAT.")
        # driver.quit()  # Descomentar para cerrar el navegador después de la revisión


def calculate_unit_price(total_price, quantity, includes_tax):
    """
    Calculates the unit price of a product with or without tax.

    :param total_price: Total price of the product
    :param quantity: Total quantity of products sold
    :param includes_tax: (1) includes tax, (0) without tax
    :return: Unit price with or without tax, formatted to 4 decimal places
    """
    if includes_tax == 1:
        unit_price = round(total_price / (quantity * 1.18), 4)
    else:
        unit_price = round(total_price / quantity, 4)

    return f"{unit_price:.4f}"


def parse_date(date_str):
    """
    Converts a date string in "dd-mm-yy" format to a datetime.date object.

    :param date_str: Date as a string in "dd-mm-yy" format.
    :return: datetime.date object if valid, or None if date_str is None.
    :raises ValueError: If the date format is invalid.
    """
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%d-%m-%y").date()
    except ValueError:
        raise ValueError("Invalid date format. Expected format: dd-mm-yy.")


def validate_date(date_emision):
    today_date = datetime.today().date()
    formatted_today = today_date.strftime("%d/%m/%Y")

    try:
        # Convertir la fecha de emisión a objeto date
        date_emision_obj = datetime.strptime(date_emision, "%d/%m/%Y").date()

        # Verificar si la fecha de emisión es mayor a 2 días antes de hoy
        if (today_date - date_emision_obj).days > 2:
            print("[ERROR] La fecha de emisión es mayor a 2 días")
            return None  # Indicar que la fecha no es válida

        return formatted_today  # Retorna la fecha actual en formato correcto

    except ValueError as e:
        print(f"[ERROR] Ocurrió un error en la validación de fecha: {e}")
        return None  # Indicar error



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
            print("El valor de la caja coincide con el total esperado.")
            return True
        else:
            print(f"El valor de la caja ({actual_value}) no coincide con el total esperado ({total}).")
            return False

    except Exception as e:
        print("Error al validar el valor:", e)
        return False





# Ejecutar el de prueba
if __name__ == "__main__":
    json_file_path = '../DataBase/response.json'
    # Abrir y cargar el contenido del archivo JSON
    data = []
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        send_billing_sunat(data,sender_id=2)
