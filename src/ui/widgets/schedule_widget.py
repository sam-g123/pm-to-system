
# # Prevent Qt platform plugin errors in some environments. There are conflicts with PyQt5 + OpenCV
# import os
# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QTextEdit
from PyQt5.QtCore import QTimer
from scheduling.nlp_parser import TaskParser  # Import from scheduling module

class ScheduleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.parser = TaskParser()  # Initialize NLP parser
        layout = QVBoxLayout()
        
        self.title = QLabel("Task Scheduler", self)
        layout.addWidget(self.title)
        
        self.input_label = QLabel("Enter Task (e.g., 'Finish report by Friday'):", self)
        layout.addWidget(self.input_label)
        
        self.task_input = QLineEdit(self)
        layout.addWidget(self.task_input)
        
        self.parse_button = QPushButton("Parse & Schedule", self)
        self.parse_button.clicked.connect(self.parse_and_schedule)
        layout.addWidget(self.parse_button)
        
        self.output = QTextEdit("Parsed tasks will appear here...", self)
        self.output.setMaximumHeight(150)
        layout.addWidget(self.output)
        
        self.setLayout(layout)
        self.timer = QTimer()  # For potential real-time updates (e.g., feedback loop)
        self.timer.timeout.connect(self.update_schedule)  # Placeholder
        self.timer.start(5000)  # Every 5s for demo
    
    def parse_and_schedule(self):
        text = self.task_input.text()
        if text:
            entities = self.parser.parse_task(text)
            # Mock scheduling output (expand with scheduler.py later)
            output_text = f"Parsed: Tasks={entities['tasks']}, Deadlines={entities['deadlines']}\nSuggested Schedule: High priority first (RL agent placeholder)."
            self.output.setText(output_text)
        else:
            self.output.setText("Please enter a task.")
    
    def update_schedule(self):
        # TODO: Integrate feedback loop from focus_detection (e.g., reschedule if distracted)
        pass