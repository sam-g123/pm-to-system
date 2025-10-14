# Main window with tabs for Focus, Schedule, and Score
# Prevent Qt platform plugin errors in some environments. There are conflicts with PyQt5 + OpenCV
# import os
# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5.QtWidgets import QMainWindow, QTabWidget
from .widgets.focus_widget import FocusWidget
from .widgets.schedule_widget import ScheduleWidget
from .widgets.score_widget import ScoreWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Productivity System")
        self.setGeometry(100, 100, 800, 600)
        
        tabs = QTabWidget()
        tabs.addTab(FocusWidget(), "Focus")
        tabs.addTab(ScheduleWidget(), "Schedule")
        tabs.addTab(ScoreWidget(), "Score")
        
        self.setCentralWidget(tabs)