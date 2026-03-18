from PyQt6.QtWidgets import QLabel
from Satellite.spatial_sql import SpatialDB
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen
from controltools.coordinates import GeoCoordinate

class SatelliteLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.view_lon = None
        self.view_lat = None
        self.lon_per_pix = None
        self.lat_per_pix = None
        
        self.tile_worker = None
        self.setScaledContents(True)
        
        self.last_pos = None
        self.dragging = False
        
        self.chosen_lon = None
        self.chosen_lat = None
        self.choose = True
        
        self.coors = []
        
    def set_images(self, folder):
        if self.tile_worker:
            self.tile_worker.close()
            self.tile_thread.quit()
            self.tile_thread.wait()
        self.db = SpatialDB(folder)
        self.tile_thread = QThread()
        self.tile_worker = Tile_Worker(self.db)
        self.tile_worker.initialized.connect(self.initialized)
        self.tile_worker.finished.connect(self.set_image)
        self.tile_worker.moveToThread(self.tile_thread)
        
        self.tile_thread.start()
        self.tile_worker.create_table()
        self.tile_worker.initialize(self.height(), self.width())
        
    def initialized(self, object):
        self.view_lon, self.view_lat, self.lon_per_pix, self.lat_per_pix = object
        self.render()
        
    def render(self):
        self.tile_worker.render_image(self.view_lon, self.view_lat, self.lon_per_pix, self.lat_per_pix, self.height(), self.width())
        
    def set_image(self, img):
        height, width, _ = img.shape
        qimage = QImage(img.data, width, height, width * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)
        
    def mousePressEvent(self, event):
        if not self.tile_worker:
            return
        if event.button() == Qt.MouseButton.RightButton:
            self.dragging = True
            self.last_pos = event.pos()
        if event.button() == Qt.MouseButton.LeftButton and self.choose:
            pos = event.pos()
            x = pos.x()
            y = pos.y()
            dx = x - self.width() / 2
            dy = y - self.height() / 2
            self.chosen_lon = self.view_lon + dx * self.lon_per_pix
            self.chosen_lat = self.view_lat - dy * self.lat_per_pix
            self.update()
            
    def mouseMoveEvent(self, event):
        if not self.dragging:
            return
        pos = event.pos()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        self.view_lon -= dx * self.lon_per_pix
        self.view_lat += dy * self.lat_per_pix
        self.render()
        self.last_pos = pos
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.dragging = False
    
    def wheelEvent(self, event):
        if not self.tile_worker:
            return
        delta = event.angleDelta().y()
        
        if delta > 0:
            scale = 0.8
        else:
            scale = 1.25
        self.lon_per_pix *= scale
        self.lat_per_pix *= scale
        self.render()
    
    def paintEvent(self, a0):
        super().paintEvent(a0)
        
        if self.choose:
            if self.chosen_lon is None or self.chosen_lat is None:
                return
            dx = (self.chosen_lon - self.view_lon) / self.lon_per_pix
            dy = (self.view_lat - self.chosen_lat) / self.lat_per_pix
            x = int(self.width() / 2 + dx)
            y = int(self.height() / 2 + dy)
            painter = QPainter(self)
            pen = QPen(Qt.GlobalColor.red, 2)
            painter.setPen(pen)

            size = 10
            painter.drawLine(x - size, y, x + size, y)
            painter.drawLine(x, y - size, x, y + size)
            
            for coor in self.coors:
                dx = (coor.lon - self.view_lon) / self.lon_per_pix
                dy = (self.view_lat - coor.lat) / self.lat_per_pix
                x = int(self.width() / 2 + dx)
                y = int(self.height() / 2 + dy)
                painter.drawLine(x - size, y, x + size, y)
                painter.drawLine(x, y - size, x, y + size)
            
            painter.end()
        else:
            x = int(self.width() / 2)
            y = int(self.height() / 2)
            painter = QPainter(self)
            pen = QPen(Qt.GlobalColor.red, 2)
            painter.setPen(pen)
            size = 10
            painter.drawLine(x - size, y, x + size, y)
            painter.drawLine(x, y - size, x, y + size)
            painter.end()
    
    def render_position(self, B, L):
        self.tile_worker.render_image(L, B, self.lon_per_pix, self.lat_per_pix, self.height(), self.width())
        
    def save(self):
        geocoordinate = GeoCoordinate(self.chosen_lon, self.chosen_lat)
        self.coors.append(geocoordinate)
        return geocoordinate
        
class Tile_Worker(QObject):
    finished = pyqtSignal(object)
    initialized = pyqtSignal(object)
    
    def __init__(self, db: SpatialDB):
        super().__init__()
        self.db = db
        
    def close(self):
        self.db.close()
        
    def create_table(self):
        self.db.create_table()
    
    def initialize(self, height, width):
        center_lon, center_lat = self.db.get_center()
        tile_lon_size, tile_lat_size = self.db.get_tile_size()
        lon_per_pix = tile_lon_size / width
        lat_per_pix = tile_lat_size / height
        self.initialized.emit((center_lon, center_lat, lon_per_pix, lat_per_pix))
        
    def render_image(self, view_lon, view_lat, lon_per_pix, lat_per_pix, height, width):
        view_min_lon = view_lon - width * lon_per_pix / 2
        view_max_lon = view_lon + width * lon_per_pix / 2
        view_min_lat = view_lat - height * lat_per_pix / 2
        view_max_lat = view_lat + height * lat_per_pix / 2
        self.db.query_tiles(view_min_lon, view_max_lon, view_min_lat, view_max_lat)
        img = self.db.tiles2img(height, width)
        self.finished.emit(img)