from PyQt5.QtWidgets import QApplication
from Frontend.ui_main import BoletaApp
from DataBase.admin_bd import modo_consola_sqlite

import sys

def main():
    if "--admin" in sys.argv:
        modo_consola_sqlite()
        print("Modo administrador activado.")
    else:
        app = QApplication(sys.argv)
        window = BoletaApp()
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error al ejecutar la app",e)

