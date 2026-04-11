# Video — Functionality

This directory contains video processing utilities.

## Key Files

### `processor.py`
- **`VideoProcessor`** class for video summarization and clip extraction
- `summarize_video()`: Creates a summary video from alert timestamps
  - Extracts 5-second clips before and after each alert
  - Merges overlapping intervals
  - Adds "Alert Segment" overlay text
  - Auto-transcodes to H.264 + faststart for browser compatibility via ffmpeg
- `extract_thumbnail()`: Captures a JPEG thumbnail at a specific timestamp
- Uses `ThreadPoolExecutor` for non-blocking async operation
