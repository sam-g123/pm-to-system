import numpy as np
from src.focus_detection.eye_analysis import EyeAnalysis

def test_set_calibrated_threshold():
    ea = EyeAnalysis()
    # typical open_mean and closed_mean values
    ea.set_calibrated_threshold(open_mean=0.35, closed_mean=0.05)
    assert 0.10 < ea.ear_threshold < 0.30

def test_set_calibrated_threshold_open_only():
    ea = EyeAnalysis()
    ea.set_calibrated_threshold(open_mean=0.32, closed_mean=None)
    assert ea.ear_threshold <= 0.32 and ea.ear_threshold >= 0.12
