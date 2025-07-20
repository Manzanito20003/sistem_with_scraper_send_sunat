""" "Archivo principal que lanza la aplicación de boletas con PyQt5."""

from datetime import datetime
import logging
import sys
import os

from PyQt5.QtWidgets import QApplication
from Frontend.ui_main import BoletaApp
from DataBase.admin_bd import modo_consola_sqlite


log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"boletas_{datetime.today().date()}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)


def main():
    """Inicializar la app  y usamos un user admin para conexion en BD sqlite"""
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
        print("Error al ejecutar la app", e)
