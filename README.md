# Productivity Monitoring and Task Optimization System

## Executive Summary

This project implements a prototype for a productivity tool using machine learning (ML) and computer vision (CV). The system is divided into three core modules:

1. **Focus Detection Engine**: Real-time CV pipeline from webcam input to classify user focus via facial/body cues (e.g., head pose, eye gaze, blinks, expressions).
2. **Intelligent Scheduling and Optimization Module**: NLP for task parsing + ML for prioritization and dynamic scheduling with reinforcement learning (RL).
3. **Productivity Scoring and Reporting System**: Aggregates data into scores, patterns, and human-centered insights.

The architecture emphasizes real-time performance, multimodal fusion, and a human-centered design (HCML) to empower users without surveillance anxiety. UI is built with PyQt5 for a desktop app.

Based on the [technical report](docs/report.pdf).

## Project Structure

See `structure.txt` for the directory layout. Key directories:
- `src/`: Core modules and UI.
- `tests/`: Pytest-based tests.
- `docs/`: Report and API docs.
- `data/`: Sample inputs (gitignore large files).

## Requirements

- Python 3.10
- Webcam for CV testing
- Consumer-grade hardware (e.g., Intel i5+ for real-time inference)

## Installation

1. Clone the repo: