import airsim
from PyQt6.QtCore import pyqtSignal, QObject

class UAVcontroller(QObject):
    image_signal = pyqtSignal(object)
    position_signal = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True)
        self.client.armDisarm(True)
        self.client.takeoffAsync().join() # takeoff the drone before controlling
        self.running=True
        self.landed=False
        
    def forward(self):
        self.client.moveByVelocityAsync(2, 0, 0, 0.5).join()
        
    def backward(self):
        self.client.moveByVelocityAsync(-2, 0, 0, 0.5).join()
    
    def move_left(self):
        self.client.moveByVelocityAsync(0, -2, 0, 0.5).join()
        
    def move_right(self):
        self.client.moveByVelocityAsync(0, 2, 0, 0.5).join()
        
    def stop(self):
        self.running = False
        self.client.hoverAsync().join() # hover the drone before landing
        self.client.landAsync().join() # land the drone
        self.client.armDisarm(False)
        self.client.enableApiControl(False)
        self.landed = True