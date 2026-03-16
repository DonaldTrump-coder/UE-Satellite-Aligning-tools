from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

class WebView(QWidget):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.browser = QWebEngineView()
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.browser)
        self.browser.load(QUrl(self.url))