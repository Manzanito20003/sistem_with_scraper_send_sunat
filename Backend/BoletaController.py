import logging
from typing import List, Tuple

from pydantic import ValidationError
from rapidfuzz import process, fuzz

from Backend.models import BoletaData
from Scraping.scraper_sunat import send_billing_sunat


class BoletaController:

    def __init__(self, db):
        self.db = db

    def emitir_boleta(self, boleta_data) -> bool:
        try:
            logging.info("Iniciando validación de boleta...")
            boleta_data = BoletaData(**boleta_data)
            logging.info("Boleta data validada correctamente.")
        except ValidationError as e:
            logging.error(f"validacion fallida de boleta{e}")
            return False

        logging.info("Boleta validada correctamente, enviando a SUNAT...")
        send_billing_sunat(boleta_data.dict())
        return True

    def validar_envio(self, remitente_id, cliente_view):

        if remitente_id is None:
            return False, "Debe seleccionar un remitente."
        valid, message = cliente_view.validate()

        if not valid:
            return False, message

        return True, ""

    def armar_boleta_data(
        self,
        cliente_view,
        product_view,
        resumen_view,
        selected_remitente_id,
        tipo_documento_combo,
    ):
        try:
            logging.info("Armar datos de la Boleta...")
            data_cliente = cliente_view.obtener_datos_cliente()
            data_producto = product_view.obtener_datos_producto()
            data_resumen = resumen_view.obtener_datos_resumen()
            logging.debug(
                f"Datos de boleta: {data_cliente, data_producto, data_resumen, selected_remitente_id, tipo_documento_combo}"
            )
            if data_producto is None:
                logging.error("No hay productos en la boleta.")
                raise ValueError("Faltan productos en la boleta.")
            if data_cliente is None:
                logging.error("No hay data en cliente")
                raise ValueError("Faltan datos del cliente en la boleta.")

            if data_resumen is None:
                logging.error("No hay data en resumen de la venta")
                raise ValueError("Faltan datos del resumen de la boleta.")

            return {
                "cliente": data_cliente,
                "productos": data_producto,
                "resumen": data_resumen,
                "fecha": cliente_view.obtener_fecha(),
                "id_cliente": str(cliente_view.id_cliente_sugerido),
                "id_remitente": str(selected_remitente_id),
                "tipo_documento": tipo_documento_combo.upper(),
            }
        except Exception as e:
            logging.error(f"Error al armar los datos de la boleta: {e}")
            raise ValueError("Error al armar los datos de la boleta.") from e
    def enviar_boleta(self, data):
        """Guarda los datos de la boleta en la base de datos y la envía a SUNAT."""

        id_client = data["id_cliente"]
        id_sender = data["id_remitente"]

        logging.info("Iniciando proceso de emisión de boleta...")
        logging.info(f"ID del remitente: {id_sender}")

        try:
            logging.debug("sunat data")
            send_billing_sunat(data, id_sender)
            logging.info("Boleta enviada a SUNAT correctamente.")
        except Exception as e:
            logging.error(f"Fallo en la emisión ante SUNAT. Detalle: {e}")

        if id_client is None:
            cliente = data["cliente"]
            id_client = self.db.insert_client(
                cliente["nombre"],
                cliente["dni"] if cliente["dni"] else None,
                cliente["ruc"] if cliente["ruc"] else None,
            )
            logging.info(f" Cliente registrado con ID: {id_client}")
        if id_client is None or id_sender is None:
            logging.error("No se pudo continuar. ID Cliente o ID Sender es None.")
            return

        # Cálculo del total de la boleta
        total_pagado = data["resumen"].get("total", 0)
        igv_total = data["resumen"].get("igv_total", 0)
        logging.info(
            f"Total Boleta: S/ {total_pagado:.2f}, Total IGV: S/ {igv_total:.2f}"
        )

        try:
            for producto in data["productos"]:
                self.db.insert_product(
                    id_sender,
                    producto.get("descripcion"),
                    producto.get("unidad_medida"),
                    producto.get("precio_base"),
                    producto.get("igv"),
                )
            self.db.insert_invoice(id_client, id_sender, total_pagado, igv_total)
            logging.info(
                f"Boleta registrada correctamente en BD. (Cliente ID: {id_client}, Remitente ID: {id_sender})"
            )
        except Exception as e:
            logging.error(
                f"No se pudo completar la inserción de productos o la boleta. Detalle: {e}"
            )
            return

    # ---- DB  ---
    def match_fuzzy(self, data: List[Tuple], query: str) -> List[Tuple]:
        """
        Productos ((id, nombre, unidad, precio, igv, ...)) -> ejemplo
        Busca coincidencias aproximadas del nombre de producto con la query.
        """
        if query == "":
            return []

        data_names = [str(item[1]).lower() for item in data]
        query = query.lower()

        # Buscar coincidencias aproximadas
        results = process.extract(
            query, data_names, scorer=fuzz.WRatio, score_cutoff=60
        )

        # Emparejar con los productos originales
        matches_with_confidence = []
        for name, score, index in results:
            product = data[index]
            matches_with_confidence.append((*product, score))  # Agrega el score

        # Retornar los mejores 5 resultados (ordenados por score descendente)
        return sorted(matches_with_confidence, key=lambda x: x[-1], reverse=True)[:5]


if __name__ == "__main__":
    # Datos de prueba (id, nombre, otro campo opcional)
    sample_data = [
        (1, "Arroz Extra Superior", 5.50),
        (2, "Azúcar Rubia", 4.80),
        (3, "Aceite Vegetal", 6.00),
        (4, "Harina Integral", 3.50),
        (5, "Sal de Mesa", 1.20),
    ]

    # 🔹 Query a buscar
    query = "arros superor"  # mal escrito

    class DummyDB:
        pass

    controller = BoletaController(DummyDB())
    result = controller.match_fuzzy(sample_data, query)

    # 🔹 Verificar resultados
    print("Resultados encontrados:")
    for match in result:
        print(match)
