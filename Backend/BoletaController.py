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
        except ValidationError as e:
            logging.error(f"validacion fallida de boleta{e}")
            return False

        logging.info("Boleta validada correctamente, enviando a SUNAT...")
        logging.info("Datos de la boleta: %s", boleta_data.dict())

        result = self.guardar_boleta_db(boleta_data.dict())
        if result is False:
            return False

        send_billing_sunat(boleta_data.dict())

        logging.info("Boleta Emitida correctamente :)")
        return True

    def guardar_boleta_db(self, data):
        try:
            id_remitente = data["id_remitente"]
            nombre = data["cliente"]["nombre"]
            dni = data["cliente"]["dni"]
            ruc = data["cliente"]["ruc"]
            id_cliente = self.db.insert_client(id_remitente, nombre, dni, ruc)
            logging.info("Insertado cliente ")
            # -- guardar factura--
            total = data["resumen"]["total"]
            igv_total = data["resumen"]["igv_total"]

            # -- guardar invoice--
            serie = data["resumen"]["serie"]
            numero = data["resumen"]["numero"]
            emision_fecha = data["fecha"]
            tipo = data["tipo_documento"]
            invoice_id = self.db.insert_invoice(
                id_cliente,
                id_remitente,
                total,
                igv_total,
                tipo,
                serie,
                numero,
                emision_fecha,
            )
            logging.info("Insertado invoice ")

            # -- guardar detailes--
            productos = data["productos"]
            for p in productos:
                cantidad = p["cantidad"]
                descripcion = p["descripcion"]
                unidad = p["unidad_medida"].upper()
                precio = p["precio_base"]
                igv = p["igv"]
                total = p["precio_total"]

                product_id = self.db.insert_product(
                    id_remitente, descripcion, unidad, precio, igv
                )
                self.db.insert_invoice_detail(invoice_id, product_id, cantidad, total)

            logging.info("Insertado productos y details")
            logging.info("Data guardada correctamente BD")
            return True
        except Exception as e:
            logging.error("Hubo un error en guardar en BD %s", e)
            return False

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

    # ---- DB  ---
    def match_fuzzy(self, data: List[Tuple], query: str) -> List[Tuple]:
        """
        Productos ((id, nombre, unidad, precio, igv, ...)) -> ejemplo
        Busca coincidencias aproximadas del nombre de producto con la query.
        """
        logging.info("entrando a match_fuzzy")
        if query == "":
            return []

        data_names = [str(item[2]).lower() for item in data]
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

    # --- SENDERS ----
    def agregar_sender(self, nombre: str, ruc: str, user: str, password: str) -> bool:
        """
        Agrega un nuevo remitente a la base de datos.
        Retorna el ID del remitente agregado.
        """
        if not nombre or not ruc or not user or not password:
            logging.error("Nombre, RUC, user y password son obligatorios.")
            return None
        try:
            self.db.insert_sender(nombre, ruc, user, password)
            logging.info(f"Remitente '{nombre}' agregado correctamente.")
            return True
        except Exception as e:
            logging.error(f"Error al agregar remitente: {e}")
            return None

    def ver_senders(self):
        try:
            senders = self.db.get_senders()
            logging.info("Remitentes obtenidos correctamente.")
            return senders
        except Exception as e:
            logging.error("Error al obtener remitentes: %s", e)
            return None

    def borrar_sender(self, id_sender: int) -> bool:
        try:
            self.db.delete_sender(id_sender)
            logging.info(f"Remitente con ID {id_sender} borrado correctamente.")
            return True
        except Exception as e:
            logging.error(f"Error al borrar remitente: {e}")
            return False

    def actualizar_sender(
        self, id_sender: int, nombre: str, ruc: str, user: str, password: str
    ) -> bool:
        if not nombre or not ruc or not user or not password:
            logging.error("Nombre, RUC, user y password son obligatorios.")
            return False
        if not id_sender:
            logging.error("Fallo al pasar id_sender: %s", id_sender)
            return False
        try:
            self.db.update_sender(id_sender, nombre, ruc, user, password)
            logging.info("Remitente con ID %s actualizado correctamente.", id_sender)
            return True
        except Exception as e:
            logging.error(f"Error al actualizar remitente: {e}")
            return False

    # ---- PRODUCTOS ----
    def agregar_product(self, id_sender, name, unit, price, igv):
        """
        Agrega un nuevo producto a la base de datos.
        Retorna el ID del producto agregado.
        """
        if not name or not unit or price is None:
            logging.error("Nombre, unidad y precio son obligatorios.")
            return None
        try:
            product_id = self.db.insert_product(id_sender, name, unit, price, igv)
            logging.info(
                f"Producto '{name}' agregado correctamente con ID: {product_id}"
            )
            return product_id
        except Exception as e:
            logging.error(f"Error al agregar producto: {e}")
            return None

    def ver_productos(self, id_sender):
        """
        Obtiene todos los productos de un remitente específico.
        Retorna una lista de productos.
        """
        try:
            productos = self.db.get_products_by_sender(id_sender)
            logging.info(f"Productos obtenidos para el remitente ID {id_sender}.")
            return productos
        except Exception as e:
            logging.error(f"Error al obtener productos: {e} sender : {id_sender}")
            return []

    def borrar_product(self, id_sender, id_product):
        """
        Borra un producto de la base de datos por su ID.
        Retorna True si se borró correctamente, False en caso contrario.
        """
        try:
            self.db.delete_product_by_sender(id_sender, id_product)
            logging.info(f"Producto con ID {id_product} borrado correctamente.")
            return True
        except Exception as e:
            logging.error(f"Error al borrar producto: {e}")
            return False

    def actualizar_product(self, id_sender, id_product, name, unit, price, igv):
        """
        Actualiza un producto existente en la base de datos.
        Retorna True si se actualizó correctamente, False en caso contrario.
        """
        if not name or not unit or price is None:
            logging.error("Nombre, unidad y precio son obligatorios.")
            return False
        try:
            self.db.update_product(id_product, id_sender, name, unit, price, igv)
            logging.info(f"Producto con ID {id_product} actualizado correctamente.")
            return True
        except Exception as e:
            logging.error(f"Error al actualizar producto: {e}")
            return False

    def ver_histoial_id_sender(self, id_sender):
        try:
            return self.db.get_invoices_by_sender_id(id_sender)
        except Exception as e:
            logging.error(
                "fallo al extraer el historial para id_sender=%s, error=%s",
                id_sender,
                e,
            )
            return []

    def ver_invoice_details(self, invoice_id):
        try:
            return self.db.get_invoice_details(invoice_id)
        except Exception as e:
            logging.error("fallo al extraer details de historia")
            return []


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
