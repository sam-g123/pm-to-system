# src/focus_detection/face_detection.py

import torch
import cv2
import numpy as np
from pathlib import Path

import sys

# Add yolov7 directory to Python path
YOLOV7_ROOT = Path(__file__).parent / "yolov7"
sys.path.insert(0, str(YOLOV7_ROOT))


from .yolov7.utils.general import non_max_suppression, scale_coords
from .yolov7.utils.datasets import letterbox
from .yolov7.models.experimental import attempt_load

class FaceDetector:
    def __init__(self, 
                 model_path: str = None,
                 conf_threshold: float = 0.25,
                 iou_threshold: float = 0.45,
                 device: str = "cpu"):
        
        self.device = device
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        # Default model path
        if model_path is None:
            model_path = Path(__file__).parent / "models" / "best.pt"

        self.model_path = model_path

        # Load YOLOv7 model
        self.model = self._load_model()



    def _load_model(self):
        model = attempt_load(self.model_path, map_location=self.device)
        model = model.to(self.device)
        model.eval()
        return model



    def detect(self, image: np.ndarray):
        """Run YOLOv7 inference on an image."""
        img = image.copy()

        # Preprocess (letterbox resize)
        img_resized = letterbox(img, 640, stride=32)[0]
        img_resized = img_resized[:, :, ::-1].transpose(2, 0, 1)  # BGR→RGB & HWC→CHW
        img_resized = np.ascontiguousarray(img_resized)

        img_tensor = torch.from_numpy(img_resized).float().to(self.device)
        img_tensor /= 255.0
        img_tensor = img_tensor.unsqueeze(0)  # add batch dim

        # Inference
        with torch.no_grad():
            pred = self.model(img_tensor)[0]

        # Apply NMS
        detections = non_max_suppression(
            pred,
            self.conf_threshold,
            self.iou_threshold
        )[0]

        results = []
        if detections is not None and len(detections):
            detections[:, :4] = scale_coords(
                img_tensor.shape[2:], detections[:, :4], img.shape
            ).round()

            for *xyxy, conf, cls in detections:
                x1, y1, x2, y2 = map(int, xyxy)
                results.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": float(conf),
                    "class_id": int(cls)
                })

        return results
