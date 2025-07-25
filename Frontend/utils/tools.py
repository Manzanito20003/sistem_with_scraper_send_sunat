import logging
import sys
from PyQt5.QtWidgets import QApplication, QComboBox, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from DataBase.DatabaseManager import DatabaseManager

abreviaturas = {
    "KILOGRAMO": "KL",
    "UNIDAD": "UN",
    "CAJA": "CJ",
    "BOLSA": "BS",
}


class AutComboBox(QComboBox):
    def __init__(
        self, parent=None, row=None, cache=None, match_func=None, parse_func=None
    ):
        super().__init__(parent)
        self.parent_widget = parent
        self.row = row
        self.data_cache = cache
        self.match_func = match_func
        self.parse_func = parse_func

        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setFocus()
        self.setMinimumWidth(235)
        self.activated.connect(self.on_item_selected)

        # DEBUG
        logging.debug(
            f" data_cache: {self.data_cache}\n"
        )

    def showPopup(self):
        print("activando showpopup")
        texto = self.currentText()
        self.clear()
        self.addItem(texto)
        match=self.matching_items(texto)
        print("[DEBUG] match:",match)
        self.parsear_data_to_combo(match)
        super().showPopup()

    def matching_items(self, text):
        if text is None or self.match_func is None:
            return []
        return self.match_func(self.data_cache, text)

    def parsear_data_to_combo(self, data):
        if self.parse_func is None:
            return
        try:
            for texto, valor in self.parse_func(data):
                if not isinstance(texto, str):
                    logging.error(f"❌ texto no es str: {texto}")
                    continue
                self.addItem(texto, valor)
        except Exception as e:
            logging.exception(f"❌ Error en parsear_data_to_combo: {e}")

    def on_item_selected(self, index):
        datos = self.itemData(index)

        if datos and self.row is not None:
            if hasattr(self.parent_widget, "actualizar_producto_seleccionado"):
                self.parent_widget.actualizar_producto_seleccionado(self.row, datos)
            if hasattr(self.parent_widget, "actualizar_cliente_seleccionado"):
                self.parent_widget.actualizar_cliente_seleccionado(datos)
        else:
            print("⚠️ La fila (row) es None o no se pasó correctamente.")


# 🔧 Parsers


def parse_productos(data):
    print("DATA:",data)
    resultado = []
    for row in data:
        id_producto,_, nombre, unidad, precio, igv = row[
            :6
        ]  # Solo tomamos los 6 primeros

        abrev = abreviaturas.get(unidad, unidad)
        estado_igv = "Sí" if igv == 1 else "No"
        texto = f"{nombre} | S/ {precio:.2f} | {abrev} | {estado_igv}"
        valor = (nombre, precio, unidad, igv, id_producto)
        resultado.append((texto, valor))
    return resultado


def parse_cliente(data):
    print("TEST data: ,",data)
    resultado = []
    for row in data:
        id_cliente,_, nombre, dni, ruc = row[:5]
        texto = f"{nombre} | DNI: {dni or '-'} | RUC: {ruc or '-'}"
        valor = (nombre, dni, ruc, id_cliente)
        resultado.append((texto, valor))
    return resultado


# ▶️ Ejecutar app
if __name__ == "__main__":
    app = QApplication(sys.argv)

    sys.exit(app.exec_())
