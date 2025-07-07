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


class ClienteView(QWidget):
    def __init__(self, parent=None, tipo_documento_combo=None):
        super().__init__()
        self.parent = parent
        self.tipo_documento_combo = tipo_documento_combo

        self.num_doc_entry = None
        self.nombre_entry = None
        self.ruc_cliente = None
        self.fecha_entry = None
        self.id_cliente_sugerido = None

        self.initUI()

        self.data = {}

    def validate(self):
        """Valida los campos del formulario de cliente."""
        if self.parent.tipo_documento_combo.currentText() == "Factura":
            if not self.ruc_cliente.text().strip():
                return False, "El RUC es obligatorio para Factura."

        return True, ""

    def initUI(self):
        # Grupo visual de cliente
        cliente_box = QGroupBox("Cliente")
        cliente_layout = QGridLayout()

        # Campos
        self.num_doc_entry = QLineEdit()
        self.nombre_entry = QLineEdit()
        self.ruc_cliente = QLineEdit()
        self.fecha_entry = QDateEdit()

        # Configuración de campos
        self.num_doc_entry.setValidator(QIntValidator())
        self.num_doc_entry.setMaxLength(8)
        self.ruc_cliente.setMaxLength(11)

        self.ruc_cliente.textChanged.connect(self.actualizar_tipo_documento)
        self.fecha_entry.setCalendarPopup(True)
        self.fecha_entry.setDate(QDate.currentDate())

        # Agregar widgets al layout
        cliente_layout.addWidget(QLabel("No. DNI"), 0, 0)
        cliente_layout.addWidget(self.num_doc_entry, 0, 1, 1, 2)

        cliente_layout.addWidget(QLabel("Nombre"), 0, 3)
        cliente_layout.addWidget(self.nombre_entry, 0, 4)

        cliente_layout.addWidget(QLabel("RUC"), 1, 0)
        cliente_layout.addWidget(self.ruc_cliente, 1, 1, 1, 2)

        cliente_layout.addWidget(QLabel("Fecha"), 1, 3)
        cliente_layout.addWidget(self.fecha_entry, 1, 4, 1, 1)

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
        try:
            self.num_doc_entry.setText(cliente_data.get("dni", ""))
            self.nombre_entry.setText(cliente_data.get("cliente", ""))
            self.ruc_cliente.setText(cliente_data.get("ruc", ""))

            fecha_str = cliente_data.get("fecha", "")
            fecha_qdate = QDate.fromString(fecha_str, "dd/MM/yyyy")
            self.fecha_entry.setDate(fecha_qdate)
        except Exception as e:
            logging.error(
                f"No se pudieron cargar los datos del cliente: {e}", exc_info=True
            )

    def obtener_datos_cliente(self):
        """Obtiene los datos del cliente ingresados en el formulario."""
        self.data["nombre"] = self.nombre_entry.text()
        self.data["dni"] = self.num_doc_entry.text()
        self.data["ruc"] = self.ruc_cliente.text()
        self.data["fecha"] = self.fecha_entry.date().toString("dd/MM/yyyy")

        return self.data

    def clean_all(self):
        """Limpia todos los campos del formulario."""
        self.num_doc_entry.clear()
        self.nombre_entry.clear()
        self.ruc_cliente.clear()
        self.fecha_entry.setDate(QDate.currentDate())
