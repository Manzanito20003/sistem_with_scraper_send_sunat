"""class de resumen de la cliente"""

import logging

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox, QMessageBox


class ResumenView(QWidget):
    def __init__(self, db=None):
        super().__init__()
        self.serie_label = QLabel("Serie: B00-00")
        self.numero_label = QLabel("Número: 00")
        self.igv_label = QLabel("Total IGV: S/ 0.00")
        self.valor_label = QLabel("Valor Total: S/ 0.00")
        self.total_label = QLabel("Total importe: S/ 0.00")
        self.db = db
        self.initUI()

        self.data = {}
        self.serie = None
        self.numero = None
        self.igv_total = None
        self.valor_total = None
        self.total_importe = None

    def initUI(self):

        resumen_layout = QVBoxLayout()
        resumen_box = QGroupBox("Resumen")
        # Agregar etiquetas dinámicas

        # Agregar widgets al layout
        resumen_layout.addWidget(self.serie_label)
        resumen_layout.addWidget(self.numero_label)
        resumen_layout.addWidget(self.igv_label)
        resumen_layout.addWidget(self.valor_label)
        resumen_layout.addWidget(self.total_label)

        resumen_box.setLayout(resumen_layout)

        # Configurar el layout principal de la clase
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(resumen_box)

        self.setLayout(main_layout)

    def actualizar_total_igv_and_importe(self, total_igv, valor_total):
        self.igv_total = total_igv
        self.valor_total = valor_total
        self.total_importe = total_igv + valor_total

        self.igv_label.setText(f"Total IGV: S/ {total_igv:.2f}")
        self.valor_label.setText(f"Valor Total: S/ {valor_total:.2f}")
        self.total_label.setText(f"Total importe: S/ {self.total_importe:.2f}")

    def actualizar_serie_y_numero(self, id_sender=None, tipo_documento="BOLETA"):
        """Actualiza la serie y número de documento basado en la selección de tipo y el ID del remitente."""

        if id_sender is None:
            return
        num_documento = self.db.get_next_invoice_number(id_sender)
        if num_documento is None:
            logging.error(
                f" No se pudo obtener el número de documento para el remitente {id_sender}"
            )
            QMessageBox.critical(
                self, f"Error", f"No se pudo obtener el número de documento {id_sender}"
            )
            return  # No se pudo obtener el número

        # Determinar el prefijo según el tipo de documento
        prefijo = "B" if tipo_documento == "BOLETA" else "F"

        serie = f"{prefijo}{id_sender:02d}-{num_documento:02d}"
        numero = f"{num_documento:02d}"

        # guardar los datos
        self.serie = serie
        self.numero = numero

        self.serie_label.setText(f"Serie: {serie}")
        self.numero_label.setText(f"Número: {numero}")

        logging.info(f" Serie y Número actualizados: {serie} - {numero}")

    def obtener_datos_resumen(self):
        """Obtiene los datos del resumen."""
        logging.info("Obteniendo datos del resumen...")
        return {
            "serie": self.serie,
            "numero": self.numero,
            "sub_total": round(self.valor_total, 2),
            "igv_total": self.igv_total,
            "total": self.total_importe,
        }

    def clean_all(self):
        """Limpia todos los campos del formulario."""
        self.serie_label.setText("Serie: B00-00")
        self.numero_label.setText("Número: 00")
        self.igv_label.setText("Total IGV: S/ 0.00")
        self.valor_label.setText("Valor Total: S/ 0.00")
        self.total_label.setText("Total importe: S/ 0.00")
