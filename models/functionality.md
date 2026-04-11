# Models — Functionality

This directory contains the ML model definitions for the AURORA Sentinel detection pipeline. These models form the **ML tier** (Analytical Brain) of the dual-brain architecture.

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `detection/` | Unified YOLOv8 detector for objects, poses, and weapons |
| `privacy/` | Face anonymization for privacy compliance |
| `scoring/` | Risk scoring engine and anomaly detector |
| `weights/` | Pre-trained model weight files (.pt) |

## Pipeline Flow
1. **Detection** (`detector.py`): YOLOv8 identifies persons, weapons, objects + pose keypoints
2. **Scoring** (`risk_engine.py`): Multi-factor risk analysis → ML risk score (0–100)
3. **Anomaly** (`anomaly_detector.py`): Supplementary unsupervised anomaly detection
4. **Privacy** (`anonymizer.py`): Face blurring for operator display compliance

## Integration
- All models are loaded and managed by `backend/services/ml_service.py`
- Risk engine thresholds are configurable via `config/risk_thresholds.yaml`
