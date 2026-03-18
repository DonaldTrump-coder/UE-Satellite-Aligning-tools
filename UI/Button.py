from PyQt6.QtWidgets import QPushButton
from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

class IconButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """
            QPushButton {
                border: 2px solid #555;
                border-radius: 10px;
                padding: 4px;
                background-color: #DDD;
            }
            QPushButton:pressed {
                background-color: #AAA;
                border: 2px solid #333;
            }
        """
        )
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        padding = 30
        self.setIconSize(QtCore.QSize(self.width() - padding, self.height() - padding))