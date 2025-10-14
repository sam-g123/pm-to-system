#!/usr/bin/env python3.10
"""
Entry point: Launches PyQt5 UI and integrates modules.
"""
# Run with: python src/main.py

# Prevent Qt platform plugin errors in some environments. There are conflicts with PyQt5 + OpenCV
# import os
# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())