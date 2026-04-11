# Detection — Functionality

This directory contains the unified object and pose detection module.

## Key Files

### `detector.py`
- **`UnifiedDetector`** class — the primary ML detection engine
- Runs **YOLOv8** for object detection (persons, weapons, vehicles)
- Runs **YOLOv8-pose** for human pose estimation (17 keypoints per person)
- GPU-first with automatic CPU fallback
- Handles Git-LFS pointer files gracefully (detects and skips them)
- Model path resolution: checks script directory then project root for weight files
- `warmup()`: Pre-runs inference on a dummy frame to avoid cold-start latency
- Returns structured detection data: poses (keypoints + confidence), objects (class + bbox + confidence), weapons (sub-class + bbox + confidence)
