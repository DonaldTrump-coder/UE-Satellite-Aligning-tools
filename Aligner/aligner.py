import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from controltools.coordinates import Coordinates
# input:
# xyz: [[x1,y1,z1],[x2,y2,z2],...]
# BL: [[B1,L1],[B2,L2],...]

class Aligner: # Ax = b
    # Parameters: [r00, r01, r10, r11, t1,t2]
    # init -> initialize -> align
    def __init__(self, xyz: np.ndarray, BL: np.ndarray):
        self.xy = xyz[:, :2]
        self.BL = BL
        self.points_num = xyz.shape[0]
        self.Params = np.zeros(6) # Initialize parameters
        
    def initialize(self): # Get self.Params
        self.A = np.zeros((2 * self.points_num, 6))
        self.b = np.zeros((2 * self.points_num, 1))
        
    def get_A(self):
        for i in range(self.points_num):
            x = self.xy[i, 0]
            y = self.xy[i, 1]
            self.A[2 * i, 0] = x
            self.A[2 * i, 1] = y
            self.A[2 * i, 4] = 1
            self.A[2 * i + 1, 2] = x
            self.A[2 * i + 1, 3] = y
            self.A[2 * i + 1, 5] = 1
            
    def get_b(self):
        for i in range(self.points_num):
            self.b[2 * i, 0] = self.BL[i, 0]
            self.b[2 * i + 1, 0] = self.BL[i, 1]
        
    def align(self):
        self.get_A()
        self.get_b()
        U, S, Vt = np.linalg.svd(self.A, full_matrices=False)
        S_inv = np.diag(1 / S)
        self.Params = Vt.T @ S_inv @ U.T @ self.b
            
class Align_worker(QObject):
    unsufficient_points = pyqtSignal()
    finished = pyqtSignal(object)
    
    def __init__(self, coordinates: list[Coordinates]):
        super().__init__()
        self.coordinates = coordinates
        if self.coordinates.__len__() < 5:
            self.error = True
            self.unsufficient_points.emit()
            return
        self.error = False
    
    def calculate(self):
        if self.error:
            return
        xyz = np.array([[c.x, c.y, c.z] for c in self.coordinates])
        bl = np.array([[c.lat, c.lon] for c in self.coordinates])
        aligner = Aligner(xyz, bl)
        aligner.initialize()
        aligner.align()
        self.finished.emit(aligner.Params)