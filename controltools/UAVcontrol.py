import airsim
from PyQt6.QtCore import pyqtSignal, QObject, QTimer

class UAVcontroller(QObject): # right-hand coordinate for Airsim
    position_signal = pyqtSignal(float, float, float) # x, y, z
    
    def __init__(self):
        super().__init__()
        try:
            self.client = airsim.MultirotorClient()
            self.client.confirmConnection()
        except:
            self.running = False
            return
        self.client.enableApiControl(True)
        self.client.armDisarm(True)
        self.client.takeoffAsync().join() # takeoff the drone before controlling
        self.running=True
        self.landed=False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_control)
        self.timer.start(50)
        
        self.key_w = False
        self.key_s = False
        self.key_a = False
        self.key_d = False
        self.key_space = False
        self.key_shift = False
        self.key_q = False
        self.key_e = False
        
        self.choose = True
        
    def update_control(self):
        if self.running:
            vx, vy, vz = 0, 0, 0
            yaw_rate = 0
            if self.key_w:
                vx = 2
            if self.key_s:
                vx = -2
            if self.key_a:
                vy = -2
            if self.key_d:
                vy = 2
            if self.key_space:
                vz = -2
            if self.key_shift:
                vz = 2
            if self.key_q:
                yaw_rate = -30
            if self.key_e:
                yaw_rate = 30
            yaw_mode = airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate)
            self.client.moveByVelocityBodyFrameAsync(
                vx,
                vy,
                vz,
                0.1,
                yaw_mode=yaw_mode
            )
            if self.choose is False:
                x, y, z = self.get_state()
                self.position_signal.emit(x, y, z)
        
    def forward(self):
        self.key_w = True
        
    def backward(self):
        self.key_s = True
    
    def move_left(self):
        self.key_a = True
        
    def move_right(self):
        self.key_d = True
        
    def turn_left(self):
        self.key_q = True
        
    def turn_right(self):
        self.key_e = True
        
    def up(self):
        self.key_space = True
        
    def down(self):
        self.key_shift = True
        
    def get_state(self):
        state = self.client.getMultirotorState()
        pos = state[1][0]
        x = pos[0]
        y = pos[1]
        z = pos[2] / 100 # from cm to m
        return x, y, z
    
    def unlease(self):
        self.key_w = False
        self.key_s = False
        self.key_a = False
        self.key_d = False
        self.key_space = False
        self.key_shift = False
        self.key_q = False
        self.key_e = False
        
    def stop(self):
        if self.running is False:
            return
        self.running = False
        self.client.hoverAsync().join() # hover the drone before landing
        self.client.landAsync().join() # land the drone
        self.client.armDisarm(False)
        self.client.enableApiControl(False)
        self.landed = True