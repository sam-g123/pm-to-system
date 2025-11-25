# Main window with tabs for Focus, Schedule, and Score
# Prevent Qt platform plugin errors in some environments. There are conflicts with PyQt5 + OpenCV
# import os
# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5.QtWidgets import QMainWindow, QTabWidget, QSizePolicy
from PyQt5.QtCore import Qt
from .widgets.focus_widget import FocusWidget
from .widgets.schedule_widget_new import ScheduleWidgetNew
from .widgets.score_widget import ScoreWidget
from src.scoring import ProductivityScoring

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and initial geometry
        self.setWindowTitle("Productivity System")
        self.setGeometry(100, 100, 1024, 768)

        # Ensure standard window decorations and minimize/maximize buttons are available
        # Combine existing flags with Window and Min/Max hints to be explicit across platforms
        self.setWindowFlags(self.windowFlags() | Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Make window resizable with a sensible minimum size
        self.setMinimumSize(800, 600)

        # Create tab widget and allow it to expand to fill the window
        # Create a single shared scoring instance and pass to all widgets so they share state
        scoring = ProductivityScoring()

        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tabs.addTab(FocusWidget(scoring=scoring), "Focus")
        tabs.addTab(ScheduleWidgetNew(scoring=scoring), "Schedule")
        tabs.addTab(ScoreWidget(scoring=scoring), "Score")

        self.setCentralWidget(tabs)

        # Add a lightweight status bar message for UX
        try:
            self.statusBar().showMessage("Ready")
        except Exception:
            # Some minimal Qt builds may not include a status bar; ignore if unavailable
            pass