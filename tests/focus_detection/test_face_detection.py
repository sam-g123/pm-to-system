import numpy as np
import cv2
from src.focus_detection.face_detection import FaceDetector

def test_face_detector_loads_model():
    detector = FaceDetector()
    assert detector.model is not None

def test_face_detection_runs_on_blank_frame():
    detector = FaceDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = detector.detect(frame)
    assert results is not None
