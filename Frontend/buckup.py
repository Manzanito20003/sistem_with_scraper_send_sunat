
import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QFileDialog, QLineEdit, QHBoxLayout, QCheckBox, QGroupBox, QGridLayout, QHeaderView,
                             QListWidget, QDialog, QMessageBox, QDateEdit)
from PyQt5.QtGui import QPixmap, QFont, QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QComboBox

from Backend.img_to_json import process_image_to_json

# DB
from DataBase.database import get_senders_and_id, insert_client, insert_product, insert_invoice, get_next_invoice_number, get_products
from DataBase.database import match_client_fuzzy,match_product_fuzzy
#scrapping
from Scraping.scraper_sunat import send_billing_sunat


from PyQt5.QtWidgets import QComboBox, QTableWidgetItem, QCompleter
from PyQt5.QtCore import Qt

#log
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Muestra mensajes desde DEBUG hacia arriba
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato de log
    datefmt="%Y-%m-%d %H:%M:%S",  # Formato de fecha
    handlers=[
        logging.FileHandler("app.log"),  # Guarda logs en un archivo
        logging.StreamHandler()  # Muestra logs en consola
    ]
)




def enviar_boleta(data, sender_id, id_client=None):
    """Guarda los datos de la boleta en la base de datos y la envía a SUNAT."""

    logging.info("Iniciando proceso de emisión de boleta...")

    if not data:
        logging.error(" No hay datos cargados en data. ¿Cargaste un JSON correctamente?")
        return

    if 'cliente' not in data or 'dni' not in data or 'ruc' not in data:
        logging.error("JSON no contiene los datos esperados: cliente, dni, ruc.")
        return

    id_sender = sender_id
    logging.info(f"ID del remitente seleccionado: {id_sender}")

    if id_client is None:

        id_client = insert_client(
            data.get('cliente', ''),
            data.get('dni') if data.get('dni') else None,
            data.get('ruc') if data.get('ruc') else None
        )


        logging.info(f" Cliente registrado con ID: {id_client}")

    if id_client is None or id_sender is None:
        logging.error("No se pudo continuar. ID Cliente o ID Sender es None.")
        return

    # 🔹 Cálculo del total de la boleta
    total_pagado = data.get("total", 0)
    igv_total = sum(p.get('Igv', 0) * p.get('precio_base', 0) * 0.18 for p in data.get('productos', []))  # IGV = 18%
    logging.info(f"Total Boleta: S/ {total_pagado:.2f}, Total IGV: S/ {igv_total:.2f}")

    # 🔹 Insertar productos en la BD
    try:
        for producto in data.get('productos', []):
            insert_product(
                id_client,
                producto.get('descripcion', ''),
                producto.get('unidad_medida', ''),
                producto.get('precio_base', 0),
                producto.get('Igv', 0)
            )
        logging.info(f"Se insertaron {len(data.get('productos', []))} productos en la BD.")

        # 🔹 Insertar la boleta en la BD
        insert_invoice(id_client, id_sender, total_pagado, igv_total)
        logging.info(f"✅ Boleta registrada correctamente en BD. (Cliente ID: {id_client}, Remitente ID: {id_sender})")

    except Exception as e:
        logging.error(f"❌ No se pudo completar la inserción de productos o la boleta. Detalle: {e}")
        return

    # 🔹 Enviar a SUNAT (Simulación)
    try:
        send_billing_sunat(data, sender_id)
        logging.info("✅Boleta enviada a SUNAT correctamente.")
    except Exception as e:
        logging.error(f"❌ Fallo en la emisión ante SUNAT. Detalle: {e}")






