from PyQt5.QtWidgets import QApplication
from ui_main import BoletaApp  # Importa tu clase de UI
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BoletaApp()
    window.show()
    sys.exit(app.exec_())
