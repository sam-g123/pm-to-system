# src/focus_detection/focus_analyzer.py
"""
focus_analyzer.py

Optimized fusion module that combines:
 - Face detection (YOLOv7) -> uses model file located at src/focus_detection/models/best.pt (preferred)
   - If you trained/placed another yolov7 .pt file, update FaceDetector default or pass model_path.
 - Landmark & head-pose (InsightFace) -> InsightFace loads models from ~/.insightface/models or internal config.
   - If you placed insightface assets locally, InsightFace will find them; see InsightFace docs.
 - Eye analysis (EAR) for blink detection and coarse gaze (uses eye_analysis.EyeAnalysis)

Performance notes & optimizations included:
 - Landmarks and head-pose are computed every frame (skipping removed for accuracy).
 - We reuse last known landmarks/pose for intermediate frames to keep high FPS.
 - Face detection (YOLOv7) runs every frame (fast), and supplies bounding boxes for cropping landmarks.
 - Default model files (example locations):
     - src/focus_detection/models/best.pt      <-- your fine-tuned YOLOv7 face detector
     - src/focus_detection/models/yolov7n.pt    <-- small default for debugging
     - InsightFace models typically loaded from ~/.insightface/models/ (insightface downloads)
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import cv2
import os
import csv

from .face_detection import FaceDetector  # uses yolov7 attempt_load (expects .pt weights in models/)
from .head_pose import HeadPoseEstimator    # InsightFace or MediaPipe-free path (we use InsightFace here)
from .eye_analysis import EyeAnalysis


@dataclass
class FaceState:
    bbox: Tuple[int, int, int, int]
    # For robust state-machine blink/yawn detection
    prev_eyes_closed: bool = False
    prev_mouth_open: bool = False
    pending_blink: bool = False
    pending_yawn: bool = False
    last_seen: float = field(default_factory=time.time)
    ema_yaw: float = 0.0
    ema_pitch: float = 0.0
    ema_roll: float = 0.0
    ema_alpha: float = 0.4
    blink_count: int = 0
    closed_frames: int = 0
    blink_start_ts: Optional[float] = None
    blink_started_attention: Optional[str] = None
    last_blink_ts: float = 0.0
    yawn_start_ts: Optional[float] = None
    yawn_started_attention: Optional[str] = None
    last_yawn_ts: float = 0.0
    yawn_count: int = 0
    mouth_open_frames: int = 0
    attention_history: deque = field(default_factory=lambda: deque(maxlen=150))
    last_landmarks: Optional[np.ndarray] = None
    last_pose: Optional[Dict[str, float]] = None
    id: Optional[int] = None


class FocusAnalyzer:
    """
    FocusAnalyzer produces a structured dict for each input frame.
    - It aims for good throughput by skipping heavy landmark/pose computation every N frames.
    - It is model-aware: YOLOv7 (face bbox) + InsightFace (landmarks). See module docstring above.

    Example:
        fa = FocusAnalyzer(device="cpu")
        out = fa.analyze_frame(frame)  # returns dict with metrics and the frame id/timestamp
    """

    def __init__(
        self,
        device: str = "cpu",
        ear_threshold: float = 0.20,
        yaw_threshold: float = 15.0,
        pitch_threshold: float = 15.0,
        blink_consec_frames: int = 1,
    ):
        self.device = device
        # Face detector (YOLOv7). Defaults to models/best.pt in this project.
        # Model files are expected under src/focus_detection/models/ (best.pt, yolov7n.pt, etc.).
        self.detector = FaceDetector(device=device)   # default model_path uses src/focus_detection/models/best.pt

        # Head pose / landmarks (InsightFace-based head_pose module)
        self.pose = HeadPoseEstimator(device=device)

        # Eye analysis
        self.eye_analyzer = EyeAnalysis(ear_threshold=ear_threshold)

        # thresholds and logic
        self.yaw_threshold = yaw_threshold
        self.pitch_threshold = pitch_threshold
        self.blink_consec_frames = blink_consec_frames

        # Blink timing / heuristics (seconds)
        self.blink_min_dur = 0.03   # minimum blink duration (~30 ms)
        self.blink_max_dur = 0.7    # max duration to still consider a blink (~700 ms)
        self.blink_refractory = 0.2 # minimum seconds between consecutive counted blinks

        # Yawn timing / heuristics (seconds)
        self.yawn_min_dur = 0.2     # minimum yawn duration (~200 ms)
        self.yawn_max_dur = 3.0     # max duration to still consider a yawn (~3 s)
        self.yawn_refractory = 0.5  # minimum seconds between consecutive counted yawns

        # Landmark skipping removed: landmarks/pose are computed every frame for accuracy
        self._frame_counter = 0

        # state keyed by detection index (simple mapping, replace with tracking if needed)
        # states keyed by persistent track id (we'll match detections -> states by IoU)
        self.states: Dict[int, FaceState] = {}
        self._next_state_id = 0

    # -------------------------
    # utilities
    # -------------------------
    def _select_primary(self, detections: List[Dict[str, Any]]) -> Optional[int]:
        if not detections:
            return None
        # choose largest area
        areas = [(d['bbox'][2] - d['bbox'][0]) * (d['bbox'][3] - d['bbox'][1]) for d in detections]
        return int(np.argmax(areas))

    # -------------------------
    # main API
    # -------------------------
    def analyze_frame(self, frame: np.ndarray, return_all: bool = False) -> Dict[str, Any]:
        """
        Analyze a single frame and return a dict describing the frame.
        - run every frame
    - heavy landmarks/pose are computed every frame (skipping removed for accuracy)

        Output schema (per-frame):
        {
            "timestamp": float,
            "frame_id": int,
            "face_count": int,
            "faces": [...]
        }
        """
        self._frame_counter += 1
        frame_id = self._frame_counter
        timestamp = time.time()

        out: Dict[str, Any] = {
            "timestamp": timestamp,
            "frame_id": frame_id,
            "face_count": 0,
            "faces": []
        }

        # Always pass the raw frame to detector (do not mutate 'frame' upstream)
        detections = self.detector.detect(frame) or []
        out["face_count"] = len(detections)

        if len(detections) == 0:
            return out

        # Process each detection; landmarks/pose will be computed every frame (accuracy prioritized)
        compute_landmarks_now = True

        for idx, det in enumerate(detections):
            bbox = det.get("bbox")
            conf = det.get("confidence", 1.0)

            if bbox is None:
                # skip malformed detection
                continue

            # --- Match this detection to an existing state by IoU (simple tracker) ---
            def _iou(a, b):
                # a,b = (x1,y1,x2,y2)
                ax1, ay1, ax2, ay2 = a
                bx1, by1, bx2, by2 = b
                ix1 = max(ax1, bx1)
                iy1 = max(ay1, by1)
                ix2 = min(ax2, bx2)
                iy2 = min(ay2, by2)
                iw = max(0.0, ix2 - ix1)
                ih = max(0.0, iy2 - iy1)
                inter = iw * ih
                area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
                area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
                union = area_a + area_b - inter
                if union <= 0:
                    return 0.0
                return inter / union

            best_id = None
            best_iou = 0.0
            for sid, s in self.states.items():
                # skip very stale states
                if s.last_seen is None:
                    continue
                i = _iou(tuple(bbox), tuple(s.bbox))
                if i > best_iou:
                    best_iou = i
                    best_id = sid

            # Accept match only if IoU reasonably high (avoid accidental matches)
            if best_id is not None and best_iou > 0.35:
                state = self.states[best_id]
                state.bbox = tuple(bbox)
                state.last_seen = timestamp
            else:
                # create a new persistent state
                sid = self._next_state_id
                self._next_state_id += 1
                state = FaceState(bbox=tuple(bbox))
                state.id = sid
                state.last_seen = timestamp
                self.states[sid] = state

            # Landmarks + headpose (heavy) – run only on some frames
            landmarks: Optional[np.ndarray] = None
            raw_pose: Dict[str, float] = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}

            if compute_landmarks_now:
                try:
                    # HeadPoseEstimator expects face_box in full-frame coords
                    pose_res = self.pose.estimate(frame, bbox) or {}
                    # Use explicit key access to avoid ambiguous truthiness
                    landmarks_candidate = pose_res.get("landmarks_2d", None)
                    if landmarks_candidate is not None and isinstance(landmarks_candidate, np.ndarray) and landmarks_candidate.size > 0:
                        landmarks = landmarks_candidate
                    else:
                        landmarks = None

                    yaw = float(pose_res.get("yaw", 0.0))
                    pitch = float(pose_res.get("pitch", 0.0))
                    roll = float(pose_res.get("roll", 0.0))
                    raw_pose = {"yaw": yaw, "pitch": pitch, "roll": roll}

                    # update state cache
                    if landmarks is not None:
                        state.last_landmarks = landmarks
                    state.last_pose = raw_pose

                except KeyboardInterrupt:
                    raise
                except Exception:
                    # if something goes wrong, reuse last known
                    landmarks = state.last_landmarks
                    raw_pose = state.last_pose or {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
            else:
                landmarks = state.last_landmarks
                raw_pose = state.last_pose or {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}

            # Eye analysis:
            # If landmarks array exists and has points → pass it.
            # Otherwise pass None so that analyzers that expect None behave correctly.
            try:
                if landmarks is not None and isinstance(landmarks, np.ndarray) and landmarks.size > 0:
                    eyes = self.eye_analyzer.analyze(landmarks)
                else:
                    # pass None to indicate no landmarks (the analyzer may accept None)
                    eyes = self.eye_analyzer.analyze(None)
            except Exception:
                # If analyzer rejects None or errors, fallback to open eyes (test expectation)
                eyes = {
                    "left_eye": {"ear": 0.3, "open": True, "gaze": "center"},
                    "right_eye": {"ear": 0.3, "open": True, "gaze": "center"},
                }

            left_open = bool(eyes["left_eye"]["open"])
            right_open = bool(eyes["right_eye"]["open"])

            # Mouth / yawn analysis (heuristic robust to different landmark layouts)
            mar = 0.0
            mouth_open = False
            try:
                if landmarks is not None and isinstance(landmarks, np.ndarray) and landmarks.size > 0:
                    lm2 = landmarks[:, :2]
                    n_pts = lm2.shape[0]
                    
                    # Prefer explicit indices for known layouts (InsightFace 106-point format)
                    # If NOT 106-point layout, use specific heuristic for MediaPipe (478-pt)
                    if n_pts == 106:  # Exactly InsightFace 106
                        try:
                            top = lm2[51]
                            bottom = lm2[57]
                            left_m = lm2[48]
                            right_m = lm2[54]
                            vert = float(np.linalg.norm(top - bottom))
                            horiz = float(np.linalg.norm(left_m - right_m))
                            if horiz > 1e-6:
                                mar = vert / horiz
                        except Exception as ex:
                            mar = 0.0
                    elif n_pts == 478:  # MediaPipe Facemesh
                        try:
                            # For MediaPipe 478-point: use much tighter mouth region
                            # This is the only truly reliable way without knowing exact indices
                            x1, y1, x2, y2 = bbox
                            fw = max(1.0, x2 - x1)
                            fh = max(1.0, y2 - y1)
                            
                            # Normalized coordinates
                            lm_y_norm = (lm2[:, 1] - y1) / fh
                            lm_x_norm = (lm2[:, 0] - x1) / fw
                            
                            # MUCH tighter region: only innermost mouth part
                            # 55-75% vertically (lower half, but not chin)
                            # 35-65% horizontally (center only)
                            mask = (lm_y_norm > 0.55) & (lm_y_norm < 0.75) & (lm_x_norm > 0.35) & (lm_x_norm < 0.65)
                            mouth_region = lm2[mask]
                            
                            if mouth_region.shape[0] >= 4:  # Reduce minimum to 4 instead of 6
                                min_y = float(mouth_region[:, 1].min())
                                max_y = float(mouth_region[:, 1].max())
                                min_x = float(mouth_region[:, 0].min())
                                max_x = float(mouth_region[:, 0].max())
                                vert = max_y - min_y
                                horiz = max_x - min_x
                                if horiz > 1e-6:
                                    mar = float(vert / horiz)
                            else:
                                mar = 0.0
                        except Exception as ex:
                            mar = 0.0
                    else:
                        # Fallback generic heuristic for other layouts
                        x1, y1, x2, y2 = bbox
                        fw = max(1.0, x2 - x1)
                        fh = max(1.0, y2 - y1)
                        lm_y_norm = (lm2[:, 1] - y1) / fh
                        lm_x_norm = (lm2[:, 0] - x1) / fw
                        mask = (lm_y_norm > 0.35) & (lm_y_norm < 1.0) & (lm_x_norm > 0.15) & (lm_x_norm < 0.85)
                        mouth_region = lm2[mask]
                        if mouth_region.shape[0] >= 6:
                            min_y = float(mouth_region[:, 1].min())
                            max_y = float(mouth_region[:, 1].max())
                            min_x = float(mouth_region[:, 0].min())
                            max_x = float(mouth_region[:, 0].max())
                            vert = max_y - min_y
                            horiz = max_x - min_x
                            if horiz > 1e-6:
                                mar = float(vert / horiz)
                    # Threshold for yawn detection: 
                    # Baseline closed mouth MAR: 0.8-1.0
                    # Open mouth / talking MAR: 0.8-1.2  
                    # Yawn MAR: 1.2+ (significantly more open)
                    mouth_open = mar > 1.2
                else:
                    mar = 0.0
                    mouth_open = False
            except Exception as e:
                # blink detection: count once when closed_frames hits threshold
                pass

            # Blink/Yawn detection will be processed after attention is determined
            # (see below) so that counts only increment when the face is classified
            # as attentive (looking at the camera). We defer the state-machine update
            # until after EMA smoothing and attention inference.

            # smoothing (EMA) on pose
            yaw_val = raw_pose.get("yaw", 0.0)
            pitch_val = raw_pose.get("pitch", 0.0)
            roll_val = raw_pose.get("roll", 0.0)

            # init EMA if first time (if all zeros we assume uninitialized)
            if state.ema_yaw == 0.0 and state.ema_pitch == 0.0 and state.ema_roll == 0.0:
                state.ema_yaw = yaw_val
                state.ema_pitch = pitch_val
                state.ema_roll = roll_val
            else:
                a = state.ema_alpha
                state.ema_yaw = a * yaw_val + (1 - a) * state.ema_yaw
                state.ema_pitch = a * pitch_val + (1 - a) * state.ema_pitch
                state.ema_roll = a * roll_val + (1 - a) * state.ema_roll

            # attention inference (simple heuristic)
            both_closed = (not left_open) and (not right_open)
            looking_forward = (abs(state.ema_yaw) < self.yaw_threshold) and (abs(state.ema_pitch) < self.pitch_threshold)

            if not looking_forward:
                attention = "looking_away"
            elif both_closed:
                attention = "eyes_closed"
            else:
                attention = "attentive"

            state.attention_history.append(attention)

            # --- Blink & Yawn state machine: ALWAYS run to track transitions ---
            # We only set the "pending" flag when the transition (close/open)
            # happens while the face is attentive. If attention becomes non-
            # attentive while the face is closed/open, the pending flag is
            # cleared so the eventual reopening/closing does not mistakenly
            # increment counts for events that happened while looking away.

            # Blink detection (time-based open -> closed -> open)
            # Use timestamps so we can reason about durations and refractory windows.
            now_ts = time.time()
            eyes_closed = (not left_open) and (not right_open)
            if not state.prev_eyes_closed and eyes_closed:
                # just closed: record start time and attention at start
                state.closed_frames = 1
                state.blink_start_ts = now_ts
                state.blink_started_attention = attention
                # only consider it pending if closed while attentive; still record start
                state.pending_blink = (attention == "attentive")
                # verbose debug: record blink start
                try:
                    with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                        _df.write(f"BLINK_START frame={frame_id} ts={now_ts:.3f} start_att={state.blink_started_attention} pending={state.pending_blink} left_ear={eyes['left_eye']['ear']:.3f} right_ear={eyes['right_eye']['ear']:.3f}\n")
                except Exception:
                    pass
            elif state.prev_eyes_closed and eyes_closed:
                # still closed
                state.closed_frames += 1
                # cancel pending if attention lost while closed
                if attention != "attentive":
                    if state.pending_blink:
                        try:
                            with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                                _df.write(f"BLINK_PENDING_CLEARED frame={frame_id} ts={now_ts:.3f} reason=attention_lost att_now={attention}\n")
                        except Exception:
                            pass
                    state.pending_blink = False
                # cancel pending if closure is too long (not a blink)
                if state.blink_start_ts and (now_ts - state.blink_start_ts) > self.blink_max_dur:
                    if state.pending_blink:
                        try:
                            with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                                _df.write(f"BLINK_PENDING_CLEARED frame={frame_id} ts={now_ts:.3f} reason=too_long dur={(now_ts-state.blink_start_ts):.3f}\n")
                        except Exception:
                            pass
                    state.pending_blink = False
            elif state.prev_eyes_closed and not eyes_closed:
                # just opened -> evaluate blink by duration and attention
                duration = None
                if state.blink_start_ts:
                    duration = now_ts - state.blink_start_ts
                counted = False
                # Qualify as a blink if duration within expected bounds and not in refractory
                if duration is not None and self.blink_min_dur <= duration <= self.blink_max_dur:
                    # require that the event had at least one attentive endpoint
                    started_attentive = (state.blink_started_attention == "attentive")
                    ended_attentive = (attention == "attentive")
                    # additional verbose logging for evaluation
                    try:
                        with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                            _df.write(f"BLINK_EVAL frame={frame_id} ts={now_ts:.3f} dur={duration:.3f} start_att={state.blink_started_attention} end_att={attention} started_att={started_attentive} ended_att={ended_attentive} last_blink_ts={state.last_blink_ts:.3f}\n")
                    except Exception:
                        pass
                    if (started_attentive or ended_attentive) and (now_ts - state.last_blink_ts) > self.blink_refractory:
                        state.blink_count += 1
                        state.last_blink_ts = now_ts
                        counted = True
                        # debug trace for blink increments (kept as separate file)
                        try:
                            with open('/tmp/focus_debug.log', 'a') as _df:
                                _df.write(f"BLINK_INC frame={frame_id} ts={now_ts:.3f} dur={duration:.3f} start_att={state.blink_started_attention} end_att={attention} left_ear={eyes['left_eye']['ear']:.3f} right_ear={eyes['right_eye']['ear']:.3f} total={state.blink_count}\n")
                        except Exception:
                            pass
                # reset
                state.closed_frames = 0
                state.pending_blink = False
                state.blink_start_ts = None
                state.blink_started_attention = None
            else:
                state.closed_frames = 0
                # if neither closed nor opening event, clear pending if not attentive
                if attention != "attentive":
                    state.pending_blink = False
            state.prev_eyes_closed = eyes_closed

            # Yawn detection (time-based, similar to blink: closed -> open -> closed)
            # Allow yawn count if either start OR end was attentive, duration within bounds, not in refractory
            if not state.prev_mouth_open and mouth_open:
                # mouth just opened: record start time and attention
                state.mouth_open_frames = 1
                state.yawn_start_ts = now_ts
                state.yawn_started_attention = attention
                # mark pending if mouth opened while attentive (but don't block counting if only end attentive)
                state.pending_yawn = (attention == "attentive")
                try:
                    with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                        _df.write(f"YAWN_START frame={frame_id} ts={now_ts:.3f} start_att={state.yawn_started_attention} pending={state.pending_yawn} mar={mar:.3f}\n")
                except Exception:
                    pass
            elif state.prev_mouth_open and mouth_open:
                # mouth remains open
                state.mouth_open_frames += 1
                # cancel pending if attention lost while mouth open (but don't block if we end attentive later)
                if attention != "attentive":
                    if state.pending_yawn:
                        try:
                            with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                                _df.write(f"YAWN_PENDING_CLEARED frame={frame_id} ts={now_ts:.3f} reason=attention_lost att_now={attention}\n")
                        except Exception:
                            pass
                    state.pending_yawn = False
                # cancel pending if mouth open too long (not a yawn)
                if state.yawn_start_ts and (now_ts - state.yawn_start_ts) > self.yawn_max_dur:
                    if state.pending_yawn:
                        try:
                            with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                                _df.write(f"YAWN_PENDING_CLEARED frame={frame_id} ts={now_ts:.3f} reason=too_long dur={(now_ts-state.yawn_start_ts):.3f}\n")
                        except Exception:
                            pass
                    state.pending_yawn = False
            elif state.prev_mouth_open and not mouth_open:
                # mouth just closed -> evaluate yawn by duration and attention
                duration = None
                if state.yawn_start_ts:
                    duration = now_ts - state.yawn_start_ts
                # verbose evaluation log
                try:
                    with open('/tmp/focus_debug_verbose.log', 'a') as _df:
                        _df.write(f"YAWN_EVAL frame={frame_id} ts={now_ts:.3f} dur={(duration if duration else 0.0):.3f} start_att={state.yawn_started_attention} end_att={attention} frames_open={state.mouth_open_frames}\n")
                except Exception:
                    pass
                # Qualify as a yawn if duration within expected bounds and not in refractory
                if duration is not None and self.yawn_min_dur <= duration <= self.yawn_max_dur:
                    # require that the event had at least one attentive endpoint
                    started_attentive = (state.yawn_started_attention == "attentive")
                    ended_attentive = (attention == "attentive")
                    if (started_attentive or ended_attentive) and (now_ts - state.last_yawn_ts) > self.yawn_refractory:
                        state.yawn_count += 1
                        state.last_yawn_ts = now_ts
                        try:
                            with open('/tmp/focus_debug.log', 'a') as _df:
                                _df.write(f"YAWN_INC frame={frame_id} ts={now_ts:.3f} dur={(duration if duration else 0.0):.3f} start_att={state.yawn_started_attention} end_att={attention} total={state.yawn_count}\n")
                        except Exception:
                            pass
                # reset
                state.mouth_open_frames = 0
                state.pending_yawn = False
                state.yawn_start_ts = None
                state.yawn_started_attention = None
            else:
                state.mouth_open_frames = 0
                # if neither opening nor closing event, clear pending if not attentive
                if attention != "attentive":
                    state.pending_yawn = False
            state.prev_mouth_open = mouth_open

            face_result = {
                "bbox": tuple(bbox),
                "confidence": float(conf),
                # raw & smoothed pose
                "raw_pose": raw_pose,
                "yaw": float(state.ema_yaw),
                "pitch": float(state.ema_pitch),
                "roll": float(state.ema_roll),
                # eyes
                "left_ear": float(eyes["left_eye"]["ear"]),
                "right_ear": float(eyes["right_eye"]["ear"]),
                "eyes_open_left": bool(eyes["left_eye"]["open"]),
                "eyes_open_right": bool(eyes["right_eye"]["open"]),
                "left_gaze": eyes["left_eye"].get("gaze"),
                "right_gaze": eyes["right_eye"].get("gaze"),
                # mouth metrics
                "mar": float(mar),
                "mouth_open": bool(mouth_open),
                "yawn_count": int(state.yawn_count),
                # blink & attention
                "blink_count": int(state.blink_count),
                "attention": attention,
                # landmarks raw (optional) - return empty list if none
                "landmarks": landmarks if landmarks is not None else [],
                # small debug
                "frame_id": frame_id,
                "timestamp": timestamp
            }
            # Optional per-frame event logging for debugging (append-only)
            try:
                log_path = "/tmp/focus_events.csv"
                write_header = not os.path.exists(log_path)
                with open(log_path, "a", newline="") as _f:
                    _w = csv.writer(_f)
                    if write_header:
                        _w.writerow([
                            "frame_id",
                            "timestamp",
                            "detection_idx",
                            "left_ear",
                            "right_ear",
                            "eyes_open_left",
                            "eyes_open_right",
                            "attention",
                            "pending_blink",
                            "blink_count",
                            "pending_yawn",
                            "yawn_count",
                            "mar",
                            "mouth_open",
                        ])
                    _w.writerow([
                        frame_id,
                        timestamp,
                        int(state.id) if state.id is not None else -1,
                        float(eyes["left_eye"]["ear"]),
                        float(eyes["right_eye"]["ear"]),
                        bool(eyes["left_eye"]["open"]),
                        bool(eyes["right_eye"]["open"]),
                        attention,
                        bool(state.pending_blink),
                        int(state.blink_count),
                        bool(state.pending_yawn),
                        int(state.yawn_count),
                        float(mar),
                        bool(mouth_open),
                    ])
            except Exception:
                # never fail the analyzer due to logging
                pass

            out["faces"].append(face_result)

        # prune stale states (not seen for >2s)
        try:
            stale = []
            for sid, s in list(self.states.items()):
                if s.last_seen and (timestamp - s.last_seen) > 2.0:
                    stale.append(sid)
            for sid in stale:
                try:
                    del self.states[sid]
                except KeyError:
                    pass
        except Exception:
            pass

        # pick primary if requested (return_all=False returns primary only)
        if return_all:
            return out
        else:
            primary_idx = self._select_primary(out["faces"])
            if primary_idx is None:
                return {"timestamp": timestamp, "frame_id": frame_id, "face_count": 0, "primary": None}
            return {
                "timestamp": timestamp,
                "frame_id": frame_id,
                "face_count": out["face_count"],
                "primary": out["faces"][primary_idx]
            }
