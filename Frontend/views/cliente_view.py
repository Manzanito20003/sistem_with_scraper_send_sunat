"""Declaracion de la Vista Cliente"""

import logging

from PyQt5.QtCore import QDate
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QGroupBox,
    QGridLayout,
    QLineEdit,
    QDateEdit,
    QLabel,
    QWidget,
    QVBoxLayout,
)
from Frontend.utils.tools import AutComboBox, parse_cliente


class ClienteView(QWidget):
    """Clase Vista del cliente para poder ser unido con la interfaz principal"""

    def __init__(self, parent=None, tipo_documento_combo=None, cache=None):
        super().__init__()
        self.parent = parent
        self.tipo_documento_combo = tipo_documento_combo

        self.num_doc_entry = None
        self.nombre_entry = None
        self.ruc_cliente = None
        self.fecha_entry = None
        self.id_cliente_sugerido = None

        self.clientes_cache = cache
        self.initUI()

    def validate(self):
        """Valida los campos del formulario de cliente."""
        if self.parent.tipo_documento_combo.currentText() == "Factura":
            if not self.ruc_cliente.text().strip():
                return False, "El RUC es obligatorio para Factura."

        return True, ""

    def initUI(self):
        """Iniciar UI de la parte del Cliente"""
        # Grupo visual de cliente
        cliente_box = QGroupBox("Cliente")
        cliente_layout = QGridLayout()

        # Campos
        self.num_doc_entry = QLineEdit()
        self.nombre_entry = AutComboBox(
            parent=self,
            row=0,
            cache=self.clientes_cache,
            match_func=self.parent.controller.match_fuzzy,  # ya funciona con cualquier lista de tuplas
            parse_func=parse_cliente,
        )
        self.ruc_cliente = QLineEdit()
        self.fecha_entry = QDateEdit()

        # Configuración de campos
        self.num_doc_entry.setValidator(QIntValidator())
        self.num_doc_entry.setMaxLength(8)
        self.ruc_cliente.setMaxLength(11)

        self.ruc_cliente.textChanged.connect(self.actualizar_tipo_documento)
        self.fecha_entry.setCalendarPopup(True)
        self.fecha_entry.setDate(QDate.currentDate())

        # Fila 1
        cliente_layout.addWidget(QLabel("No. DNI"), 0, 0)
        cliente_layout.addWidget(self.num_doc_entry, 0, 1)

        cliente_layout.addWidget(QLabel("Nombre"), 0, 2)
        cliente_layout.addWidget(self.nombre_entry, 0, 3)

        # Fila 2
        cliente_layout.addWidget(QLabel("RUC"), 1, 0)
        cliente_layout.addWidget(self.ruc_cliente, 1, 1)

        cliente_layout.addWidget(QLabel("Fecha"), 1, 2)
        cliente_layout.addWidget(self.fecha_entry, 1, 3)

        cliente_layout.setColumnStretch(0, 1)  # Etiqueta "No. DNI" / "RUC"
        cliente_layout.setColumnStretch(1, 2)  # Campo de entrada
        cliente_layout.setColumnStretch(2, 1)  # Etiqueta "Nombre" / "Fecha"
        cliente_layout.setColumnStretch(3, 2)  # Campo de entrada


        cliente_box.setLayout(cliente_layout)

        # Layout principal para este widget
        main_layout = QVBoxLayout()
        main_layout.addWidget(cliente_box)
        self.setLayout(main_layout)

    def actualizar_tipo_documento(self):
        """Cambia automáticamente el tipo de documento a 'Factura' si se ingresa un RUC."""
        if self.ruc_cliente.text().strip():
            self.parent.tipo_documento_combo.setCurrentText("Factura")
        else:
            self.parent.tipo_documento_combo.setCurrentText("Boleta")

    def fill_form_client(self, cliente_data):
        """Llenado de los datos del cliente"""
        try:
            self.num_doc_entry.setText(cliente_data.get("dni", ""))
            self.nombre_entry.setEditText(cliente_data.get("cliente", ""))
            self.ruc_cliente.setText(cliente_data.get("ruc", ""))

            fecha_str = cliente_data.get("fecha", "")
            fecha_qdate = QDate.fromString(fecha_str, "dd/MM/yyyy")
            self.fecha_entry.setDate(fecha_qdate)
        except Exception as e:
            logging.error(
                f"No se pudieron cargar los datos del cliente: {e}", exc_info=True
            )

    def actualizar_cliente_seleccionado(self, cliente_data):
        """Actualiza los campos del formulario con los datos del cliente seleccionado."""

        logging.info("Actualizando datos del cliente sugerido")
        try:
            if cliente_data:
                nombre = cliente_data[0] or ""
                dni = cliente_data[1] or ""
                ruc = cliente_data[2] or ""
                id_cliente = cliente_data[3]

                self.nombre_entry.setEditText(nombre)
                self.num_doc_entry.setText(dni)
                self.ruc_cliente.setText(ruc)
                self.id_cliente_sugerido = id_cliente
        except Exception as e:
            logging.error(
                f"Error al actualizar cliente seleccionado: {e}", exc_info=True
            )

    def obtener_datos_cliente(self):
        """Retorna un diccionario limpio con los datos del cliente."""
        nombre = self.nombre_entry.currentText().strip().upper()
        dni = self.num_doc_entry.text().strip()
        ruc = self.ruc_cliente.text().strip()
        return {
            "nombre": nombre or None,
            "dni": dni or None,
            "ruc": ruc or None,
        }

    def clean_all(self):
        """Limpia todos los campos del formulario."""
        self.num_doc_entry.clear()
        self.nombre_entry.clear()
        self.ruc_cliente.clear()
        self.fecha_entry.setDate(QDate.currentDate())

    def obtener_fecha(self):
        fecha_str = self.fecha_entry.date().toString("dd/MM/yyyy")
        return fecha_str
