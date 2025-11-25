"""
schedule_widget_new.py

Enhanced UI widget for task scheduling with Gemini-powered features:
1. Task Duration Estimation - Uses Gemini AI to estimate task duration
2. Distraction Warning System - Detects open apps/tabs that may distract from current task
3. Productivity Scoring Integration - Shows productivity metrics and recommendations
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QTextEdit, QFrame, QComboBox, QSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QScrollArea
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
from typing import Optional, List, Dict, Any
import json

from src.scheduling.data_structures import Task, TaskStatus
from src.scheduling.scheduler import Scheduler
from src.scheduling.nlp_parser import DurationEstimator
from src.scheduling.feedback_loop import DistractionWatcher
from src.scheduling.open_apps import get_open_apps_and_tabs
from src.scoring import ProductivityScoring


class TaskEstimationWorker(QThread):
    """Worker thread for duration estimation to avoid blocking UI."""
    duration_ready = pyqtSignal(float)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task_name: str, description: str):
        super().__init__()
        self.task_name = task_name
        self.description = description
        self.estimator = DurationEstimator()
    
    def run(self):
        try:
            minutes = self.estimator.mcp.estimate_duration(self.task_name, self.description)
            self.duration_ready.emit(minutes)
        except Exception as e:
            self.error_occurred.emit(str(e))


class DistractionCheckWorker(QThread):
    """Worker thread for distraction detection to avoid blocking UI."""
    check_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task: Task):
        super().__init__()
        self.task = task
        self.watcher = DistractionWatcher()
    
    def run(self):
        try:
            open_items = get_open_apps_and_tabs()
            result = self.watcher.mcp.detect_distractions(
                task={"name": self.task.name, "attached_apps": self.task.attached_apps},
                open_items=open_items
            )
            self.check_complete.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ScheduleWidgetNew(QWidget):
    """Enhanced widget for task scheduling with Gemini AI integration."""

    def __init__(self, scoring = None):
        super().__init__()
        # Accept shared scoring instance if provided
        from src.scoring import ProductivityScoring
        self.scoring = scoring if scoring is not None else ProductivityScoring()
        self.scheduler = Scheduler(db_path=":memory:", parent_widget=self)
        self.current_task: Optional[Task] = None
        self.task_counter = 0
        
        # Worker threads
        self.estimation_worker = None
        self.distraction_worker = None
        
        self.init_ui()
        
        # Auto-update recommendations and distraction checks
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_recommendations)
        self.update_timer.start(10000)  # Every 10 seconds

    def init_ui(self):
        """Initialize the UI layout."""
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(8)

        # Title
        title = QLabel("Task Scheduler with AI-Powered Insights")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setContentsMargins(4, 4, 4, 8)

        # central widget inside scroll area
        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(12)

        central_layout.addWidget(title)

        # ===== TASK INPUT SECTION =====
        input_section = QFrame()
        input_section.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f9f9f9; }")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(6)

        input_title = QLabel("Add New Task")
        input_title_font = QFont()
        input_title_font.setBold(True)
        input_title.setFont(input_title_font)
        input_layout.addWidget(input_title)

        # Task Name Input
        task_name_label = QLabel("Task Name:")
        self.task_name_input = QLineEdit()
        self.task_name_input.setPlaceholderText("e.g., Write report on Q3 sales")
        self.task_name_input.setMinimumWidth(360)
        input_layout.addWidget(task_name_label)
        input_layout.addWidget(self.task_name_input)

        # Task Description Input
        desc_label = QLabel("Task Description:")
        self.task_description_input = QTextEdit()
        self.task_description_input.setPlaceholderText(
            "e.g., Draft sections for executive summary, analyze data from Q3_data.csv, create 5 slides..."
        )
        self.task_description_input.setMinimumHeight(80)
        self.task_description_input.setMaximumHeight(200)
        input_layout.addWidget(desc_label)
        input_layout.addWidget(self.task_description_input)

        # Attached Apps Input
        apps_label = QLabel("Attached Applications (comma-separated):")
        self.attached_apps_input = QLineEdit()
        self.attached_apps_input.setPlaceholderText("e.g., word, excel, powerpoint")
        self.attached_apps_input.setMinimumWidth(360)
        input_layout.addWidget(apps_label)
        input_layout.addWidget(self.attached_apps_input)

        # Manual Duration Override
        duration_label = QLabel("Manual Duration Override (minutes, optional):")
        self.manual_duration_input = QSpinBox()
        self.manual_duration_input.setMinimum(0)
        self.manual_duration_input.setMaximum(480)  # 8 hours max
        self.manual_duration_input.setValue(0)
        self.manual_duration_input.setToolTip("Leave as 0 to use Gemini estimation")
        input_layout.addWidget(duration_label)
        input_layout.addWidget(self.manual_duration_input)

        # Add Task Button
        self.add_task_button = QPushButton("Add Task & Estimate Duration")
        self.add_task_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }"
        )
        self.add_task_button.clicked.connect(self.add_and_estimate_task)
        input_layout.addWidget(self.add_task_button)
        input_layout.addStretch()

        input_section.setLayout(input_layout)
        central_layout.addWidget(input_section)

        # ===== TASK DURATION ESTIMATION SECTION =====
        duration_section = QFrame()
        duration_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        duration_layout = QVBoxLayout()
        duration_layout.setSpacing(6)

        duration_title = QLabel("📊 Task Duration Estimation")
        duration_title_font = QFont()
        duration_title_font.setBold(True)
        duration_title.setFont(duration_title_font)
        duration_layout.addWidget(duration_title)

        self.duration_display = QLabel("Add a task to estimate duration using Gemini AI")
        self.duration_display.setWordWrap(True)
        self.duration_display.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        duration_layout.addWidget(self.duration_display)

        duration_section.setLayout(duration_layout)
        central_layout.addWidget(duration_section)

        # ===== DISTRACTION WARNING SECTION =====
        distraction_section = QFrame()
        distraction_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        distraction_layout = QVBoxLayout()
        distraction_layout.setSpacing(6)

        distraction_title = QLabel("⚠️ Distraction Warning System")
        distraction_title_font = QFont()
        distraction_title_font.setBold(True)
        distraction_title.setFont(distraction_title_font)
        distraction_layout.addWidget(distraction_title)

        self.distraction_text = QTextEdit()
        self.distraction_text.setReadOnly(True)
        self.distraction_text.setMaximumHeight(120)
        self.distraction_text.setText("Start a task to monitor for distractions.\nGemini will analyze your open apps and alert you to potential focus killers.")
        distraction_layout.addWidget(self.distraction_text)

        distraction_section.setLayout(distraction_layout)
        central_layout.addWidget(distraction_section)

        # ===== BREAK RECOMMENDATIONS SECTION =====
        break_section = QFrame()
        break_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        break_layout = QVBoxLayout()
        break_layout.setSpacing(6)

        break_title = QLabel("☕ Break Recommendations")
        break_title_font = QFont()
        break_title_font.setBold(True)
        break_title.setFont(break_title_font)
        break_layout.addWidget(break_title)

        self.break_rec_label = QLabel("No session data yet. Start focus detection to get recommendations.")
        self.break_rec_label.setWordWrap(True)
        break_layout.addWidget(self.break_rec_label)

        break_section.setLayout(break_layout)
        central_layout.addWidget(break_section)

        # ===== PERSONALIZED FEEDBACK SECTION =====
        feedback_section = QFrame()
        feedback_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        feedback_layout = QVBoxLayout()
        feedback_layout.setSpacing(6)

        feedback_title = QLabel("💡 Personalized Feedback")
        feedback_title_font = QFont()
        feedback_title_font.setBold(True)
        feedback_title.setFont(feedback_title_font)
        feedback_layout.addWidget(feedback_title)

        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setMaximumHeight(100)
        feedback_layout.addWidget(self.feedback_text)

        feedback_section.setLayout(feedback_layout)
        central_layout.addWidget(feedback_section)

        # ===== ACTIVE TASK SECTION =====
        active_section = QFrame()
        active_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; background-color: #f0f8ff; }")
        active_layout = QVBoxLayout()
        active_layout.setSpacing(6)

        active_title = QLabel("🎯 Currently Active Task")
        active_title_font = QFont()
        active_title_font.setBold(True)
        active_title.setFont(active_title_font)
        active_layout.addWidget(active_title)

        self.active_task_label = QLabel("No active task")
        self.active_task_label.setWordWrap(True)
        active_layout.addWidget(self.active_task_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.start_task_button = QPushButton("Start Task")
        self.start_task_button.setEnabled(False)
        self.start_task_button.clicked.connect(self.start_current_task)
        button_layout.addWidget(self.start_task_button)

        self.check_distractions_button = QPushButton("Check for Distractions")
        self.check_distractions_button.setEnabled(False)
        self.check_distractions_button.clicked.connect(self.check_distractions_now)
        button_layout.addWidget(self.check_distractions_button)

        active_layout.addLayout(button_layout)
        active_section.setLayout(active_layout)
        central_layout.addWidget(active_section)

        central_layout.addStretch()

        central.setLayout(central_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)

        outer_layout.addWidget(scroll)
        self.setLayout(outer_layout)

    def add_and_estimate_task(self):
        """Add a new task and estimate its duration using Gemini."""
        task_name = self.task_name_input.text().strip()
        description = self.task_description_input.toPlainText().strip()
        attached_apps_str = self.attached_apps_input.text().strip()
        attached_apps = [app.strip() for app in attached_apps_str.split(",")] if attached_apps_str else []
        
        if not task_name:
            QMessageBox.warning(self, "Input Error", "Please enter a task name.")
            return
        
        if not description:
            QMessageBox.warning(self, "Input Error", "Please enter a task description.")
            return
        
        # Create task object
        self.task_counter += 1
        self.current_task = Task(
            id=self.task_counter,
            name=task_name,
            description=description,
            attached_apps=attached_apps,
            status=TaskStatus.DUE
        )
        # Add to scheduler
        try:
            self.scheduler.add_task(self.current_task)
        except Exception:
            # Non-fatal: proceed even if scheduler persistence is not available
            pass
        
        # Check for manual override
        if self.manual_duration_input.value() > 0:
            self.current_task.estimated_minutes = float(self.manual_duration_input.value())
            self.display_duration_result(self.current_task.estimated_minutes)
            self.update_active_task_display()
        else:
            # Start estimation worker thread
            self.duration_display.setText("⏳ Estimating task duration with Gemini AI...")
            self.duration_display.setStyleSheet("QLabel { color: #FF9800; font-style: italic; }")
            
            self.estimation_worker = TaskEstimationWorker(task_name, description)
            self.estimation_worker.duration_ready.connect(self.on_duration_estimated)
            self.estimation_worker.error_occurred.connect(self.on_estimation_error)
            self.estimation_worker.start()
        # ensure UI shows the new task
        self.update_active_task_display()
    
    def on_duration_estimated(self, minutes: float):
        """Callback when duration estimation completes."""
        self.current_task.estimated_minutes = minutes
        self.display_duration_result(minutes)
        self.update_active_task_display()
    
    def on_estimation_error(self, error_msg: str):
        """Callback when duration estimation fails."""
        self.duration_display.setText(f"❌ Duration estimation failed: {error_msg}")
        self.duration_display.setStyleSheet("QLabel { color: #f44336; }")
    
    def display_duration_result(self, minutes: float):
        """Display the estimated duration."""
        hours = minutes / 60
        if hours >= 1:
            duration_text = f"Estimated Duration: {hours:.1f} hours ({minutes:.0f} minutes)"
        else:
            duration_text = f"Estimated Duration: {minutes:.0f} minutes"
        
        self.duration_display.setText(duration_text)
        self.duration_display.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
    
    def update_active_task_display(self):
        """Update the active task display section."""
        if self.current_task:
            task_info = f"Task: {self.current_task.name}\n"
            task_info += f"Description: {self.current_task.description}\n"
            if self.current_task.attached_apps:
                task_info += f"Attached Apps: {', '.join(self.current_task.attached_apps)}\n"
            if self.current_task.estimated_minutes:
                hours = self.current_task.estimated_minutes / 60
                if hours >= 1:
                    task_info += f"Duration: {hours:.1f} hours"
                else:
                    task_info += f"Duration: {self.current_task.estimated_minutes:.0f} minutes"
            
            self.active_task_label.setText(task_info)
            self.start_task_button.setEnabled(True)
            self.check_distractions_button.setEnabled(True)
    
    def start_current_task(self):
        """Start the currently selected task."""
        if not self.current_task:
            QMessageBox.warning(self, "No Task", "Please add a task first.")
            return
        # Update status and notify scheduler
        self.current_task.status = TaskStatus.IN_PROGRESS
        try:
            result = self.scheduler.start_task(self.current_task)
            msgs = result.get("messages", [])
        except Exception:
            msgs = []

        # Update UI
        self.active_task_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
        info_text = f"Task '{self.current_task.name}' started!\n\n"
        if self.current_task.estimated_minutes:
            info_text += f"Estimated time: {self.current_task.estimated_minutes:.0f} minutes\n\n"
        if msgs:
            info_text += "\n".join(msgs)

        QMessageBox.information(self, "Task Started", info_text)

        # Auto-check for distractions after a short delay
        QTimer.singleShot(1000, self.check_distractions_now)
    
    def check_distractions_now(self):
        """Check for distractions immediately."""
        if not self.current_task:
            QMessageBox.warning(self, "No Task", "Please start a task first.")
            return
        
        self.distraction_text.setText("🔍 Analyzing open applications and tabs...")
        self.distraction_text.setStyleSheet("QTextEdit { color: #FF9800; }")
        
        self.distraction_worker = DistractionCheckWorker(self.current_task)
        self.distraction_worker.check_complete.connect(self.on_distraction_check_complete)
        self.distraction_worker.error_occurred.connect(self.on_distraction_check_error)
        self.distraction_worker.start()
    
    def on_distraction_check_complete(self, result: Dict[str, Any]):
        """Callback when distraction check completes."""
        distractions = result.get("distractions", [])
        rationale = result.get("rationale", "Analysis complete.")
        suggestion = result.get("suggestion", "")
        
        if distractions:
            distraction_msg = "⚠️ POTENTIAL DISTRACTIONS DETECTED:\n\n"
            for distraction in distractions:
                distraction_msg += f"  • {distraction}\n"
            distraction_msg += f"\n📝 Reason:\n{rationale}\n\n"
            distraction_msg += f"💡 Suggestion:\n{suggestion}"
            
            self.distraction_text.setText(distraction_msg)
            self.distraction_text.setStyleSheet("QTextEdit { color: #f44336; background-color: #ffebee; }")
            
            # Also show a warning dialog
            QMessageBox.warning(
                self,
                "Distraction Alert",
                distraction_msg
            )
        else:
            distraction_msg = "✅ No distractions detected!\n\n"
            distraction_msg += f"Rationale: {rationale}\n\n"
            if suggestion:
                distraction_msg += f"Tip: {suggestion}"
            
            self.distraction_text.setText(distraction_msg)
            self.distraction_text.setStyleSheet("QTextEdit { color: #4CAF50; background-color: #f1f8e9; }")
    
    def on_distraction_check_error(self, error_msg: str):
        """Callback when distraction check fails."""
        self.distraction_text.setText(f"❌ Distraction check failed: {error_msg}")
        self.distraction_text.setStyleSheet("QTextEdit { color: #f44336; }")
    
    def add_frame_data(self, pipeline_output: dict):
        """
        Add frame data from focus detection pipeline.
        
        Args:
            pipeline_output: Output dict from FocusPipeline.process_frame()
        """
        try:
            self.scoring.add_frame_from_pipeline(pipeline_output)
        except Exception as e:
            print(f"Error adding frame data: {e}")

    def update_recommendations(self):
        """Update all recommendation displays based on current scores."""
        try:
            if not self.scoring.frames_history:
                return

            insights = self.scoring.get_insights()
            
            # Update break recommendations
            break_rec = insights.get("break_recommendation", {})
            if break_rec:
                break_text = (
                    f"Type: {break_rec.get('break_type_description', 'N/A')}\n"
                    f"Recommended in: {break_rec.get('next_break_in_seconds', 0):.0f} seconds\n"
                    f"Reason: {break_rec.get('rationale', 'Based on current metrics')}"
                )
                self.break_rec_label.setText(break_text)
            
            # Update personalized feedback
            feedback_list = insights.get("personalized_feedback", [])
            if feedback_list:
                feedback_text = "\n".join([f"• {fb}" for fb in feedback_list])
                self.feedback_text.setText(feedback_text)
        
        except Exception as e:
            print(f"Error updating recommendations: {e}")
