"""
data_structures.py

Defines standardized data structures for passing data between focus_detection and scoring modules.
This ensures type safety, clarity, and easy integration across the pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class AttentionState(Enum):
    """Enumeration of possible attention states."""
    ATTENTIVE = "attentive"
    LOOKING_AWAY = "looking_away"
    UNKNOWN = "unknown"


@dataclass
class FaceMetrics:
    """Metrics for a single detected face."""
    bbox: tuple  # (x1, y1, x2, y2)
    confidence: float  # 0-1 detection confidence
    yaw: float  # Horizontal head rotation in degrees
    pitch: float  # Vertical head rotation in degrees
    roll: float  # Head tilt in degrees
    left_ear: float  # Eye aspect ratio (left eye)
    right_ear: float  # Eye aspect ratio (right eye)
    eyes_open_left: bool
    eyes_open_right: bool
    blink_count: int
    mar: float
    mouth_open: bool
    yawn_count: int
    attention: AttentionState  # Attention classification
    left_gaze: Optional[List[float]] = None
    right_gaze: Optional[List[float]] = None


@dataclass
class FrameData:
    """Complete data for a single frame from focus detection."""
    frame_id: int
    timestamp: float  # Unix timestamp
    face_count: int
    face_detected: bool
    faces: List[FaceMetrics] = field(default_factory=list)
    primary: Optional[FaceMetrics] = None  # Largest/most prominent face
    proc_time: float = 0.0  # Frame processing time (seconds)
    proc_fps: float = 0.0  # Processing FPS
    capture_time: float = 0.0  # Capture time (seconds)
    extra_debug: Dict[str, Any] = field(default_factory=dict)  # Any extra debug info

    @classmethod
    def from_pipeline_output(cls, output: Dict[str, Any]) -> "FrameData":
        """
        Convert pipeline output dictionary to FrameData.
        
        Args:
            output: Output dictionary from FocusPipeline.process_frame()
            
        Returns:
            FrameData instance
        """
        faces = []
        for face_dict in output.get("faces", []):
            attention_str = face_dict.get("attention", "unknown").lower()
            try:
                attention = AttentionState(attention_str)
            except ValueError:
                attention = AttentionState.UNKNOWN
            
            face = FaceMetrics(
                bbox=tuple(face_dict.get("bbox", (0, 0, 0, 0))),
                confidence=float(face_dict.get("confidence", 0.0)),
                yaw=float(face_dict.get("yaw", 0.0)),
                pitch=float(face_dict.get("pitch", 0.0)),
                roll=float(face_dict.get("roll", 0.0)),
                left_ear=float(face_dict.get("left_ear", 0.0)),
                right_ear=float(face_dict.get("right_ear", 0.0)),
                eyes_open_left=bool(face_dict.get("eyes_open_left", False)),
                eyes_open_right=bool(face_dict.get("eyes_open_right", False)),
                blink_count=int(face_dict.get("blink_count", 0)),
                mar=float(face_dict.get("mar", 0.0)),
                mouth_open=bool(face_dict.get("mouth_open", False)),
                yawn_count=int(face_dict.get("yawn_count", 0)),
                attention=attention,
                left_gaze=face_dict.get("left_gaze"),
                right_gaze=face_dict.get("right_gaze"),
            )
            faces.append(face)
        
        # Extract primary face
        primary = None
        if output.get("primary"):
            primary_dict = output["primary"]
            attention_str = primary_dict.get("attention", "unknown").lower()
            try:
                attention = AttentionState(attention_str)
            except ValueError:
                attention = AttentionState.UNKNOWN
            
            primary = FaceMetrics(
                bbox=tuple(primary_dict.get("bbox", (0, 0, 0, 0))),
                confidence=float(primary_dict.get("confidence", 0.0)),
                yaw=float(primary_dict.get("yaw", 0.0)),
                pitch=float(primary_dict.get("pitch", 0.0)),
                roll=float(primary_dict.get("roll", 0.0)),
                left_ear=float(primary_dict.get("left_ear", 0.0)),
                right_ear=float(primary_dict.get("right_ear", 0.0)),
                eyes_open_left=bool(primary_dict.get("eyes_open_left", False)),
                eyes_open_right=bool(primary_dict.get("eyes_open_right", False)),
                blink_count=int(primary_dict.get("blink_count", 0)),
                mar=float(primary_dict.get("mar", 0.0)),
                mouth_open=bool(primary_dict.get("mouth_open", False)),
                yawn_count=int(primary_dict.get("yawn_count", 0)),
                attention=attention,
                left_gaze=primary_dict.get("left_gaze"),
                right_gaze=primary_dict.get("right_gaze"),
            )
        
        debug = output.get("debug", {})
        
        return cls(
            frame_id=int(output.get("frame_id", 0)),
            timestamp=float(output.get("timestamp", 0.0)),
            face_count=int(output.get("face_count", 0)),
            face_detected=bool(output.get("face_detected", False)),
            faces=faces,
            primary=primary,
            proc_time=float(debug.get("proc_time", 0.0)),
            proc_fps=float(debug.get("proc_fps", 0.0)),
            capture_time=float(debug.get("capture_time", 0.0)),
            extra_debug=output.get("extra_debug", {}),
        )


@dataclass
class SessionMetrics:
    """Aggregated metrics for a session (multiple frames)."""
    total_frames: int = 0
    frames_with_face: int = 0
    total_attentive_frames: int = 0
    total_looking_away_frames: int = 0
    total_unknown_frames: int = 0
    total_blinks: int = 0
    average_ear: float = 0.0
    average_yaw: float = 0.0
    average_pitch: float = 0.0
    average_fps: float = 0.0
    session_duration: float = 0.0  # seconds


@dataclass
class ProductivityScore:
    """Final productivity score with breakdown."""
    overall_score: float  # 0-100
    focus_score: float  # 0-100 (based on attention)
    engagement_score: float  # 0-100 (based on eye metrics)
    stability_score: float  # 0-100 (based on head position stability)
    components: Dict[str, float] = field(default_factory=dict)  # Breakdown of score components
    insights: List[str] = field(default_factory=list)  # Human-readable insights
    recommendations: List[str] = field(default_factory=list)  # Actionable recommendations
