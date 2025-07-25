from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class InvoiceDetailsDialog(QDialog):
    def __init__(self, details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalles de la Boleta")
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        tabla = QTableWidget()
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(["Producto", "Cantidad", "Unidad", "Precio Unit.", "Subtotal"])
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row_idx, (qty, subtotal, _, _, _, name, unit, price, _) in enumerate(details):
            tabla.insertRow(row_idx)
            datos = [name, qty, unit, price, subtotal]
            for col_idx, dato in enumerate(datos):
                item = QTableWidgetItem(str(dato))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                tabla.setItem(row_idx, col_idx, item)

        layout.addWidget(tabla)


class HistorialDialog(QDialog):
    def __init__(self, controller, id_sender, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.id_sender = id_sender

        self.setWindowTitle("Historial de Boletas")
        self.resize(900, 600)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Pestaña historial
        self.historial_tab = QWidget()
        self._init_historial_tab()
        self.tabs.addTab(self.historial_tab, "Historial")

        # Pestaña estadísticas
        self.stats_tab = QWidget()
        self._init_stats_tab()
        self.tabs.addTab(self.stats_tab, "Estadísticas")

        # Cargar datos iniciales
        self.cargar_historial()

    def _init_historial_tab(self):
        layout = QVBoxLayout(self.historial_tab)

        boton_actualizar = QPushButton("Actualizar")
        boton_actualizar.clicked.connect(self.cargar_historial)
        boton_ver_detalles = QPushButton("Ver Detalles")
        boton_ver_detalles.clicked.connect(self.mostrar_detalles)
        hlayout = QHBoxLayout()
        hlayout.addWidget(boton_actualizar)
        hlayout.addWidget(boton_ver_detalles)
        layout.addLayout(hlayout)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(
            ["ID Boleta", "Cliente", "Remitente", "Total", "Tipo", "IGV", "Fecha Emisión"]
        )
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Cliente
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Remitente
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla)

    def _init_stats_tab(self):
        layout = QVBoxLayout(self.stats_tab)
        self.stats_label = QLabel("Estadísticas:")
        layout.addWidget(self.stats_label)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def cargar_historial(self):
        data = self.controller.ver_histoial_id_sender(self.id_sender)
        self.tabla.setRowCount(0)
        if not data:
            return

        for row_idx, fila in enumerate(data):
            self.tabla.insertRow(row_idx)
            for col_idx, dato in enumerate(fila):
                item = QTableWidgetItem(str(dato))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.tabla.setItem(row_idx, col_idx, item)

        self._update_stats(data)

    def mostrar_detalles(self):
        row = self.tabla.currentRow()
        if row < 0:
            return
        invoice_id = int(self.tabla.item(row, 0).text())
        details = self.controller.ver_invoice_details(invoice_id)
        dlg = InvoiceDetailsDialog(details, self)
        dlg.exec_()

    def _update_stats(self, data):
        # Estadísticas básicas
        totales = [float(fila[3]) for fila in data]
        total = sum(totales)
        promedio = total / len(totales)
        maximo = max(totales)
        self.stats_label.setText(
            f"Estadísticas: Boletas={len(totales)}, Total={total:.2f}, "
            f"Promedio={promedio:.2f}, Máximo={maximo:.2f}"
        )

        # Gráfico de cantidad de boletas por cliente
        clientes = {}
        for _, cliente, *_ in data:
            clientes[cliente] = clientes.get(cliente, 0) + 1

        self.ax.clear()
        bars = self.ax.bar(clientes.keys(), clientes.values(), color="#58D68D", edgecolor="black")
        self.ax.set_title("Cantidad de Ventas por Cliente")
        self.ax.set_ylabel("Cantidad de Boletas")
        for bar in bars:
            h = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2, h + 0.2, str(int(h)),
                         ha='center', va='bottom')
        self.canvas.draw()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Simulación: se debe pasar el controller real
    from Backend.BoletaController import BoletaController
    from DataBase.DatabaseManager import DatabaseManager

    db = DatabaseManager()
    controller = BoletaController(db)

    dialog = HistorialDialog(controller, id_sender=1)
    dialog.exec_()
