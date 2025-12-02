# src/scheduling/tracker.py

import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from src.config import WARNING_THRESHOLD
# Import your ML pipeline function here, e.g.:
# from src.Focus_detection.pipeline import get_current_focus_status 


class FocusTracker(QObject):
    """Worker object that runs the monitoring logic."""
    
    # Define a signal that will be emitted when the alert is triggered
    alert_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True

    def stop(self):
        """Method to safely stop the thread loop."""
        self._is_running = False

    def monitoring_loop(self):
        """The main logic loop that runs continuously."""
        non_concentration_start_time = time.time()
        is_alert_active = False

        while self._is_running:
            # Replace this with your actual ML call:
            concentrating_now = self.get_concentration_status_placeholder() 
            current_time = time.time()

            if concentrating_now:
                non_concentration_start_time = current_time
                is_alert_active = False

            elif not is_alert_active:
                non_concentration_duration = current_time - non_concentration_start_time
                
                if non_concentration_duration >= WARNING_THRESHOLD:
                    # EMIT THE SIGNAL! This is the safe cross-thread communication.
                    self.alert_triggered.emit()
                    is_alert_active = True
                    
            time.sleep(0.1) 

    # Placeholder for the actual ML function call
    def get_concentration_status_placeholder(self):
        # Replace this with a call to your Focus_detection module
        if int(time.time()) % 15 < 6:
            return False 
        return True 


def start_monitoring():
    """Returns the worker object and its thread."""
    # QThread setup pattern
    thread = QThread()
    tracker_worker = FocusTracker()
    tracker_worker.moveToThread(thread)
    
    # Connect signals: start the loop when the thread starts
    thread.started.connect(tracker_worker.monitoring_loop)
    
    # Start the thread
    thread.start()
    
    return tracker_worker, thread # Return both to keep them alive