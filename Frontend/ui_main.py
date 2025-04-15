

from PyQt5.QtWidgets import ( QWidget, QLabel, QPushButton, QVBoxLayout,
                             QFileDialog, QHBoxLayout, QGroupBox,
                              QDialog, QMessageBox)
from PyQt5.QtGui import QPixmap

from Backend.img_to_json import process_image_to_json

# DB
from DataBase.database import insert_client, insert_product, insert_invoice, get_next_invoice_number, get_products
from DataBase.database import match_client_fuzzy
from Frontend.cliente_view import ClienteView
from Frontend.producto_view import ProductView
from Frontend.remitente_dialog import RemitenteDialog
from Frontend.resumen_view import ResumenView
#scrapping
from Scraping.scraper_sunat import send_billing_sunat


from PyQt5.QtWidgets import QComboBox, QTableWidgetItem, QCompleter
from PyQt5.QtCore import Qt

#log
import logging
import json

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format log
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()

    ]
)


from PyQt5.QtCore import QThread, pyqtSignal

class BoletaWorker(QThread):
    finished = pyqtSignal()           # Señal cuando termina con éxito
    error = pyqtSignal(str)           # Señal si hay un error (con mensaje)

    def __init__(self, data_boleta):
        super().__init__()
        self.data_boleta = data_boleta

    def run(self):  # Esta función en segundo plano para enviar la boleta
        try:
            enviar_boleta(self.data_boleta)
            self.finished.emit()             # Señal de éxito
        except Exception as e:
            self.error.emit(str(e))          # Señal de error


def enviar_boleta(data):
    """Guarda los datos de la boleta en la base de datos y la envía a SUNAT."""

    id_client=data["id_cliente"]
    id_sender=data["id_remitente"]
    logging.info("Iniciando proceso de emisión de boleta...")
    print("tuype:",type(data))



    logging.info(f"ID del remitente seleccionado: {id_sender}")

    if id_client is None:
        cliente=data["cliente"]
        id_client = insert_client(
            cliente["nombre"],
            cliente["dni"] if cliente["dni"]  else None,
            cliente["ruc"] if cliente["ruc"]  else None
        )


        logging.info(f" Cliente registrado con ID: {id_client}")

    if id_client is None or id_sender is None:
        logging.error("No se pudo continuar. ID Cliente o ID Sender es None.")
        return

    # 🔹 Cálculo del total de la boleta
    total_pagado = data.get("total", 0)
    igv_total=data.get("igv_total",0)
    logging.info(f"Total Boleta: S/ {total_pagado:.2f}, Total IGV: S/ {igv_total:.2f}")

    # 🔹 Insertar productos en la BD
    try:
        for producto in data['productos']:
            print("producto",producto)
            print("descripcion",producto.get("descripcion"))
            insert_product(
                id_sender,
                producto.get("descripcion"),
                producto.get("unidad_medida"),
                producto.get("precio_base"),
                producto.get("Igv")
            )


        # 🔹 Insertar la boleta en la BD
        insert_invoice(id_client, id_sender, total_pagado, igv_total)
        logging.info(f"Boleta registrada correctamente en BD. (Cliente ID: {id_client}, Remitente ID: {id_sender})")

    except Exception as e:
        logging.error(f"No se pudo completar la inserción de productos o la boleta. Detalle: {e}")
        return

    # 🔹 Enviar a SUNAT (Simulación)
    try:
        send_billing_sunat(data, id_sender)
        logging.info("Boleta enviada a SUNAT correctamente.")
    except Exception as e:
        logging.error(f"Fallo en la emisión ante SUNAT. Detalle: {e}")







class BoletaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_remitente_id = None
        self.tipo_documento_combo= None
        self.product_view = ProductView(self)  # ✅ Pasamos `self` como `parent`
        self.cliente_view = ClienteView(self,self.tipo_documento_combo)
        self.resumen_view = ResumenView()
        self.initUI()

        self.actualizar_tipo_documento= None

    def subir_imagen(self):
        logging.info(" Iniciando función subir_imagen...")

        try:
            # Selección de archivo
            file_path, _ = QFileDialog.getOpenFileName()

            if not file_path:
                logging.warning(" No se seleccionó ningún archivo.")
                QMessageBox.critical("Fallo la eleccion de img.")
                return

            # Procesar imagen
            data = process_image_to_json(file_path)

            # Convertir JSON a diccionario
            data = json.loads(data)



            # Extraer y registrar contenido
            cliente_data = data["cliente"]
            product_data = data["productos"]


            # Mostrar imagen (si lo deseas)
            self.display_image(file_path)

            self.cliente_view.fill_form_client(cliente_data)

            self.product_view.fill_form_fields(product_data)

            logging.info("Imagen procesada y datos cargados correctamente.")

        except json.JSONDecodeError as e:
            logging.error(f" Error al decodificar el JSON: {e}")
            QMessageBox.critical(self, "Error", f"El archivo no contiene un JSON válido.\n{e}")

        except Exception as e:
            logging.error(f"Error inesperado al procesar la imagen: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{e}")
    def initUI(self):
        main_layout = QHBoxLayout()

        # Frame izquierdo
        left_frame = QVBoxLayout()

        # Sección de Imagen
        self.img_label = QLabel(self)
        self.img_label.setPixmap(QPixmap("camera_icon.png").scaled(300, 300, Qt.KeepAspectRatio))
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

        self.tipo_documento_combo.currentTextChanged.connect(
            lambda current_texto: self.resumen_view.actualizar_serie_y_numero(
                self.selected_remitente_id,
                current_texto
            )
        )

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
        right_frame.addWidget(self.cliente_view)  # Ahora devuelve un QWidget

        # Sección de Productos
        right_frame.addWidget(self.product_view)  # Ahora devuelve un QWidget

        # Sección de Resumen
        right_frame.addWidget(self.resumen_view)  # ✅ Esto ahora funciona correctamente
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
        logging.info("Procesando boleta...")

        if self.selected_remitente_id is None:
            print("[❌ ERROR] No se ha seleccionado un remitente.")
            QMessageBox.warning(self, "Error", "Debe seleccionar un remitente antes de emitir la boleta.")
            return

        data_cliente=self.cliente_view.obtener_datos_cliente()
        data_producto=self.product_view.obtener_datos_producto()
        data_resumen=self.resumen_view.obtener_datos_resumen()

        data_boleta={
            "cliente":data_cliente,
            "productos":data_producto,
            "resumen":data_resumen
        }

        logging.info(f"Datos actualizados de boleta: {data_boleta}")

        if not data_boleta or 'productos' not in data_boleta or len(data_boleta['productos']) == 0:
            logging.error("No hay productos en la boleta. No se puede continuar.")
            QMessageBox.warning(self, "Error", "Debe agregar al menos un producto antes de emitir la boleta.")
            return

        id_cliente = self.cliente_view.id_cliente_sugerido  # ✅ Obtener desde cliente_view

        tipo_documento = self.tipo_documento_combo.currentText()
        data_boleta["id_cliente"]=id_cliente
        data_boleta["id_remitente"]=self.selected_remitente_id
        data_boleta["tipo_documento"] = tipo_documento

        logging.info(f"Enviando {tipo_documento} con los siguientes datos:\n"
                     f"Cliente ID: {id_cliente}\n"
                     f"Remitente ID: {self.selected_remitente_id}\n"
                     f"Total: S/ {data_boleta.get('total', 0):.2f}")

        try:
            self.worker = BoletaWorker(data_boleta)
            self.worker.finished.connect(lambda: QMessageBox.information(self, "Éxito", "La boleta fue emitida correctamente."))
            self.worker.error.connect(lambda msg: QMessageBox.critical(self, "Error", f"Ocurrió un error al emitir la boleta:\n{msg}"))

            self.enviar_button.setEnabled(False)  # Opcional: desactivar botón mientras trabaja

            self.worker.start()



        except Exception as e:
            logging.error(f"Ocurrió un error al procesar la boleta: {e}")
            QMessageBox.critical(self, "Error", f"Ocurrió un error al emitir la boleta:\n{e}")

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

                self.resumen_view.actualizar_serie_y_numero(self.selected_remitente_id, self.tipo_documento_combo.currentText())
            else:
                logging.error(" No se pudo obtener el remitente seleccionado.")
                QMessageBox.warning(self, "Error", "No se pudo obtener el remitente seleccionado.")
        else:
            logging.warning(" El selector de remitente se cerró sin seleccionar.")