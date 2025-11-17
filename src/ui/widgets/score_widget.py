
"""
score_widget.py

UI widget for displaying productivity scores and insights.
Shows overall score, component breakdown, and personalized recommendations.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from typing import List, Dict, Any

from src.scoring import ProductivityScoring


class ScoreWidget(QWidget):
    """Widget for displaying productivity scores and insights."""

    def __init__(self, scoring: ProductivityScoring = None):
        super().__init__()
        # Use shared scoring instance if provided; otherwise create one
        self.scoring = scoring if scoring is not None else ProductivityScoring()
        self.init_ui()
        
        # Track recent frames separately for short-term analysis
        self.recent_frame_window = 60  # Analyze last 60 frames (~2 seconds at 30fps)
        
        # Auto-update timer (every 5 seconds)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_display)
        self.timer.start(5000)

    def init_ui(self):
        """Initialize the UI layout."""
        # Create a scrollable container so the entire Score tab can scroll when content is tall
        outer_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Internal content widget and layout (this holds the existing content)
        content = QFrame()
        content_layout = QVBoxLayout()

        # Title
        title = QLabel("Productivity Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        content_layout.addWidget(title)

        # Score section (small vertical weight)
        score_section = self.create_score_section()
        content_layout.addWidget(score_section)

        # Components breakdown
        components_section = self.create_components_section()
        content_layout.addWidget(components_section)

        # Insights section (expandable)
        insights_section = self.create_insights_section()
        content_layout.addWidget(insights_section)

        # Recommendations section (expandable)
        recommendations_section = self.create_recommendations_section()
        content_layout.addWidget(recommendations_section)

        # Reset button
        reset_button = QPushButton("Reset Session")
        reset_button.clicked.connect(self.reset_session)
        content_layout.addWidget(reset_button)

        # Let content expand vertically inside the scroll area
        content_layout.addStretch()
        content.setLayout(content_layout)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll.setWidget(content)

        outer_layout.addWidget(scroll)
        self.setLayout(outer_layout)

    def create_score_section(self) -> QFrame:
        """Create the overall score display section."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        layout = QVBoxLayout()
        
        # Overall score
        score_label = QLabel("Overall Productivity Score")
        score_font = QFont()
        score_font.setPointSize(12)
        score_font.setBold(True)
        score_label.setFont(score_font)
        layout.addWidget(score_label)
        
        self.overall_score_label = QLabel("0%")
        score_display_font = QFont()
        score_display_font.setPointSize(36)
        score_display_font.setBold(True)
        self.overall_score_label.setFont(score_display_font)
        self.overall_score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.overall_score_label)
        
        # Progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.overall_progress)
        
        # Allow the score section to expand horizontally but not take excessive vertical space
        frame.setLayout(layout)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return frame

    def create_components_section(self) -> QFrame:
        """Create component scores display section."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        layout = QVBoxLayout()
        
        components_label = QLabel("Score Components")
        components_font = QFont()
        components_font.setPointSize(12)
        components_font.setBold(True)
        components_label.setFont(components_font)
        layout.addWidget(components_label)
        
        # Create component widgets
        self.focus_score_widget = self.create_component_widget("🎯 Focus", 0)
        self.engagement_score_widget = self.create_component_widget("👀 Engagement", 0)
        self.stability_score_widget = self.create_component_widget("📍 Stability", 0)
        self.fatigue_score_widget = self.create_component_widget("😴 Fatigue", 0)
        
        layout.addWidget(self.focus_score_widget)
        layout.addWidget(self.engagement_score_widget)
        layout.addWidget(self.stability_score_widget)
        layout.addWidget(self.fatigue_score_widget)
        
        frame.setLayout(layout)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return frame

    def create_component_widget(self, label: str, score: float) -> QFrame:
        """Create a single component score widget."""
        frame = QFrame()
        layout = QHBoxLayout()
        
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(150)
        layout.addWidget(label_widget)
        
        score_label = QLabel(f"{score:.0f}%")
        score_label.setMinimumWidth(50)
        layout.addWidget(score_label)
        
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(int(score))
        layout.addWidget(progress)
        
        frame.setLayout(layout)
        return frame

    def create_insights_section(self) -> QFrame:
        """Create insights display section."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        layout = QVBoxLayout()
        
        insights_label = QLabel("Insights")
        insights_font = QFont()
        insights_font.setPointSize(12)
        insights_font.setBold(True)
        insights_label.setFont(insights_font)
        layout.addWidget(insights_label)
        
        # Scrollable insights area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Let the scroll area expand to use available vertical space
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.insights_container = QFrame()
        self.insights_layout = QVBoxLayout()
        self.insights_container.setLayout(self.insights_layout)
        # Ensure the container expands vertically within the scroll area
        self.insights_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(self.insights_container)

        layout.addWidget(scroll)
        frame.setLayout(layout)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return frame

    def create_recommendations_section(self) -> QFrame:
        """Create recommendations display section."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        layout = QVBoxLayout()
        
        rec_label = QLabel("Recommendations")
        rec_font = QFont()
        rec_font.setPointSize(12)
        rec_font.setBold(True)
        rec_label.setFont(rec_font)
        layout.addWidget(rec_label)
        
        # Scrollable recommendations area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.recommendations_container = QFrame()
        self.recommendations_layout = QVBoxLayout()
        self.recommendations_container.setLayout(self.recommendations_layout)
        self.recommendations_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(self.recommendations_container)

        layout.addWidget(scroll)
        frame.setLayout(layout)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return frame

    def refresh_display(self):
        """Update all displayed scores and insights."""
        try:
            # Get overall session score
            score = self.scoring.get_current_score()
            
            # Get insights from RECENT frames only (window-based analysis)
            # This provides short-term feedback instead of overall session feedback
            recent_frames = self.scoring.frames_history[-self.recent_frame_window:]
            if recent_frames:
                # Calculate metrics for recent window
                recent_engine = self.scoring.engine
                recent_focus, _ = recent_engine.calculate_focus_score(recent_frames)
                recent_eng, _ = recent_engine.calculate_engagement_score(recent_frames)
                recent_stab, _ = recent_engine.calculate_stability_score(recent_frames)
                
                # Generate insights from recent behavior patterns
                recent_focus_patterns = self.scoring.insights.analyze_focus_patterns(recent_frames)
                recent_fatigue = self.scoring.insights.detect_fatigue(recent_frames)
                
                # Generate fresh insights based on recent data
                recent_insights = self._generate_recent_insights(
                    recent_focus_patterns,
                    recent_fatigue,
                    (recent_focus + recent_eng + recent_stab) / 3,
                )
                recent_recommendations = self._generate_recent_recommendations(
                    recent_focus_patterns,
                    recent_fatigue,
                    recent_focus,
                )
            else:
                recent_insights = ["• No frames yet - start focus detection"]
                recent_recommendations = ["• Ensure video is being captured correctly"]
            
            # Update overall score
            self.overall_score_label.setText(f"{score.overall_score:.0f}%")
            self.overall_progress.setValue(int(score.overall_score))
            self.overall_score_label.setStyleSheet(
                f"color: {self.get_score_color(score.overall_score)};"
            )
            
            # Update component scores
            self.update_component_widget(
                self.focus_score_widget,
                "🎯 Focus",
                score.focus_score
            )
            self.update_component_widget(
                self.engagement_score_widget,
                "👀 Engagement",
                score.engagement_score
            )
            self.update_component_widget(
                self.stability_score_widget,
                "📍 Stability",
                score.stability_score
            )
            
            # Update fatigue score (if available in components)
            fatigue_score = score.components.get("fatigue", 0.0)
            self.update_component_widget(
                self.fatigue_score_widget,
                "😴 Fatigue",
                fatigue_score
            )
            
            # Update insights from recent window analysis
            self.update_insights_display(recent_insights)
            
            # Update recommendations
            self.update_recommendations_display(recent_recommendations)
            
        except Exception as e:
            print(f"Error updating display: {e}")

    def update_component_widget(self, widget: QFrame, label: str, score: float):
        """Update a component widget with new score."""
        layout = widget.layout()
        
        # Update score label
        if layout.count() >= 2:
            score_label = layout.itemAt(1).widget()
            if score_label:
                score_label.setText(f"{score:.0f}%")
        
        # Update progress bar
        if layout.count() >= 3:
            progress = layout.itemAt(2).widget()
            if progress:
                progress.setValue(int(score))
                progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid grey;
                        border-radius: 5px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {self.get_score_color(score)};
                    }}
                """)

    def update_insights_display(self, insights: list):
        """Update insights display."""
        # Clear existing insights safely (some items may be spacers or layouts)
        while self.insights_layout.count():
            item = self.insights_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()
                continue
            # If it's a nested layout, clear its children
            inner = item.layout()
            if inner is not None:
                while inner.count():
                    child = inner.takeAt(0)
                    if child is None:
                        continue
                    cw = child.widget()
                    if cw is not None:
                        cw.deleteLater()
            # SpacerItem or other: nothing to delete
        
        # Add new insights
        for insight in insights:
            label = QLabel(f"• {insight}")
            label.setWordWrap(True)
            self.insights_layout.addWidget(label)
        
        self.insights_layout.addStretch()

    def update_recommendations_display(self, recommendations: list):
        """Update recommendations display."""
        # Clear existing recommendations safely (handle None widgets/spacers)
        while self.recommendations_layout.count():
            item = self.recommendations_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()
                continue
            inner = item.layout()
            if inner is not None:
                while inner.count():
                    child = inner.takeAt(0)
                    if child is None:
                        continue
                    cw = child.widget()
                    if cw is not None:
                        cw.deleteLater()
            # SpacerItem or other: nothing to delete
        
        # Add new recommendations
        for rec in recommendations:
            label = QLabel(f"• {rec}")
            label.setWordWrap(True)
            self.recommendations_layout.addWidget(label)
        
        self.recommendations_layout.addStretch()

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

    def reset_session(self):
        """Reset the current session."""
        self.scoring.reset()
        self.refresh_display()
        print("Session reset - ready for new data")

    @staticmethod
    def get_score_color(score: float) -> str:
        """Get color based on score value."""
        if score >= 90:
            return "#4CAF50"  # Green
        elif score >= 75:
            return "#8BC34A"  # Light green
        elif score >= 60:
            return "#FFC107"  # Amber
        elif score >= 45:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red

    def _generate_recent_insights(
        self,
        focus_patterns: Dict[str, Any],
        fatigue_analysis: Dict[str, Any],
        recent_avg_score: float,
    ) -> List[str]:
        """
        Generate insights based on recent frame window (last ~2 seconds).
        
        Args:
            focus_patterns: Pattern analysis from recent window
            fatigue_analysis: Fatigue detection from recent window
            recent_avg_score: Average score from recent window
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Focus consistency insight
        if "insufficient_data" not in focus_patterns:
            consistency = focus_patterns.get("focus_consistency", 0)
            avg_focus = focus_patterns.get("average_focus", 0)
            
            if avg_focus > 0.85:
                insights.append(f"🟢 Strong focus: {avg_focus*100:.0f}% attentive")
            elif avg_focus > 0.6:
                insights.append(f"🟡 Moderate focus: {avg_focus*100:.0f}% attentive")
            else:
                insights.append(f"🔴 Low focus: {avg_focus*100:.0f}% attentive")
            
            if consistency > 0.85:
                insights.append("👍 Very consistent focus")
            elif consistency < 0.5:
                insights.append("⚠️ Focus is fluctuating frequently")
        
        # Fatigue detection
        fatigue_level = fatigue_analysis.get("fatigue_level", 0)
        if fatigue_level > 0.6:
            insights.append("😴 Signs of fatigue - consider a break")
        elif fatigue_level > 0.3:
            insights.append("🔄 Some eye strain detected")
        
        # Looking away behavior
        looking_away_ratio = fatigue_analysis.get("looking_away_ratio", 0)
        if looking_away_ratio > 0.3:
            insights.append(f"👀 Looking away {looking_away_ratio*100:.0f}% of time")
        
        if not insights:
            insights.append("✅ No issues detected - good focus")
        
        return insights

    def _generate_recent_recommendations(
        self,
        focus_patterns: Dict[str, Any],
        fatigue_analysis: Dict[str, Any],
        recent_focus_score: float,
    ) -> List[str]:
        """
        Generate recommendations based on detected issues in recent window.
        
        Args:
            focus_patterns: Pattern analysis
            fatigue_analysis: Fatigue detection
            recent_focus_score: Recent focus score
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Fatigue-based recommendations
        fatigue_level = fatigue_analysis.get("fatigue_level", 0)
        if fatigue_level > 0.6:
            recommendations.append("Take a 15-20 minute break")
            recommendations.append("Hydrate and stretch your neck")
            recommendations.append("Close your eyes for 20-30 seconds")
        elif fatigue_level > 0.3:
            recommendations.append("Stand and stretch briefly")
            recommendations.append("Look away from screen for 10 seconds")
        
        # Focus-based recommendations
        if "insufficient_data" not in focus_patterns:
            avg_focus = focus_patterns.get("average_focus", 0)
            if avg_focus < 0.5:
                recommendations.append("Minimize notifications and distractions")
                recommendations.append("Use a focus timer (Pomodoro technique)")
            
            consistency = focus_patterns.get("focus_consistency", 0)
            if consistency < 0.5:
                recommendations.append("Your focus is inconsistent - check your environment")
        
        # Looking away recommendations
        looking_away_ratio = fatigue_analysis.get("looking_away_ratio", 0)
        if looking_away_ratio > 0.3:
            recommendations.append("Adjust your screen position and lighting")
            recommendations.append("Make sure you're sitting comfortably")
        
        if not recommendations:
            recommendations.append("Continue maintaining your focus")
            recommendations.append("Stay hydrated and take occasional breaks")
        
        return recommendations
