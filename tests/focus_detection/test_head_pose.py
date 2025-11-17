import numpy as np
from src.focus_detection.head_pose import HeadPoseEstimator

def test_head_pose_returns_expected_keys():
    estimator = HeadPoseEstimator()

    # Fake landmarks (should match what mediapipe or your face model will output)
    fake_landmarks = np.random.rand(468, 3)  # 468 mediapipe-style landmarks

    result = estimator.estimate(fake_landmarks)

    assert isinstance(result, dict)
    assert "pitch" in result
    assert "yaw" in result
    assert "roll" in result

def test_head_pose_output_ranges():
    estimator = HeadPoseEstimator()

    fake_landmarks = np.random.rand(468, 3)

    result = estimator.estimate(fake_landmarks)

    assert -90 <= result["pitch"] <= 90
    assert -90 <= result["yaw"] <= 90
    assert -90 <= result["roll"] <= 90
