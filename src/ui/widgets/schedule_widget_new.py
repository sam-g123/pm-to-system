"""
schedule_widget.py

UI widget for task scheduling and productivity recommendations.
Integrates with scoring data to provide context-aware scheduling.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QTextEdit, QFrame
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont

from src.scoring import ProductivityScoring


class ScheduleWidget(QWidget):
    """Widget for task scheduling and recommendations."""

    def __init__(self):
        super().__init__()
        self.scoring = ProductivityScoring()
        self.init_ui()
        
        # Auto-update recommendations based on current scores
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_recommendations)
        self.timer.start(10000)  # Every 10 seconds

    def init_ui(self):
        """Initialize the UI layout."""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Productivity Scheduler & Recommendations")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Break Recommendations Section
        break_section = QFrame()
        break_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        break_layout = QVBoxLayout()
        
        break_title = QLabel("Break Recommendations")
        break_title_font = QFont()
        break_title_font.setBold(True)
        break_title.setFont(break_title_font)
        break_layout.addWidget(break_title)
        
        self.break_rec_label = QLabel("No session data yet. Start focus detection to get recommendations.")
        self.break_rec_label.setWordWrap(True)
        break_layout.addWidget(self.break_rec_label)
        
        break_section.setLayout(break_layout)
        main_layout.addWidget(break_section)
        
        # Personalized Feedback Section
        feedback_section = QFrame()
        feedback_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        feedback_layout = QVBoxLayout()
        
        feedback_title = QLabel("Personalized Feedback")
        feedback_title_font = QFont()
        feedback_title_font.setBold(True)
        feedback_title.setFont(feedback_title_font)
        feedback_layout.addWidget(feedback_title)
        
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setMaximumHeight(150)
        feedback_layout.addWidget(self.feedback_text)
        
        feedback_section.setLayout(feedback_layout)
        main_layout.addWidget(feedback_section)
        
        # Health Tips Section
        tips_section = QFrame()
        tips_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        tips_layout = QVBoxLayout()
        
        tips_title = QLabel("Health & Productivity Tips")
        tips_title_font = QFont()
        tips_title_font.setBold(True)
        tips_title.setFont(tips_title_font)
        tips_layout.addWidget(tips_title)
        
        self.tips_text = QTextEdit()
        self.tips_text.setReadOnly(True)
        self.tips_text.setMaximumHeight(150)
        tips_layout.addWidget(self.tips_text)
        
        tips_section.setLayout(tips_layout)
        main_layout.addWidget(tips_section)
        
        # Fatigue Analysis
        fatigue_section = QFrame()
        fatigue_section.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        fatigue_layout = QVBoxLayout()
        
        fatigue_title = QLabel("Fatigue Analysis")
        fatigue_title_font = QFont()
        fatigue_title_font.setBold(True)
        fatigue_title.setFont(fatigue_title_font)
        fatigue_layout.addWidget(fatigue_title)
        
        self.fatigue_label = QLabel("Fatigue Level: N/A")
        fatigue_layout.addWidget(self.fatigue_label)
        
        self.fatigue_rec_label = QLabel("Recommendations will appear as data is collected.")
        self.fatigue_rec_label.setWordWrap(True)
        fatigue_layout.addWidget(self.fatigue_rec_label)
        
        fatigue_section.setLayout(fatigue_layout)
        main_layout.addWidget(fatigue_section)
        
        main_layout.addStretch()
        self.setLayout(main_layout)

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
            
            # Update health tips
            tips_list = insights.get("health_tips", [])
            if tips_list:
                # Show 3 random tips
                import random
                selected_tips = random.sample(tips_list, min(3, len(tips_list)))
                tips_text = "\n".join([f"• {tip}" for tip in selected_tips])
                self.tips_text.setText(tips_text)
            
            # Update fatigue analysis
            fatigue = insights.get("fatigue_analysis", {})
            if fatigue:
                fatigue_level = fatigue.get("fatigue_level", 0)
                fatigue_desc = fatigue.get("fatigue_description", "Unknown")
                
                self.fatigue_label.setText(
                    f"Fatigue Level: {fatigue_level*100:.0f}% - {fatigue_desc}"
                )
                
                # Recommendation based on fatigue
                if fatigue_level > 0.7:
                    self.fatigue_rec_label.setText(
                        "⚠️ High fatigue detected. Take a 15-20 minute break and rest your eyes."
                    )
                elif fatigue_level > 0.4:
                    self.fatigue_rec_label.setText(
                        "😐 Moderate fatigue. Consider a 10-15 minute break."
                    )
                else:
                    self.fatigue_rec_label.setText(
                        "✅ Low fatigue. Keep up the good work!"
                    )
        
        except Exception as e:
            print(f"Error updating recommendations: {e}")
