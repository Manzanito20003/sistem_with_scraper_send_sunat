"""class de resumen de la cliente"""
import logging

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox, QMessageBox

from DataBase.database import get_next_invoice_number


class ResumenView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.data = {}
        self.serie=""
        self.numero=""
        self.igv_total=""
        self.total=""


    def initUI(self):
        print("ResumenView")

        resumen_layout = QVBoxLayout()

        resumen_box = QGroupBox("Resumen")

        # 🔹 Agregar etiquetas dinámicas
        self.serie_label = QLabel("Serie: B00-00")
        self.numero_label = QLabel("Número: 00")
        self.igv_label = QLabel("Total IGV: S/ 0.00")  # 🟢 Cambiará dinámicamente
        self.total_label = QLabel("Total importe: S/ 0.00")  # 🟢 Cambiará dinámicamente

        # Agregar widgets al layout
        resumen_layout.addWidget(self.serie_label)
        resumen_layout.addWidget(self.numero_label)
        resumen_layout.addWidget(self.igv_label)
        resumen_layout.addWidget(self.total_label)

        resumen_box.setLayout(resumen_layout)

        # Configurar el layout principal de la clase
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(resumen_box)

        self.setLayout(main_layout)

    def actualizar_total_igv_and_importe(self, total_igv, total_importe):
        self.igv_total=total_igv
        self.total=total_importe

        self.igv_label.setText(f"Total IGV: S/ {total_igv:.2f}")
        self.total_label.setText(f"Total importe: S/ {total_importe:.2f}")


    def actualizar_serie_y_numero(self,id_sender,tipo_documento):
        """Actualiza la serie y número de documento basado en la selección de tipo y el ID del remitente."""

        if(id_sender==None):
            id_sender=0


        num_documento = get_next_invoice_number(id_sender)
        if num_documento is None:
            logging.error(f" No se pudo obtener el número de documento para el remitente {id_sender}")
            QMessageBox.critical(self, f"Error", f"No se pudo obtener el número de documento {id_sender}")
            return # No se pudo obtener el número

        # 🔹 Determinar el prefijo según el tipo de documento
        prefijo = "B" if tipo_documento == "Boleta" else "F"

        serie = f"{prefijo}{id_sender:02d}-{num_documento:02d}"
        numero = f"{num_documento:02d}"

        #guardar los datos
        self.serie=serie
        self.numero=numero

        self.serie_label.setText(f"Serie: {serie}")
        self.numero_label.setText(f"Número: {numero}")

        logging.info(f" Serie y Número actualizados: {serie} - {numero}")

    def obtener_datos_resumen(self):
        """Obtiene los datos del resumen."""


        return {
            "serie": self.serie,
            "numero": self.numero,
            "igv_total": self.igv_total,
            "total": self.total
        }




