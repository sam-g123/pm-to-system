# Productivity Monitoring and Task Optimization System Documentation

## Overview

This system is a modular productivity tool leveraging machine learning (ML) and computer vision (CV) to monitor user focus, optimize task scheduling, and provide actionable productivity insights. It is designed for real-time desktop use, prioritizing user empowerment and privacy.

### Core Modules

1. **Focus Detection Engine** (`src/focus_detection/`)

   - Real-time CV pipeline using webcam input.
   - Detects and analyzes facial/body cues: head pose, eye gaze, blinks, and expressions.
   - Integrates MediaPipe and YOLOv7 for landmark and object detection.
   - Multimodal fusion combines CNN/MLP outputs for unified focus scoring.

2. **Intelligent Scheduling and Optimization** (`src/scheduling/`)

   - Parses tasks using NLP (SpaCy-based tokenization and custom NER).
   - Prioritizes tasks via supervised ML (Logistic Regression/SVM).
   - Dynamic scheduling using RL/optimization (TensorFlow/PyTorch).
   - Feedback loop integrates focus data to adapt scheduling.

3. **Productivity Scoring and Reporting** (`src/scoring/`)

   - Aggregates focus and scheduling data into productivity scores.
   - Uses weighted regression and clustering for insights.
   - Human-centered recommendations for empathetic productivity improvement.

4. **User Interface** (`src/ui/`)
   - Built with PyQt5 for a desktop experience.
   - Central window with tabs for each module.
   - Reusable widgets for focus dashboard, task list, and productivity scores.

## Directory Structure

- `README.md`: Project summary and setup instructions.
- `requirements.txt`, `requirements-dev.txt`: Dependency management.
- `install_requirements.py`: Automated installation script (use this, not pip directly).
- `src/`: Main source code.
  - `main.py`: Entry point; launches UI and integrates modules.
  - `focus_detection/`: CV pipeline and models.
  - `scheduling/`: NLP and ML for task management.
  - `scoring/`: Productivity metrics and reporting.
  - `ui/`: PyQt5 UI and widgets.
- `tests/`: Unit and integration tests (pytest).
- `docs/`: Technical report and documentation.
- `data/`: Sample data (e.g., task logs, webcam frames; gitignored).

## Installation & Requirements

- **Python 3.10** required.
- **Webcam** for CV features.
- **Consumer-grade hardware** (Intel i5+ recommended).

### Setup Steps

1. Clone the repository.
2. Create and activate a Python 3.10 virtual environment.
3. Run `python install_requirements.py` to install dependencies.
   - _Do NOT use pip install on requirements.txt directly due to dependency conflicts (PyQt5, OpenCV, etc.)._
   - Ensure a stable internet connection during installation.

## Usage

- Launch the application via `src/main.py`.
- The UI provides access to focus monitoring, task scheduling, and productivity reporting.
- Sample data and test scripts are available for development and validation.

## Design Principles

- **Real-time performance**: Optimized for low-latency inference and feedback.
- **Multimodal fusion**: Combines multiple ML/CV signals for robust focus detection.
- **Human-centered design**: Empowers users with insights, avoids surveillance anxiety.
- **Extensible architecture**: Modular codebase for easy feature addition and testing.

## References

- Technical report: `docs/report.pdf`
- For further details, see code comments and module docstrings.

---

_This documentation summarizes the system's architecture, setup, and usage. For API details and advanced configuration, refer to the source code and technical report._
