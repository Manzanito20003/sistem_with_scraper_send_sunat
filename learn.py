from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout
import sys

class Ventana(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ejemplo de Layouts Combinados")
        self.setGeometry(100, 100, 300, 200)

        # Layout principal (vertical)
        main_layout = QVBoxLayout()

        # Layout secundario (horizontal)
        h_layout = QHBoxLayout()
        h_layout.addWidget(QPushButton("A"))
        h_layout.addWidget(QPushButton("B"))

        # Botón independiente en el layout principal
        main_layout.addWidget(QPushButton("Botón 1"))
        main_layout.addLayout(h_layout)  # Agregamos el layout horizontal dentro del vertical
        main_layout.addWidget(QPushButton("Botón 2"))

        self.setLayout(h_layout)

# Ejecutar la app
app = QApplication(sys.argv)
ventana = Ventana()
ventana.show()
sys.exit(app.exec_())
