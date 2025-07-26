from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QAction,
    QMessageBox,
    QHeaderView,
)
import logging


class RemitenteDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Remitentes")
        self.resize(700, 400)

        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ToolBar
        toolbar = QToolBar("Opciones")
        toolbar.addAction(QAction("Crear", self, triggered=self.crear_remitente))
        toolbar.addAction(
            QAction("Actualizar", self, triggered=self.actualizar_remitente)
        )
        toolbar.addAction(QAction("Eliminar", self, triggered=self.borrar_remitente))
        toolbar.addAction(QAction("Ver", self, triggered=self.cargar_remitentes))
        layout.addWidget(toolbar)

        # Formulario
        form_layout = QHBoxLayout()
        self.nombre = QLineEdit()
        self.ruc = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()

        form_layout.addWidget(QLabel("Nombre"))
        form_layout.addWidget(self.nombre)
        form_layout.addWidget(QLabel("RUC"))
        form_layout.addWidget(self.ruc)
        form_layout.addWidget(QLabel("Usuario"))
        form_layout.addWidget(self.user)
        form_layout.addWidget(QLabel("Contraseña"))
        form_layout.addWidget(self.password)

        layout.addLayout(form_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Nombre", "RUC", "Usuario", "Contraseña"]
        )
        self.tabla.setColumnWidth(1, 265)
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_remitentes()

    def crear_remitente(self):
        if (
            not self.nombre.text()
            or not self.ruc.text()
            or not self.user.text()
            or not self.password.text()
        ):
            QMessageBox.warning(self, "Advertencia", "Complete todos los campos.")
            return
        try:
            self.controller.agregar_sender(
                self.nombre.text(),
                self.ruc.text(),
                self.user.text(),
                self.password.text(),
            )
            QMessageBox.information(self, "Éxito", "Remitente creado.")
            self.cargar_remitentes()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def actualizar_remitente(self):
        try:
            row = self.tabla.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Advertencia", "Seleccione un remitente.")
                return

            id_remitente = int(self.tabla.item(row, 0).text())
            nombre = self.tabla.item(row, 1).text()
            ruc = self.tabla.item(row, 2).text()
            user = self.tabla.item(row, 3).text()
            password = self.tabla.item(row, 4).text()

            self.controller.actualizar_sender(id_remitente, nombre, ruc, user, password)
            QMessageBox.information(self, "Actualizado", "Remitente actualizado.")
            self.cargar_remitentes()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def borrar_remitente(self):
        try:
            row = self.tabla.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Advertencia", "Seleccione un remitente.")
                return

            id_remitente = int(self.tabla.item(row, 0).text())

            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Eliminar remitente con ID {id_remitente}?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if confirm == QMessageBox.Yes:
                self.controller.borrar_sender(id_remitente)
                QMessageBox.information(self, "Eliminado", "Remitente eliminado.")
                self.cargar_remitentes()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def cargar_remitentes(self):
        self.tabla.setRowCount(0)
        remitentes = self.controller.ver_senders()
        if not remitentes:
            return
        for row_idx, row in enumerate(remitentes):
            self.tabla.insertRow(row_idx)
            print("[DEBUG] row_idx:", row_idx, "data:", row)
            for col_idx, dato in enumerate(row):
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(str(dato)))
