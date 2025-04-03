from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QComboBox, QLabel

class ClienteView(QWidget):  # ✅ Hereda de QWidget para ser un widget gráfico
    def __init__(self, parent=None, tipo_documento_combo=None):
        super().__init__(parent)  # ✅ Llamamos al constructor de QWidget
        self.tipo_documento_combo = tipo_documento_combo if tipo_documento_combo else QComboBox()

        # Agregamos opciones al combo si está vacío
        if not tipo_documento_combo:
            self.tipo_documento_combo.addItems(["DNI", "Pasaporte", "Licencia"])

        # Creamos un layout para organizar los widgets
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Seleccione Tipo de Documento:"))
        layout.addWidget(self.tipo_documento_combo)
        self.setLayout(layout)  # ✅ Se asigna el layout al QWidget

class MainApp(QMainWindow):  # ✅ Hereda de QMainWindow para ser la ventana principal
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Clientes")

        # Creamos el combo y lo pasamos a ClienteView
        combo = QComboBox()
        combo.addItems(["DNI", "RUC", "Carnet Extranjería"])

        self.view = ClienteView(self, combo)  # ✅ Pasamos el combo a ClienteView
        self.setCentralWidget(self.view)  # ✅ Se muestra ClienteView dentro de la ventana

if __name__ == "__main__":
    app = QApplication([])
    ventana = MainApp()
    ventana.show()
    app.exec_()
