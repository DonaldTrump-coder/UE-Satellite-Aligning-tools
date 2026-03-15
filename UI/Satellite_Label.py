from PyQt5.QtWidgets import QLabel
from Satellite.spatial_sql import SpatialDB
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap

class SatelliteLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.view_lon = None
        self.view_lat = None
        self.lon_per_pix = None
        self.lat_per_pix = None
        
        self.tile_worker = None
        self.setScaledContents(True)
        
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
        height, width, channel = img.shape
        qimage = QImage(img.data, width, height, width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)
        
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