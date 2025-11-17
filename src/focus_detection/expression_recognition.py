import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

class HeadPoseEstimator:
    def __init__(self, detection_size=(640, 640), device="cuda"):
        """
        Initialize InsightFace model for 2D facial landmark detection.
        """
        self.app = FaceAnalysis(
            name="buffalo_l", 
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0 if device == "cuda" else -1, det_size=detection_size)

        # 3D model landmarks for solvePnP (based on 68 points)
        self.model_points_68 = np.array([
            (0.0, 0.0, 0.0),            # Nose tip           (30)
            (0.0, -330.0, -65.0),       # Chin               (8)
            (-225.0, 170.0, -135.0),    # Left eye left      (36)
            (225.0, 170.0, -135.0),     # Right eye right    (45)
            (-150.0, -150.0, -125.0),   # Left mouth corner  (48)
            (150.0, -150.0, -125.0)     # Right mouth corner (54)
        ], dtype=np.float32)

    def _select_points(self, landmarks):
        """
        Extract the six key 2D points needed for PnP.
        Landmarks follow InsightFace's 106-point layout.
        """

        # Mapping for InsightFace (106-point):
        nose_tip = landmarks[30]
        chin = landmarks[8]
        left_eye_corner = landmarks[36]
        right_eye_corner = landmarks[45]
        mouth_left = landmarks[48]
        mouth_right = landmarks[54]

        points_2d = np.array([
            nose_tip,
            chin,
            left_eye_corner,
            right_eye_corner,
            mouth_left,
            mouth_right
        ], dtype=np.float32)

        return points_2d

    def estimate(self, frame, face_box):
        """
        Estimate head pose for a detected face.
        face_box = (x1, y1, x2, y2)
        """
        x1, y1, x2, y2 = face_box
        face_region = frame[y1:y2, x1:x2]

        # Run InsightFace on cropped region
        faces = self.app.get(face_region)

        if len(faces) == 0:
            return None

        face = faces[0]
        landmarks = face.landmark_2d_106

        # Shift landmark coordinates to full-frame reference
        landmarks[:, 0] += x1
        landmarks[:, 1] += y1

        # Extract the 6 facial points needed
        image_points = self._select_points(landmarks)

        # Camera model (approx identity)
        h, w = frame.shape[:2]
        focal_length = w
        camera_center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, camera_center[0]],
            [0, focal_length, camera_center[1]],
            [0, 0, 1]
        ], dtype=np.float32)

        dist_coeffs = np.zeros((4, 1))  # No lens distortion

        # Solve PnP
        success, rotation_vec, translation_vec = cv2.solvePnP(
            self.model_points_68,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        # Convert rotation vector to yaw/pitch/roll
        rmat, _ = cv2.Rodrigues(rotation_vec)
        sy = np.sqrt(rmat[0, 0]**2 + rmat[1, 0]**2)

        yaw = np.arctan2(rmat[2, 1], rmat[2, 2]) * 180 / np.pi
        pitch = np.arctan2(-rmat[2, 0], sy) * 180 / np.pi
        roll = np.arctan2(rmat[1, 0], rmat[0, 0]) * 180 / np.pi

        return {
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "rotation_vector": rotation_vec,
            "translation_vector": translation_vec,
            "landmarks_2d": landmarks,
            "face_box": face_box
        }
