# Synthetic Data — Functionality

This directory contains utilities for generating and managing synthetic test data.

## Key Files

### `video_generator.py`
- Generates synthetic surveillance videos for testing
- Creates controlled scenarios: fights, normal activity, sports, etc.
- Configurable: number of people, actions, camera angles, lighting
- Enables reproducible testing without privacy concerns

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `videos/` | Generated synthetic video files and dataset metadata |

## Purpose
- Generate diverse test scenarios algorithmically
- Avoid privacy issues with real surveillance footage
- Create edge cases that are rare in real data
- Enable unit testing with predictable inputs
