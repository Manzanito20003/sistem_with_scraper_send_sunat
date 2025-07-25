from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint

class ZoomLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pixmap_original = None
        self.cursor_pos = None
        self.zoom_factor = 2       # cuanto se amplía
        self.zoom_radius = 50      # tamaño visible de la lupa (círculo)

    def setPixmap(self, pixmap: QPixmap):
        super().setPixmap(pixmap)
        # Guardamos el QPixmap directamente (evita overhead de QImage)
        self.pixmap_original = pixmap
        self.update()

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        self.update()

    def leaveEvent(self, event):
        self.cursor_pos = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.pixmap_original and self.cursor_pos:
            painter = QPainter(self)
            zoom_size = self.zoom_radius * 2

            # Coordenadas originales (imagen mostrada)
            x = self.cursor_pos.x()
            y = self.cursor_pos.y()

            # Limitar bordes para que no salga del widget
            x = max(self.zoom_radius, min(x, self.width() - self.zoom_radius))
            y = max(self.zoom_radius, min(y, self.height() - self.zoom_radius))

            # Coordenadas relativas a la imagen original
            ratio_x = x / self.width()
            ratio_y = y / self.height()
            src_x = int(ratio_x * self.pixmap_original.width())
            src_y = int(ratio_y * self.pixmap_original.height())

            # Porción que se toma (antes de escalar)
            src_rect = self.pixmap_original.copy(
                src_x - self.zoom_radius,
                src_y - self.zoom_radius,
                zoom_size,
                zoom_size
            )

            # Escalamos el contenido pero no el tamaño del círculo
            zoomed = src_rect.scaled(
                zoom_size * self.zoom_factor,
                zoom_size * self.zoom_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Ajuste para centrar la imagen aumentada dentro del círculo
            offset = int((zoomed.width() - zoom_size) / 2)
            draw_x = x - self.zoom_radius
            draw_y = y - self.zoom_radius

            # Recorte circular
            painter.setClipPath(self._circular_clip(QPoint(x, y), self.zoom_radius))
            painter.drawPixmap(draw_x - offset, draw_y - offset, zoomed)
            painter.setClipping(False)

            # Dibujar borde de la lupa
            painter.setBrush(QBrush(Qt.transparent))
            painter.setPen(QPen(Qt.black, 2))
            painter.drawEllipse(draw_x, draw_y, zoom_size, zoom_size)
            painter.end()

    def _circular_clip(self, center: QPoint, radius: int):
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        return path
