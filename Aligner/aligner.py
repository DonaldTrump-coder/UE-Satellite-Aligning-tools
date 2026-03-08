# input:
# XYZ: [[X1,Y1,Z1],[X2,Y2,Z2],...]
# BL: [[B1,L1],[B2,L2],...]

class Aligner:
    def __init__(self, XYZ, BL):
        self.XYZ = XYZ
        self.BL = BL