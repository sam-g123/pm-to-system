"""
reporting.py

Generates reports and summaries from productivity scores.
Provides formatted output for UI display and data export.
"""

from typing import List, Dict, Any
from datetime import datetime
from .data_structures import ProductivityScore, SessionMetrics
from .productivity_score import ProductivityScoringEngine


class ScoreReporter:
    """Generates formatted reports from productivity scores."""

    def __init__(self):
        """Initialize reporter."""
        self.engine = ProductivityScoringEngine()

    def format_score_display(self, score: ProductivityScore) -> Dict[str, str]:
        """
        Format score for UI display.
        
        Args:
            score: ProductivityScore object
            
        Returns:
            Dictionary with formatted strings for UI
        """
        return {
            "overall": f"{score.overall_score:.0f}%",
            "focus": f"{score.focus_score:.0f}%",
            "engagement": f"{score.engagement_score:.0f}%",
            "stability": f"{score.stability_score:.0f}%",
            "overall_description": self._get_score_description(score.overall_score),
            "focus_description": self._get_score_description(score.focus_score),
            "engagement_description": self._get_score_description(score.engagement_score),
            "stability_description": self._get_score_description(score.stability_score),
        }

    def format_insights(self, score: ProductivityScore) -> List[str]:
        """
        Format insights for UI display.
        
        Args:
            score: ProductivityScore object
            
        Returns:
            List of formatted insight strings
        """
        return score.insights

    def format_recommendations(self, score: ProductivityScore) -> List[str]:
        """
        Format recommendations for UI display.
        
        Args:
            score: ProductivityScore object
            
        Returns:
            List of formatted recommendation strings
        """
        return score.recommendations

    def generate_text_report(self, score: ProductivityScore, session: SessionMetrics) -> str:
        """
        Generate a detailed text report.
        
        Args:
            score: ProductivityScore object
            session: SessionMetrics object
            
        Returns:
            Formatted text report string
        """
        report = []
        report.append("=" * 70)
        report.append("PRODUCTIVITY ANALYSIS REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Overall scores
        report.append("OVERALL PRODUCTIVITY SCORE")
        report.append(f"  Overall: {score.overall_score:.1f}% {self._get_score_emoji(score.overall_score)}")
        report.append("")
        
        report.append("COMPONENT SCORES")
        report.append(f"  Focus:       {score.focus_score:.1f}% {self._get_score_emoji(score.focus_score)}")
        report.append(f"  Engagement:  {score.engagement_score:.1f}% {self._get_score_emoji(score.engagement_score)}")
        report.append(f"  Stability:   {score.stability_score:.1f}% {self._get_score_emoji(score.stability_score)}")
        report.append("")
        
        # Session statistics
        report.append("SESSION STATISTICS")
        report.append(f"  Total Frames:        {session.total_frames:,}")
        report.append(f"  Frames with Face:    {session.frames_with_face:,}")
        report.append(f"  Attentive Frames:    {session.total_attentive_frames:,}")
        report.append(f"  Looking Away Frames: {session.total_looking_away_frames:,}")
        report.append(f"  Unknown Frames:      {session.total_unknown_frames:,}")
        report.append(f"  Total Blinks:        {session.total_blinks}")
        report.append(f"  Avg Eye Aspect Ratio: {session.average_ear:.3f}")
        report.append(f"  Avg Yaw (Rotation):  {session.average_yaw:.1f}°")
        report.append(f"  Avg Pitch (Tilt):    {session.average_pitch:.1f}°")
        report.append(f"  Average FPS:         {session.average_fps:.1f}")
        report.append(f"  Session Duration:    {session.session_duration:.1f}s ({session.session_duration/60:.1f}m)")
        report.append("")
        
        # Insights
        report.append("INSIGHTS")
        for insight in score.insights:
            report.append(f"  • {insight}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        for rec in score.recommendations:
            report.append(f"  • {rec}")
        report.append("")
        
        report.append("=" * 70)
        report.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        
        return "\n".join(report)

    def generate_csv_row(self, score: ProductivityScore, session: SessionMetrics) -> str:
        """
        Generate a CSV row for data export.
        
        Args:
            score: ProductivityScore object
            session: SessionMetrics object
            
        Returns:
            CSV row string
        """
        values = [
            datetime.now().isoformat(),
            f"{score.overall_score:.1f}",
            f"{score.focus_score:.1f}",
            f"{score.engagement_score:.1f}",
            f"{score.stability_score:.1f}",
            session.total_frames,
            session.frames_with_face,
            session.total_attentive_frames,
            session.total_looking_away_frames,
            f"{session.average_ear:.3f}",
            f"{session.average_yaw:.1f}",
            f"{session.average_pitch:.1f}",
            f"{session.average_fps:.1f}",
            f"{session.session_duration:.1f}",
        ]
        return ",".join(str(v) for v in values)

    @staticmethod
    def get_csv_header() -> str:
        """
        Get CSV header row.
        
        Returns:
            CSV header string
        """
        headers = [
            "timestamp",
            "overall_score",
            "focus_score",
            "engagement_score",
            "stability_score",
            "total_frames",
            "frames_with_face",
            "attentive_frames",
            "looking_away_frames",
            "average_ear",
            "average_yaw",
            "average_pitch",
            "average_fps",
            "session_duration",
        ]
        return ",".join(headers)

    @staticmethod
    def _get_score_description(score: float) -> str:
        """Get textual description of score."""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Acceptable"
        elif score >= 45:
            return "Fair"
        else:
            return "Needs Improvement"

    @staticmethod
    def _get_score_emoji(score: float) -> str:
        """Get emoji representation of score."""
        if score >= 90:
            return "🌟"
        elif score >= 75:
            return "✅"
        elif score >= 60:
            return "👍"
        elif score >= 45:
            return "⚠️"
        else:
            return "❌"
