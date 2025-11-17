import numpy as np
from src.focus_detection.eye_analysis import EyeAnalysis


def make_landmarks():
    """
    Return a base 106x2 landmark array filled with zeros.
    Tests will overwrite eye indices.
    """
    lm = np.zeros((106, 2), dtype=float)
    return lm


def test_eye_analysis_initializes():
    ea = EyeAnalysis()
    assert ea.ear_threshold == 0.20


def test_ear_calculation_open_and_closed():
    ea = EyeAnalysis(ear_threshold=0.20)

    lm = make_landmarks()

    # LEFT EYE: set points such that EAR is high (~0.5) -> open
    # p1..p6 for left eye indices 60..65
    # construct: p1=(0,0), p4=(4,0) width=4
    # p2=(1,1), p6=(1,-1) -> dist=2
    # p3=(2,1), p5=(2,-1) -> dist=2 => EAR = (2+2)/(2*4) = 0.5
    left = {
        60: (0.0, 0.0),
        61: (1.0, 1.0),
        62: (2.0, 1.0),
        63: (4.0, 0.0),
        64: (2.0, -1.0),
        65: (1.0, -1.0),
    }
    for k, v in left.items():
        lm[k] = v

    # RIGHT EYE: set closed (EAR small)
    # p1=(0,0), p4=(4,0)
    # p2=(1,0.1), p6=(1,-0.1) -> dist=0.2
    # p3=(2,0.1), p5=(2,-0.1) -> dist=0.2 => EAR = (0.2+0.2)/(2*4) = 0.05
    right = {
        66: (0.0, 0.0),
        67: (1.0, 0.1),
        68: (2.0, 0.1),
        69: (4.0, 0.0),
        70: (2.0, -0.1),
        71: (1.0, -0.1),
    }
    for k, v in right.items():
        lm[k] = v

    out = ea.analyze(lm)

    assert "left_eye" in out and "right_eye" in out
    assert out["left_eye"]["ear"] > out["right_eye"]["ear"]
    assert out["left_eye"]["open"] is True
    assert out["right_eye"]["open"] is False


def test_gaze_quantization_left_center_right():
    ea = EyeAnalysis()

    lm = make_landmarks()

    # left eye landmarks: bounding box from x=0 to x=4
    # center gaze -> mean x ~2
    left_center = {
        60: (0.0, 0.0),
        61: (1.0, 1.0),
        62: (2.0, 1.0),
        63: (4.0, 0.0),
        64: (2.0, -1.0),
        65: (1.0, -1.0),
    }
    # left gaze -> move mean x near left edge (e.g., points shifted left)
    left_left = {
        60: (0.0, 0.0),
        61: (0.2, 1.0),
        62: (0.4, 1.0),
        63: (2.5, 0.0),  # right-most still > left, bounding box smaller
        64: (0.4, -1.0),
        65: (0.2, -1.0),
    }
    # right gaze -> move mean x near right edge
    left_right = {
        60: (0.0, 0.0),
        61: (3.2, 1.0),
        62: (3.4, 1.0),
        63: (4.0, 0.0),
        64: (3.4, -1.0),
        65: (3.2, -1.0),
    }

    # test center
    for k, v in left_center.items():
        lm[k] = v
    out = ea.analyze(lm)
    assert out["left_eye"]["gaze"] in {"center", "up", "down"}  # center is acceptable

    # test left
    for k, v in left_left.items():
        lm[k] = v
    out = ea.analyze(lm)
    assert out["left_eye"]["gaze"] == "left"

    # test right
    for k, v in left_right.items():
        lm[k] = v
    out = ea.analyze(lm)
    assert out["left_eye"]["gaze"] == "right"
