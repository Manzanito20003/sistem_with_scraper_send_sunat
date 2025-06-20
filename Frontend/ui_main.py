# Standard
import json
import logging

# Third-party
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QGroupBox, QDialog, QMessageBox, QComboBox
)

# App-specific
from Backend.BoletaController import BoletaController, BoletaWorker
from Backend.img_to_json import process_image_to_json
from DataBase.DatabaseManager import DatabaseManager
from Frontend.cliente_view import ClienteView
from Frontend.producto_view import ProductView
from Frontend.remitente_dialog import RemitenteDialog
from Frontend.resumen_view import ResumenView

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
        self.controller = BoletaController(self.db)

        self.selected_remitente_id = None
        self.tipo_documento_combo= None
        self.product_view = ProductView(self,)
        self.cliente_view = ClienteView(self,self.tipo_documento_combo)
        self.resumen_view = ResumenView(db=self.db)
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

            data= process_image_to_json(file_path)  # Procesar la imagen
            data = json.loads(data)
            self.cargar_datos_img(data)  # Cargar los datos en la vista
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
        logging.info("Procesando boleta...")

        if not self.controller.validar_envio(self.selected_remitente_id, self.cliente_view):
            return

        boleta_data = self.controller.armar_boleta_data(
            self.cliente_view, self.product_view, self.resumen_view,
            self.selected_remitente_id,
            self.tipo_documento_combo.currentText()
        )

        logging.info(f"Datos actualizados de boleta: {boleta_data}")

        self.enviar_button.setEnabled(False)
        self.controller.emitir_boleta(boleta_data)
        print("enviado")
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
    def on_boleta_emitida(self):
        QMessageBox.information(self, "Éxito", "Boleta emitida correctamente")
        self.enviar_button.setEnabled(True)

    def on_boleta_error(self, mensaje):
        QMessageBox.critical(self, "Error", f"No se pudo emitir la boleta:\n{mensaje}")
        self.enviar_button.setEnabled(True)



