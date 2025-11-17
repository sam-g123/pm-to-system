# src/focus_detection/pipeline.py
"""
pipeline.py

Headless pipeline that processes video frames for focus detection without Qt visualization.
Runs the FocusAnalyzer and outputs structured data ready for the scoring module,
with terminal output for testing and FPS monitoring.

This module replaces the original Qt window-based approach with a headless design that:
- Processes frames from camera input OR video files
- Produces scoring-ready output per frame
- Prints metrics to terminal for debugging and optimization
- Tracks and displays FPS for performance monitoring
"""

import sys
import time
import os
from typing import Any, Callable, Dict, List, Optional, Union
from collections import deque

import cv2
import numpy as np

from .focus_analyzer import FocusAnalyzer


class FocusPipeline:
    """
    Headless focus detection pipeline that processes video frames and outputs
    structured data suitable for the scoring module.
    """

    def __init__(
        self,
        source: Union[int, str] = 0,
        device: str = "cpu",
        output_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        fps_window: int = 30,
        source_type: str = "camera",
    ):
        """
        Initialize the headless focus detection pipeline.

        Args:
            source: Camera index (int) or video file path (str)
            device: Device to run models on ('cpu' or 'cuda')
            (landmark skipping removed) landmarks are processed every frame for accuracy
            output_callback: Optional callback function for processed frames
            fps_window: Number of frames for FPS averaging
            source_type: 'camera' for webcam or 'video' for video files (auto-detected if not specified)
        """
        self.source = source
        self.device = device
        self.output_callback = output_callback
        self.fps_window = fps_window
        
        # Auto-detect source type if not specified
        if source_type == "auto":
            if isinstance(source, int):
                self.source_type = "camera"
            elif isinstance(source, str) and os.path.isfile(source):
                self.source_type = "video"
            else:
                raise ValueError(f"Invalid source: {source}")
        else:
            self.source_type = source_type

        # Initialize analyzer (landmarks processed every frame)
        self.analyzer = FocusAnalyzer(device=device)

        # Print diagnostic info about detector
        try:
            rep = getattr(self.analyzer, "detector").report()
            print(">>> Pipeline startup model report:", rep)
        except Exception as e:
            print(">>> Pipeline: failed to report detector info:", e)

        # Open video capture (camera or file)
        self.cap = self._open_source()
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open {self.source_type} source: {self.source}")

        # Get video properties
        self.fps_source = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # FPS tracking
        self._frame_times = deque(maxlen=fps_window)
        self._fps_smooth = None
        self._last_display_time = time.time()
        self._frame_count = 0

        print(f"Pipeline initialized:")
        print(f"  Source: {self.source_type} (source={self.source})")
        print(f"  Device: {device}")
        print(f"  Landmark processing: every frame (skipping disabled for accuracy)")
        if self.source_type == "video":
            print(f"  Video properties: {self.frame_width}x{self.frame_height}, "
                  f"{self.fps_source:.1f} FPS, {self.total_frames} frames")

    def _open_source(self) -> cv2.VideoCapture:
        """
        Open video capture from camera or file.

        Returns:
            cv2.VideoCapture object
        """
        if self.source_type == "camera":
            if not isinstance(self.source, int):
                raise ValueError(f"Camera source must be int, got {type(self.source)}")
            print(f"Opening camera index {self.source}...")
            return cv2.VideoCapture(self.source)
        
        elif self.source_type == "video":
            if not isinstance(self.source, str):
                raise ValueError(f"Video source must be str, got {type(self.source)}")
            
            if not os.path.isfile(self.source):
                raise FileNotFoundError(f"Video file not found: {self.source}")
            
            print(f"Opening video file: {self.source}...")
            return cv2.VideoCapture(self.source)
        
        else:
            raise ValueError(f"Unknown source_type: {self.source_type}")

    def _prepare_scoring_output(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform the raw analysis result into the format expected by the scoring module.

        Args:
            analysis_result: Raw output from FocusAnalyzer.analyze_frame()

        Returns:
            Dictionary formatted for scoring module consumption
        """
        output = {
            "timestamp": analysis_result.get("timestamp"),
            "frame_id": analysis_result.get("frame_id"),
            "face_count": analysis_result.get("face_count", 0),
            "face_detected": analysis_result.get("face_count", 0) > 0,
            "faces": [],
            "debug": analysis_result.get("debug", {}),
        }

        # Process each detected face
        for face in analysis_result.get("faces", []):
            face_output = {
                "bbox": face.get("bbox"),
                "confidence": face.get("confidence"),
                "yaw": face.get("yaw"),
                "pitch": face.get("pitch"),
                "roll": face.get("roll"),
                "left_ear": face.get("left_ear"),
                "right_ear": face.get("right_ear"),
                "eyes_open_left": face.get("eyes_open_left"),
                "eyes_open_right": face.get("eyes_open_right"),
                "blink_count": face.get("blink_count"),
                "attention": face.get("attention"),
                "left_gaze": face.get("left_gaze"),
                "right_gaze": face.get("right_gaze"),
                "mar": face.get("mar"),
                "mouth_open": face.get("mouth_open"),
                "yawn_count": face.get("yawn_count"),
            }
            output["faces"].append(face_output)

        # Add primary face if available
        if output["faces"]:
            # Select the face with largest bounding box area
            largest_idx = 0
            largest_area = 0
            for idx, face in enumerate(output["faces"]):
                bbox = face.get("bbox", (0, 0, 0, 0))
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                if area > largest_area:
                    largest_area = area
                    largest_idx = idx
            output["primary"] = output["faces"][largest_idx]
        else:
            output["primary"] = None

        return output

    def _update_fps(self, frame_time: float) -> Optional[float]:
        """
        Update FPS tracking and return smoothed FPS value.

        Args:
            frame_time: Time taken to process the frame

        Returns:
            Smoothed FPS value or None if not enough samples
        """
        if frame_time > 0:
            self._frame_times.append(frame_time)

        if len(self._frame_times) < 3:
            return None

        avg_time = sum(self._frame_times) / len(self._frame_times)
        fps = 1.0 / max(avg_time, 1e-6)

        if self._fps_smooth is None:
            self._fps_smooth = fps
        else:
            self._fps_smooth = 0.9 * self._fps_smooth + 0.1 * fps

        return self._fps_smooth

    def _print_frame_output(self, output: Dict[str, Any]) -> None:
        """
        Print frame processing results to terminal for testing.

        Args:
            output: Processed frame output from scoring format
        """
        fps = output.get("debug", {}).get("proc_fps", 0)
        proc_time = output.get("debug", {}).get("proc_time", 0)
        frame_id = output.get("frame_id", 0)

        if output.get("primary"):
            primary = output["primary"]
            attention = primary.get("attention", "unknown")
            yaw = primary.get("yaw", 0.0)
            pitch = primary.get("pitch", 0.0)
            left_ear = primary.get("left_ear", 0.0)
            right_ear = primary.get("right_ear", 0.0)
            blink_count = primary.get("blink_count", 0)
            yawn_count = primary.get("yawn_count", 0)

            print(
                f"[{frame_id:04d}] FACES={output['face_count']} | "
                f"ATTN={attention:15s} | "
                f"YAW={yaw:6.1f}° | "
                f"PITCH={pitch:6.1f}° | "
                f"EAR_L={left_ear:.2f} | "
                f"EAR_R={right_ear:.2f} | "
                f"BLINK={blink_count:3d} | "
                f"YAWN={yawn_count:3d} | "
                f"TIME={proc_time*1000:.1f}ms | "
                f"FPS={fps:5.1f}"
            )
        else:
            print(
                f"[{frame_id:04d}] FACES=0 | "
                f"TIME={proc_time*1000:.1f}ms | "
                f"FPS={fps:5.1f}"
            )

    def process_frame(self) -> Optional[Dict[str, Any]]:
        """
        Capture and process a single frame.

        Returns:
            Processed output in scoring format, or None if frame capture failed
        """
        t_cap_start = time.time()
        ret, frame = self.cap.read()
        t_cap_end = time.time()
        
        if not ret:
            print("Warning: Failed to read frame from camera")
            return None

        # Measure processing time
        t0 = time.time()

        # Analyze the frame
        raw_result = self.analyzer.analyze_frame(frame, return_all=True)

        t1 = time.time()
        proc_time = max(1e-6, (t1 - t0))
        cap_time = t_cap_end - t_cap_start

        # Update FPS
        fps = self._update_fps(proc_time)

        # Add FPS to debug info
        raw_result["debug"] = {
            "proc_fps": float(fps) if fps is not None else 0.0,
            "proc_time": float(proc_time),
            "capture_time": float(cap_time),
        }

        # Transform to scoring format
        output = self._prepare_scoring_output(raw_result)
        output["debug"] = raw_result["debug"]

        # Print output to terminal
        self._print_frame_output(output)

        # Call user callback if provided
        if self.output_callback:
            try:
                self.output_callback(output)
            except Exception as e:
                print(f"Error in output callback: {e}")

        return output

    def run(self, num_frames: Optional[int] = None) -> None:
        """
        Run the pipeline, processing frames until interrupted.

        Args:
            num_frames: Maximum number of frames to process (None = infinite)
        """
        self._frame_count = 0

        try:
            print("\n" + "=" * 120)
            print("Starting focus detection pipeline (headless mode)")
            print("=" * 120)
            print("Press Ctrl+C to stop\n")

            while num_frames is None or self._frame_count < num_frames:
                output = self.process_frame()
                if output is None:
                    break
                self._frame_count += 1

        except KeyboardInterrupt:
            print("\n" + "=" * 120)
            print(f"Pipeline interrupted after {self._frame_count} frames")
            print("=" * 120)
        except Exception as e:
            print(f"Error during pipeline execution: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Release camera/video resources."""
        try:
            if self.cap.isOpened():
                self.cap.release()
                source_name = "camera" if self.source_type == "camera" else "video"
                print(f"{source_name.capitalize()} released")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()


def main():
    """
    Main entry point for running the pipeline from command line.

    Examples:
        # Use default camera
        python -m src.focus_detection.pipeline
        
        # Use specific camera
        python -m src.focus_detection.pipeline --camera 1
        
        # Use video file
        python -m src.focus_detection.pipeline --video src/focus_detection/videos/sample.mp4
        
        # Use GPU
        python -m src.focus_detection.pipeline --device cuda
        
        # Process 100 frames from video
        python -m src.focus_detection.pipeline --video src/focus_detection/videos/sample.mp4 --frames 100
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Headless focus detection pipeline for scoring module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Real-time camera processing (default)
  python -m src.focus_detection.pipeline

  # Specific camera
  python -m src.focus_detection.pipeline --camera 1

  # Video file processing
  python -m src.focus_detection.pipeline --video src/focus_detection/videos/sample.mp4

  # GPU acceleration
  python -m src.focus_detection.pipeline --device cuda

  # Video with GPU
  python -m src.focus_detection.pipeline --video src/focus_detection/videos/sample.mp4 --device cuda --landmark-skip 4

  # Process only 100 frames
  python -m src.focus_detection.pipeline --video src/focus_detection/videos/sample.mp4 --frames 100
        """
    )
    
    # Source selection (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--camera",
        type=int,
        default=None,
        help="Camera index to use (default: 0). Example: --camera 0 or --camera 1",
    )
    source_group.add_argument(
        "--video",
        type=str,
        default=None,
        help="Path to video file. Example: --video src/focus_detection/videos/sample.mp4",
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to run models on (default: cpu)",
    )
    # landmark skipping removed: landmarks are processed every frame for accuracy
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Maximum number of frames to process (default: all frames)",
    )

    args = parser.parse_args()

    # Determine source
    if args.video:
        source = args.video
        source_type = "video"
    elif args.camera is not None:
        source = args.camera
        source_type = "camera"
    else:
        # Default to camera 0
        source = 0
        source_type = "camera"

    # Optional: Define a custom callback for consuming the output
    def custom_callback(output: Dict[str, Any]) -> None:
        """Example callback for further processing."""
        if output.get("primary"):
            # Could send to scoring module here
            pass

    pipeline = FocusPipeline(
        source=source,
        device=args.device,
        output_callback=None,  # Set to custom_callback if needed
        fps_window=30,
        source_type=source_type,
    )

    pipeline.run(num_frames=args.frames)


if __name__ == "__main__":
    main()
