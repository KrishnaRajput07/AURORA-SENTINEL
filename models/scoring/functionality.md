# Scoring — Functionality

This directory contains the risk scoring and anomaly detection modules that power the ML tier of the two-tier scoring architecture.

## Key Files

### `risk_engine.py`
- **`RiskScoringEngine`** — advanced multi-factor risk scoring engine (1,123 lines)
- Combines behavioral signals, spatial context, and temporal tracking into a unified threat score
- **Configurable thresholds**: Loads from `config/risk_thresholds.yaml` with sensible defaults
- **Key analysis modules**:
  - **Temporal validation**: Validates risk scores across a rolling window of frames (default 20 frames)
  - **Proximity detection**: Identifies when people are too close, with escalation weighting
  - **Strike velocity detection**: Tracks rapid limb movements (punches/kicks) via keypoint history
  - **Grappling detection**: Identifies sustained close combat via bounding box overlap
  - **Aggression scoring**: Analyzes raised arms, fighting stance, extended arms, wide stance
  - **Risk escalation**: Minimum scores for aggression+proximity, grappling, strike+proximity
  - **Suppression bypass**: Bypasses temporal suppression for high-confidence detections (weapons, high aggression)
- **Calibration phase**: Learns "normal" crowd behavior for the first 30 seconds
- Per-person keypoint velocity tracking for strike detection

### `anomaly_detector.py`
- **`AnomalyDetector`** — unsupervised anomaly detection using `IsolationForest` (scikit-learn)
- Extracts feature vectors from detection data: person count, object count, spatial variance, average proximity
- Trainable on normal behavior data; supports model serialization via pickle
- Used as an auxiliary signal alongside the primary risk engine
