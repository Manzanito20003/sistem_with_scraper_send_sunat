import sys
import time

from PyQt5.QtWidgets import QApplication, QComboBox, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from DataBase.DatabaseManager import DatabaseManager  # asegúrate de que esta función esté bien implementada


class AutComboBox(QComboBox):

    def __init__(self, parent=None, row=None):
        # name_combo es el nombre por defecto (no usado aún)
        super().__init__(parent)
        self.parent_widget = parent
        self.row = row
        self.abreviaturas = {
            "KILOGRAMO": "KL",
            "UNIDAD": "UN",
            "CAJA": "CJ",
            "BOLSA": "BS"
        }

        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setFocus()
        self.setMinimumWidth(235)



        # ️ Timer para hacer debounce
        # self.debounce_timer = QTimer()
        # self.debounce_timer.setSingleShot(True)
        # self.debounce_timer.setInterval(500)  # 500 ms de espera
        # self.debounce_timer.timeout.connect(self.on_editing_finished)
        #
        # #  Detectar cuando se edita el texto
        # self.lineEdit().textEdited.connect(self.restart_debounce)

        # 🎯 Detectar selección de item
        self.activated.connect(self.on_item_selected)

    def showPopup(self):
        print("⚡ Desplegando la lista, aquí puedes cargar datos o actualizar")
        # Puedes cargar las opciones aquí antes de mostrar el combo
        # Por ejemplo:
        texto = self.currentText()
        self.clear()
        self.addItem(texto)
        self.parsear_data_to_combo(self.matching_items(texto))

        # Ahora sí mostramos el popup
        super().showPopup()
    def restart_debounce(self):
        self.debounce_timer.start()

    def on_editing_finished(self):
        print("Se dejó de escribir")

        descripcion_actual = self.currentText()
        self.setCurrentIndex(-1)  # No seleccionar nada por defecto
        self.setEditText(descripcion_actual)  # Mantener texto
        print("Descripción actual:", descripcion_actual)
        ## Si el texto está vacío, limpiar el combo
        if descripcion_actual.split() == "":

            return


        self.clear()
        data_match = self.matching_items(descripcion_actual)

        # Mantener texto ingresado
        text = self.lineEdit().text()
        print("Texto escrito:", text)
        self.addItem(text)

        # Agregar los resultados encontrados
        self.parsear_data_to_combo(data_match)

    def matching_items(self, text):
        data_match = match_product_fuzzy(text)
        print("Data match:", data_match)
        return data_match

    def parsear_data_to_combo(self, data):
        for id_producto, nombre, unidad, precio, igv, _ in data:
            abrev = self.abreviaturas.get(unidad, unidad)
            estado_igv = "Sí" if igv == 1 else "No"
            texto_opcion = f"{nombre} | S/ {precio:.2f} | {abrev} | {estado_igv}"
            self.addItem(texto_opcion, (nombre, precio, unidad, igv, id_producto))

    def on_item_selected(self, index):
        print(f"Ítem seleccionado: {index}")

        datos = self.itemData(index)
        if datos and self.row is not None:
            if hasattr(self.parent_widget, "actualizar_producto_seleccionado"):
                self.parent_widget.actualizar_producto_seleccionado(self.row, datos)
        else:
            print("Error: la fila (row) es None o no se pasó correctamente.")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        combo = AutComboBox(self)
        combo2 = AutComboBox(self)

        layout.addWidget(combo)
        layout.addWidget(combo2)
        self.setLayout(layout)

    def actualizar_producto_seleccionado(self, index, datos):
        nombre, precio, unidad, igv, id_producto = datos
        print(f"Producto seleccionado: {nombre} | Precio: {precio} | Unidad: {unidad} | IGV: {igv} | ID: {id_producto}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
