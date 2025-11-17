"""
Scoring module initialization and public API.
Provides easy access to scoring engine and data structures.
"""

from .data_structures import (
    AttentionState,
    FaceMetrics,
    FrameData,
    SessionMetrics,
    ProductivityScore,
)
from .productivity_score import ProductivityScoringEngine
from .reporting import ScoreReporter
from .human_centered import HumanCenteredInsights


class ProductivityScoring:
    """
    Main interface for productivity scoring.
    Coordinates scoring engine, reporting, and insights.
    """

    def __init__(self):
        """Initialize scoring system."""
        self.engine = ProductivityScoringEngine()
        self.reporter = ScoreReporter()
        self.insights = HumanCenteredInsights()
        self.frames_history = []

    def add_frame(self, frame_data: FrameData) -> None:
        """
        Add a frame to the scoring history.
        
        Args:
            frame_data: FrameData from focus detection pipeline
        """
        self.frames_history.append(frame_data)

    def add_frame_from_pipeline(self, pipeline_output: dict) -> None:
        """
        Add a frame from pipeline output dictionary.
        Automatically converts to FrameData format.
        
        Args:
            pipeline_output: Output dict from FocusPipeline.process_frame()
        """
        frame_data = FrameData.from_pipeline_output(pipeline_output)
        self.add_frame(frame_data)

    def get_current_score(self) -> ProductivityScore:
        """
        Get productivity score for all frames processed so far.
        
        Returns:
            ProductivityScore object
        """
        return self.engine.calculate_overall_score(self.frames_history)

    def get_session_metrics(self) -> SessionMetrics:
        """
        Get aggregated session metrics.
        
        Returns:
            SessionMetrics object
        """
        return self.engine.calculate_session_metrics(self.frames_history)

    def get_formatted_display(self) -> dict:
        """
        Get formatted output ready for UI display.
        
        Returns:
            Dictionary with formatted strings for each metric
        """
        score = self.get_current_score()
        return self.reporter.format_score_display(score)

    def get_insights(self) -> dict:
        """
        Get comprehensive insights including patterns and recommendations.
        
        Returns:
            Dictionary with insights, recommendations, and analysis
        """
        score = self.get_current_score()
        session = self.get_session_metrics()
        
        focus_patterns = self.insights.analyze_focus_patterns(self.frames_history)
        fatigue = self.insights.detect_fatigue(self.frames_history)
        feedback = self.insights.get_personalized_feedback(
            focus_patterns,
            fatigue,
            score.overall_score,
        )
        break_rec = self.insights.estimate_optimal_break_time(
            session.session_duration,
            focus_patterns,
            fatigue,
        )
        
        return {
            "productivity_score": score,
            "session_metrics": session,
            "score_display": self.reporter.format_score_display(score),
            "insights": self.reporter.format_insights(score),
            "recommendations": self.reporter.format_recommendations(score),
            "personalized_feedback": feedback,
            "focus_patterns": focus_patterns,
            "fatigue_analysis": fatigue,
            "break_recommendation": break_rec,
            "health_tips": self.insights.get_health_tips(),
        }

    def get_text_report(self) -> str:
        """
        Get detailed text report.
        
        Returns:
            Formatted text report string
        """
        score = self.get_current_score()
        session = self.get_session_metrics()
        return self.reporter.generate_text_report(score, session)

    def reset(self) -> None:
        """Reset frame history and start fresh."""
        self.frames_history = []

    def export_csv_row(self) -> str:
        """
        Export current scores as CSV row.
        
        Returns:
            CSV formatted row string
        """
        score = self.get_current_score()
        session = self.get_session_metrics()
        return self.reporter.generate_csv_row(score, session)


# Public API
__all__ = [
    "ProductivityScoring",
    "ProductivityScoringEngine",
    "ScoreReporter",
    "HumanCenteredInsights",
    "AttentionState",
    "FaceMetrics",
    "FrameData",
    "SessionMetrics",
    "ProductivityScore",
]