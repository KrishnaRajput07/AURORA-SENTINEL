import cv2
import numpy as np
import sys
import os
import time

# Add root to sys.path
sys.path.append(os.getcwd())

from models.detection.detector import UnifiedDetector
from models.scoring.risk_engine import RiskScoringEngine
from models.privacy.anonymizer import PrivacyAnonymizer

def run_live_monitor():
    """
    Simulate a live monitor by processing a video and showing it in a window
    """
    print("Initializing Live Monitor...")
    try:
        detector = UnifiedDetector()
        risk_engine = RiskScoringEngine()
        anonymizer = PrivacyAnonymizer()
    except Exception as e:
        print(f"Failed to initialize models: {e}")
        return

    # Use the user's video
    video_path = 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_015_x264.mp4'
    
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    
    # Get video properties for delay calculation
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps)
    
    print("\nStarting Live Feed... (Press 'q' to quit)")
    
    frame_count = 0
    
    while True:
        start_time = time.time()
        
        ret, frame = cap.read()
        if not ret:
            # Loop video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            
        # Resize for better visibility if too large
        height, width = frame.shape[:2]
        if width > 1280:
            frame = cv2.resize(frame, (1280, 720))
        
        # 1. Detect
        detection = detector.process_frame(frame)
        
        # 2. Risk Score
        risk_score, risk_factors = risk_engine.calculate_risk(detection)
        alert = risk_engine.generate_alert(risk_score, risk_factors)
        
        # 3. Annotate
        # Draw bounding boxes
        for obj in detection['objects']:
            bbox = obj['bbox']
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
            cv2.putText(frame, obj['class'], (int(bbox[0]), int(bbox[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        # Draw Risk Panel
        # Create a semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (20, 20), (350, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Risk Text
        color = (0, 255, 0) # Green
        if risk_score > 50: color = (0, 165, 255) # Orange
        if risk_score > 75: color = (0, 0, 255) # Red
        
        cv2.putText(frame, f"RISK SCORE: {risk_score:.1f}", (40, 60), cv2.FONT_HERSHEY_TRIPLEX, 1.0, color, 2)
        cv2.putText(frame, f"LEVEL: {alert['level']}", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Show Top Factor
        if alert['top_factors']:
            factor_text = f"Main: {alert['top_factors'][0]['name']}"
            cv2.putText(frame, factor_text, (40, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Show
        cv2.imshow("Aurora Sentinel - Real-time Analysis", frame)
        
        # FPS Control
        process_time = time.time() - start_time
        wait_time = max(1, delay - int(process_time * 1000))
        
        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            break
            
        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_live_monitor()
