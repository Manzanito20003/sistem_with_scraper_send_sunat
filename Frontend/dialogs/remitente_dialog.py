"""Archivo de Ventana emergente Remitente"""

import logging

from PyQt5.QtWidgets import QMessageBox, QPushButton, QListWidget, QVBoxLayout, QDialog


class RemitenteDialog(QDialog):
    """Ventana emergente para seleccionar un remitente con su ID."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.selected_remitente = None
        self.selected_remitente_id = None
        self.db = db
        self.initUI()

    def initUI(self):
        """Iniciar UI remitente dialog"""
        self.setWindowTitle("Seleccionar Remitente")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()

        # Depuración: Ver si get_senders_and_id() funciona
        try:
            logging.info(" Intentando obtener remitentes...")
            remitentes = self.db.get_senders_and_id()  # Lista de (id, nombre)

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
            print("[INFO] Remitente seleccionado:", selected_items)
            nombre_seleccionado = selected_items[0].text()
            remitente_id = self.remitentes.get(nombre_seleccionado)

            logging.info(
                f" Remitente seleccionado: {nombre_seleccionado}," f"ID: {remitente_id}"
            )

            if remitente_id is None:
                raise ValueError(
                    f"No se encontró un ID para el remitente '{nombre_seleccionado}'."
                )

            self.selected_remitente = nombre_seleccionado
            self.selected_remitente_id = remitente_id
            self.accept()
        except Exception as e:
            error_msg = f"Error al seleccionar remitente: {e}"
            logging.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
