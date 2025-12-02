# main.py - REVISED

"""
main.py

Entry point for the Productivity System UI application.
Starts the main window with integrated focus detection and scoring.
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget # Import QWidget for type hinting
from PyQt5.QtCore import QThread
from src.ui.main_window import MainWindow
from src.scheduling.tracker import start_monitoring, FocusTracker
from src.ui.alert_ui import show_popup_alert # The alert function

# Global variables to hold the worker and thread references
tracker_worker: FocusTracker = None
tracker_thread: QThread = None


def main():
    """Initialize and run the application."""
    global tracker_worker, tracker_thread
    
    app = QApplication(sys.argv)
    
    # 1. Start the monitoring thread
    tracker_worker, tracker_thread = start_monitoring()

    # 2. Initialize the main UI window
    window = MainWindow()
    window.setWindowTitle("Productivity System - Focus Detection & Scoring")
    
    # 3. Connect the Signal to the Slot (The synchronization!)
    # The worker thread's signal is connected to the UI function.
    # The alert function runs safely in the main (UI) thread when signaled.
    tracker_worker.alert_triggered.connect(show_popup_alert)
    
    window.show()
    
    # Ensure threads are cleanly stopped on exit
    exit_code = app.exec_()
    
    # Clean up the thread before exiting
    tracker_worker.stop()
    tracker_thread.quit()
    tracker_thread.wait()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()