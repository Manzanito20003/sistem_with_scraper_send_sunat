import json
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QCheckBox, QTableWidget, QCompleter, QHeaderView, QComboBox, \
    QTableWidgetItem, QWidget, QMessageBox

from DataBase.database import get_products
from PyQt5.QtWidgets import  QWidget, QVBoxLayout


class ProductView(QWidget):
    """aqui separaremos la logica de la vista de la logica de los productos"""
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent  # Referencia al contenedor principal
        self.data = {}  # ✅ Inicializar datos del formulario
        self.productos_disponibles = self.cargar_productos()  # ✅ Cargar productos correctamente
        self.productos_table = None  # Inicializar correctamente la tabla

        self.initUI()


    def initUI(self):
        logging.info("Inicializando ProductView...")  # 🔹 Log para ver si se ejecuta el constructor

        """Inicializa y devuelve el widget de productos."""
        productos_widget = QWidget()  # 🔹 Crear un QWidget contenedor
        productos_layout = QVBoxLayout(productos_widget)  # 🔹 Asociar el layout al widget

        productos_box = QGroupBox("Productos")
        productos_layout_inner = QVBoxLayout()
        ver_sugerencias = QCheckBox("Ver Todas las sugerencias")

        self.productos_table = QTableWidget(1, 7)  # Cambiar de 8 a 7 columnas
        self.productos_table.setHorizontalHeaderLabels(
            ["Cantidad", "Unidad", "Descripción", "Precio Base", "IGV", "Total IGV", "Precio total"]
        )

        self.productos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.productos_table.setColumnWidth(0, 80)  # Cantidad (más estrecha)
        self.productos_table.setColumnWidth(4, 80)  # IGV (más estrecha)
        self.productos_table.setColumnWidth(2, 200)  # Descripción

        self.productos_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.productos_table.setFont(QFont("Arial", 10))

        productos_layout_inner.addWidget(ver_sugerencias)
        productos_layout_inner.addWidget(self.productos_table)
        productos_box.setLayout(productos_layout_inner)

        productos_layout.addWidget(productos_box)  # 🔹 Agregar productos_box al layout contenedor
        self.productos_table.cellClicked.connect(self.activar_autocompletado)

        self.setLayout(productos_layout)  # 🔹 Asignar el layout al widget principal

    def cargar_productos(self):
        """Carga todos los productos desde la base de datos al iniciar la app."""
        try:
            self.productos_disponibles = get_products()  # Lista de tuplas (id, nombre, unidad, precio)
            logging.info(f"Se cargaron {len(self.productos_disponibles)} productos en memoria.")
        except Exception as e:
            logging.error(f"[ERROR] No se pudieron cargar los productos: {e}")
            self.productos_disponibles = []

    def activar_autocompletado(self, row, col):
        """Activa un QComboBox editable con autocompletado dinámico al hacer clic en la descripción."""
        try:
            if col != 2:  # Solo en la columna de Descripción
                return

            logging.info(f"[INFO] Activando autocompletado en fila {row}...")

            # Obtener descripción actual (si hay)
            descripcion_actual = self.productos_table.item(row, 2).text() if self.productos_table.item(row, 2) else ""

            # Crear QComboBox editable
            combo_box = QComboBox()
            combo_box.setEditable(True)
            combo_box.setMinimumWidth(300)
            combo_box.setInsertPolicy(QComboBox.NoInsert)  # Evita duplicados
            combo_box.setCurrentText(descripcion_actual)
            combo_box.setFocus()

            # Agregar todos los productos disponibles como opciones completas
            sugerencias = []
            for producto in self.productos_disponibles:
                id_producto, nombre, unidad, precio = producto
                texto_opcion = f"{nombre} | S/ {precio:.2f} | {unidad}"
                combo_box.addItem(texto_opcion, (nombre, precio, unidad, id_producto))
                sugerencias.append(texto_opcion)


            # Configurar QCompleter
            completer = QCompleter(sugerencias)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)

            combo_box.setCompleter(completer)

            # Conectar selección
            combo_box.currentIndexChanged.connect(lambda index: self.actualizar_producto_seleccionado(row, combo_box))

            # Reemplazar la celda con el combo
            self.productos_table.setCellWidget(row, 2, combo_box)

            # Mostrar popup inmediatamente (opcional)
            combo_box.showPopup()

        except Exception as e:
            logging.error(f"[ERROR] al activar autocompletado: {e}")

    def actualizar_producto_seleccionado(self, row, combo_box):
        """Cuando el usuario elige un producto del QComboBox, actualiza la fila con sus datos."""

        datos_producto = combo_box.currentData()
        if not datos_producto:
            return

        nombre, precio, unidad, id_producto = datos_producto

        # 🔹 Asegurar que no haya un QComboBox previo en la celda
        self.productos_table.removeCellWidget(row, 2)

        # 🔹 Actualizar valores en la tabla
        self.productos_table.setItem(row, 2, QTableWidgetItem(nombre))  # Descripción
        self.productos_table.setItem(row, 1, QTableWidgetItem(unidad))  # Unidad de medida
        self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio Base
        self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio Total

        logging.info(f" Producto seleccionado: {nombre}, ID: {id_producto}, Precio: {precio}, Unidad: {unidad}")

    def fill_form_fields(self, data):
        """Llena los campos del formulario con los datos del JSON."""
        logging.info(" Llenando campos de productos")

        if not data:
            logging.error(" No hay datos para llenar el formulario.")
            return


        # Llenar tabla de productos
        productos = data
        print("productos:",productos)
        self.productos_table.setRowCount(len(productos))
        print("Entrando a llenar los productos")

        try:
            for row, producto in enumerate(productos):
                cantidad = producto.get("cantidad", 1)
                precio = producto.get("precio_base", 0)
                precio_total=producto.get("precio_total", 0)

                #segun la regla de negocio el cliente solo pasa la boleta con el precio total del producto  aveces con precio base .
                if precio == 0 and precio_total != 0:
                    precio = precio_total / cantidad if cantidad > 0 else 0

                aplica_igv = producto.get("Igv", 0) == 1
                total_producto = cantidad*precio
                igv_producto = total_producto*0.18 if aplica_igv else 0

                # 🔹 Crear el QComboBox para IGV
                igv_combo = QComboBox()
                igv_combo.addItems(["No", "Sí"])
                igv_combo.setCurrentText("Sí" if aplica_igv else "No")
                igv_combo.currentTextChanged.connect(lambda text, row=row: self.actualizar_igv_producto(row))

                # crear el Qcombox para Unidad de medida
                unidad_combo = QComboBox()
                unidad_combo.addItems(["CAJA", "KILOGRAMO","BOLSA","UNIDAD"])
                unidad_combo.setCurrentText(producto.get("unidad_medida", "UNIDAD"))



                self.productos_table.setItem(row, 0, QTableWidgetItem(str(cantidad)))  # Cantidad
                self.productos_table.setCellWidget(row, 1, unidad_combo) # Unidad Qcombobox
                self.productos_table.setItem(row, 2,QTableWidgetItem(producto.get("descripcion", "")))  # Descripción
                self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio
                self.productos_table.setCellWidget(row, 4, igv_combo)  # IGV con QComboBox
                self.productos_table.setItem(row, 5, QTableWidgetItem(f"S/ {igv_producto:.2f}"))  # Total IGV
                self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {total_producto:.2f}"))  # Total Producto

            # 🔹 Conectar evento para actualizar el total si el usuario cambia la cantidad o el precio
            self.productos_table.itemChanged.connect(self.recalcular_por_cambios)
            # 🔹 Actualizar resumen
            self.actualizar_resumen()
        except Exception as e:
            logging.error(f"Ocurrió un problema al llenar los datos en la fila {row}: {e}")
            logging.error(f" Datos del producto problemático: {producto}")

    def obtener_datos_producto(self):
        """Toma los valores actuales de los campos y los guarda en self.data."""
        logging.info(" Actualizando datos...")

        # 🔹 Evita intentar json.loads si self.data ya es un diccionario
        if isinstance(self.data, str):
            try:
                self.data = json.loads(self.data)
            except json.JSONDecodeError as e:
                logging.error(" No se pudo decodificar JSON: {e}")
                return

        if not isinstance(self.data, dict):
            logging.error(" self.data no es un diccionario válido.")
            return

        # 🔹 Actualizar productos desde la tabla
        productos = []
        for row in range(self.productos_table.rowCount()):
            try:
                cantidad = float(self.productos_table.item(row, 0).text()) if self.productos_table.item(row, 0) else 1
                precio = float(self.productos_table.item(row, 3).text().replace("S/ ", "")) if self.productos_table.item(row,3) else 0.0
                igv = 1 if self.productos_table.cellWidget(row,
                                                           4).currentText() == "Sí" else 0  # Obtiene el valor del QComboBox
                total_igv = float(
                    self.productos_table.item(row, 5).text().replace("S/ ", "")) if self.productos_table.item(row,
                                                                                                              5) else 0.0
                total_producto = float(
                    self.productos_table.item(row, 6).text().replace("S/ ", "")) if self.productos_table.item(row,
                                                                                                              6) else 0.0

                producto = {
                    "cantidad": cantidad,
                    "descripcion": self.productos_table.item(row, 2).text() if self.productos_table.item(row,
                                                                                                         3) else "",
                    "unidad_medida": self.productos_table.cellWidget(row, 1).currentText() if self.productos_table.cellWidget(
                        row, 1) else "UNIDAD",
                    "precio_base": precio,
                    "Igv": igv,
                    "Total IGV": total_igv,
                    "precio_total": total_producto
                }

                print("producto :",producto)
                productos.append(producto)

            except ValueError as e:
                logging.warning(f" Error al procesar fila {row}: {e}")


        self.data= productos


        return self.data
    def actualizar_igv_producto(self, row: int) -> None:
        """Recalcula el IGV y ajusta el precio base para mantener el precio total constante.
           Si IGV es "Sí", el precio base se reduce manteniendo el precio total.
           Si IGV es "No", el precio base vuelve a su valor original."""

        logging.info(f"[INFO] Actualizando IGV del producto en fila {row}...")

        if row < 0 or row >= self.productos_table.rowCount():
            logging.warning(f"[WARNING] Fila {row} fuera de rango. No se puede actualizar IGV.")
            return

        # Obtener elementos de la tabla
        cantidad_item = self.productos_table.item(row, 0)  # Cantidad
        total_item = self.productos_table.item(row, 6)  # Precio Total del Producto
        precio_base_item = self.productos_table.item(row, 3)  # Precio Base
        igv_combo = self.productos_table.cellWidget(row, 4)  # Obtener el QComboBox de IGV

        # Verificación de existencia
        if not cantidad_item:
            logging.error(f"[ERROR] No se encontró la celda de cantidad en la fila {row}.")
            return
        if not total_item:
            logging.error(f"[ERROR] No se encontró la celda de total en la fila {row}.")
            return
        if not precio_base_item:
            logging.error(f"[ERROR] No se encontró la celda de precio base en la fila {row}.")
            return
        if igv_combo is None:
            logging.error(f"[ERROR] No se encontró un QComboBox en la fila {row}.")
            return  # Evitar crash

        try:
            #la cantidad puede ser tipo float
            cantidad = float(cantidad_item.text()) if cantidad_item.text() else 1
            total = float(total_item.text().replace("S/ ", "").replace(",", ".")) if total_item.text() else 0.0
            precio_base_actual = float(
                precio_base_item.text().replace("S/ ", "").replace(",", ".")) if precio_base_item.text() else 0.0
            aplica_igv = igv_combo.currentText() == "Sí"

            if cantidad <= 0:
                logging.warning(f"[WARNING] Cantidad inválida en fila {row}.")
                QMessageBox.warning(self, "Cantidad inválida", f"La cantidad en la fila {row} no es válida.")
                return # Evitar división por 0

            logging.info(
                f"[INFO] Cantidad: {cantidad}, Total: {total}, Precio Base: {precio_base_actual}, IGV: {aplica_igv}")

            # 🔹 Desconectar señales temporalmente
            logging.debug(f"[DEBUG] Bloqueando señales en fila {row}...")
            self.productos_table.blockSignals(True)
            igv_combo.blockSignals(True)

            # Aplicar lógica de IGV
            if aplica_igv:
                if not hasattr(self, "precios_base_originales"):#si no existe el atributo precios_base_originales
                    self.precios_base_originales = {}


                self.precios_base_originales[row] = precio_base_actual  # Guardamos el valor precio_base actual
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
                f"[DEBUG] Actualizando fila {row}: Precio Base: {precio_base:.4f}, IGV Total: {igv_total:.2f}")
            self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio_base:.4f}"))  # Precio Base
            self.productos_table.setItem(row, 5, QTableWidgetItem(f"S/ {igv_total:.2f}"))  # Total IGV

            logging.info(
                f"[INFO] Fila {row} actualizada correctamente: Precio Base: S/ {precio_base:.4f}, IGV Total: S/ {igv_total:.2f}")

        except ValueError as e:
            logging.error(f"[ERROR] Error en los valores de la fila {row}: {e}")

        finally:
            # 🔹 Volver a habilitar señales después de actualizar la tabla
            logging.debug(f"[DEBUG] Desbloqueando señales en fila {row}...")
            self.productos_table.blockSignals(False)
            igv_combo.blockSignals(False)
    def actualizar_unidad_producto(self, row: int) -> None:
        """Actualiza la unidad de medida del producto en la fila dada."""
        logging.info(f"[INFO] Actualizando unidad de medida del producto en fila {row}...")

        if row < 0 or row >= self.productos_table.rowCount():
            logging.warning(f"[WARNING] Fila {row} fuera de rango. No se puede actualizar la unidad.")
            return

    def actualizar_producto_seleccionado(self, row, combo_box):
        """Cuando el usuario elige un producto del QComboBox, actualiza la fila con sus datos."""

        datos_producto = combo_box.currentData()
        if not datos_producto:
            return

        nombre, precio, unidad, id_producto = datos_producto

        # 🔹 Asegurar que no haya un QComboBox previo en la celda
        self.productos_table.removeCellWidget(row, 2)

        # 🔹 Actualizar valores en la tabla
        self.productos_table.setItem(row, 2, QTableWidgetItem(nombre))  # Descripción
        self.productos_table.setItem(row, 1, QTableWidgetItem(unidad))  # Unidad de medida
        self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio Base
        self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {precio:.2f}"))  # Precio Total

        logging.info(f" Producto seleccionado: {nombre}, ID: {id_producto}, Precio: {precio}, Unidad: {unidad}")

    def actualizar_resumen(self):
        """Calcula y actualiza el Total IGV y el Total Importe usando la columna 'precio_total'."""
        print("entrando a actualizar_resumen")

        # 🔹 Desconectar señales temporalmente para evitar loops infinitos
        self.productos_table.blockSignals(True)

        total_importe = 0
        total_igv = 0

        for row in range(self.productos_table.rowCount()):
            total_producto_item = self.productos_table.item(row, 6)  # Total Producto
            igv_item = self.productos_table.item(row, 5)  # Total IGV

            try:
                total_producto = float(
                    total_producto_item.text().replace("S/ ", "").replace(",", ".")) if total_producto_item else 0.0
                igv_producto = float(igv_item.text().replace("S/ ", "").replace(",", ".")) if igv_item else 0.0

                total_importe += total_producto
                total_igv += igv_producto

            except ValueError as e:
                logging.warning(f"No se pudo calcular el total en fila {row}: {e}")

        # 🔹 Actualizar etiquetas de resumen
        self.parent.resumen_view.actualizar_total_igv_and_importe(total_igv, total_importe)


        logging.info(f" Resumen actualizado - IGV: S/ {total_igv:.2f}, Total: S/ {total_importe:.2f}")

        # 🔹 Volver a conectar señales
        self.productos_table.blockSignals(False)

    def recalcular_por_cambios(self, item):

        col_cantidad = 0
        col_precio_base = 3
        col_total = 6

        row = item.row()
        col = item.column()

        self.productos_table.blockSignals(True)  # 🚫 Evita bucles infinitos

        if col == col_precio_base:
            self.actualizar_precio_base(row)
        elif col == col_cantidad:
            self.actualizar_cantidad(row)
        elif col == col_total:
            self.actualizar_precio_total(row)

        self.productos_table.blockSignals(False)  # ✅ Reactiva señales

    def actualizar_precio_base(self, row):
        """Si cambia el precio base, recalcula el total."""
        precio_base_item = self.productos_table.item(row, 3)
        cantidad_item = self.productos_table.item(row, 0)

        if precio_base_item and cantidad_item:
            try:
                precio_base = float(precio_base_item.text().replace("S/ ", "").replace(",", ".")) # Precio Base
                cantidad = float(cantidad_item.text())
                total = precio_base * cantidad

                self.productos_table.setItem(row, 6, QTableWidgetItem(f"S/ {total:.2f}"))  # Mantener total fijo
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
            logging.info(f"Precio Total: {precio_total}, Cantidad: {cantidad}, IGV: {igv_combo.currentText()}")
            if igv_combo.currentText() == "Sí":
                logging.info("allando el preico base con igv afecto")
                precio_base = precio_total / (cantidad * 1.18)  # ✅ Deshace el IGV
            else:
                logging.info("allando el preico base con igv no afecto")
                precio_base = precio_total / cantidad  # ✅ Mantiene el precio base

            #actualizamos el precio base
            self.productos_table.setItem(row, 3, QTableWidgetItem(f"S/ {precio_base:.4f}"))  # Precio Base


        except ValueError:
            logging.warning(f"Error al actualizar precio total en fila {row}.")
