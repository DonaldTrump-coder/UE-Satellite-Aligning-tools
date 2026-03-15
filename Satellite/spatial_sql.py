from Satellite.satellites_reader import get_bound, geo_to_pixel
import sqlite3
import os
import rasterio
import numpy as np
import cv2

class SpatialDB: # query_tiles -> tiles2img
    def __init__(self, folder):
        self.folder = folder
        self.conn = sqlite3.connect(os.path.join(folder, 'tiles.db'))
        self.cursor = self.conn.cursor()
        self.index_created = False
        self.tiles = None
        self.tile_lon_size = 0
        self.tile_lat_size = 0
        
    def close(self):
        if self.conn:
            self.conn.close()
    
    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiles
            (
                id INTEGER PRIMARY KEY,
                path TEXT
            )
            """)
        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS tiles_index
            USING rtree
            (
                id,
                min_lon, max_lon,
                min_lat, max_lat
            )
            """)
        self.cursor.execute("DELETE FROM tiles")
        self.cursor.execute("DELETE FROM tiles_index")
        
        tile_id = 0
        total_lon = 0
        total_lat = 0
        total_tiles = 0
        
        for file in os.listdir(self.folder):
            if not file.endswith(".tif"):
                continue
            path = os.path.join(self.folder, file)
            bounds = get_bound(path)
            min_lon, max_lon, min_lat, max_lat = bounds.left, bounds.right, bounds.bottom, bounds.top
            tile_id += 1
            self.cursor.execute(
                "INSERT INTO tiles VALUES (?,?)",
                (tile_id, path)
            )
            self.cursor.execute(
                "INSERT INTO tiles_index VALUES (?,?,?,?,?)",
                (tile_id, min_lon, max_lon, min_lat, max_lat)
            )
            
            if tile_id == 1:
                self.tile_lon_size = max_lon - min_lon
                self.tile_lat_size = max_lat - min_lat
            
            tile_center_lon = (min_lon + max_lon) / 2
            tile_center_lat = (min_lat + max_lat) / 2
            total_lon += tile_center_lon
            total_lat += tile_center_lat
            total_tiles += 1
            
        self.conn.commit()
        self.index_created = True
        
        self.center_lon = total_lon / total_tiles
        self.center_lat = total_lat / total_tiles
        
    def query_tiles(self, view_min_lon, view_max_lon, view_min_lat, view_max_lat):
        self.view_min_lon = view_min_lon
        self.view_max_lon = view_max_lon
        self.view_min_lat = view_min_lat
        self.view_max_lat = view_max_lat
        if not self.index_created:
            return None
        self.cursor.execute(
            """
            SELECT
                tiles.path,
                tiles_index.min_lon,
                tiles_index.max_lon,
                tiles_index.min_lat,
                tiles_index.max_lat
            FROM tiles
            JOIN tiles_index
            ON tiles.id = tiles_index.id
            WHERE
                tiles_index.max_lon >= ?
            AND tiles_index.min_lon <= ?
            AND tiles_index.max_lat >= ?
            AND tiles_index.min_lat <= ?
            """,(view_min_lon,view_max_lon,view_min_lat,view_max_lat)
        )
        self.tiles = self.cursor.fetchall()
        
    def tiles2img(self, height, width):
        canvas = np.zeros((height,width,3),dtype=np.uint8)
        for path, min_lon, max_lon, min_lat, max_lat in self.tiles:
            with rasterio.open(path) as src:
                img = src.read([1,2,3])
                img = img.transpose((1,2,0))
            
            x0, y1 = geo_to_pixel(min_lon, min_lat, self.view_min_lon, self.view_max_lon, self.view_min_lat, self.view_max_lat, height, width)
            x1, y0 = geo_to_pixel(max_lon, max_lat, self.view_min_lon, self.view_max_lon, self.view_min_lat, self.view_max_lat, height, width)
            
            w = x1 - x0
            h = y1 - y0
            tile = cv2.resize(img,(w,h))
            
            cx0 = max(0,x0)
            cy0 = max(0,y0)
            cx1 = min(width,x1)
            cy1 = min(height,y1)
            
            tx0 = cx0 - x0
            ty0 = cy0 - y0
            tx1 = tx0 + (cx1 - cx0)
            ty1 = ty0 + (cy1 - cy0)
            tile_crop = tile[ty0:ty1, tx0:tx1]
            
            canvas[cy0:cy1, cx0:cx1] = tile_crop
        return canvas
    
    def get_center(self):
        return self.center_lon, self.center_lat
    
    def get_tile_size(self):
        return self.tile_lon_size, self.tile_lat_size