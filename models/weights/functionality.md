# Weights — Functionality

This directory stores pre-trained model weight files for the ML detection pipeline.

## Contents
- `weapon_model.pt` — YOLOv8 weapon detection weights (currently a Git-LFS pointer — actual weights need to be pulled via `git lfs pull`)

## Notes
- The `UnifiedDetector` in `models/detection/detector.py` resolves weight paths by checking this directory and the project root
- Git-LFS pointer files are detected and skipped gracefully by the detector
