# Example widget for Focus tab

# Prevent Qt platform plugin errors in some environments. There are conflicts with PyQt5 + OpenCV
# import os
# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer
from focus_detection.pipeline import FocusPipeline

class FocusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pipeline = FocusPipeline()
        layout = QVBoxLayout()
        self.label = QLabel("Focus Score: 0%", self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_focus)
        self.timer.start(1000)  # Update/sec
    
    def update_focus(self):
        score = self.pipeline.process_frame()
        self.label.setText(f"Focus Score: {int(score)}%")
    
    def closeEvent(self, event):
        self.pipeline.release()

# Add basic schedule_widget.py and score_widget.py with QLabel/QLineEdit for inputs.