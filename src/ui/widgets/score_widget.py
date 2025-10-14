
# Prevent Qt platform plugin errors in some environments. There are conflicts with PyQt5 + OpenCV
# import os
# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QProgressBar
from PyQt5.QtCore import QTimer
from scoring.productivity_score import calculate_score  # Import from scoring module

class ScoreWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.title = QLabel("Productivity Score", self)
        layout.addWidget(self.title)
        
        self.score_label = QLabel("Score: 0%", self)
        layout.addWidget(self.score_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.calc_button = QPushButton("Calculate Score", self)
        self.calc_button.clicked.connect(self.update_score)
        layout.addWidget(self.calc_button)
        
        self.insights_label = QLabel("Insights: No data yet (clustering placeholder).", self)
        layout.addWidget(self.insights_label)
        
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_score)  # Auto-update for demo
        self.timer.start(10000)  # Every 10s
    
    def update_score(self):
        # Mock inputs (expand with real data from focus/scheduling)
        focus_time = 0.8  # Fraction focused
        completion_rate = 0.9
        time_efficiency = 0.85
        score = calculate_score(focus_time, completion_rate, time_efficiency)
        
        self.score_label.setText(f"Score: {int(score)}%")
        self.progress_bar.setValue(int(score))
        
        # Mock insights (expand with reporting.py clustering)
        if score > 80:
            self.insights_label.setText("Great job! Sustained focus – try a rewarding task next.")
        elif score > 50:
            self.insights_label.setText("Solid session. Suggestion: Short break detected via EAR blinks.")
        else:
            self.insights_label.setText("Room to improve. Pattern: Low focus post-lunch (clustering insight).")