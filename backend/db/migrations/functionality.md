# Database Migrations — Functionality

This directory contains SQL migration scripts for schema evolution.

## Migrations

### `20260303173123_add_two_tier_scoring_fields.sql`
- Adds two-tier scoring columns to the `alerts` table:
  - `ml_score` (FLOAT) — ML risk score (0–100)
  - `ai_score` (FLOAT) — AI risk score (0–100)
  - `final_score` (FLOAT) — Weighted/aggregated score used for alerting
  - `detection_source` (VARCHAR) — Source indicator: "ml", "ai", "both", or "none"
  - `ai_explanation` (VARCHAR) — AI reasoning text
  - `ai_scene_type` (VARCHAR) — Scene classification: "real_fight", "boxing", "drama", "normal"
  - `ai_confidence` (FLOAT) — AI confidence level (0–1)
- Supports backward compatibility — `database.py` also has a runtime `ensure_alert_columns()` fallback for SQLite
