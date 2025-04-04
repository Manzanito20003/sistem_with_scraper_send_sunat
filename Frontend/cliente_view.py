import json
import logging

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLineEdit, QDateEdit, QLabel, QCheckBox, QWidget, QVBoxLayout

from DataBase.database import match_client_fuzzy


class ClienteView(QWidget):
    def __init__(self, parent=None, tipo_documento_combo=None):
        super().__init__()  # ✅ Llamar al constructor de la clase base

        self.parent = parent
        self.tipo_documento_combo = tipo_documento_combo  # ✅ Ahora tiene acceso a tipo_documento_combo

        self.num_doc_entry = None
        self.nombre_entry = None
        self.ruc_cliente = None
        self.fecha_entry = None

        self.ver_sugerencia = None
        self.nombre_anterior = None
        self.dni_anterior = None
        self.ruc_anterior = None
        self.id_cliente_sugerido = None
        self.tipo_documento_combo = None

        self.initUI()

        self.data = {}

    def initUI(self):
        # Grupo visual de cliente
        cliente_box = QGroupBox("Cliente")
        cliente_layout = QGridLayout()

        # Campos
        self.num_doc_entry = QLineEdit()
        self.nombre_entry = QLineEdit()
        self.ruc_cliente = QLineEdit()
        self.fecha_entry = QDateEdit()
        self.ver_sugerencia = QCheckBox("Ver sugerencia")

        # Configuración de campos
        self.ruc_cliente.textChanged.connect(self.actualizar_tipo_documento)
        self.fecha_entry.setCalendarPopup(True)
        self.fecha_entry.setDate(QDate.currentDate())
        self.num_doc_entry.setValidator(QIntValidator())



        # Agregar widgets al layout
        cliente_layout.addWidget(QLabel("No. DNI"), 0, 0)
        cliente_layout.addWidget(self.num_doc_entry, 0, 1, 1, 2)

        cliente_layout.addWidget(QLabel("Nombre"), 0, 3)
        cliente_layout.addWidget(self.nombre_entry, 0, 4)

        cliente_layout.addWidget(self.ver_sugerencia, 0, 5)

        cliente_layout.addWidget(QLabel("RUC"), 1, 0)
        cliente_layout.addWidget(self.ruc_cliente, 1, 1, 1, 2)

        cliente_layout.addWidget(QLabel("Fecha"), 1, 5)
        cliente_layout.addWidget(self.fecha_entry, 1, 6, 1, 1)

        cliente_box.setLayout(cliente_layout)

        # Layout principal para este widget
        main_layout = QVBoxLayout()
        main_layout.addWidget(cliente_box)
        self.setLayout(main_layout)


    def actualizar_tipo_documento(self):
        """Cambia automáticamente el tipo de documento a 'Factura' si se ingresa un RUC."""

        if self.ruc_cliente.text().strip():  # Si hay un RUC ingresado
            self.parent.tipo_documento_combo.setCurrentText("Factura")

        else:
            self.parent.tipo_documento_combo.setCurrentText("Boleta")

    def toggle_sugerencias(self, state):
        if state == Qt.Checked:
            self.nombre_anterior = self.nombre_entry.text()
            self.dni_anterior = self.num_doc_entry.text()
            self.ruc_anterior = self.ruc_cliente.text()

            cliente = self.nombre_entry.text()
            try:
                result = match_client_fuzzy(cliente)[0]
                print(result)

                self.id_cliente_sugerido = result[0]

                self.nombre_entry.setText(result[1])
                self.num_doc_entry.setText(result[2])
                self.ruc_cliente.setText(result[3])


                # ✅ Actualizar `BoletaApp`
                if self.parent:
                    self.parent.id_cliente_sugerido = self.id_cliente_sugerido

            except Exception as e:
                print(f"Error al buscar sugerencias: {e}")

    def fill_form_client(self, cliente_data):
        try:
            self.num_doc_entry.setText(cliente_data.get("dni", ""))
            self.nombre_entry.setText(cliente_data.get("cliente", ""))
            self.ruc_cliente.setText(cliente_data.get("ruc", ""))
            #para el fecha
            fecha_str=cliente_data.get("fecha","")
            fecha_qdate = QDate.fromString(fecha_str, "dd/MM/yy")
            self.fecha_entry.setDate(fecha_qdate)
        except Exception as e:
            logging.error(f"No se pudieron cargar los datos del cliente: {e}", exc_info=True)

    def obtener_datos_cliente(self):
        """Obtiene los datos del cliente ingresados en el formulario."""
        self.data['nombre'] = self.nombre_entry.text()
        self.data['dni'] = self.num_doc_entry.text()
        self.data['ruc'] = self.ruc_cliente.text()
        self.data["fecha"] = self.fecha_entry.date().toString("dd/MM/yyyy")  # ✅ Formato correcto

        return self.data