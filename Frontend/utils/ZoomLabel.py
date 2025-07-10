from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QPainter, QImage, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint


class ZoomLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pixmap_original = None
        self.cursor_pos = None
        self.zoom_factor = 3
        self.zoom_radius = 50  # radio de la lupa

    def setPixmap(self, pixmap: QPixmap):
        super().setPixmap(pixmap)
        self.pixmap_original = pixmap.toImage()
        self.repaint()

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        self.repaint()

    def leaveEvent(self, event):
        self.cursor_pos = None
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.pixmap_original and self.cursor_pos:
            painter = QPainter(self)
            zoom_size = self.zoom_radius * 2

            # Coordenadas en la imagen original
            x = self.cursor_pos.x()
            y = self.cursor_pos.y()

            # Limitar bordes
            x = max(self.zoom_radius, min(x, self.width() - self.zoom_radius))
            y = max(self.zoom_radius, min(y, self.height() - self.zoom_radius))

            src_rect = self.pixmap_original.copy(
                x - self.zoom_radius,
                y - self.zoom_radius,
                zoom_size,
                zoom_size
            )

            # Escalamos la porción con zoom
            zoomed = QPixmap.fromImage(src_rect).scaled(
                zoom_size * self.zoom_factor,
                zoom_size * self.zoom_factor,
                Qt.KeepAspectRatio,
                Qt.FastTransformation
            )

            # Coordenadas para dibujar la lupa centrada en el cursor
            draw_x = x - self.zoom_radius
            draw_y = y - self.zoom_radius

            # Dibujar borde de lupa
            painter.setBrush(QBrush(Qt.transparent))
            painter.setPen(QPen(Qt.black, 2))
            painter.drawEllipse(draw_x, draw_y, zoom_size, zoom_size)

            # Dibujar contenido de lupa (recortado)
            painter.setClipPath(self._circular_clip(QPoint(x, y), self.zoom_radius))
            painter.drawPixmap(draw_x, draw_y, zoomed)
            painter.end()

    def _circular_clip(self, center: QPoint, radius: int):
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        return path
