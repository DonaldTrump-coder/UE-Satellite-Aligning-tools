from UI.Application import Application
import sys
from PyQt6.QtWidgets import QApplication
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = \
"--autoplay-policy=no-user-gesture-required"

UE_address = "http://127.0.0.1"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Application(UE_address)
    window.show()
    sys.exit(app.exec())