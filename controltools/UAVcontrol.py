import airsim
from PyQt5.QtCore import QThread, pyqtSignal

class UAVcontroller(QThread):
    def __init__(self):
        super().__init__()
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True)
        self.client.armDisarm(True)
        self.client.takeoffAsync().join() # takeoff the drone before controlling
        self.running=True
        self.landed=False
        
    def run(self):
        pass