from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QAction, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from UI.Satellite_Label import SatelliteLabel

class Application(QMainWindow):
    def __init__(self, address):
        super().__init__()
        self.setWindowTitle("UE-Satellite Aligner")
        self.resize(1400, 800)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout()
        self.image_browser = QWebEngineView()
        self.image_browser.load(QUrl(address))
        label_widget = QWidget()
        main_layout.addWidget(self.image_browser, 2)
        main_layout.addWidget(label_widget, 1)
        main_widget.setLayout(main_layout)
        
        label_layout = QVBoxLayout()
        label_widget.setLayout(label_layout)
        self.label_list = QListWidget()
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("border: 2px solid red;")
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
    
    def import_satellite(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Satellite Images Folder",  # 对话框标题
            "./data",                               # 默认路径
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if not folder:
            return
        
        self.satellite_widget.set_images(folder)