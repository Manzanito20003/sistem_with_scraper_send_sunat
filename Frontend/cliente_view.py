import json
import logging

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLineEdit, QDateEdit, QLabel, QCheckBox, QWidget

from DataBase.database import match_client_fuzzy


class ClienteView(QWidget):
    def __init__(self, parent=None, tipo_documento_combo=None):
        super().__init__()  # ✅ Llamar al constructor de la clase base

        self.parent = parent
        self.tipo_documento_combo = tipo_documento_combo  # ✅ Ahora tiene acceso a tipo_documento_combo

        self.num_doc_entry = None
        self.nombre_entry = None
        self.direccion_entry = None
        self.ruc_cliente = None
        self.fecha_entry = None

        self.cliente_nuevo = None
        self.ver_sugerencia = None
        self.nombre_anterior = None
        self.dni_anterior = None
        self.ruc_anterior = None
        self.direccion_anterior = None
        self.id_cliente_sugerido = None
        self.tipo_documento_combo = None

        self.initUI()

        self.data = {}

    def initUI(self):
        cliente_widget= QWidget()
        cliente_box = QGroupBox("Cliente")
        cliente_layout = QGridLayout(cliente_widget)

        self.num_doc_entry = QLineEdit()
        self.nombre_entry = QLineEdit()
        self.direccion_entry = QLineEdit()
        self.ruc_cliente = QLineEdit()

        self.ruc_cliente.textChanged.connect(self.actualizar_tipo_documento)

        self.fecha_entry = QDateEdit()
        self.fecha_entry.setCalendarPopup(True)
        self.fecha_entry.setDate(QDate.currentDate())

        self.nombre_entry.textChanged.connect(lambda text: self.nombre_entry.setText(text.upper()))
        self.direccion_entry.textChanged.connect(lambda text: self.direccion_entry.setText(text.upper()))
        self.ruc_cliente.textChanged.connect(lambda text: self.ruc_cliente.setText(text.upper()))

        self.num_doc_entry.setValidator(QIntValidator())

        self.cliente_nuevo = QLabel("Coincidencia: 0.00%")
        self.cliente_nuevo.setStyleSheet("font-weight: bold; color: blue;")

        self.ver_sugerencia = QCheckBox("Ver sugerencia")
        #self.ver_sugerencia.stateChanged.connect(self.toggle_sugerencias)

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
        cliente_layout.addWidget(self.fecha_entry, 1, 6, 1, 1)

        cliente_box.setLayout(cliente_layout)

        self.setLayout(cliente_layout)

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
            self.direccion_anterior = self.direccion_entry.text()

            cliente = self.nombre_entry.text()
            try:
                result = match_client_fuzzy(cliente)[0]
                print(result)

                self.id_cliente_sugerido = result[0]

                self.nombre_entry.setText(result[1])
                self.num_doc_entry.setText(result[2])
                self.ruc_cliente.setText(result[3])
                self.direccion_entry.setText("")

                self.cliente_nuevo.setText(f"Coincidencia:{result[4]:.2f}%")

                # ✅ Actualizar `BoletaApp`
                if self.parent:
                    self.parent.id_cliente_sugerido = self.id_cliente_sugerido

            except Exception as e:
                print(f"Error al buscar sugerencias: {e}")

    def fill_form_client(self,cliente_data):
        print("Datos del cliente", cliente_data)
        try:
            if isinstance(cliente_data, str):
                cliente_data = json.loads(cliente_data)
            print("case1")
            self.num_doc_entry.setText(cliente_data.get("dni", ""))
            print("case2")
            self.nombre_entry.setText(cliente_data.get("cliente", ""))
            print("case3")

            #self.ruc_cliente.setText(cliente_data.get("ruc", ""))
            print("case4")
            logging.info(" Cargado los datos del cliente")
        except Exception as e:
            logging.error(f" No se pudieron cargar los datos del cliente: {e}")
            return
    def obtener_datos_cliente(self):
        """Obtiene los datos del cliente ingresados en el formulario."""
        self.data['nombre'] = self.nombre_entry.text()
        self.data['dni'] = self.num_doc_entry.text()
        self.data['ruc'] = self.ruc_cliente.text()
        self.data['direccion'] = self.direccion_entry.text()
        self.data["fecha"] = self.fecha_entry.date().toString("dd/MM/yyyy")  # ✅ Formato correcto

        return self.data