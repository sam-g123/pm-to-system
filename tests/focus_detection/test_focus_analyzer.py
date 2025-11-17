import numpy as np
import types
from unittest.mock import patch

import pytest

from src.focus_detection.focus_analyzer import FocusAnalyzer

class DummyDetector:
    def __init__(self, detections):
        self._detections = detections
    def detect(self, frame):
        return self._detections


class DummyPose:
    def __init__(self, yaw=0.0, pitch=0.0, roll=0.0, landmarks=None):
        self._yaw = yaw
        self._pitch = pitch
        self._roll = roll
        self._landmarks = landmarks if landmarks is not None else np.zeros((106,2))

    def estimate(self, frame, bbox):
        return {
            "yaw": self._yaw,
            "pitch": self._pitch,
            "roll": self._roll,
            "landmarks_2d": self._landmarks
        }


class DummyEyes:
    def __init__(self, left_open=True, right_open=True, left_ear=0.3, right_ear=0.3):
        self._left_open = left_open
        self._right_open = right_open
        self._left_ear = left_ear
        self._right_ear = right_ear

    def analyze(self, landmarks):
        return {
            "left_eye": {
                "ear": float(self._left_ear),
                "open": bool(self._left_open),
                "gaze": "center"
            },
            "right_eye": {
                "ear": float(self._right_ear),
                "open": bool(self._right_open),
                "gaze": "center"
            }
        }


def test_attention_attentive_and_blink_count():
    # Force landmark computation on every frame to match FocusAnalyzer behavior.
    det = [{"bbox": (10,10,110,110), "confidence": 0.99}]
    fa = FocusAnalyzer(device="cpu")
    fa.detector = DummyDetector(det)
    fa.pose = DummyPose(yaw=0.0, pitch=0.0)
    fa.eye_analyzer = DummyEyes(left_open=True, right_open=True)

    frame = np.zeros((240,320,3), dtype=np.uint8)

    # First analysis: eyes open -> attentive
    result = fa.analyze_frame(frame, return_all=False)
    assert result["face_count"] == 1
    assert result["primary"]["attention"] == "attentive"

    # Now simulate eyes closed for several frames to produce a blink
    fa.eye_analyzer = DummyEyes(left_open=False, right_open=False, left_ear=0.05, right_ear=0.05)

    for _ in range(fa.blink_consec_frames + 1):
        fa.analyze_frame(frame, return_all=False)

    # Request a fresh reading (the earlier "result" must not be reused)
    final_res = fa.analyze_frame(frame, return_all=True)
    primary_face = final_res["faces"][0]

    assert primary_face["blink_count"] >= 1


def test_looking_away_detection():
    # Again force landmark computation every frame.
    det = [{"bbox": (0,0,200,200), "confidence": 0.9}]
    fa = FocusAnalyzer(device="cpu", yaw_threshold=10.0)
    fa.detector = DummyDetector(det)

    # Large yaw should classify as looking away
    fa.pose = DummyPose(yaw=45.0, pitch=0.0)
    fa.eye_analyzer = DummyEyes()

    frame = np.zeros((480,640,3), dtype=np.uint8)

    res = fa.analyze_frame(frame, return_all=False)
    assert res["primary"]["attention"] == "looking_away"
