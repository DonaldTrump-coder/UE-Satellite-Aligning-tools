from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QFileDialog, QListWidgetItem
from UI.WebView import WebView
from UI.Satellite_Label import SatelliteLabel
from controltools.UAVcontrol import UAVcontroller
from PyQt6.QtCore import QThread, QTimer, Qt
from PyQt6.QtGui import QAction, QIcon
from Aligner.aligner_mode import AlignerMode
from UI.Button import IconButton
from controltools.coordinates import Coordinates
from Aligner.aligner import Align_worker
import numpy as np
import os

class Application(QMainWindow):
    def __init__(self, address):
        super().__init__()
        self.setWindowTitle("UE-Satellite Aligner")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout()
        self.image_browser = WebView(address)
        label_widget = QWidget()
        main_layout.addWidget(self.image_browser, 2)
        main_layout.addWidget(label_widget, 1)
        main_widget.setLayout(main_layout)
        
        label_layout = QVBoxLayout()
        label_widget.setLayout(label_layout)
        self.label_list = QListWidget()
        self.buttons_widget = QWidget()
        self.satellite_widget = SatelliteLabel()
        label_layout.addWidget(self.label_list, 8)
        label_layout.addWidget(self.buttons_widget, 2)
        label_layout.addWidget(self.satellite_widget, 14)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.add_btn = IconButton()
        self.add_btn.setIcon(QIcon("resources/plus.png"))
        self.minus_btn = IconButton()
        self.minus_btn.setIcon(QIcon("resources/minus.png"))
        self.align_btn = IconButton()
        self.align_btn.setIcon(QIcon("resources/align.png"))
        buttons_layout.addWidget(self.align_btn)
        buttons_layout.addWidget(self.minus_btn)
        buttons_layout.addWidget(self.add_btn)
        self.buttons_widget.setLayout(buttons_layout)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_btn.clicked.connect(self.add_coordinates)
        self.align_btn.clicked.connect(self.align)
        
        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        option_menu = menubar.addMenu("Options")
        open_sat_action = QAction("Open Images", self)
        file_menu.addAction(open_sat_action)
        
        open_sat_action.triggered.connect(self.import_satellite)
        QTimer.singleShot(0, self.start_control)
        
        self.controller = None
        self.aligner_mode = AlignerMode.LABEL
        self.satellite_widget.choose = True
        
        self.coordinates = []
        self.folder = None
        self.params = None
        
        self.resize(1400, 800)
        
    def resize(self, w, h):
        super().resize(w, h)
        self.add_btn.setMinimumWidth(int(self.buttons_widget.size().width() * 0.15))
        self.add_btn.setMaximumWidth(int(self.buttons_widget.size().width() * 0.15))
        self.minus_btn.setMinimumWidth(int(self.buttons_widget.size().width() * 0.15))
        self.minus_btn.setMaximumWidth(int(self.buttons_widget.size().width() * 0.15))
        self.align_btn.setMinimumWidth(int(self.buttons_widget.size().width() * 0.15))
        self.align_btn.setMaximumWidth(int(self.buttons_widget.size().width() * 0.15))
        
    def start_control(self):
        self.UAV_thread = QThread()
        self.controller = UAVcontroller()
        self.controller.position_signal.connect(self.change_position)
        self.controller.moveToThread(self.UAV_thread)
        self.UAV_thread.start()
    
    def import_satellite(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Satellite Images Folder",
            "./data",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if not folder:
            return
        
        self.satellite_widget.set_images(folder)
        self.folder = folder
        file_path = os.path.join(self.folder, "params.txt")
        if not os.path.isfile(file_path):
            return
        self.params = np.loadtxt(file_path)
        r00, r01, r10, r11, t0, t1 = self.params[0], self.params[1], self.params[2], self.params[3], self.params[4], self.params[5]
        self.B = np.array([[r00, r01, t0],[r10, r11, t1]])
            
        self.aligner_mode = AlignerMode.APPLICATION
        self.controller.choose = False
        self.satellite_widget.choose = False
        
    def closeEvent(self, event):
        if self.controller:
            self.controller.stop()
        if self.UAV_thread:
            self.UAV_thread.quit()
            
        if self.satellite_widget.tile_worker:
            self.satellite_widget.tile_worker.close()
            self.satellite_widget.tile_thread.quit()
        
        event.accept()
        
    def keyPressEvent(self, event):
        if not self.controller:
            return
        key = event.key()
        
        if key == Qt.Key.Key_W:
            self.controller.forward()
        elif key == Qt.Key.Key_S:
            self.controller.backward()
        elif key == Qt.Key.Key_A:
            self.controller.move_left()
        elif key == Qt.Key.Key_D:
            self.controller.move_right()
        elif key == Qt.Key.Key_Q:
            self.controller.turn_left()
        elif key == Qt.Key.Key_E:
            self.controller.turn_right()
        elif key == Qt.Key.Key_Space:
            self.controller.up()
        elif key == Qt.Key.Key_Shift:
            self.controller.down()
            
    def keyReleaseEvent(self, event):
        if not self.controller:
            return
        self.controller.unlease()
        
    def add_coordinates(self):
        if not self.controller:
            return
        geocoor = self.satellite_widget.save()
        x, y, z = self.controller.get_state()
        item = QListWidgetItem(f"{self.coordinates.__len__()+1}")
        self.label_list.addItem(item)
        self.coordinates.append(Coordinates(x, y, z, geocoor.lon, geocoor.lat))
        
    def align(self):
        self.align_thread = QThread()
        align_worker = Align_worker(self.coordinates)
        align_worker.unsufficient_points.connect(self.unsuffcient_warning)
        align_worker.finished.connect(self.aligned)
        align_worker.moveToThread(self.align_thread)
        self.align_thread.start()
        align_worker.calculate()
        
    def unsuffcient_warning(self):
        pass
        
    def aligned(self, params):
        self.align_thread.quit()
        if self.folder:
            np.savetxt(os.path.join(self.folder, "params.txt"), params)
            self.params = params
            r00, r01, r10, r11, t0, t1 = self.params[0], self.params[1], self.params[2], self.params[3], self.params[4], self.params[5]
            self.B = np.array([[r00, r01, t0],[r10, r11, t1]])
            
            self.aligner_mode = AlignerMode.APPLICATION
            self.controller.choose = False
            self.satellite_widget.choose = False
            
    def change_position(self, x, y, z):
        x = np.array([[x], [y], [1]])
        BL = self.B @ x
        self.satellite_widget.render_position(BL[0][0], BL[1][0])