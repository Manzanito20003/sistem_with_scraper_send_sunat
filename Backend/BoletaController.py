import logging

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

#scrapping
from Scraping.scraper_sunat import send_billing_sunat


# logica de negocio
# lgocia de interfaz
# llamadas a service
# control de estado

class BoletaController:

    def __init__(self,db):
        self.db = db

        pass
    def emitir_boleta(self, boleta_data):
        """
        Envio de la boleta con scraping
        """
        logging.info("Boleta emitida correctamente.")
        send_billing_sunat(boleta_data)

        return True


    def validar_envio(self,remitente_id, cliente_view):

        if remitente_id is None:
            QMessageBox.warning(None, "Error", "Debe seleccionar un remitente.")
            return False

        valid, message = cliente_view.validate()

        if not valid:
            logging.warning("Los datos del cliente no son válidos.")
            QMessageBox.warning(None, "Error", message)
            return False

        return True

    def armar_boleta_data(self,cliente_view,product_view,resumen_view,selected_remitente_id,tipo_documento_combo):

        data_cliente = cliente_view.obtener_datos_cliente()
        data_producto = product_view.obtener_datos_producto()
        data_resumen = resumen_view.obtener_datos_resumen()

        if data_producto is None:
            if not data_producto:
                raise ValueError("No hay productos en la boleta.")

        return {
            "cliente": data_cliente,
            "productos": data_producto,
            "resumen": data_resumen,
            "id_cliente": cliente_view.id_cliente_sugerido,
            "id_remitente": selected_remitente_id,
            "tipo_documento": tipo_documento_combo
        }




    def enviar_boleta(self,data):
        """Guarda los datos de la boleta en la base de datos y la envía a SUNAT."""

        id_client = data["id_cliente"]
        id_sender = data["id_remitente"]

        logging.info("Iniciando proceso de emisión de boleta...")
        logging.info(f"ID del remitente seleccionado: {id_sender}")

        try:
            send_billing_sunat(data, id_sender)
            logging.info("Boleta enviada a SUNAT correctamente.")
        except Exception as e:
            logging.error(f"Fallo en la emisión ante SUNAT. Detalle: {e}")

        if id_client is None:
            cliente = data["cliente"]
            id_client = self.db.insert_client(
                cliente["nombre"],
                cliente["dni"] if cliente["dni"] else None,
                cliente["ruc"] if cliente["ruc"] else None
            )
            logging.info(f" Cliente registrado con ID: {id_client}")
        if id_client is None or id_sender is None:
            logging.error("No se pudo continuar. ID Cliente o ID Sender es None.")
            return

        # 🔹 Cálculo del total de la boleta
        total_pagado = data.get("total", 0)
        igv_total = data.get("igv_total", 0)
        logging.info(f"Total Boleta: S/ {total_pagado:.2f}, Total IGV: S/ {igv_total:.2f}")

        # 🔹 Insertar productos en la BD
        try:
            for producto in data['productos']:
                self.db.insert_product(
                    id_sender,
                    producto.get("descripcion"),
                    producto.get("unidad_medida"),
                    producto.get("precio_base"),
                    producto.get("Igv")
                )
            self.db.insert_invoice(id_client, id_sender, total_pagado, igv_total)
            logging.info(f"Boleta registrada correctamente en BD. (Cliente ID: {id_client}, Remitente ID: {id_sender})")
        except Exception as e:
            logging.error(f"No se pudo completar la inserción de productos o la boleta. Detalle: {e}")
            return

class BoletaWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, boleta_data, controller):
        super().__init__()
        self.boleta_data = boleta_data
        self.controller = controller

    def run(self):
        try:
            self.controller.emitir_boleta(self.boleta_data)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