class RemitenteDialog(QDialog):
    """Ventana emergente para seleccionar un remitente con su ID."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Remitente")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()

        # Depuración: Ver si get_senders_and_id() funciona
        try:
            logging.info(" Intentando obtener remitentes...")
            remitentes = get_senders_and_id()  # Lista de (id, nombre)

            if not remitentes:  # Si la lista está vacía
                raise ValueError("No se encontraron remitentes en la base de datos.")

            logging.info(f" Remitentes obtenidos: {remitentes}")

            # Diccionario {nombre: id} para fácil acceso
            self.remitentes = {r[1]: r[0] for r in remitentes}
        except Exception as e:

            error_msg = f"Error al obtener remitentes: {e}"
            logging.error(" {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            self.remitentes = {}

        # Agregar los nombres a la lista visual
        self.list_widget.addItems(self.remitentes.keys())
        layout.addWidget(self.list_widget)

        select_button = QPushButton("Seleccionar")
        select_button.clicked.connect(self.select_remitente)
        layout.addWidget(select_button)

        self.setLayout(layout)

    def select_remitente(self):
        """Obtiene el remitente seleccionado y guarda su ID."""
        try:
            selected_items = self.list_widget.selectedItems()

            if not selected_items:
                print("[WARNING] Ningún remitente seleccionado.")
                QMessageBox.warning(self, "Advertencia", "Seleccione un remitente.")
                return

            nombre_seleccionado = selected_items[0].text()
            remitente_id = self.remitentes.get(nombre_seleccionado)

            # Depuración: Verificar si encontramos el ID
            logging.info(f" Remitente seleccionado: {nombre_seleccionado}, ID: {remitente_id}")

            if remitente_id is None:
                raise ValueError(f"No se encontró un ID para el remitente '{nombre_seleccionado}'.")

            self.selected_remitente = nombre_seleccionado
            self.selected_remitente_id = remitente_id
            self.accept()
        except Exception as e:
            error_msg = f"Error al seleccionar remitente: {e}"
            logging.error(f" {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

class BoletaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_remitente_id = None
        self.data = []
        self.productos_originales = {}
        self.initUI()
        self.cargar_productos= self.cargar_productos()


    def subir_imagen(self):
        file_path, _ = QFileDialog.getOpenFileName()
        if file_path:
            self.data=process_image_to_json(file_path)
            self.display_image(file_path)
            self.fill_form_fields(self.data)

    def initUI(self):
        main_layout = QHBoxLayout()

        # Frame izquierdo
        left_frame = QVBoxLayout()

        # Sección de Imagen
        self.img_label = QLabel(self)
        self.img_label.setPixmap(QPixmap("../resources/camera_icon.png").scaled(400, 400, Qt.KeepAspectRatio))
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_button = QPushButton("Subir Imagen", self)
        self.img_button.clicked.connect(self.subir_imagen)  # Ahora se asocia correctamente a la instancia


        left_frame.addWidget(self.img_label)
        left_frame.addWidget(self.img_button)

        # Sección de Datos de Boleta
        remitente_box = QGroupBox("Datos de boleta")
        remitente_box.setFixedWidth(300)

        remitente_layout = QVBoxLayout()

        # 🔹 Agregar ComboBox para seleccionar el tipo de documento
        tipo_label = QLabel("Tipo de documento:")
        self.tipo_documento_combo = QComboBox()
        self.tipo_documento_combo.addItems(["Boleta", "Factura"])
        self.tipo_documento_combo.currentTextChanged.connect(self.actualizar_serie_boleta)  # Llamar a actualizar

        self.remitente_label = QLabel("Remitente: Ninguno")
        self.remitente_label.setWordWrap(True)  # Permite que el texto se divida en varias líneas
        self.remitente_label.setFixedWidth(150)  # Ajusta el ancho máximo del QLabel (cámbialo según tu UI)


        remitente_button = QPushButton("Seleccionar Remitente")
        remitente_button.clicked.connect(self.abrir_seleccion_remitente)

        # 🔹 Agregar elementos al layout en filas separadas
        remitente_layout.addWidget(tipo_label)
        remitente_layout.addWidget(self.tipo_documento_combo)
        remitente_layout.addWidget(self.remitente_label)
        remitente_layout.addWidget(remitente_button)

        remitente_box.setLayout(remitente_layout)
        left_frame.addWidget(remitente_box)

        main_layout.addLayout(left_frame)

        # Frame derecho
        right_frame = QVBoxLayout()

        # Sección de Cliente
        cliente_box = QGroupBox("Cliente")
        cliente_layout = QGridLayout()


        self.num_doc_entry = QLineEdit()
        self.nombre_entry = QLineEdit()
        self.direccion_entry = QLineEdit()
        self.ruc_cliente = QLineEdit()

        self.ruc_cliente.textChanged.connect(self.actualizar_tipo_documento)

        self.fecha_entry = QDateEdit()
        self.fecha_entry.setCalendarPopup(True)  # Muestra un calendario emergente
        self.fecha_entry.setDate(QDate.currentDate())  # Pone la fecha actual como predeterminada

        #upper to entry
        self.nombre_entry.textChanged.connect(lambda text: self.nombre_entry.setText(text.upper()))
        self.direccion_entry.textChanged.connect(lambda text: self.direccion_entry.setText(text.upper()))
        self.ruc_cliente.textChanged.connect(lambda text: self.ruc_cliente.setText(text.upper()))

        #validator
        # Para números enteros
        self.num_doc_entry.setValidator(QIntValidator())  # Solo números enteros (0-9)

        # Para números decimales
        self.precio_entry = QLineEdit()
        self.precio_entry.setValidator(QDoubleValidator())  # Permite números con decimales

        self.cliente_nuevo = QLabel("Coincidencia: 0.00%")
        self.cliente_nuevo.setStyleSheet("font-weight: bold; color: blue;")
        # Crear el checkbox y conectarlo a una función
        self.ver_sugerencia = QCheckBox("Ver sugerencia")
        self.ver_sugerencia.stateChanged.connect(self.toggle_sugerencias)


        cliente_layout.addWidget(QLabel("No. DNI"), 0, 0)
        cliente_layout.addWidget(self.num_doc_entry, 0, 1, 1, 2)

        cliente_layout.addWidget(QLabel("Nombre"), 0, 3)
        cliente_layout.addWidget(self.nombre_entry, 0, 4)

        cliente_layout.addWidget(self.ver_sugerencia, 0, 5)
        cliente_layout.addWidget(QLabel("RUC"), 1, 0)
        cliente_layout.addWidget(self.ruc_cliente, 1, 1, 1, 2)

        cliente_layout.addWidget(QLabel("Dirección"), 1, 3)
        cliente_layout.addWidget(self.direccion_entry, 1, 4, 1, 1)


        cliente_layout.addWidget(QLabel("Fecha"), 1, 5)
        cliente_layout.addWidget(self.fecha_entry, 1,6,1,1 )

        cliente_box.setLayout(cliente_layout)
        right_frame.addWidget(cliente_box)

        # Sección de Productos
        productos_box = QGroupBox("Productos")
        productos_layout = QVBoxLayout()
        ver_sugerencias = QCheckBox("Ver Todas las sugerencias")

        self.productos_table = QTableWidget(1, 7)  # Cambiar de 8 a 7 columnas
        self.productos_table.setHorizontalHeaderLabels(
            ["Cantidad", "Unidad", "Descripción", "Precio Base", "IGV", "Total IGV", "Precio total"]
        )
        self.productos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Fijar las columnas específicas
        self.productos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # Cantidad
        self.productos_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)  # IGV

        # Ajustar el ancho de las columnas necesarias
        self.productos_table.setColumnWidth(0, 80)  # Cantidad (más estrecha)
        self.productos_table.setColumnWidth(4, 80)  # IGV (más estrecha)
        self.productos_table.setColumnWidth(2, 200)  #descipcion


        # Las demás columnas se ajustan automáticamente
        self.productos_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)


        self.productos_table.setFont(QFont("Arial", 10))
        productos_layout.addWidget(ver_sugerencias)
        productos_layout.addWidget(self.productos_table)
        productos_box.setLayout(productos_layout)
        right_frame.addWidget(productos_box)

        self.productos_table.cellClicked.connect(self.activar_autocompletado)


        # Sección de Resumen
        resumen_box = QGroupBox("Resumen de Boleta")
        resumen_layout = QVBoxLayout()

        # 🔹 Agregar etiquetas dinámicas
        self.serie_label = QLabel("Serie: B00-00")
        self.numero_label = QLabel("Número: 00")

        self.igv_label = QLabel("Total IGV: S/ 0.00")  # 🟢 Cambiará dinámicamente
        self.total_label = QLabel("Total importe: S/ 0.00")  # 🟢 Cambiará dinámicamente

        resumen_layout.addWidget(self.serie_label)
        resumen_layout.addWidget(self.numero_label)
        resumen_layout.addWidget(self.igv_label)
        resumen_layout.addWidget(self.total_label)
        resumen_box.setLayout(resumen_layout)
        right_frame.addWidget(resumen_box)

        # Botón de Envío
        self.enviar_button = QPushButton("Emitir", self)
        self.enviar_button.setStyleSheet(
            "background-color: green; color: white; font-size: 14px; padding: 12px; border-radius: 5px;")
        self.enviar_button.setMinimumHeight(40)
        self.enviar_button.clicked.connect(lambda: self.procesar_boleta())
        right_frame.addWidget(self.enviar_button)

        main_layout.addLayout(right_frame)
        self.setLayout(main_layout)
        self.setWindowTitle("Resumen de Boleta")
        self.resize(1200, 600)

    def cargar_productos(self):
        """Carga todos los productos desde la base de datos al iniciar la app."""
        try:
            self.productos_disponibles = get_products()  # Lista de tuplas (id, nombre, unidad, precio)
            logging.info(f"Se cargaron {len(self.productos_disponibles)} productos en memoria.")
        except Exception as e:
            logging.error(f"[ERROR] No se pudieron cargar los productos: {e}")
            self.productos_disponibles = []

    def activar_autocompletado(self, row, col):
        """Si el usuario hace clic en la celda de descripción, activa el autocompletado."""
        if col == 2:  # Columna de Descripción
            self.configurar_autocompletado(row)

    def configurar_autocompletado(self, row):
        """Activa un QComboBox editable con autocompletado dinámico basado en los productos precargados."""
        try:
            logging.info(f"[INFO] Configurando autocompletado en fila {row}...")

            # 🔹 Obtener la descripción actual
            descripcion_actual = self.productos_table.item(row, 2).text() if self.productos_table.item(row, 2) else ""

            if not descripcion_actual.strip():
                logging.warning(f"[WARNING] Descripción vacía en fila {row}. No se puede autocompletar.")
                return

            # 🔹 Filtrar productos precargados según lo que escribe el usuario
            productos_similares = [p for p in self.productos_disponibles if descripcion_actual.lower() in p[1].lower()]

            if not productos_similares:
                logging.info(f"[INFO] No se encontraron coincidencias para '{descripcion_actual}'.")
                return

            # 🔹 Crear un QComboBox editable con autocompletado
            combo_box = QComboBox()
            combo_box.setEditable(True)
            combo_box.setMinimumWidth(300)  # Asegurar visibilidad
            combo_box.addItem(descripcion_actual, (descripcion_actual, None, None, None))  # Producto original

            sugerencias = []
            for producto in productos_similares:
                id_producto, nombre, unidad, precio = producto  # Asegúrate de que get_products() retorna estos valores
                texto_opcion = f"{nombre} | S/ {precio:.2f} | {unidad}"
                combo_box.addItem(texto_opcion, (nombre, precio, unidad, id_producto))
                sugerencias.append(texto_opcion)

            # 🔹 Configurar autocompletado inteligente
            completer = QCompleter(sugerencias)
            completer.setCaseSensitivity(Qt.CaseInsensitive)  # Ignorar mayúsculas/minúsculas
            completer.setFilterMode(Qt.MatchContains)  # Mostrar coincidencias parciales
            combo_box.setCompleter(completer)

            # ✅ Capturar Enter para seleccionar el producto resaltado
            def on_enter_pressed():
                logging.info("[INFO] Enter presionado en autocompletado.")
                index = combo_box.currentIndex()
                if index >= 0:
                    logging.info(f"[INFO] Producto seleccionado: {combo_box.currentText()}")
                    combo_box.setCurrentIndex(index)
                    self.actualizar_producto_seleccionado(row, combo_box)

            # 🔹 Conectar eventos para la selección
            combo_box.activated.connect(lambda: combo_box.hidePopup())  # Cierra automáticamente el popup
            combo_box.currentIndexChanged.connect(lambda index: self.actualizar_producto_seleccionado(row, combo_box))
            combo_box.lineEdit().returnPressed.connect(on_enter_pressed)

            # 🔹 Insertar el QComboBox en la celda
            self.productos_table.setCellWidget(row, 2, combo_box)

        except Exception as e:
            logging.error(f"[ERROR] Ocurrió un problema en configurar_autocompletado: {e}")

    def actualizar_producto_seleccionado(self, row, combo_box):
        """Cuando el usuario elige un producto del QComboBox, actualiza la fila con sus datos."""

        datos_producto = combo_box.currentData()
        if not datos_producto:
            return

        nombre, precio, unidad, id_producto = datos_producto

        # 🔹 Asegurar que no haya un QComboBox previo en la celda
        self.productos_table.removeCellWidget(row, 2)

        # 🔹 Actualizar valores en la tabla
        self.productos_table.setItem(row, 2, QTableWidgetItem(nombre))  # Descripción
        self.productos_table.setItem(row, 1, QTableWidgetItem(unidad))  # Unidad de medida
        self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio Base
        self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio Total

        logging.info(f" Producto seleccionado: {nombre}, ID: {id_producto}, Precio: {precio}, Unidad: {unidad}")

    def actualizar_tipo_documento(self):
        """Cambia automáticamente el tipo de documento a 'Factura' si se ingresa un RUC, o a 'Boleta' si se borra."""
        if self.ruc_cliente.text().strip():  # Si hay un RUC ingresado
            self.tipo_documento_combo.setCurrentText("Factura")
        else:  # Si el RUC está vacío
            self.tipo_documento_combo.setCurrentText("Boleta")

    def actualizar_serie_boleta(self):
        """Actualiza la serie y número de documento basado en la selección de tipo y el ID del remitente."""

        id_sender = self.selected_remitente_id
        if id_sender is None:
            print("[ERROR] No se ha seleccionado un remitente.")
            return

        num_documento = get_next_invoice_number(id_sender)
        if num_documento is None:
            num_documento = 1  # 🔹 Evitar errores si la BD devuelve None

        # 🔹 Determinar el prefijo según el tipo de documento
        tipo_documento = self.tipo_documento_combo.currentText()
        prefijo = "B" if tipo_documento == "Boleta" else "F"

        serie = f"{prefijo}{id_sender:02d}-{num_documento:02d}"
        numero = f"{num_documento:02d}"

        self.serie_label.setText(f"Serie: {serie}")
        self.numero_label.setText(f"Número: {numero}")

        logging.info(f" Serie y Número actualizados: {serie} - {numero}")

    def actualizar_resumen(self):
        """Calcula y actualiza el Total IGV y el Total Importe usando la columna 'precio_total'."""
        print("entrando a actualizar_resumen")

        # 🔹 Desconectar señales temporalmente para evitar loops infinitos
        self.productos_table.blockSignals(True)

        total_importe = 0
        total_igv = 0

        for row in range(self.productos_table.rowCount()):
            total_producto_item = self.productos_table.item(row, 6)  # Total Producto
            igv_item = self.productos_table.item(row, 5)  # Total IGV

            try:
                total_producto = float(
                    total_producto_item.text().replace("S/ ", "").replace(",", ".")) if total_producto_item else 0.0
                igv_producto = float(igv_item.text().replace("S/ ", "").replace(",", ".")) if igv_item else 0.0

                total_importe += total_producto
                total_igv += igv_producto

            except ValueError as e:
                logging.warning(f"No se pudo calcular el total en fila {row}: {e}")

        self.igv_label.setText(f"Total IGV: S/ {total_igv:.2f}")
        self.total_label.setText(f"Total importe: S/ {total_importe:.2f}")

        logging.info(f" Resumen actualizado - IGV: S/ {total_igv:.2f}, Total: S/ {total_importe:.2f}")

        # 🔹 Volver a conectar señales
        self.productos_table.blockSignals(False)

    def actualizar_total_producto(self, row: int) -> None:
        """Recalcula el total del producto cuando cambia la cantidad o el precio base,
           manteniendo el precio total fijo si cambia el IGV."""

        if row < 0 or row >= self.productos_table.rowCount():
            return

        cantidad_item = self.productos_table.item(row, 0)  # Cantidad
        precio_base_item = self.productos_table.item(row, 3)  # Precio Base
        total_item = self.productos_table.item(row, 6)  # Precio Total
        igv_combo = self.productos_table.cellWidget(row, 4)  # QComboBox de IGV

        if not cantidad_item or not precio_base_item or not total_item or not igv_combo:
            return

        try:
            # ❌ 🚨 Evita bucles infinitos
            self.productos_table.blockSignals(True)  # 🔹 Desactiva señales

            cantidad = int(cantidad_item.text()) if cantidad_item.text().isdigit() else 1
            precio_base = float(
                precio_base_item.text().replace("S/ ", "").replace(",", ".")) if precio_base_item.text() else 0.0
            total_actual = float(total_item.text().replace("S/ ", "").replace(",", ".")) if total_item.text() else 0.0
            aplica_igv = igv_combo.currentText() == "Sí"

            if cantidad <= 0:
                cantidad = 1  # Evitar división por 0

            # 🟢 **Caso 1: El usuario cambió el precio base o cantidad → Recalcular total**
            total_calculado = round(precio_base * cantidad, 2)

            # 🔹 Si el IGV está activado, agregar 18% al total
            if aplica_igv:
                total_calculado = round(total_calculado * 1.18, 2)

            # 🔹 Si el total calculado es diferente del total registrado, actualizarlo
            if abs(total_calculado - total_actual) > 0.01:
                total_actual = total_calculado  # Sincronizar con el nuevo cálculo

            # 🟢 **Caso 2: El usuario cambió el IGV → Mantener el precio total y ajustar el precio base**
            if aplica_igv:
                precio_base = round(total_actual / (cantidad * 1.18), 4)
                igv_total = round((precio_base * cantidad * 0.18), 2)
            else:
                precio_base = round(total_actual / cantidad, 4)
                igv_total = 0.0

            # 🔹 Actualizar valores en la tabla sin disparar itemChanged
            self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio_base:.4f}"))  # Precio Base
            self.productos_table.setItem(row, 5, QTableWidgetItem(f"S/ {igv_total:.2f}"))  # Total IGV
            self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {total_actual:.2f}"))  # Mantener total fijo

        except ValueError as e:
            logging.warning(f" Error en los valores de la fila {row}: {e}")

        finally:
            self.productos_table.blockSignals(False)  # ✅ 🔹 Reactiva señales

            self.actualizar_resumen()
            logging.info(f" Fila {row} actualizada correctamente.")

    def actualizar_igv_producto(self, row: int) -> None:
        """Recalcula el IGV y ajusta el precio base para mantener el precio total constante.
           Si IGV es "Sí", el precio base se reduce manteniendo el precio total.
           Si IGV es "No", el precio base vuelve a su valor original."""

        logging.info(f"[INFO] Actualizando IGV del producto en fila {row}...")

        if row < 0 or row >= self.productos_table.rowCount():
            logging.warning(f"[WARNING] Fila {row} fuera de rango. No se puede actualizar IGV.")
            return

        # Obtener elementos de la tabla
        cantidad_item = self.productos_table.item(row, 0)  # Cantidad
        total_item = self.productos_table.item(row, 6)  # Precio Total del Producto
        precio_base_item = self.productos_table.item(row, 3)  # Precio Base
        igv_combo = self.productos_table.cellWidget(row, 4)  # Obtener el QComboBox de IGV

        # Verificación de existencia
        if not cantidad_item:
            logging.error(f"[ERROR] No se encontró la celda de cantidad en la fila {row}.")
            return
        if not total_item:
            logging.error(f"[ERROR] No se encontró la celda de total en la fila {row}.")
            return
        if not precio_base_item:
            logging.error(f"[ERROR] No se encontró la celda de precio base en la fila {row}.")
            return
        if igv_combo is None:
            logging.error(f"[ERROR] No se encontró un QComboBox en la fila {row}.")
            return  # Evitar crash

        try:
            cantidad = int(cantidad_item.text()) if cantidad_item.text().isdigit() else 1
            total = float(total_item.text().replace("S/ ", "").replace(",", ".")) if total_item.text() else 0.0
            precio_base_actual = float(
                precio_base_item.text().replace("S/ ", "").replace(",", ".")) if precio_base_item.text() else 0.0
            aplica_igv = igv_combo.currentText() == "Sí"

            if cantidad <= 0:
                cantidad = 1  # Evitar divisiones por 0

            logging.info(
                f"[INFO] Cantidad: {cantidad}, Total: {total}, Precio Base: {precio_base_actual}, IGV: {aplica_igv}")

            # 🔹 Desconectar señales temporalmente
            logging.debug(f"[DEBUG] Bloqueando señales en fila {row}...")
            self.productos_table.blockSignals(True)
            igv_combo.blockSignals(True)

            # Aplicar lógica de IGV
            if aplica_igv:
                if not hasattr(self, "precios_base_originales"):
                    self.precios_base_originales = {}

                if row not in self.precios_base_originales:
                    self.precios_base_originales[row] = precio_base_actual  # Guardamos el valor original

                # 🔹 Recalcular precio base quitando IGV, manteniendo el precio total constante
                precio_base = round(total / (cantidad * 1.18), 4)
                igv_unitario = round(precio_base * 0.18, 4)
                igv_total = round(igv_unitario * cantidad, 2)

            else:
                # 🔹 Restaurar el precio base original si existe, de lo contrario mantener el actual
                precio_base = self.precios_base_originales.get(row, precio_base_actual)
                igv_total = 0.0

            # 🔹 Actualizar los valores en la tabla sin disparar eventos adicionales
            logging.debug(
                f"[DEBUG] Actualizando fila {row}: Precio Base: {precio_base:.4f}, IGV Total: {igv_total:.2f}")
            self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio_base:.4f}"))  # Precio Base
            self.productos_table.setItem(row, 5, QTableWidgetItem(f"S/ {igv_total:.2f}"))  # Total IGV

            logging.info(
                f"[INFO] Fila {row} actualizada correctamente: Precio Base: S/ {precio_base:.4f}, IGV Total: S/ {igv_total:.2f}")

        except ValueError as e:
            logging.error(f"[ERROR] Error en los valores de la fila {row}: {e}")

        finally:
            # 🔹 Volver a habilitar señales después de actualizar la tabla
            logging.debug(f"[DEBUG] Desbloqueando señales en fila {row}...")
            self.productos_table.blockSignals(False)
            igv_combo.blockSignals(False)

    def toggle_sugerencias(self, state):
        """Muestra o esconde sugerencias cuando se activa/desactiva el checkbox."""
        if state == Qt.Checked:
            # 🔹 Guardar el estado actual antes de cambiarlo
            self.nombre_anterior = self.nombre_entry.text()
            self.dni_anterior = self.num_doc_entry.text()
            self.ruc_anterior = self.ruc_cliente.text()
            self.direccion_anterior = self.direccion_entry.text()

            # 🔹 Obtener sugerencia basada en el nombre ingresado
            cliente = self.nombre_entry.text()
            try:
                result= match_client_fuzzy(cliente)[0]
                print(result)
                self.id_cliente_sugerido = result[0]  # Guardar el ID del cliente sugerido

                name=result[1]
                dni=result[2]
                ruc=result[3]
                confidence=result[4]


            except Exception as e:
                print(f"Error al buscar sugerencias: {e}")
                return
            # 🔹 Cargar datos sugeridos en el formulario
            self.nombre_entry.setText(name)
            self.num_doc_entry.setText(dni)
            self.ruc_cliente.setText(ruc)
            self.direccion_entry.setText("")  # O puedes sugerir una dirección si está disponible

            # 🔹 Mostrar confianza en el QLabel
            self.cliente_nuevo.setText(f"Coincidencia:{confidence:.2f}%")
            logging.info(" Checkbox activado: Mostrando sugerencias...")

        else:
            # 🔹 Restaurar valores originales
            self.nombre_entry.setText(self.nombre_anterior)
            self.num_doc_entry.setText(self.dni_anterior)
            self.ruc_cliente.setText(self.ruc_anterior)
            self.direccion_entry.setText(self.direccion_anterior)

            self.id_cliente_sugerido = None  # Resetear ID si se desactiva la sugerencia

            self.cliente_nuevo.setText("Coincidencia: 0.00%")

            logging.info(" Checkbox desactivado: Restaurando valores originales...")

    def procesar_boleta(self):
        """Actualiza los datos y luego los envía a la base de datos."""

        logging.info(" Procesando boleta...")

        # 🔹 Validar si hay un remitente seleccionado
        if self.selected_remitente_id is None:
            print("[❌ ERROR] No se ha seleccionado un remitente. No se puede continuar.")
            QMessageBox.warning(self, "Error", "Debe seleccionar un remitente antes de emitir la boleta.")
            return


        # 🔹 Asegurar que los datos están actualizados
        self.actualizar_datos()
        logging.info(" Datos actualizados correctamente:", self.data)

        # 🔹 Validar si hay datos en self.data
        if not self.data or 'productos' not in self.data or len(self.data['productos']) == 0:
            logging.error(" No hay productos en la boleta. No se puede continuar.")
            QMessageBox.warning(self, "Error", "Debe agregar al menos un producto antes de emitir la boleta.")
            return

        # 🔹 Obtener el ID del cliente sugerido
        id_cliente = self.id_cliente_sugerido if hasattr(self, 'id_cliente_sugerido') else None
        # 🔹 Obtener el tipo de documento seleccionado
        tipo_documento = self.tipo_documento_combo.currentText()
        self.data["tipo_documento"] = tipo_documento

        print(f"🔹 [INFO] Enviando {tipo_documento} con los siguientes datos:\n"
              f"    Cliente ID: {id_cliente}\n"
              f"    Remitente ID: {self.selected_remitente_id}\n"
              f"    Tipo: {tipo_documento}\n"
              f"    Total: S/ {self.data.get('total', 0):.2f}")

        try:
            enviar_boleta(self.data, self.selected_remitente_id, id_cliente)
            logging.info(" Boleta procesada correctamente.")
            QMessageBox.information(self, "Éxito", "La boleta fue emitida correctamente.")
        except Exception as e:
            logging.error(f" Ocurrió un error al procesar la boleta: {e}")
            QMessageBox.critical(self, "Error", f"Ocurrió un error al emitir la boleta:\n{e}")

    def actualizar_datos(self):
        """Toma los valores actuales de los campos y los guarda en self.data."""
        logging.info(" Actualizando datos...")

        # 🔹 Evita intentar json.loads si self.data ya es un diccionario
        if isinstance(self.data, str):
            try:
                self.data = json.loads(self.data)
            except json.JSONDecodeError as e:
                logging.error(" No se pudo decodificar JSON: {e}")
                return

        if not isinstance(self.data, dict):
            logging.error(" self.data no es un diccionario válido.")
            return

        # 🔹 Actualizar cliente
        self.data['cliente'] = self.nombre_entry.text()
        self.data['dni'] = self.num_doc_entry.text()
        self.data['ruc'] = self.ruc_cliente.text()
        self.data['direccion'] = self.direccion_entry.text()
        self.data["fecha"] = self.fecha_entry.date().toString("dd/MM/yyyy")  # ✅ Formato correcto
        self.data["tipo_venta"]=self.tipo_documento_combo.currentText()

        # 🔹 Actualizar productos desde la tabla
        productos = []
        for row in range(self.productos_table.rowCount()):
            try:
                cantidad = int(self.productos_table.item(row, 0).text()) if self.productos_table.item(row, 0) else 1
                precio = float(
                    self.productos_table.item(row, 3).text().replace("S/ ", "")) if self.productos_table.item(row,
                                                                                                              3) else 0.0
                igv = 1 if self.productos_table.cellWidget(row,
                                                           4).currentText() == "Sí" else 0  # Obtiene el valor del QComboBox
                total_igv = float(
                    self.productos_table.item(row, 5).text().replace("S/ ", "")) if self.productos_table.item(row,
                                                                                                              5) else 0.0
                total_producto = float(
                    self.productos_table.item(row, 6).text().replace("S/ ", "")) if self.productos_table.item(row,
                                                                                                              6) else 0.0

                producto = {
                    "cantidad": cantidad,
                    "descripcion": self.productos_table.item(row, 2).text() if self.productos_table.item(row,
                                                                                                         3) else "",
                    "unidad_medida": self.productos_table.item(row, 1).text() if self.productos_table.item(row,
                                                                                                           2) else "",
                    "precio_base": precio,
                    "Igv": igv,
                    "Total IGV": total_igv,
                    "precio_total": total_producto
                }

                print("producto :",producto)
                productos.append(producto)

            except ValueError as e:
                logging.warning(f" Error al procesar fila {row}: {e}")

        self.data['productos'] = productos
        self.data['total'] = sum(p['precio_total'] for p in productos)  # 🔹 Recalcular total automáticamente

        logging.info(" Datos actualizados en self.data:", self.data)

    def fill_form_fields(self, data):
        """Llena los campos del formulario con los datos del JSON."""
        data =json.loads(data)
        if not data:
            logging.error(" No hay datos para llenar el formulario.")
            return

        # Cargar datos del cliente
        try:
            self.num_doc_entry.setText(data.get("dni", ""))
            self.nombre_entry.setText(data.get("cliente", ""))
            self.direccion_entry.setText(data.get("direccion", ""))
            self.ruc_cliente.setText(data.get("ruc", ""))
            logging.info(" Cargado los datos del cliente")
        except Exception as e:
            logging.error(" No se pudieron cargar los datos del cliente: {e}")
            return

        # Llenar tabla de productos
        productos = data.get("productos", [])
        self.productos_table.setRowCount(len(productos))
        print("Entrando a llenar los productos")

        try:
            for row, producto in enumerate(productos):
                cantidad = producto.get("cantidad", 1)
                precio = producto.get("precio_base", 0)
                precio_total=producto.get("precio_total", 0)

                #segun la regla de negocio el cliente solo pasa la boleta con el precio total del producto  aveces con precio base .

                if precio == 0 and precio_total != 0:
                    precio = precio_total / cantidad if cantidad > 0 else 0


                aplica_igv = producto.get("Igv", 0) == 1

                total_producto = cantidad*precio
                igv_producto = total_producto*0.18 if aplica_igv else 0



                # 🔹 Crear el QComboBox para IGV
                igv_combo = QComboBox()
                igv_combo.addItems(["No", "Sí"])
                igv_combo.setCurrentText("Sí" if aplica_igv else "No")


                igv_combo.currentTextChanged.connect(lambda text, row=row: self.actualizar_igv_producto(row))


                self.productos_table.setItem(row, 0, QTableWidgetItem(str(cantidad)))  # Cantidad
                self.productos_table.setItem(row, 1, QTableWidgetItem(producto.get("unidad_medida", "")))  # Unidad
                self.productos_table.setItem(row, 2,
                                                 QTableWidgetItem(producto.get("descripcion", "")))  # Descripción
                self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio
                self.productos_table.setCellWidget(row, 4, igv_combo)  # IGV con QComboBox
                self.productos_table.setItem(row, 5, QTableWidgetItem(f"S/ {igv_producto:.2f}"))  # Total IGV
                self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {total_producto:.2f}"))  # Total Producto

            # 🔹 Conectar evento para actualizar el total si el usuario cambia la cantidad o el precio
            self.productos_table.itemChanged.connect(lambda item: self.actualizar_total_producto(item.row()))

            self.actualizar_resumen()
        except Exception as e:
            logging.error(" Ocurrió un problema al llenar los datos en la fila {row}: {e}")
            logging.error(" Datos del producto problemático: {producto}")


    def display_image(self, file_path):
        """Muestra la imagen seleccionada en la interfaz."""
        pixmap = QPixmap(file_path).scaled(300, 300, Qt.KeepAspectRatio)
        self.img_label.setPixmap(pixmap)

    def abrir_seleccion_remitente(self):
        logging.info(" Abriendo selector de remitente...")
        dialog = RemitenteDialog(self)

        if dialog.exec_() == QDialog.Accepted:
            logging.info(" Remitente seleccionado correctamente.")

            if hasattr(dialog, 'selected_remitente') and hasattr(dialog, 'selected_remitente_id'):
                self.selected_remitente = dialog.selected_remitente
                self.selected_remitente_id = dialog.selected_remitente_id

                logging.info(f" Nombre Remitente: {self.selected_remitente}, ID: {self.selected_remitente_id}")

                self.remitente_label.setText(f"Remitente: {self.selected_remitente}")


                # 🔹 Actualizar la serie y número de boleta

                self.actualizar_serie_boleta()
            else:
                logging.error(" No se pudo obtener el remitente seleccionado.")
                QMessageBox.warning(self, "Error", "No se pudo obtener el remitente seleccionado.")
        else:
            logging.warning(" El selector de remitente se cerró sin seleccionar.")