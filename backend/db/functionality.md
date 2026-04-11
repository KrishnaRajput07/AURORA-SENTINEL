# Database — Functionality

This directory manages database connectivity, ORM models, and schema migrations.

## Key Files

### `database.py`
- Configures SQLAlchemy engine and session factory
- Default: SQLite (`./aurora.db`) with 30s timeout; supports PostgreSQL via `DATABASE_URL` env var
- Graceful fallback: if the configured DB connection fails, automatically falls back to SQLite
- `ensure_alert_columns()`: Runtime backward-compatible schema safety — adds missing two-tier scoring columns to the `alerts` table without requiring destructive migrations (SQLite only)

### `models.py`
- **`Alert`** — Core alert record with fields for:
  - Basic: id, timestamp, level (CRITICAL/HIGH/MEDIUM/LOW), risk_score, camera_id, location, risk_factors (JSON), video_clip_path
  - Two-tier scoring: ml_score, ai_score, final_score, detection_source, ai_explanation, ai_scene_type, ai_confidence
  - Lifecycle: status (pending/acknowledged/resolved)
  - Accountability: operator_name, acknowledged_at, resolved_at
  - Resolution: resolution_type, resolution_notes
- **`SystemSetting`** — Key-value store for runtime-configurable settings (e.g., maintenance_mode, vlm_interval_seconds)
- **`ClipRecord`** — Tracks auto-captured video clips with camera_id, alert_id (FK), file_path, duration, captured_at, and expires_at for retention management

### `migrations/`
- SQL migration scripts for schema evolution (see `migrations/functionality.md`)
