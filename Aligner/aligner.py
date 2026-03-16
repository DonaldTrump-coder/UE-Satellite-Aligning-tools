import numpy as np
# input:
# XYZ: [[X1,Y1,Z1],[X2,Y2,Z2],...]
# BL: [[B1,L1],[B2,L2],...]

class Aligner: # v = Bx - f
    # Parameters: [s1, s2, s3, alpha, beta, gamma, l1, l2, l3, H1, H2, ..., Hn]
    # init -> initialize -> align
    def __init__(self, xyz: np.ndarray, BL: np.ndarray):
        self.xyz = xyz
        self.BL = BL
        self.points_num = xyz.shape[0]
        self.Params = np.zeros(9 + self.points_num) # Initialize parameters
        self.dparams = np.zeros_like(self.Params) # Initialize parameter gradients
        self.a = 6378137
        self.e = 0.08181919
        self.epsilon_tol = 1e-2
        
    def initialize(self, height): # Get self.Params
        self.Params[9:] = height
        self.XYZ = np.zeros((self.points_num, 3))
        for i in range(self.points_num):
            self.XYZ[i][0], self.XYZ[i][1], self.XYZ[i][2] = self.get_XYZ(self.BL[i][0], self.BL[i][1], self.Params[9+i])
        
        xyz_mean = np.mean(self.xyz, axis=0)
        XYZ_mean = np.mean(self.XYZ, axis=0)
        xyz_norm = self.xyz - xyz_mean
        XYZ_norm = self.XYZ - XYZ_mean
        
        # estimate rotation (Kabsch Algorithm)
        H = XYZ_norm.T @ xyz_norm
        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[2,:] *= -1
            R = Vt.T @ U.T
        
        # estimate scale
        A = np.zeros((3 * self.points_num, 3))
        b = np.zeros(3 * self.points_num)
        for i in range(self.points_num):
            Xi = XYZ_norm[i]
            Yi = xyz_norm[i]
            
            A[3*i, :] = R[0,:] * Xi
            A[3*i+1, :] = R[1,:] * Xi
            A[3*i+2, :] = R[2,:] * Xi
            b[3*i:3*i+3] = Yi
        
        S = np.linalg.lstsq(A, b, rcond=None)[0]
        
        #estimate translations
        T = xyz_mean - S * (R @ XYZ_mean.T)
        
        self.Params[0], self.Params[1], self.Params[2] = S[0], S[1], S[2]
        if abs(R[2,0]) < 1 - 1e-6:
            self.Params[3], self.Params[4], self.Params[5] = np.arctan2(R[2,1], R[2,2]), np.arcsin(-R[2,0]), np.arctan2(R[1,0], R[0,0])
        else:
            self.Params[3] = np.arctan2(-R[0,1], R[0,2]) if R[2,0] < 0 else np.arctan2(R[0,1], -R[0,2])
            self.Params[4] = np.pi/2 if R[2,0] < 0 else -np.pi/2
            self.Params[5] = 0
        self.Params[6], self.Params[7], self.Params[8] = T[0], T[1], T[2]
        
    def align(self):
        while 1:
            self.get_XYZs()
            self.get_R()
            self.get_B()
            self.get_f()
            U, S, Vt = np.linalg.svd(self.B, full_matrices=False)
            S_inv = np.diag([1/s if s > 1e-10 else 0 for s in S])
            self.dparams = Vt.T @ S_inv @ U.T @ self.f
            self.Params += self.dparams
            if np.max(np.abs(self.dparams)) < self.epsilon_tol:
                break
    
    def get_XYZ(self, B, L, H):
        N = self.a / (np.sqrt(1 - self.e**2 * np.sin(B)**2))
        X = (N + H) * np.cos(B) * np.cos(L)
        Y = (N + H) * np.cos(B) * np.sin(L)
        Z = (N * (1 - self.e**2) + H) * np.sin(B)
        return X, Y, Z
    
    def get_XYZs(self):
        self.XYZ = np.zeros((self.points_num, 3))
        for i in range(self.points_num):
            self.XYZ[i][0], self.XYZ[i][1], self.XYZ[i][2] = self.get_XYZ(self.BL[i][0], self.BL[i][1], self.Params[9+i])
            
    def get_R(self):
        alpha, beta, gamma = self.Params[3], self.Params[4], self.Params[5]
        self.R = np.zeros((3, 3))
        self.R[0,0] = np.cos(gamma) * np.cos(beta)
        self.R[0,1] = np.cos(gamma) * np.sin(beta) * np.sin(alpha) - np.sin(gamma) * np.cos(alpha)
        self.R[0,2] = np.cos(gamma) * np.sin(beta) * np.cos(alpha) + np.sin(gamma) * np.sin(alpha)
        self.R[1,0] = np.sin(gamma) * np.cos(beta)
        self.R[1,1] = np.sin(gamma) * np.sin(beta) * np.sin(alpha) + np.cos(gamma) * np.cos(alpha)
        self.R[1,2] = np.sin(gamma) * np.sin(beta) * np.cos(alpha) - np.cos(gamma) * np.sin(alpha)
        self.R[2,0] = -np.sin(beta)
        self.R[2,1] = np.cos(beta) * np.sin(alpha)
        self.R[2,2] = np.cos(beta) * np.cos(alpha)
            
    def get_B(self):
        self.B = np.zeros((3 * self.points_num, 9 + self.points_num))
        a1, a2, a3 = self.R[0,:]
        b1, b2, b3 = self.R[1,:]
        c1, c2, c3 = self.R[2,:]
        s1, s2, s3 = self.Params[0], self.Params[1], self.Params[2]
        alpha, beta, gamma = self.Params[3], self.Params[4], self.Params[5]
        for i in range(self.points_num):
            Xi, Yi, Zi = self.XYZ[i]
            Bi, Li = self.BL[i]
            self.B[3 * i, 0] = a1 * Xi + b1 * Yi + c1 * Zi # ds1
            self.B[3 * i, 3] = s1 * Yi * (np.cos(gamma) * np.sin(beta) * np.cos(alpha) + np.sin(gamma) * np.sin(alpha)) + s1 * Zi * (-np.cos(gamma) * np.sin(beta) * np.sin(alpha) + np.sin(gamma) * np.cos(alpha)) # dalpha
            self.B[3 * i, 4] = -s1 * Xi * np.cos(gamma) * np.sin(beta) + s1 * Yi * (np.cos(gamma) * np.cos(beta) * np.sin(alpha)) + s1 * Zi * (np.cos(gamma) * np.cos(beta) * np.cos(alpha)) # dbeta
            self.B[3 * i, 5] = -s1 * Xi * np.cos(beta) * np.sin(gamma) + s1 * Yi * (-np.sin(gamma) * np.sin(beta) * np.sin(alpha) - np.cos(gamma) * np.cos(alpha)) + s1 * Zi * (-np.sin(gamma) * np.sin(beta) * np.cos(alpha) + np.cos(gamma) * np.sin(alpha)) # dgamma
            self.B[3 * i, 6] = 1 # dl1
            self.B[3 * i, 9 + i] = s1 * a1 * np.cos(Bi) * np.cos(Li) + s1 * a2 * np.cos(Bi) * np.sin(Li) + s1 * a3 * np.sin(Bi) # dHi
            
            self.B[3 * i + 1, 1] = b1 * Xi + b2 * Yi + b3 * Zi # ds2
            self.B[3 * i + 1, 3] = s2 * Yi * (np.sin(gamma) * np.sin(beta) * np.cos(alpha) - np.cos(gamma) * np.sin(alpha)) + s2 * Zi * (-np.sin(gamma) * np.sin(beta) * np.sin(alpha) - np.cos(gamma) * np.cos(alpha)) # dalpha
            self.B[3 * i + 1, 4] = -s2 * Xi * np.sin(gamma) * np.sin(beta) + s2 * Yi * np.sin(gamma) * np.cos(beta) * np.sin(alpha) + s2 * Zi * np.sin(gamma) * np.cos(beta) * np.cos(alpha) # dbeta
            self.B[3 * i + 1, 5] = s2 * Xi * np.cos(gamma) * np.cos(beta) + s2 * Yi * (np.cos(gamma) * np.sin(beta) * np.sin(alpha) - np.sin(gamma) * np.cos(alpha)) + s2 * Zi * (np.cos(gamma) * np.sin(beta) * np.cos(alpha) + np.sin(gamma) * np.sin(alpha)) # dgamma
            self.B[3 * i + 1, 7] = 1 # dl2
            self.B[3 * i + 1, 9 + i] = s2 * b1 * np.cos(Bi) * np.cos(Li) + s2 * b2 * np.cos(Bi) * np.sin(Li) + s2 * b3 * np.sin(Bi) # dHi
            
            self.B[3 * i + 2, 2] = c1 * Xi + c2 * Yi + c3 * Zi # ds3
            self.B[3 * i + 2, 3] = s3 * Yi * np.cos(beta) * np.cos(alpha) - s3 * Zi * np.cos(beta) * np.sin(alpha) # dalpha
            self.B[3 * i + 2, 4] = -s3 * Xi * np.cos(beta) - s3 * Yi * np.sin(beta) * np.sin(alpha) - s3 * Zi * np.sin(beta) * np.cos(alpha) # dbeta
            self.B[3 * i + 2, 8] = 1 # dl3
            self.B[3 * i + 2, 9 + i] = s3 * c1 * np.cos(Bi) * np.cos(Li) + s3 * c2 * np.cos(Bi) * np.sin(Li) + s3 * c3 * np.sin(Bi) # dHi
        
        # constructing B matrix
        
    def get_f(self):
        self.f = np.zeros(3 * self.points_num)
        a1, a2, a3 = self.R[0,:]
        b1, b2, b3 = self.R[1,:]
        c1, c2, c3 = self.R[2,:]
        s1, s2, s3 = self.Params[0], self.Params[1], self.Params[2]
        l1, l2, l3 = self.Params[6], self.Params[7], self.Params[8]
        for i in range(self.points_num):
            Xi, Yi, Zi = self.XYZ[i]
            xi, yi, zi = self.xyz[i]
            self.f[3 * i] = xi - s1 * (a1 * Xi + a2 * Yi + a3 * Zi) - l1
            self.f[3 * i + 1] = yi - s2 * (b1 * Xi + b2 * Yi + b3 * Zi) - l2
            self.f[3 * i + 2] = zi - s3 * (c1 * Xi + c2 * Yi + c3 * Zi) - l3