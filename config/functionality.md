# Config — Functionality

Configuration files for system behavior and thresholds.

## Files

### `risk_thresholds.yaml`
- Comprehensive risk scoring configuration (139 lines)
- All thresholds documented with comments explaining impact
- **Sections**:
  - `temporal`: Validation ratio, window size, suppression max
  - `proximity`: Distance threshold, escalation multiplier, baseline weight
  - `strike`: Velocity threshold, history length
  - `grappling`: Distance, overlap, persistence frames
  - `aggression`: Scores for raised arms, strike, fighting stance, etc.
  - `escalation`: Minimum scores for specific scenarios
  - `suppression_bypass`: When to bypass temporal suppression
  - `two_tier`: Alert threshold and AI timeout
  - `alert_colors`: Thresholds for visual indicators
  - `validation`: Acceptable ranges for all parameters

## Usage
- Loaded by `RiskScoringEngine` on initialization
- Allows tuning detection sensitivity without code changes
- YAML format for human readability and version control
