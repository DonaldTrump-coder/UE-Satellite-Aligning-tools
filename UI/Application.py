from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QFileDialog
from UI.WebView import WebView
from UI.Satellite_Label import SatelliteLabel
from controltools.UAVcontrol import UAVcontroller
from PyQt6.QtCore import QThread, QTimer
from PyQt6.QtGui import QAction

class Application(QMainWindow):
    def __init__(self, address):
        super().__init__()
        self.setWindowTitle("UE-Satellite Aligner")
        self.resize(1400, 800)
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
        buttons_widget = QWidget()
        self.satellite_widget = SatelliteLabel()
        label_layout.addWidget(self.label_list, 6)
        label_layout.addWidget(buttons_widget, 1)
        label_layout.addWidget(self.satellite_widget, 12)
        
        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        option_menu = menubar.addMenu("Options")
        open_sat_action = QAction("Open Images", self)
        file_menu.addAction(open_sat_action)
        
        open_sat_action.triggered.connect(self.import_satellite)
        QTimer.singleShot(0, self.start_control)
        
        self.controller = None
        
    def start_control(self):
        self.UAV_thread = QThread()
        self.controller = UAVcontroller()
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
        
    def closeEvent(self, event):
        if self.controller:
            self.controller.stop()
        if self.UAV_thread:
            self.UAV_thread.quit()
            self.UAV_thread.wait()
            
        if self.satellite_widget.tile_worker:
            self.satellite_widget.tile_worker.close()
            self.satellite_widget.tile_thread.quit()
            self.satellite_widget.tile_thread.wait()
        
        event.accept()