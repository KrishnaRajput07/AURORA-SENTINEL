# Privacy — Functionality

This directory contains the face anonymization module for privacy compliance.

## Key Files

### `anonymizer.py`
- **`PrivacyAnonymizer`** class — anonymizes faces and sensitive information in video frames
- Two-stage face detection:
  1. **Primary**: Uses YOLO pose keypoints (indices 0–4 = nose, eyes, ears) to locate head region
  2. **Fallback**: Uses OpenCV Haar cascade (`haarcascade_frontalface_default.xml`)
- Applies Gaussian blur with padding (30% of person height) for robust coverage
- Boundary-safe cropping to prevent crashes on edge cases
- Processes all detected faces in a frame, returning the anonymized frame
