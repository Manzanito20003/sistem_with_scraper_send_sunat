"""UI principal para el manejo de los componenetes y vistas"""

import json
import logging

# Third-party
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QGroupBox,
    QDialog,
    QMessageBox,
    QComboBox,
)
from Frontend.utils.Threads import TaskWorker

# App-specific
from Backend.BoletaController import BoletaController
from Backend.utils.img_to_json import process_image_to_json
from DataBase.DatabaseManager import DatabaseManager
from Frontend.cliente_view import ClienteView
from Frontend.producto_view import ProductView
from Frontend.remitente_dialog import RemitenteDialog
from Frontend.resumen_view import ResumenView
from Frontend.utils.ZoomLabel import ZoomLabel


class BoletaApp(QWidget):
    def __init__(self):
        super().__init__()

        self.img_button = None
        self.borrar_button = None
        self.remitente_label = None
        self.enviar_button = None
        self.productos_disponibles = None
        self.selected_remitente = None
        self.selected_remitente_id = None
        self.actualizar_tipo_documento = None
        self.worker = None  # para hilos

        self.db = DatabaseManager()
        self.productos_cache = self.db.get_products()
        self.clientes_cache = self.db.get_clients()

        self.controller = BoletaController(self.db)
        self.img_label = None
        self.tipo_documento_combo = QComboBox()
        self.tipo_documento_combo.addItems(["Boleta", "Factura"])

        self.product_view = ProductView(self, cache=self.productos_cache)
        self.cliente_view = ClienteView(
            self, self.tipo_documento_combo, cache=self.clientes_cache
        )
        self.resumen_view = ResumenView(db=self.db)

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()

        # Frame izquierdo
        left_frame = QVBoxLayout()

        # Sección de Imagen
        self.img_label = ZoomLabel(self)
        self.img_label.setPixmap(
            QPixmap("camera_icon.png").scaled(500, 500, Qt.KeepAspectRatio)
        )
        self.img_label.setFixedSize(300,350)

        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_button = QPushButton("Subir Imagen", self)
        # Ahora se asocia correctamente a la instancia
        self.img_button.clicked.connect(self.subir_imagen)

        left_frame.addWidget(self.img_label)
        left_frame.addWidget(self.img_button)

        # Sección de Datos de Boleta
        remitente_box = QGroupBox("Datos de boleta")
        remitente_box.setFixedWidth(300)

        remitente_layout = QVBoxLayout()

        # Botón de Borrar Todo
        self.borrar_button = QPushButton("Borrar Todo", self)
        self.borrar_button.setStyleSheet(
                '''
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border-radius: 7px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2);
                padding: 8px;
                margin: 3
                px;
            }
            QPushButton:hover {
                background-color: darkred;
            }
        """
        """  # Estilo del botón
            QPushButton:pressed {
                background-color: lightcoral;
            }


        ''')
        self.borrar_button.clicked.connect(
            self.clean_all
        )  # Conectamos la función de borrar todo

        left_frame.addWidget(self.borrar_button)  # Agregar el botón al layout izquierdo
        tipo_label = QLabel("Tipo de documento:")
        self.tipo_documento_combo = QComboBox()
        self.tipo_documento_combo.addItems(["Boleta", "Factura"])

        self.tipo_documento_combo.currentTextChanged.connect(
            lambda current_texto: self.resumen_view.actualizar_serie_y_numero(
                self.selected_remitente_id, current_texto
            )
        )

        self.remitente_label = QLabel("Remitente: Ninguno")
        self.remitente_label.setWordWrap(
            True
        )  # Permite que el texto se divida en varias líneas
        self.remitente_label.setFixedWidth(150)  # ajustar el ancho maximo

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
        right_frame.addWidget(self.resumen_view)
        # Botón de Envío
        self.enviar_button = QPushButton("Emitir", self)
        self.enviar_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)


        self.enviar_button.setMinimumHeight(40)
        self.enviar_button.clicked.connect(lambda: self.procesar_boleta())
        right_frame.addWidget(self.enviar_button)

        main_layout.addLayout(right_frame)
        self.setLayout(main_layout)
        self.setWindowTitle("Resumen de Boleta")
        self.resize(1200, 600)

    def subir_imagen(self):
        """Aqui se sube la imagen y se procesa con AI"""
        logging.info(" Iniciando función subir_imagen...")
        try:
            # Selección de archivo
            file_path, _ = QFileDialog.getOpenFileName()

            if not file_path:
                logging.warning(" No se seleccionó ningún archivo.")
                QMessageBox.critical("Fallo la eleccion de imagen.")
                return
            self.display_image(file_path)

            self.worker = TaskWorker(process_image_to_json, file_path)
            self.worker.finished.connect(self.on_img_processed)
            self.worker.error.connect(
                lambda e: QMessageBox.critical(self, "Error", str(e))
            )
            self.worker.start()

        except Exception as e:
            logging.error(f"Error inesperado al procesar la imagen: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{e}")

    def on_img_processed(self, result):
        try:
            data = json.loads(result)
            self.cargar_datos_img(data)
            logging.info("Imagen procesada y datos cargados correctamente.")
        except Exception as e:
            logging.error(f"Error cargando imagen: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def cargar_datos_img(self, data):
        # Extraer y registrar contenido
        cliente_data = data["cliente"]
        product_data = data["productos"]

        self.cliente_view.fill_form_client(cliente_data)
        self.product_view.fill_form_fields(product_data)

    def cargar_productos(self):
        """Carga todos los productos desde la base de datos al iniciar la app."""
        try:
            # Lista de tuplas (id, nombre, unidad, precio)
            self.productos_disponibles = self.db.get_products()
            logging.info(
                f"Se cargaron {len(self.productos_disponibles)} productos en memoria."
            )
        except Exception as e:
            logging.error(f"[ERROR] No se pudieron cargar los productos: {e}")
            self.productos_disponibles = []
            QMessageBox.critical(
                self, "Error", f"No se pudieron cargar los productos: {e}"
            )

    def procesar_boleta(self):
        logging.info("Procesando boleta...")

        ok, msg = self.controller.validar_envio(
            self.selected_remitente_id, self.cliente_view
        )

        if not ok:
            QMessageBox.warning(self, "Error", msg)
            return

        boleta_data = self.controller.armar_boleta_data(
            self.cliente_view,
            self.product_view,
            self.resumen_view,
            self.selected_remitente_id,
            self.tipo_documento_combo.currentText(),
        )

        logging.info(f"Datos actualizados de boleta: {boleta_data}")
        # self.enviar_button.setEnabled(False)

        # Guardamos el worker como atributo
        self.worker = TaskWorker(self.controller.emitir_boleta, boleta_data)
        self.worker.finished.connect(self.on_boleta_resultado)
        self.worker.error.connect(self.on_boleta_error)
        self.worker.start()

    def on_boleta_resultado(self, success):
        if success:
            QMessageBox.information(self, "Éxito", "Boleta emitida correctamente")
        else:
            QMessageBox.warning(self, "Error", "No se pudo emitir la boleta.")

    def on_boleta_error(self, mensaje):
        QMessageBox.critical(self, "Error crítico", f"Ocurrió un error:\n{mensaje}")
        self.enviar_button.setEnabled(True)

    def display_image(self, file_path):
        """Muestra la imagen seleccionada en la interfaz."""
        pixmap = QPixmap(file_path).scaled(500, 500, Qt.KeepAspectRatio)
        self.img_label.setPixmap(pixmap)

    def abrir_seleccion_remitente(self):
        logging.info(" Abriendo selector de remitente...")
        dialog = RemitenteDialog(self, self.db)
        if dialog.exec_() == QDialog.Accepted:
            logging.info(" Remitente seleccionado correctamente.")

            if hasattr(dialog, "selected_remitente") and hasattr(
                dialog, "selected_remitente_id"
            ):
                self.selected_remitente = dialog.selected_remitente
                self.selected_remitente_id = dialog.selected_remitente_id

                logging.info(
                    f" Nombre Remitente: {self.selected_remitente},"
                    f" ID: {self.selected_remitente_id}"
                )

                self.remitente_label.setText(f"Remitente: {self.selected_remitente}")
                self.resumen_view.actualizar_serie_y_numero(
                    self.selected_remitente_id, self.tipo_documento_combo.currentText()
                )

            else:
                logging.error(" No se pudo obtener el remitente seleccionado.")
                QMessageBox.warning(
                    self, "Error", "No se pudo obtener el remitente seleccionado."
                )
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
