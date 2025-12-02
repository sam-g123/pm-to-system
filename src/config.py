
# src/config.py

# Configuration Constant
WARNING_THRESHOLD = 6.0  # seconds

# No need for ROOT_WINDOW or THREAD_QUEUE because we are using 
# PyQt's built-in QThread and pyqtSignal for safe cross-thread communication.