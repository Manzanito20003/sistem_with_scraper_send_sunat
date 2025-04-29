

from PyQt5.QtWidgets import ( QWidget, QLabel, QPushButton, QVBoxLayout,
                             QFileDialog, QHBoxLayout, QGroupBox,
                              QDialog, QMessageBox)
from PyQt5.QtGui import QPixmap

from Backend.img_to_json import process_image_to_json
from DataBase.DatabaseManager import DatabaseManager

# DB
from Frontend.cliente_view import ClienteView
from Frontend.producto_view import ProductView
from Frontend.remitente_dialog import RemitenteDialog
from Frontend.resumen_view import ResumenView
#scrapping
from Scraping.scraper_sunat import send_billing_sunat


from PyQt5.QtWidgets import QComboBox
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

    def __init__(self, boleta_data):
        super().__init__()
        self.boleta_data = boleta_data

    def run(self):  # Esta función en segundo plano para enviar la boleta
        try:
            self.db.enviar_boleta(self.boleta_data)
            self.finished.emit()             # Señal de éxito
        except Exception as e:
            self.error.emit(str(e))          # Señal de error

class Procces_imgWorker(QThread):
    finished = pyqtSignal()           # Señal cuando termina con éxito
    error = pyqtSignal(str)           # Señal si hay un error (con mensaje)
    data_signal = pyqtSignal(dict)          # Señal para enviar los datos procesados
    def __init__(self, boleta_data):
        super().__init__()
        self.boleta_data = boleta_data

    def run(self):  # Esta función en segundo plano para enviar la boleta
        try:
            data =process_image_to_json(self.boleta_data)
            if isinstance(data, str):
                data = json.loads(data)  # Asegura que sea dict

            self.data_signal.emit(data)  # Emitir la señal con los datos procesados
            self.finished.emit()
            # Señal de éxito
        except Exception as e:
            self.error.emit(str(e))          # Señal de error




class BoletaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager() # mi conexion :)

        self.selected_remitente_id = None
        self.tipo_documento_combo= None
        self.product_view = ProductView(self,)  # ✅ Pasamos `self` como `parent`
        self.cliente_view = ClienteView(self,self.tipo_documento_combo)
        self.resumen_view = ResumenView()
        self.initUI()

        self.actualizar_tipo_documento= None

    def subir_imagen(self):
        """aqui se sube la imagen y se procesa con AI """
        logging.info(" Iniciando función subir_imagen...")
        try:
            # Selección de archivo
            file_path, _ = QFileDialog.getOpenFileName()

            if not file_path:
                logging.warning(" No se seleccionó ningún archivo.")
                QMessageBox.critical("Fallo la eleccion de img.")
                return

            # Procesar imagen
            self.worker=Procces_imgWorker(file_path)
            self.worker.finished.connect(lambda msg:logging.info("img cargado correctamente"))
            self.worker.error.connect(
                lambda msg: QMessageBox.critical(self, "Error", f"Ocurrió un error al cargar la img:\n{msg}"))
            self.worker.data_signal.connect(self.cargar_datos_img)  # Conectamos la señal directamente

            self.worker.start()

            # Mostrar imagen (si lo deseas)
            self.display_image(file_path)


            logging.info("Imagen procesada y datos cargados correctamente.")

        except Exception as e:
            logging.error(f"Error inesperado al procesar la imagen: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{e}")
    def cargar_datos_img(self, data):
        # Extraer y registrar contenido
        cliente_data = data["cliente"]
        product_data = data["productos"]



        self.cliente_view.fill_form_client(cliente_data)

        self.product_view.fill_form_fields(product_data)

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

        # Botón de Borrar Todo
        self.borrar_button = QPushButton("Borrar Todo", self)
        self.borrar_button.setStyleSheet(
            "background-color: red; color: white; font-size: 12px; padding: 12px; border-radius: 5px; size: 5px;")
        self.borrar_button.clicked.connect(self.clean_all)  # Conectamos la función de borrar todo


        left_frame.addWidget(self.borrar_button)  # Agregar el botón al layout izquierdo
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
            self.productos_disponibles = self.db.get_products()  # Lista de tuplas (id, nombre, unidad, precio)
            logging.info(f"Se cargaron {len(self.productos_disponibles)} productos en memoria.")
        except Exception as e:
            logging.error(f"[ERROR] No se pudieron cargar los productos: {e}")
            self.productos_disponibles = []
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los productos: {e}")


    def procesar_boleta(self):
        """Aqui procesamos la boleta y la enviamos a la base de datos y a sunat"""
        logging.info("Procesando boleta...")

        if self.selected_remitente_id is None:
            QMessageBox.warning(self, "Error", "Debe seleccionar un remitente antes de emitir la boleta.")
            return
        validate_cliente,result=self.cliente_view.validate()
        if validate_cliente==False:
            logging.warning("Los datos del cliente no son válidos.")
            QMessageBox.warning(self, "Error", result)
            return

        data_cliente=self.cliente_view.obtener_datos_cliente()
        data_producto=self.product_view.obtener_datos_producto()
        data_resumen=self.resumen_view.obtener_datos_resumen()

        boleta_data={
            "cliente":data_cliente,
            "productos":data_producto,
            "resumen":data_resumen
        }

        logging.info(f"Datos actualizados de boleta: {boleta_data}")

        if not boleta_data or 'productos' not in boleta_data or len(boleta_data['productos']) == 0:
            logging.error("No hay productos en la boleta."
                          " No se puede continuar.")
            QMessageBox.warning(self, "Error", "Debe agregar al menos un producto antes de emitir la boleta.")
            return

        id_cliente = self.cliente_view.id_cliente_sugerido  # ✅ Obtener desde cliente_view

        tipo_documento = self.tipo_documento_combo.currentText()
        boleta_data["id_cliente"]=id_cliente
        boleta_data["id_remitente"]=self.selected_remitente_id
        boleta_data["tipo_documento"] = tipo_documento

        logging.info(f"Enviando {tipo_documento} con los siguientes datos:\n"
                     f"Cliente ID: {id_cliente}\n"
                     f"Remitente ID: {self.selected_remitente_id}\n"
                     f"Total: S/ {boleta_data.get('total', 0):.2f}")

        try:
            self.worker = BoletaWorker(boleta_data)
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
        dialog = RemitenteDialog(self,self.db)
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

    def clean_all(self):
        """Limpia todos los campos de la interfaz."""
        self.cliente_view.clean_all()
        self.product_view.clean_all()
        self.resumen_view.clean_all()
        self.img_label.clear()
        self.selected_remitente_id = None

        # activamos el boton solo de enviar
        self.enviar_button.setEnabled(True)

    def closeEvent(self, event):
        self.db.close()  # Cerra la conexión
        event.accept()

    def enviar_boleta(self,data):
        """Guarda los datos de la boleta en la base de datos y la envía a SUNAT."""

        id_client = data["id_cliente"]
        id_sender = data["id_remitente"]

        logging.info("Iniciando proceso de emisión de boleta...")
        logging.info(f"ID del remitente seleccionado: {id_sender}")

        try:
            send_billing_sunat(data, id_sender)
            logging.info("Boleta enviada a SUNAT correctamente.")
        except Exception as e:
            logging.error(f"Fallo en la emisión ante SUNAT. Detalle: {e}")

        if id_client is None:
            cliente = data["cliente"]
            id_client = self.db.insert_client(
                cliente["nombre"],
                cliente["dni"] if cliente["dni"] else None,
                cliente["ruc"] if cliente["ruc"] else None
            )
            logging.info(f" Cliente registrado con ID: {id_client}")
        if id_client is None or id_sender is None:
            logging.error("No se pudo continuar. ID Cliente o ID Sender es None.")
            return

        # 🔹 Cálculo del total de la boleta
        total_pagado = data.get("total", 0)
        igv_total = data.get("igv_total", 0)
        logging.info(f"Total Boleta: S/ {total_pagado:.2f}, Total IGV: S/ {igv_total:.2f}")

        # 🔹 Insertar productos en la BD
        try:
            for producto in data['productos']:
                self.db.insert_product(
                    id_sender,
                    producto.get("descripcion"),
                    producto.get("unidad_medida"),
                    producto.get("precio_base"),
                    producto.get("Igv")
                )
            self.db.insert_invoice(id_client, id_sender, total_pagado, igv_total)
            logging.info(f"Boleta registrada correctamente en BD. (Cliente ID: {id_client}, Remitente ID: {id_sender})")
        except Exception as e:
            logging.error(f"No se pudo completar la inserción de productos o la boleta. Detalle: {e}")
            return
