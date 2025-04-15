from PyQt5.QtWidgets import QApplication
from Frontend.ui_main import BoletaApp
from DataBase.admin_bd import modo_consola_sqlite

import sys
if __name__ == "__main__":
    if "--admin" in sys.argv:
        modo_consola_sqlite()
        print("Modo administrador activado.")
    else:
        app = QApplication(sys.argv)
        window = BoletaApp()
        window.show()
        sys.exit(app.exec_())
