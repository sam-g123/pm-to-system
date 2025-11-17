"""
productivity_score.py

Calculates productivity scores based on focus detection metrics.
Converts raw eye gaze, head pose, and blink data into actionable productivity measures.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import statistics
import numpy as np

from .data_structures import (
    FrameData,
    SessionMetrics,
    ProductivityScore,
    AttentionState,
)


class ProductivityScoringEngine:
    """
    Converts focus detection frame data into productivity scores.
    
    Scoring approach:
    - Focus Score: Based on attention state (attentive vs looking_away)
    - Engagement Score: Based on eye metrics (blink rate, EAR)
    - Stability Score: Based on head position (yaw/pitch variance)
    - Overall Score: Weighted combination of above
    """

    def __init__(
        self,
        focus_weight: float = 0.4,
        engagement_weight: float = 0.35,
        stability_weight: float = 0.25,
    ):
        """
        Initialize scoring engine with component weights.
        
        Args:
            focus_weight: Weight for focus component (default: 0.4)
            engagement_weight: Weight for engagement component (default: 0.35)
            stability_weight: Weight for stability component (default: 0.25)
        """
        total = focus_weight + engagement_weight + stability_weight
        self.focus_weight = focus_weight / total
        self.engagement_weight = engagement_weight / total
        self.stability_weight = stability_weight / total

    def calculate_focus_score(self, frames: List[FrameData]) -> tuple[float, Dict[str, Any]]:
        """
        Calculate focus score based on attention state.
        
        Focus Score = (attentive_frames / total_frames) * 100
        
        Args:
            frames: List of frame data
            
        Returns:
            Tuple of (score 0-100, metrics dict)
        """
        if not frames:
            return 0.0, {}

        # Filter frames with detected faces
        face_frames = [f for f in frames if f.primary]
        if not face_frames:
            return 0.0, {"face_detected": False}

        # Count attentive vs looking away
        attentive_count = sum(
            1 for f in face_frames if f.primary.attention == AttentionState.ATTENTIVE
        )
        looking_away_count = sum(
            1 for f in face_frames if f.primary.attention == AttentionState.LOOKING_AWAY
        )

        focus_percentage = (attentive_count / len(face_frames)) * 100 if face_frames else 0
        
        # Score: 100% attentive = 100, 0% attentive = 0
        score = focus_percentage
        
        metrics = {
            "attentive_frames": attentive_count,
            "looking_away_frames": looking_away_count,
            "unknown_frames": len(face_frames) - attentive_count - looking_away_count,
            "focus_percentage": focus_percentage,
            "total_frames_with_face": len(face_frames),
        }
        
        return score, metrics

    def calculate_engagement_score(self, frames: List[FrameData]) -> tuple[float, Dict[str, Any]]:
        """
        Calculate engagement score based on eye metrics (blink rate, EAR).
        
        Engagement Score based on:
        - Healthy blink rate (15-30 blinks/minute optimal)
        - Eye aspect ratio (indicates eye openness)
        - Eye state consistency
        
        Args:
            frames: List of frame data
            
        Returns:
            Tuple of (score 0-100, metrics dict)
        """
        if not frames:
            return 0.0, {}

        face_frames = [f for f in frames if f.primary]
        if not face_frames:
            return 0.0, {"face_detected": False}

        # Extract metrics
        ears = []
        blink_counts = []
        eyes_open_count = 0

        for frame in face_frames:
            if frame.primary:
                # Average eye aspect ratio
                ear = (frame.primary.left_ear + frame.primary.right_ear) / 2
                ears.append(ear)
                blink_counts.append(frame.primary.blink_count)
                
                # Eyes open state
                if frame.primary.eyes_open_left or frame.primary.eyes_open_right:
                    eyes_open_count += 1

        if not ears:
            return 0.0, {}

        # Calculate metrics
        avg_ear = statistics.mean(ears)
        total_blinks = sum(blink_counts) if blink_counts else 0
        eyes_open_percentage = (eyes_open_count / len(face_frames)) * 100

        # Scoring logic:
        # - EAR < 0.15: Eyes likely closed or reduced engagement (score penalty)
        # - EAR 0.15-0.25: Normal range (full score)
        # - EAR > 0.25: Very alert
        
        ear_score = min(max((avg_ear - 0.10) / 0.15 * 100, 0), 100)
        
        # Blink rate scoring (assuming 30fps video)
        # Total blinks / duration in minutes
        # Optimal: 15-30 blinks/min
        blink_score = 100 if total_blinks > 0 else 50
        
        # Eyes open score
        eyes_open_score = eyes_open_percentage
        
        # Weighted combination
        score = (ear_score * 0.4 + blink_score * 0.3 + eyes_open_score * 0.3)
        
        metrics = {
            "average_ear": avg_ear,
            "total_blinks": total_blinks,
            "eyes_open_percentage": eyes_open_percentage,
            "ear_score": ear_score,
            "blink_score": blink_score,
            "eyes_open_score": eyes_open_score,
        }
        
        return min(max(score, 0), 100), metrics

    def calculate_stability_score(self, frames: List[FrameData]) -> tuple[float, Dict[str, Any]]:
        """
        Calculate stability score based on head position consistency.
        
        Stability Score based on:
        - Variance in head yaw (horizontal rotation)
        - Variance in head pitch (vertical rotation)
        - Sudden movement detection
        
        Args:
            frames: List of frame data
            
        Returns:
            Tuple of (score 0-100, metrics dict)
        """
        if not frames:
            return 0.0, {}

        face_frames = [f for f in frames if f.primary]
        if len(face_frames) < 2:
            return 100.0, {"insufficient_data": True}

        # Extract head positions
        yaws = [f.primary.yaw for f in face_frames]
        pitches = [f.primary.pitch for f in face_frames]

        # Calculate variance (lower = more stable)
        yaw_var = np.var(yaws) if len(yaws) > 1 else 0
        pitch_var = np.var(pitches) if len(pitches) > 1 else 0
        
        # Detect sudden movements (frame-to-frame delta)
        yaw_deltas = [abs(yaws[i] - yaws[i-1]) for i in range(1, len(yaws))]
        pitch_deltas = [abs(pitches[i] - pitches[i-1]) for i in range(1, len(pitches))]
        
        max_yaw_delta = max(yaw_deltas) if yaw_deltas else 0
        max_pitch_delta = max(pitch_deltas) if pitch_deltas else 0
        
        # Scoring: Lower variance = higher score
        # Normalize variance to 0-100 scale (higher variance = lower score)
        # Reference: variance ~100 degrees^2 = 0 score, variance ~5 degrees^2 = 100 score
        
        yaw_var_score = max(100 - (yaw_var * 2), 0)
        pitch_var_score = max(100 - (pitch_var * 2), 0)
        
        # Penalize sudden movements
        # Reference: 15° delta = slight movement, 30° delta = sudden movement
        yaw_delta_score = max(100 - (max_yaw_delta * 2), 0)
        pitch_delta_score = max(100 - (max_pitch_delta * 2), 0)
        
        # Combined score
        score = (
            yaw_var_score * 0.25 +
            pitch_var_score * 0.25 +
            yaw_delta_score * 0.25 +
            pitch_delta_score * 0.25
        )
        
        metrics = {
            "yaw_variance": float(yaw_var),
            "pitch_variance": float(pitch_var),
            "max_yaw_delta": float(max_yaw_delta),
            "max_pitch_delta": float(max_pitch_delta),
            "yaw_var_score": float(yaw_var_score),
            "pitch_var_score": float(pitch_var_score),
            "yaw_delta_score": float(yaw_delta_score),
            "pitch_delta_score": float(pitch_delta_score),
        }
        
        return min(max(score, 0), 100), metrics

    def calculate_session_metrics(self, frames: List[FrameData]) -> SessionMetrics:
        """
        Calculate aggregated metrics for a session.
        
        Args:
            frames: List of frame data
            
        Returns:
            SessionMetrics object
        """
        if not frames:
            return SessionMetrics()

        face_frames = [f for f in frames if f.primary]
        
        attentive = sum(1 for f in face_frames if f.primary.attention == AttentionState.ATTENTIVE)
        looking_away = sum(1 for f in face_frames if f.primary.attention == AttentionState.LOOKING_AWAY)
        unknown = len(face_frames) - attentive - looking_away
        
        total_blinks = sum(f.primary.blink_count for f in face_frames if f.primary)
        
        ears = [f.primary.left_ear + f.primary.right_ear for f in face_frames if f.primary]
        avg_ear = (sum(ears) / (2 * len(ears))) if ears else 0
        
        yaws = [f.primary.yaw for f in face_frames if f.primary]
        pitches = [f.primary.pitch for f in face_frames if f.primary]
        
        avg_yaw = statistics.mean(yaws) if yaws else 0
        avg_pitch = statistics.mean(pitches) if pitches else 0
        
        fps_list = [f.proc_fps for f in frames if getattr(f, "proc_fps", 0) > 0]
        avg_fps = statistics.mean(fps_list) if fps_list else 0
        
        duration = frames[-1].timestamp - frames[0].timestamp if len(frames) > 1 else 0
        
        return SessionMetrics(
            total_frames=len(frames),
            frames_with_face=len(face_frames),
            total_attentive_frames=attentive,
            total_looking_away_frames=looking_away,
            total_unknown_frames=unknown,
            total_blinks=total_blinks,
            average_ear=avg_ear,
            average_yaw=avg_yaw,
            average_pitch=avg_pitch,
            average_fps=avg_fps,
            session_duration=duration,
        )

    def calculate_overall_score(self, frames: List[FrameData]) -> ProductivityScore:
        """
        Calculate overall productivity score combining all components.
        
        Args:
            frames: List of frame data from a session
            
        Returns:
            ProductivityScore with overall score and components
        """
        if not frames:
            return ProductivityScore(
                overall_score=0.0,
                focus_score=0.0,
                engagement_score=0.0,
                stability_score=0.0,
                insights=["No frames to analyze"],
                recommendations=["Ensure video is being captured correctly"],
            )

        # Calculate component scores
        focus_score, focus_metrics = self.calculate_focus_score(frames)
        engagement_score, engagement_metrics = self.calculate_engagement_score(frames)
        stability_score, stability_metrics = self.calculate_stability_score(frames)
        # Fatigue: compute separate fatigue score (0=no fatigue, 100=high fatigue)
        fatigue_score, fatigue_metrics = self.calculate_fatigue_score(frames)

        # Calculate overall score
        overall_score = (
            focus_score * self.focus_weight +
            engagement_score * self.engagement_weight +
            stability_score * self.stability_weight
        )

        # Get session metrics
        session = self.calculate_session_metrics(frames)

        # Generate insights and recommendations
        insights = self._generate_insights(
            focus_score,
            engagement_score,
            stability_score,
            session,
        )
        recommendations = self._generate_recommendations(
            focus_score,
            engagement_score,
            stability_score,
            session,
        )

        return ProductivityScore(
            overall_score=min(max(overall_score, 0), 100),
            focus_score=focus_score,
            engagement_score=engagement_score,
            stability_score=stability_score,
            components={
                "focus": focus_score,
                "engagement": engagement_score,
                "stability": stability_score,
                "fatigue": fatigue_score,
                "focus_metrics": focus_metrics,
                "engagement_metrics": engagement_metrics,
                "stability_metrics": stability_metrics,
                "fatigue_metrics": fatigue_metrics,
            },
            insights=insights,
            recommendations=recommendations,
        )

    def calculate_fatigue_score(self, frames: List[FrameData]) -> tuple[float, Dict[str, Any]]:
        """
        Calculate a fatigue score (0-100) using a combination of metrics:
        - EAR (lower EAR -> more fatigue)
        - Blink rate (higher blinks/min -> more fatigue)
        - Yawn rate (higher yawns/min -> more fatigue)
        - Looking away ratio (more looking away -> more fatigue)
        - Head stability (less stable -> more fatigue)

        Returns (fatigue_score, metrics_dict)
        """
        if not frames:
            return 0.0, {}

        face_frames = [f for f in frames if f.primary]
        if not face_frames:
            return 0.0, {}

        # Duration in minutes for rate calculations
        duration_seconds = frames[-1].timestamp - frames[0].timestamp if len(frames) > 1 else 0.0
        duration_minutes = max(duration_seconds / 60.0, 1e-6)

        # Average EAR across frames
        ears = []
        total_blinks = 0
        total_yawns = 0
        looking_away_count = 0
        yaws = []
        pitches = []

        for f in face_frames:
            avg_ear = (f.primary.left_ear + f.primary.right_ear) / 2
            ears.append(avg_ear)
            total_blinks += int(f.primary.blink_count or 0)
            total_yawns += int(f.primary.yawn_count or 0)
            if f.primary.attention == AttentionState.LOOKING_AWAY:
                looking_away_count += 1
            yaws.append(f.primary.yaw)
            pitches.append(f.primary.pitch)

        avg_ear = float(statistics.mean(ears)) if ears else 0.0

        # Blink and yawn rates per minute
        blink_rate = total_blinks / duration_minutes
        yawn_rate = total_yawns / duration_minutes

        # Looking away ratio
        looking_away_ratio = (looking_away_count / len(face_frames)) if face_frames else 0.0

        # Head stability via existing function (returns 0-100 where higher is more stable)
        stability_score, _ = self.calculate_stability_score(frames)

        # Convert component measures to fatigue-oriented 0-100 (higher => more fatigued)
        # EAR: lower EAR => higher fatigue. Reuse engagement ear mapping but invert.
        ear_score = min(max((avg_ear - 0.10) / 0.15 * 100, 0), 100)
        ear_fatigue = 100.0 - ear_score

        # Blink rate: assume 10-40 blinks/min map (10 => 0, 40 => 100)
        blink_fatigue = min(max((blink_rate - 10.0) / (40.0 - 10.0) * 100.0, 0.0), 100.0)

        # Yawn rate: 0->0, 2+ yawns/min => 100
        yawn_fatigue = min(max((yawn_rate / 2.0) * 100.0, 0.0), 100.0)

        # Looking away ratio scaled
        looking_away_fatigue = min(max(looking_away_ratio * 100.0, 0.0), 100.0)

        # Stability fatigue: inverse of stability_score (stability_score 0..100 => fatigue 100..0)
        stability_fatigue = 100.0 - stability_score

        # Weights for components (sum to 1)
        w_ear = 0.25
        w_blink = 0.20
        w_yawn = 0.30
        w_look = 0.15
        w_stab = 0.10

        fatigue_score = (
            ear_fatigue * w_ear +
            blink_fatigue * w_blink +
            yawn_fatigue * w_yawn +
            looking_away_fatigue * w_look +
            stability_fatigue * w_stab
        )

        metrics = {
            "average_ear": avg_ear,
            "ear_fatigue": ear_fatigue,
            "blink_rate_per_min": blink_rate,
            "blink_fatigue": blink_fatigue,
            "yawn_rate_per_min": yawn_rate,
            "yawn_fatigue": yawn_fatigue,
            "looking_away_ratio": looking_away_ratio,
            "looking_away_fatigue": looking_away_fatigue,
            "stability_score": stability_score,
            "stability_fatigue": stability_fatigue,
            "weights": {"ear": w_ear, "blink": w_blink, "yawn": w_yawn, "look": w_look, "stability": w_stab},
            "duration_minutes": duration_minutes,
            "total_blinks": total_blinks,
            "total_yawns": total_yawns,
        }

        return min(max(fatigue_score, 0.0), 100.0), metrics

    def _generate_insights(
        self,
        focus_score: float,
        engagement_score: float,
        stability_score: float,
        session: SessionMetrics,
    ) -> List[str]:
        """Generate human-readable insights from scores."""
        insights = []

        if session.total_frames == 0:
            return ["No face detected during session"]

        # Focus insights
        if focus_score > 80:
            insights.append("🎯 Excellent focus - sustained attention throughout session")
        elif focus_score > 60:
            insights.append("👁️ Good focus - occasional distractions detected")
        elif focus_score > 40:
            insights.append("⚠️ Moderate focus - frequent attention lapses")
        else:
            insights.append("🔴 Low focus - consider taking a break")

        # Engagement insights
        if engagement_score > 80:
            insights.append("👀 Eyes engaged - excellent eye metrics")
        elif engagement_score > 60:
            insights.append("😐 Eyes partially engaged - normal blink rate")
        else:
            insights.append("😴 Eye engagement low - possible fatigue")

        # Stability insights
        if stability_score > 80:
            insights.append("📍 Head position very stable - minimal movement")
        elif stability_score > 60:
            insights.append("🔄 Head position relatively stable")
        else:
            insights.append("🎭 Frequent head movements detected")

        # Duration insight
        if session.session_duration > 300:  # 5 minutes
            insights.append(f"⏱️ Session duration: {session.session_duration/60:.1f} minutes")
        
        return insights

    def _generate_recommendations(
        self,
        focus_score: float,
        engagement_score: float,
        stability_score: float,
        session: SessionMetrics,
    ) -> List[str]:
        """Generate actionable recommendations based on scores."""
        recommendations = []

        if focus_score < 50:
            recommendations.append("Take a 5-minute break to reset focus")
            recommendations.append("Try the Pomodoro technique: 25 min focus + 5 min break")

        if engagement_score < 60:
            recommendations.append("Reduce eye strain: Look away from screen for 20 seconds")
            recommendations.append("Stay hydrated - dehydration affects eye health")

        if stability_score < 50:
            recommendations.append("Adjust monitor/lighting to reduce head movement")
            recommendations.append("Improve desk ergonomics")

        if session.session_duration > 3600 and focus_score < 70:  # 1 hour
            recommendations.append("Consider a longer break - you've been working for a while")

        if not recommendations:
            recommendations.append("Keep up the great work! Maintain current habits.")

        return recommendations
