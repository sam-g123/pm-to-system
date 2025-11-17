"""
focus_widget.py

UI widget for displaying real-time focus detection metrics.
Shows current face detection, attention state, and eye metrics.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

import threading
from src.focus_detection.pipeline import FocusPipeline
from src.scoring import ProductivityScoring


class FocusWidget(QWidget):
    """Widget for displaying real-time focus detection metrics."""

    def __init__(self, scoring: ProductivityScoring = None):
        super().__init__()
        self.pipeline = None
        # Use shared scoring instance if provided, otherwise create a local one
        self.scoring = scoring if scoring is not None else ProductivityScoring()
        self.frame_count = 0
        self.init_ui()
        
        # Start the pipeline with a callback
        try:
            self.start_pipeline()
        except Exception as e:
            self.status_label.setText(f"Error starting pipeline: {e}")

    def init_ui(self):
        """Initialize the UI layout."""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Real-time Focus Detection")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Status section
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Initializing...")
        status_layout.addWidget(self.status_label)
        
        status_frame.setLayout(status_layout)
        main_layout.addWidget(status_frame)
        
        # Current frame metrics
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        metrics_layout = QVBoxLayout()
        
        metrics_title = QLabel("Current Frame Metrics")
        metrics_title_font = QFont()
        metrics_title_font.setBold(True)
        metrics_title.setFont(metrics_title_font)
        metrics_layout.addWidget(metrics_title)
        
        self.frame_id_label = QLabel("Frame ID: 0")
        self.face_count_label = QLabel("Faces Detected: 0")
        self.attention_label = QLabel("Attention: Unknown")
        self.ear_label = QLabel("Eye Aspect Ratio: 0.00")
        self.head_pose_label = QLabel("Head Pose: Yaw=0°, Pitch=0°")
        self.fps_label = QLabel("FPS: 0.0")
        
        metrics_layout.addWidget(self.frame_id_label)
        metrics_layout.addWidget(self.face_count_label)
        metrics_layout.addWidget(self.attention_label)
        metrics_layout.addWidget(self.ear_label)
        metrics_layout.addWidget(self.head_pose_label)
        metrics_layout.addWidget(self.fps_label)
        
        metrics_frame.setLayout(metrics_layout)
        main_layout.addWidget(metrics_frame)
        
        # Statistics section
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        stats_layout = QVBoxLayout()
        
        stats_title = QLabel("Session Statistics")
        stats_title_font = QFont()
        stats_title_font.setBold(True)
        stats_title.setFont(stats_title_font)
        stats_layout.addWidget(stats_title)
        
        self.total_frames_label = QLabel("Total Frames: 0")
        self.attentive_frames_label = QLabel("Attentive Frames: 0")
        
        stats_layout.addWidget(self.total_frames_label)
        stats_layout.addWidget(self.attentive_frames_label)
        
        stats_frame.setLayout(stats_layout)
        main_layout.addWidget(stats_frame)
        
        main_layout.addStretch()
        self.setLayout(main_layout)

    def start_pipeline(self):
        """Start the focus detection pipeline."""
        def frame_callback(output):
            """Callback for each processed frame."""
            # Add to scoring engine
            self.scoring.add_frame_from_pipeline(output)
            
            # Update display
            self.update_frame_display(output)
            
            self.frame_count += 1
        # Initialize pipeline (constructor opens camera and models)
        self.pipeline = FocusPipeline(
            source=0,  # Default camera
            device="cpu",
            output_callback=frame_callback,
            fps_window=30,
            source_type="camera",
        )

        # Run the pipeline in a background thread so it doesn't block the Qt event loop
        try:
            self.pipeline_thread = threading.Thread(
                target=self.pipeline.run,
                kwargs={"num_frames": None},
                daemon=True,
            )
            self.pipeline_thread.start()
            self.status_label.setText("✅ Pipeline active - processing frames...")
        except Exception as e:
            self.status_label.setText(f"Error starting pipeline thread: {e}")

    def update_frame_display(self, output: dict):
        """Update display with current frame data."""
        try:
            # Frame info
            frame_id = output.get("frame_id", 0)
            face_count = output.get("face_count", 0)
            
            self.frame_id_label.setText(f"Frame ID: {frame_id}")
            self.face_count_label.setText(f"Faces Detected: {face_count}")
            
            # Metrics from primary face
            primary = output.get("primary")
            if primary:
                attention = primary.get("attention", "unknown")
                left_ear = primary.get("left_ear", 0.0)
                right_ear = primary.get("right_ear", 0.0)
                avg_ear = (left_ear + right_ear) / 2
                yaw = primary.get("yaw", 0.0)
                pitch = primary.get("pitch", 0.0)
                mar = primary.get("mar", 0.0)

                # Update labels with color coding
                attention_color = "🟢" if attention == "attentive" else "🔴"
                self.attention_label.setText(f"Attention: {attention_color} {attention.upper()}")
                self.ear_label.setText(f"Eye Aspect Ratio: {avg_ear:.3f}")
                self.head_pose_label.setText(f"Head Pose: Yaw={yaw:.1f}°, Pitch={pitch:.1f}°")
            else:
                self.attention_label.setText("Attention: No face detected")
                self.ear_label.setText("Eye Aspect Ratio: N/A")
                self.head_pose_label.setText("Head Pose: N/A")
            
            # FPS
            debug = output.get("debug", {})
            fps = debug.get("proc_fps", 0.0)
            self.fps_label.setText(f"FPS: {fps:.1f}")
            
            # Update statistics
            session = self.scoring.get_session_metrics()
            self.total_frames_label.setText(f"Total Frames: {session.total_frames}")
            self.attentive_frames_label.setText(f"Attentive Frames: {session.total_attentive_frames}")
            
        except Exception as e:
            print(f"Error updating frame display: {e}")

    def closeEvent(self, event):
        """Clean up when widget is closed."""
        if self.pipeline:
            self.pipeline.cleanup()
        event.accept()
