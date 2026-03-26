import cv2
import numpy as np
import os
import sys
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.detection.detector import UnifiedDetector
from models.scoring.risk_engine import RiskScoringEngine

def run_live_fire_detection():
    """
    Accesses the laptop camera and runs fire detection in real-time.
    """
    print("--- AURORA LIVE FIRE DETECTION ---")
    print("Initializing Models (this may take a moment)...")
    
    # Initialize Detector and Risk Engine
    detector = UnifiedDetector()
    # Skip calibration for immediate scoring
    risk_engine = RiskScoringEngine(bypass_calibration=True)
    
    if detector.fire_model is None:
        print("[ERROR] Fire model (fir.pt) not loaded correctly. Check paths or LFS status.")
        return

    # Initialize Camera with optimizations for WSL2/usbipd
    # Try index 0, then 1, 2 if those fail
    cap = None
    for index in [0, 1, 2]:
        print(f"Trying camera index {index}...")
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            # Set MJPG to handle potential bandwidth issues with usbipd-win
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduce latency
            print(f"[INFO] Successfully opened camera {index}.")
            break
    
    if cap is None or not cap.isOpened():
        print("[ERROR] Could not open webcam after trying multiple indices.")
        return

    print("\nLive Feed Started. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # 1. Processing
        start_time = time.time()
        detection_data = detector.process_frame(frame)
        risk_score, factors = risk_engine.calculate_risk(detection_data)
        fps = 1.0 / (time.time() - start_time)

        # 2. Draw Fire/Smoke results
        fire_detections = detection_data.get('fire', [])
        for det in fire_detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            conf = det['confidence']
            label = det['class']
            
            # Orange for fire/smoke
            color = (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, f"THREAT: {label.upper()} {int(conf*100)}%", 
                        (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # 3. Draw UI Overlay
        # Background for status bar
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
        
        status_color = (0, 0, 255) if risk_score > 50 else (0, 255, 0)
        cv2.putText(frame, f"RISK: {risk_score:.1f}%", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1]-120, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)

        # 4. Show Result
        cv2.imshow('AURORA - Live Fire Detection System', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Live feed closed.")

if __name__ == "__main__":
    run_live_fire_detection()
