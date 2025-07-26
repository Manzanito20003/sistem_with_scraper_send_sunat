"""widget para Productos"""

import logging
from functools import partial

from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QGroupBox,
    QTableWidget,
    QHeaderView,
    QComboBox,
    QTableWidgetItem,
    QMessageBox,
    QPushButton,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from Frontend.utils.tools import AutComboBox, parse_productos


class ProductView(QWidget):
    """Aqui separaremos la logica de la vista de la logica de los productos"""

    def __init__(self, parent=None, cache=None):
        super().__init__()

        self.precios_base_originales = {}
        self.parent = parent  # Referencia al contenedor principal
        self.data = {}
        self.productos_table = None
        self.productos_cache = cache
        self.initUI()

    def initUI(self):
        """Inicializa y devuelve el widget de productos."""
        logging.info("Inicializando ProductView...")
        productos_widget = QWidget()
        productos_layout = QVBoxLayout(productos_widget)

        productos_box = QGroupBox("Productos")
        productos_layout_inner = QVBoxLayout()

        btn_agregar_producto = QPushButton("Agregar producto")
        btn_agregar_producto.clicked.connect(self.agregar_fila_manual)
        productos_layout_inner.addWidget(btn_agregar_producto)

        self.productos_table = QTableWidget(0, 8)  # cantidad de columnas
        self.productos_table.setHorizontalHeaderLabels(
            [
                "Cantidad",
                "Unidad",
                "Descripción",
                "Precio Base",
                "IGV",
                "Total IGV",
                "Precio total",
                "Borrar",
            ]
        )

        self.productos_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.productos_table.setColumnWidth(0, 60)  # Cantidad (más estrecha)
        self.productos_table.setColumnWidth(4, 60)  # IGV (más estrecha)
        self.productos_table.setColumnWidth(2, 200)  # Descripción
        self.productos_table.setColumnWidth(7, 50)  # Precio Base

        self.productos_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.productos_table.setFont(QFont("Arial", 10))

        productos_layout_inner.addWidget(self.productos_table)
        productos_box.setLayout(productos_layout_inner)

        # Asegurarse de que la celda sea editable
        self.productos_table.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.SelectedClicked
        )

        productos_layout.addWidget(productos_box)
        self.productos_table.itemChanged.connect(self.recalcular_por_cambios)
        self.setLayout(productos_layout)

    def actualizar_producto_seleccionado(self, row, datos_producto):
        """Cuando el usuario elige un producto del QComboBox, actualiza la fila con sus datos."""

        if not datos_producto:
            logging.error("no hay datos del producto")
            return

        nombre, precio, unidad, igv, id_producto = datos_producto

        combo = self.productos_table.cellWidget(row, 2)
        if combo:
            combo.setEditText(nombre)

        # Actualizar valores en la tabla
        self.productos_table.setItem(
            row, 1, QTableWidgetItem(unidad)
        )  # Unidad de medida

        self.productos_table.setItem(
            row, 3, QTableWidgetItem(f"S/ {precio:.2f}")
        )  # Precio Base
        self.productos_table.setItem(
            row, 4, QTableWidgetItem("Sí" if igv == 1 else "No")
        )  # igv

        logging.info(
            f"Producto seleccionado: {nombre}, ID: {id_producto}, Precio: {precio}, Unidad: {unidad}"
        )

        self.actualizar_resumen()

    def fill_form_fields(self, data):
        logging.info(" Llenando campos de productos")
        if not data:
            logging.error(" No hay datos para llenar el formulario.")
            return

        productos = data
        self.productos_table.setRowCount(len(productos))

        try:
            for row, producto in enumerate(productos):
                cantidad = producto.get("cantidad", 1)
                precio = producto.get("precio_base", 0)
                precio_total = producto.get("precio_total", 0)

                if precio == 0 and precio_total != 0:
                    precio = precio_total / cantidad if cantidad > 0 else 0

                aplica_igv = producto.get("Igv", 0) == 1
                total_producto = cantidad * precio
                igv_producto = total_producto * 0.18 if aplica_igv else 0

                igv_combo = QComboBox()
                igv_combo.addItems(["No", "Sí"])
                igv_combo.setCurrentText("Sí" if aplica_igv else "No")

                try:
                    igv_combo.currentTextChanged.disconnect()
                except TypeError:
                    pass

                igv_combo.currentTextChanged.connect(
                    partial(self.actualizar_igv_producto, row)
                )

                unidad_combo = QComboBox()
                unidad_combo.addItems(["CAJA", "KILOGRAMO", "BOLSA", "UNIDAD"])
                unidad_combo.setCurrentText(producto.get("unidad_medida", "UNIDAD"))

                self.productos_table.setItem(row, 0, QTableWidgetItem(str(cantidad)))
                self.productos_table.setCellWidget(row, 1, unidad_combo)

                if not hasattr(self.parent, "controller"):
                    logging.error("Parent no tiene 'controller'")
                    return

                combo = AutComboBox(
                    parent=self,
                    row=row,
                    cache=self.productos_cache,
                    match_func=self.parent.controller.match_fuzzy,
                    parse_func=parse_productos,
                )
                combo.setEditText(producto.get("descripcion", ""))
                self.productos_table.setCellWidget(row, 2, combo)

                self.productos_table.setItem(
                    row, 3, QTableWidgetItem(f"S/ {precio:.2f}")
                )
                self.productos_table.setCellWidget(row, 4, igv_combo)
                self.productos_table.setItem(
                    row, 5, QTableWidgetItem(f"S/ {igv_producto:.2f}")
                )
                self.productos_table.setItem(
                    row, 6, QTableWidgetItem(f"S/ {total_producto:.2f}")
                )

                self.agregar_boton_borrar(row)

        except Exception as e:
            logging.error(
                f"Ocurrió un problema al llenar los datos en la fila {row}: {e}"
            )
            logging.error(
                f" Datos del producto problemático: {producto.get('descripcion')}"
            )

    def obtener_datos_producto(self):
        """Toma los valores actuales de los campos y los guarda en self.data"""
        logging.info("Obteniendo datos de productos")

        # Actualizar productos desde la tabla
        productos = []
        for row in range(self.productos_table.rowCount()):
            try:
                cantidad = (
                    float(self.productos_table.item(row, 0).text())
                    if self.productos_table.item(row, 0)
                    else 1
                )
                precio = (
                    float(self.productos_table.item(row, 3).text().replace("S/ ", ""))
                    if self.productos_table.item(row, 3)
                    else 0.0
                )
                igv = (
                    1
                    if self.productos_table.cellWidget(row, 4).currentText() == "Sí"
                    else 0
                )  # Obtiene el valor del QComboBox
                total_igv = (
                    float(self.productos_table.item(row, 5).text().replace("S/ ", ""))
                    if self.productos_table.item(row, 5)
                    else 0.0
                )
                total_producto = (
                    float(self.productos_table.item(row, 6).text().replace("S/ ", ""))
                    if self.productos_table.item(row, 6)
                    else 0.0
                )
                # Test para obtener el valor de la celda con QComboBox (AutComboBox)
                combo_box = self.productos_table.cellWidget(row, 2)

                if isinstance(
                    combo_box, AutComboBox
                ):  # Comprobar si el widget es un AutComboBox
                    descripcion = (
                        combo_box.currentText()
                    )  # Obtener el texto seleccionado
                    logging.info(f"Descripción seleccionada: {descripcion}")
                else:
                    logging.warning("No hay AutComboBox en esta celda.")
                    descripcion = ""  # Si no es un AutComboBox, retorna un valor vacío

                producto = {
                    "cantidad": cantidad,
                    "descripcion": descripcion.upper(),
                    "unidad_medida": (
                        self.productos_table.cellWidget(row, 1).currentText()
                        if self.productos_table.cellWidget(row, 1)
                        else "UNIDAD"
                    ),
                    "precio_base": precio,
                    "igv": igv,
                    "igv_total": total_igv,
                    "precio_total": total_producto,
                }

                productos.append(producto)

            except ValueError as e:
                logging.warning(f" Error al procesar fila {row}: {e}")

        self.data = productos
        logging.info("Productos obtenidos correctamente")
        return self.data

    def actualizar_igv_producto(self, row: int) -> None:
        """Recalcula el IGV y ajusta el precio base para mantener el precio total constante.
        Si IGV es "Sí", el precio base se reduce manteniendo el precio total.
        Si IGV es "No", el precio base vuelve a su valor original."""

        logging.info(f"[INFO] Actualizando IGV del producto en fila {row}...")

        if row < 0 or row >= self.productos_table.rowCount():
            logging.warning(
                f"[WARNING] Fila {row} fuera de rango. No se puede actualizar IGV."
            )
            return

        # Obtener elementos de la tabla
        cantidad_item = self.productos_table.item(row, 0)  # Cantidad
        total_item = self.productos_table.item(row, 6)  # Precio Total del Producto
        precio_base_item = self.productos_table.item(row, 3)  # Precio Base
        igv_combo = self.productos_table.cellWidget(row, 4)

        if not cantidad_item:
            logging.error(
                f"[ERROR] No se encontró la celda de cantidad en la fila {row}."
            )
            return
        if not total_item:
            logging.error(f"[ERROR] No se encontró la celda de total en la fila {row}.")
            return
        if not precio_base_item:
            logging.error(
                f"[ERROR] No se encontró la celda de precio base en la fila {row}."
            )
            return
        if igv_combo is None:
            logging.error(f"[ERROR] No se encontró un QComboBox en la fila {row}.")
            return  # Evitar crash

        try:
            # la cantidad puede ser tipo float
            cantidad = float(cantidad_item.text()) if cantidad_item.text() else 1
            total = (
                float(total_item.text().replace("S/ ", "").replace(",", "."))
                if total_item.text()
                else 0.0
            )
            precio_base_actual = (
                float(precio_base_item.text().replace("S/ ", "").replace(",", "."))
                if precio_base_item.text()
                else 0.0
            )
            aplica_igv = igv_combo.currentText() == "Sí"

            if cantidad <= 0:
                logging.warning(f"[WARNING] Cantidad inválida en fila {row}.")
                QMessageBox.warning(
                    self,
                    "Cantidad inválida",
                    f"La cantidad en la fila {row} no es válida.",
                )
                return  # Evitar división por 0

            logging.info(
                f"[INFO] Cantidad: {cantidad}, Total: {total}, Precio Base: {precio_base_actual}, IGV: {aplica_igv}"
            )

            # 🔹 Desconectar señales temporalmente
            logging.debug(f"[DEBUG] Bloqueando señales en fila {row}...")
            self.productos_table.blockSignals(True)
            igv_combo.blockSignals(True)

            # Aplicar lógica de IGV
            if aplica_igv:
                if not hasattr(
                    self, "precios_base_originales"
                ):  # si no existe el atributo precios_base_originales
                    pass

                self.precios_base_originales[row] = (
                    precio_base_actual  # Guardamos el valor precio_base actual
                )
                # 🔹 Recalcular precio base quitando IGV, manteniendo el precio total constante
                precio_base = round(total / (cantidad * 1.18), 4)
                igv_unitario = round(precio_base * 0.18, 4)
                igv_total = round(igv_unitario * cantidad, 2)

            else:
                # 🔹 Restaurar el precio base original si existe, de lo contrario mantener el actual
                precio_base = self.precios_base_originales.get(row, precio_base_actual)
                igv_total = 0.0

            # 🔹 Actualizar los valores en la tabla sin disparar eventos adicionales
            logging.debug(
                f"[DEBUG] Actualizando fila {row}: Precio Base: {precio_base:.4f}, IGV Total: {igv_total:.2f}"
            )
            self.productos_table.setItem(
                row, 3, QTableWidgetItem(f"S/ {precio_base:.4f}")
            )  # Precio Base
            self.productos_table.setItem(
                row, 5, QTableWidgetItem(f"S/ {igv_total:.2f}")
            )  # Total IGV

            self.actualizar_resumen()
            logging.info(
                f"[INFO] Fila {row} actualizada correctamente: Precio Base: S/ {precio_base:.4f}, IGV Total: S/ {igv_total:.2f}"
            )

        except ValueError as e:
            logging.error(f"[ERROR] Error en los valores de la fila {row}: {e}")

        finally:
            # 🔹 Volver a habilitar señales después de actualizar la tabla
            logging.debug(f"[DEBUG] Desbloqueando señales en fila {row}...")
            self.productos_table.blockSignals(False)
            igv_combo.blockSignals(False)

    def actualizar_unidad_producto(self, row: int) -> None:
        """Actualiza la unidad de medida del producto en la fila dada."""
        logging.info(
            f"[INFO] Actualizando unidad de medida del producto en fila {row}..."
        )

        if row < 0 or row >= self.productos_table.rowCount():
            logging.warning(
                f"[WARNING] Fila {row} fuera de rango. No se puede actualizar la unidad."
            )
            return

    def actualizar_resumen(self):
        """Calcula y actualiza el Total IGV y el Total Importe usando la columna 'precio_total'."""
        logging.info("entrando a actualizar_resumen")
        self.productos_table.blockSignals(True)

        total_importe = 0
        total_igv = 0

        for row in range(self.productos_table.rowCount()):
            total_producto_item = self.productos_table.item(row, 6)  # Total Producto
            igv_item = self.productos_table.item(row, 5)  # Total IGV

            try:
                total_producto = (
                    float(
                        total_producto_item.text().replace("S/ ", "").replace(",", ".")
                    )
                    if total_producto_item
                    else 0.0
                )
                igv_producto = (
                    float(igv_item.text().replace("S/ ", "").replace(",", "."))
                    if igv_item
                    else 0.0
                )

                total_importe += total_producto
                total_igv += igv_producto

            except ValueError as e:
                logging.warning(f"No se pudo calcular el total en fila {row}: {e}")

        # 🔹 Actualizar etiquetas de resumen
        self.parent.resumen_view.actualizar_total_igv_and_importe(
            total_igv, total_importe - total_igv
        )

        logging.info(
            f" Resumen actualizado - IGV: S/ {total_igv:.2f}, Total: S/ {total_importe:.2f}, IGV:{total_igv}"
        )

        # 🔹 Volver a conectar señales
        self.productos_table.blockSignals(False)

    def recalcular_por_cambios(self, item):
        logging.info("cambios por modificaion en tabla")

        col_cantidad = 0
        col_precio_base = 3
        col_total = 6

        row = item.row()
        col = item.column()

        self.productos_table.blockSignals(True)

        if col == col_precio_base:
            self.actualizar_precio_base(row)
        elif col == col_cantidad:
            self.actualizar_cantidad(row)
        elif col == col_total:
            self.actualizar_precio_total(row)
        self.productos_table.blockSignals(False)  # Reactivar señales

    def actualizar_precio_base(self, row):
        """Si cambia el precio base, recalcula el total."""
        precio_base_item = self.productos_table.item(row, 3)
        cantidad_item = self.productos_table.item(row, 0)

        if precio_base_item and cantidad_item:
            try:
                precio_base = float(
                    precio_base_item.text().replace("S/ ", "").replace(",", ".")
                )  # Precio Base
                cantidad = float(cantidad_item.text())
                total = precio_base * cantidad

                self.productos_table.setItem(
                    row, 6, QTableWidgetItem(f"S/ {total:.2f}")
                )  # Mantener total fijo

                self.actualizar_resumen()
            except ValueError:
                logging.warning(f"Error al actualizar precio base en fila {row}.")

    def actualizar_cantidad(self, row):
        """Si cambia la cantidad, recalcula el total."""
        self.actualizar_precio_base(row)  # reutilizacion de codigo

    def actualizar_precio_total(self, row):
        """Si cambia el precio total, recalcula el precio base manteniendo la cantidad."""
        total_item = self.productos_table.item(row, 6)
        cantidad_item = self.productos_table.item(row, 0)
        igv_combo = self.productos_table.cellWidget(row, 4)
        if not total_item or not cantidad_item or not igv_combo:
            return

        try:
            precio_total = float(total_item.text().replace("S/ ", "").replace(",", "."))
            cantidad = float(cantidad_item.text())
            logging.info(f"Actualizando precio base por precio total en fila {row}...")
            logging.info(
                f"Precio Total: {precio_total}, Cantidad: {cantidad}, IGV: {igv_combo.currentText()}"
            )
            if igv_combo.currentText() == "Sí":
                logging.info("allando el preico base con igv afecto")
                precio_base = precio_total / (cantidad * 1.18)
            else:
                logging.info("allando el preico base con igv no afecto")
                precio_base = precio_total / cantidad

            # actualizamos el precio base
            self.productos_table.setItem(
                row, 3, QTableWidgetItem(f"S/ {precio_base:.4f}")
            )  # Precio Base

            self.actualizar_resumen()

        except ValueError:
            logging.warning(f"Error al actualizar precio total en fila {row}.")

    def agregar_fila_manual(self):
        fila = self.productos_table.rowCount()
        self.productos_table.insertRow(fila)

        self.productos_table.setItem(fila, 0, QTableWidgetItem("1"))  # Cantidad default

        unidad_combo = QComboBox()
        unidad_combo.addItems(["CAJA", "KILOGRAMO", "BOLSA", "UNIDAD"])
        self.productos_table.setCellWidget(fila, 1, unidad_combo)

        if not hasattr(self.parent, "controller"):
            logging.error("Parent no tiene 'controller'")
            return
        combo = AutComboBox(
            parent=self,
            row=fila,
            cache=self.productos_cache,
            match_func=self.parent.controller.match_fuzzy,
            parse_func=parse_productos,
        )
        combo.setEditText("")
        self.productos_table.setCellWidget(fila, 2, combo)

        self.productos_table.setItem(
            fila, 3, QTableWidgetItem("S/ 0.00")
        )  # Precio base

        igv_combo = QComboBox()
        igv_combo.addItems(["No", "Sí"])

        # Desconectar cualquier conexión previa (por seguridad)
        try:
            igv_combo.currentTextChanged.disconnect()
        except TypeError:
            pass

        igv_combo.currentTextChanged.connect(
            partial(self.actualizar_igv_producto, fila)
        )
        self.productos_table.setCellWidget(fila, 4, igv_combo)

        self.productos_table.setItem(fila, 5, QTableWidgetItem("S/ 0.00"))  # Total IGV
        self.productos_table.setItem(fila, 6, QTableWidgetItem("S/ 0.00"))  # Total
        self.agregar_boton_borrar(fila)

    def agregar_boton_borrar(self, row):
        """Agregar un botón para borrar la fila especificada."""
        boton_borrar = QPushButton("X")

        boton_borrar.setStyleSheet(
            '''
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border-radius: 7px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2);
                padding: 8px;
                margin: 3
                px;
            }
            QPushButton:hover {
                background-color: darkred;
            }
        """
        """  # Estilo del botón
            QPushButton:pressed {
                background-color: lightcoral;
            }


        '''
        )
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(15)
        sombra.setXOffset(0)
        sombra.setYOffset(4)
        sombra.setColor(QColor(0, 0, 0, 160))  # sombra gris oscura
        boton_borrar.setGraphicsEffect(sombra)
        # Conectar el clic del botón con el método que borra la fila
        boton_borrar.clicked.connect(lambda: self.borrar_fila(row))

        # Colocar el botón en la celda correspondiente (columna 7)
        self.productos_table.setCellWidget(row, 7, boton_borrar)

    def borrar_fila(self, row):
        """Eliminar la fila de la tabla."""
        self.productos_table.removeRow(row)
        self.actualizar_resumen()

    def clean_all(self):
        """Limpia todos los campos de la tabla de productos."""
        self.productos_table.setRowCount(0)
