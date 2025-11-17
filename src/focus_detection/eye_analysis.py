import numpy as np
from typing import Dict, Any, Sequence


# Indices for common landmark layouts. We support MediaPipe (468) and InsightFace (106).
# MediaPipe (468) canonical eye indices (approximate):
MP_LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
MP_RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

# InsightFace 106 indices (approximate mapping used elsewhere in this project):
IF_LEFT_EYE_IDX = [60, 61, 62, 63, 64, 65]
IF_RIGHT_EYE_IDX = [66, 67, 68, 69, 70, 71]


class EyeAnalysis:
    def __init__(self, ear_threshold: float = 0.20):
        """
        Simple Eye Analysis using landmark-based EAR and coarse gaze.
        :param ear_threshold: EAR threshold under which eye is considered 'closed'
        """
        self.ear_threshold = float(ear_threshold)

    @staticmethod
    def _euclidean(a: Sequence[float], b: Sequence[float]) -> float:
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        return float(np.linalg.norm(a - b))
    
    def get_eye_landmarks_from_face(self, landmarks: np.ndarray):
        """
        Extract left and right eye landmarks from full-face landmarks array (106 points).
        Returns (left_eye (6,2), right_eye (6,2))
        """
        lm = np.asarray(landmarks, dtype=float)
        if lm.ndim != 2 or lm.shape[1] < 2:
            raise ValueError("landmarks must be an Nx2 or Nx3 array")

        # Determine which index set to use based on number of landmarks
        n_pts = lm.shape[0]
        lm2 = lm[:, :2]

        if n_pts >= 468:
            # MediaPipe FaceMesh layout
            left_idx = MP_LEFT_EYE_IDX
            right_idx = MP_RIGHT_EYE_IDX
        elif n_pts >= 106:
            # InsightFace 106 layout
            left_idx = IF_LEFT_EYE_IDX
            right_idx = IF_RIGHT_EYE_IDX
        else:
            # Not enough points - return zeros to signal missing data
            return np.zeros((6, 2), dtype=float), np.zeros((6, 2), dtype=float)

        # Safety: if indices exceed available points, fallback to zeros
        if max(left_idx + right_idx) >= n_pts:
            return np.zeros((6, 2), dtype=float), np.zeros((6, 2), dtype=float)

        left_eye = lm2[left_idx, :]
        right_eye = lm2[right_idx, :]
        return left_eye, right_eye


    def eye_aspect_ratio(self, eye_landmarks: np.ndarray) -> float:
        """
        Compute EAR for one eye.
        eye_landmarks: (6, 2) array of eye landmark coordinates p1..p6
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        if eye_landmarks.shape[0] != 6:
            raise ValueError("eye_landmarks must have shape (6, 2)")

        p1 = eye_landmarks[0]
        p2 = eye_landmarks[1]
        p3 = eye_landmarks[2]
        p4 = eye_landmarks[3]
        p5 = eye_landmarks[4]
        p6 = eye_landmarks[5]

        A = self._euclidean(p2, p6)
        B = self._euclidean(p3, p5)
        C = self._euclidean(p1, p4)

        if C == 0:
            return 0.0
        ear = (A + B) / (2.0 * C)
        return float(ear)

    def _coarse_gaze(self, eye_landmarks: np.ndarray) -> str:
        """
        Coarse gaze direction from eye landmarks.
        - Compute bounding box of eye landmarks
        - Approximate 'iris' center as mean of the 6 landmarks (cheap heuristic)
        - Compute horizontal/vertical ratio and quantize to left/center/right and up/center/down
        """
        xs = eye_landmarks[:, 0]
        ys = eye_landmarks[:, 1]
        min_x, max_x = float(xs.min()), float(xs.max())
        min_y, max_y = float(ys.min()), float(ys.max())

        if max_x - min_x <= 0 or max_y - min_y <= 0:
            return "center"

        cx = float(xs.mean())
        cy = float(ys.mean())

        h_ratio = (cx - min_x) / (max_x - min_x)
        v_ratio = (cy - min_y) / (max_y - min_y)

        # Horizontal quantization
        if h_ratio < 0.35:
            horiz = "left"
        elif h_ratio > 0.65:
            horiz = "right"
        else:
            horiz = "center"

        # Vertical quantization
        if v_ratio < 0.35:
            vert = "up"
        elif v_ratio > 0.65:
            vert = "down"
        else:
            vert = "center"

        # Prefer horizontal as primary signal for screen-facing tasks
        if horiz != "center":
            return horiz
        return vert

    def analyze(self, landmarks: np.ndarray) -> Dict[str, Any]:
        """
        Analyze eyes given the full-face landmarks array.

        :param landmarks: np.ndarray of shape (N, 2) or (N, 3) where N >= 72 (106 recommended)
        :return: dict with left_eye and right_eye sub-dicts
        """
        lm = np.asarray(landmarks, dtype=float)
        if lm.ndim != 2 or lm.shape[1] < 2:
            raise ValueError("landmarks must be an Nx2 or Nx3 array")

        # Ensure at least 72 points (safe-check)
        n_pts = lm.shape[0]
        # If 3D provided, use only first two dims
        lm2 = lm[:, :2]

        def get_eye(idx_list):
            if max(idx_list) >= n_pts:
                # Not enough landmarks — return neutral/empty structure
                empty = np.zeros((6, 2), dtype=float)
                return empty
            return lm2[idx_list, :]

        # Choose index set dynamically based on landmark count
        n_pts = lm2.shape[0]
        if n_pts >= 468:
            left_idx = MP_LEFT_EYE_IDX
            right_idx = MP_RIGHT_EYE_IDX
        elif n_pts >= 106:
            left_idx = IF_LEFT_EYE_IDX
            right_idx = IF_RIGHT_EYE_IDX
        else:
            left_idx = []
            right_idx = []

        left_eye = get_eye(left_idx) if left_idx else np.zeros((6, 2), dtype=float)
        right_eye = get_eye(right_idx) if right_idx else np.zeros((6, 2), dtype=float)

        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)

        left_open = left_ear >= self.ear_threshold
        right_open = right_ear >= self.ear_threshold

        left_gaze = self._coarse_gaze(left_eye)
        right_gaze = self._coarse_gaze(right_eye)

        return {
            "left_eye": {
                "ear": float(left_ear),
                "open": bool(left_open),
                "gaze": left_gaze
            },
            "right_eye": {
                "ear": float(right_ear),
                "open": bool(right_open),
                "gaze": right_gaze
            }
        }
