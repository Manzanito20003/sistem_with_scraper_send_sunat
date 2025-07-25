"""Manejo de un producto en la base de datos  UPDATE - CREATE- DELETE """
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QComboBox, QToolBar, QAction, QMessageBox
)
import logging
class ProductosDialog(QDialog):
    def __init__(self, controller, remitente_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Productos")
        self.resize(700, 400)

        self.controller = controller
        self.remitente_id = remitente_id

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ToolBar superior
        toolbar = QToolBar("Opciones")
        toolbar.addAction(QAction("Crear", self, triggered=self.crear_producto))
        toolbar.addAction(QAction("Actualizar", self, triggered=self.actualizar_producto))
        toolbar.addAction(QAction("Eliminar", self, triggered=self.borrar_producto))
        toolbar.addAction(QAction("Ver", self, triggered=self.cargar_productos))
        layout.addWidget(toolbar)

        # Formulario
        form_layout = QHBoxLayout()
        self.nombre = QLineEdit()
        self.unidad = QComboBox()
        self.unidad.addItems(["KILOGRAMO", "UNIDAD", "CAJA", "BOLSA"])
        self.precio = QLineEdit()
        self.igv = QComboBox()
        self.igv.addItems(["Sí", "No"])
       

        #form_layout.addWidget(QLabel("agregar producto -->"))
        form_layout.addWidget(QLabel("Nombre"))
        form_layout.addWidget(self.nombre)
        form_layout.addWidget(QLabel("Unidad"))
        form_layout.addWidget(self.unidad)
        form_layout.addWidget(QLabel("Precio"))
        form_layout.addWidget(self.precio)
        form_layout.addWidget(QLabel("IGV"))
        form_layout.addWidget(self.igv)

        layout.addLayout(form_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setEditTriggers(QTableWidget.AllEditTriggers)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Unidad", "Precio", "IGV", "Total"])
        self.tabla.setColumnWidth(1, 265)
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_productos()

    def crear_producto(self):
        if not self.nombre.text() or not self.precio.text():
            QMessageBox.warning(self, "Advertencia", "Por favor, complete todos los campos.")
            return
        try:
            self.controller.agregar_product(
                self.remitente_id,
                self.nombre.text().upper(),
                self.unidad.currentText(),
                float(self.precio.text()),
                1 if self.igv.currentText() == "Sí" else 0
            )
            QMessageBox.information(self, "Éxito", "Producto creado.")
            self.cargar_productos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def actualizar_producto(self):
        if not self.nombre.text() or not self.precio.text():
            QMessageBox.warning(self, "Advertencia", "Por favor, complete todos los campos.")
            return
        try:
            row = self.tabla.currentRow()
            id_producto = int(self.tabla.item(row, 0).text())
            nombre = self.tabla.item(row, 1).text().upper()
            unidad = self.tabla.item(row, 2).text()
            precio = float(self.tabla.item(row, 3).text())
            igv = 1 if self.tabla.item(row, 4).text().lower() in ["sí", "1", "si"] else 0

            self.controller.actualizar_product(
                self.remitente_id,
                id_producto,
                nombre,
                unidad,
                precio,
                igv
            )
            QMessageBox.information(self, "Actualizado", "Producto actualizado.")
            self.cargar_productos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


    def borrar_producto(self):
        
        try:
            row = self.tabla.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Advertencia", "Seleccione un producto en la tabla.")
                return

            id_producto = int(self.tabla.item(row, 0).text())

            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Está seguro de eliminar el producto con ID {id_producto}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if confirm == QMessageBox.Yes:
                self.controller.borrar_product(self.remitente_id, id_producto)
                QMessageBox.information(self, "Eliminado", "Producto eliminado.")
                self.cargar_productos()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


    def cargar_productos(self):
        self.tabla.setRowCount(0)
        logging.info("Cargando productos para el remitente:%s", self.remitente_id)    
        productos = self.controller.ver_productos(self.remitente_id)
        for row_idx, row in enumerate(productos):
            id_producto,_, nombre, unidad, precio, igv,_ = row
            datos = [id_producto, nombre, unidad, precio, "Sí" if igv else "No", precio * (1.18 if igv else 1)]
            self.tabla.insertRow(row_idx)
            for col_idx,dato in enumerate(datos):
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(str(dato)))




if __name__ == "__main__":
    import sys
    import os
    from PyQt5.QtWidgets import QApplication

    # ✅ Agregar la raíz del proyecto al path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

    # ✅ Importaciones ahora funcionarán
    from Backend.BoletaController import BoletaController
    from DataBase.DatabaseManager import DatabaseManager

    # Inicializar la app Qt
    app = QApplication(sys.argv)

    # Crear la base de datos y el controlador
    db = DatabaseManager()
    controller = BoletaController(db)

    # ID de remitente de prueba
    id_remitente = 1  # Asegúrate de que exista en tu DB

    # Crear y mostrar el diálogo de productos
    from Frontend.dialogs.productos_dialog import ProductosDialog
    dialogo = ProductosDialog(db, controller, remitente_id=id_remitente)
    dialogo.show()

    sys.exit(app.exec_())
