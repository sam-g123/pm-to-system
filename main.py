"""
main.py

Entry point for the Productivity System UI application.
Starts the main window with integrated focus detection and scoring.
"""

import sys
from PyQt5.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.setWindowTitle("Productivity System - Focus Detection & Scoring")
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
