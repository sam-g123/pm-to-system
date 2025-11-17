"""
human_centered.py

Human-centered insights and analysis.
Provides personalized feedback based on productivity patterns.
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from .data_structures import FrameData, AttentionState


class HumanCenteredInsights:
    """
    Analyzes patterns in focus/attention data to provide personalized insights.
    Considers circadian rhythms, fatigue patterns, and individual baselines.
    """

    def __init__(self):
        """Initialize insights analyzer."""
        self.baseline_focus = None
        self.fatigue_threshold = 0.4  # Threshold below which we detect fatigue
        self.improvement_threshold = 1.1  # 10% improvement from baseline

    def analyze_focus_patterns(self, frames: List[FrameData]) -> Dict[str, Any]:
        """
        Analyze focus patterns over time.
        
        Args:
            frames: List of frame data
            
        Returns:
            Dictionary with pattern analysis
        """
        if not frames or len(frames) < 10:
            return {"insufficient_data": True}

        # Group frames by time windows (every 30 seconds if possible)
        window_size = 30  # frames (assuming ~30fps = 1 second per frame)
        focus_windows = []

        for i in range(0, len(frames), window_size):
            window_frames = frames[i : i + window_size]
            attentive_count = sum(
                1 for f in window_frames
                if f.primary and f.primary.attention == AttentionState.ATTENTIVE
            )
            if window_frames and any(f.primary for f in window_frames):
                focus_ratio = attentive_count / sum(1 for f in window_frames if f.primary)
                focus_windows.append(focus_ratio)

        if not focus_windows:
            return {"insufficient_data": True}

        # Detect patterns
        avg_focus = sum(focus_windows) / len(focus_windows)
        focus_variance = (
            sum((x - avg_focus) ** 2 for x in focus_windows) / len(focus_windows)
        )
        focus_std = focus_variance ** 0.5

        # Detect focus decline (fatigue)
        first_half = focus_windows[: len(focus_windows) // 2]
        second_half = focus_windows[len(focus_windows) // 2 :]
        
        first_half_avg = sum(first_half) / len(first_half) if first_half else 0
        second_half_avg = sum(second_half) / len(second_half) if second_half else 0
        
        focus_trend = second_half_avg - first_half_avg

        return {
            "average_focus": avg_focus,
            "focus_consistency": 1.0 - min(focus_std, 1.0),  # 1 = perfect consistency
            "focus_trend": focus_trend,  # Positive = improving, negative = declining
            "fatigue_detected": focus_trend < -0.1,
            "focus_windows": focus_windows,
        }

    def detect_fatigue(self, frames: List[FrameData]) -> Dict[str, Any]:
        """
        Detect signs of fatigue from eye metrics and focus patterns.
        
        Args:
            frames: List of frame data
            
        Returns:
            Dictionary with fatigue analysis
        """
        if not frames:
            return {"fatigue_level": 0, "no_data": True}

        face_frames = [f for f in frames if f.primary]
        if not face_frames:
            return {"fatigue_level": 0, "no_face": True}

        # Indicators of fatigue:
        # 1. Lower EAR (eyes more closed)
        # 2. Higher blink rate (eyes getting strained)
        # 3. More looking away episodes
        # 4. Head drooping (pitch more negative)

        ears = [f.primary.left_ear + f.primary.right_ear for f in face_frames]
        avg_ear = sum(ears) / (2 * len(ears)) if ears else 0

        looking_away_count = sum(
            1 for f in face_frames if f.primary.attention == AttentionState.LOOKING_AWAY
        )
        looking_away_ratio = looking_away_count / len(face_frames)

        pitches = [f.primary.pitch for f in face_frames]
        avg_pitch = sum(pitches) / len(pitches) if pitches else 0

        # Fatigue scoring (0-1)
        # Lower EAR = more fatigue
        ear_fatigue = max(0, 1 - (avg_ear / 0.2))  # 0.2 is normal EAR
        
        # More looking away = more fatigue
        looking_away_fatigue = looking_away_ratio
        
        # Negative pitch (head tilted down) = more fatigue
        pitch_fatigue = max(0, -avg_pitch / 30.0)  # -30° = high fatigue
        
        # Combined fatigue score
        fatigue_level = (ear_fatigue * 0.4 + looking_away_fatigue * 0.4 + pitch_fatigue * 0.2)
        fatigue_level = min(max(fatigue_level, 0), 1)

        return {
            "fatigue_level": fatigue_level,
            "fatigue_description": self._get_fatigue_description(fatigue_level),
            "ear_fatigue_indicator": ear_fatigue,
            "looking_away_ratio": looking_away_ratio,
            "pitch_fatigue_indicator": pitch_fatigue,
            "average_ear": avg_ear,
            "average_pitch": avg_pitch,
        }

    def get_personalized_feedback(
        self,
        focus_patterns: Dict[str, Any],
        fatigue_analysis: Dict[str, Any],
        current_score: float,
    ) -> List[str]:
        """
        Generate personalized feedback based on patterns and current performance.
        
        Args:
            focus_patterns: Output from analyze_focus_patterns()
            fatigue_analysis: Output from detect_fatigue()
            current_score: Current productivity score (0-100)
            
        Returns:
            List of personalized feedback strings
        """
        feedback = []

        # Fatigue-based feedback
        fatigue_level = fatigue_analysis.get("fatigue_level", 0)
        if fatigue_level > 0.7:
            feedback.append("🛑 You appear fatigued. Consider a substantial break (15-20 min).")
        elif fatigue_level > 0.4:
            feedback.append("😑 Mild fatigue detected. Stand up, stretch, and look away from screen.")
        
        # Focus consistency feedback
        if "focus_consistency" in focus_patterns:
            consistency = focus_patterns["focus_consistency"]
            if consistency > 0.9:
                feedback.append("🎯 Excellent focus consistency! You're in the zone.")
            elif consistency < 0.5:
                feedback.append("🔄 Your focus is fluctuating. Try reducing distractions.")

        # Trend-based feedback
        if "focus_trend" in focus_patterns:
            trend = focus_patterns["focus_trend"]
            if trend > 0.1:
                feedback.append("📈 Your focus is improving! Keep the momentum.")
            elif trend < -0.1:
                feedback.append("📉 Your focus is declining. Time to reset?")

        # Score-based feedback
        if current_score > 85:
            feedback.append("🌟 Outstanding performance! Maintain this level.")
        elif current_score < 40:
            feedback.append("⚠️ Productivity is low. Take a break and come back refreshed.")

        if not feedback:
            feedback.append("Your productivity is steady. Good job maintaining focus!")

        return feedback

    def estimate_optimal_break_time(
        self,
        session_duration: float,
        focus_patterns: Dict[str, Any],
        fatigue_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Estimate when to take a break based on session duration and patterns.
        
        Args:
            session_duration: Session duration in seconds
            focus_patterns: Output from analyze_focus_patterns()
            fatigue_analysis: Output from detect_fatigue()
            
        Returns:
            Dictionary with break recommendations
        """
        fatigue_level = fatigue_analysis.get("fatigue_level", 0)
        
        # Pomodoro technique: 25 min work, 5 min break
        # But adjust based on fatigue
        
        base_work_duration = 25 * 60  # 25 minutes in seconds
        
        if fatigue_level > 0.7:
            recommended_break = max(0, 15 * 60 - session_duration)
            break_type = "long"
        elif fatigue_level > 0.4:
            recommended_break = max(0, 20 * 60 - session_duration)
            break_type = "medium"
        else:
            recommended_break = max(0, base_work_duration - session_duration)
            break_type = "pomodoro"

        return {
            "recommended_break_duration": recommended_break,
            "break_type": break_type,
            "break_type_description": {
                "pomodoro": "5-10 minute break",
                "medium": "10-15 minute break",
                "long": "15-20 minute break",
            }.get(break_type, "5-10 minute break"),
            "next_break_in_seconds": recommended_break,
            "rationale": f"Based on detected fatigue level: {fatigue_level:.1%}",
        }

    @staticmethod
    def _get_fatigue_description(fatigue_level: float) -> str:
        """Get textual description of fatigue level."""
        if fatigue_level < 0.2:
            return "Fresh and alert"
        elif fatigue_level < 0.4:
            return "Slightly fatigued"
        elif fatigue_level < 0.6:
            return "Moderately fatigued"
        elif fatigue_level < 0.8:
            return "Quite fatigued"
        else:
            return "Very fatigued"

    def get_health_tips(self) -> List[str]:
        """Get general eye health and productivity tips."""
        return [
            "📖 Follow the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds",
            "💧 Stay hydrated - dehydration affects focus and eye health",
            "🪟 Ensure proper lighting - reduce glare and eye strain",
            "🛋️ Adjust your monitor to eye level to maintain good posture",
            "⏰ Use the Pomodoro technique: 25 minutes work, 5 minutes break",
            "🚶 Take regular breaks to walk and stretch",
            "😴 Ensure 7-9 hours of sleep for optimal productivity",
            "🎧 Use background music or white noise if it helps focus",
            "🧘 Try deep breathing exercises during breaks",
            "📵 Minimize distractions - phone, notifications, etc.",
        ]
