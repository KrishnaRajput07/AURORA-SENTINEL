import cv2
import numpy as np
import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from models.detection.detector import UnifiedDetector
from models.scoring.risk_engine import RiskScoringEngine
from models.privacy.anonymizer import PrivacyAnonymizer

def create_demo_video():
    """
    Create annotated demo video showing system capabilities
    """
    # Initialize models
    print("Initializing models...")
    try:
        detector = UnifiedDetector()
        risk_engine = RiskScoringEngine()
        anonymizer = PrivacyAnonymizer()
    except Exception as e:
        print(f"Failed to initialize models: {e}")
        return
    
    # Input/output paths
    # User provided video
    input_video = 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_015_x264.mp4'
    if not os.path.exists(input_video):
        print(f"Input video {input_video} not found. Using dummy generator.")
        input_video = None
        
    output_video = 'demo_output.mp4'
    
    if input_video:
        cap = cv2.VideoCapture(input_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    else:
        # Dummy video generator
        fps = 30.0
        width = 1280
        height = 720
        cap = None
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    print("Creating demo video...")
    
    frame_count = 0
    max_frames = 300 if not input_video else 100000 
    
    while frame_count < max_frames:
        if cap:
            ret, frame = cap.read()
            if not ret:
                break
        else:
            # Generate dummy frame with noise
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Add some moving blobs to simulate people ?
            # Just noise for now to prevent crash
            cv2.randu(frame, 0, 255)
        
        # Process frame
        detection = detector.process_frame(frame)
        risk_score, risk_factors = risk_engine.calculate_risk(detection)
        alert = risk_engine.generate_alert(risk_score, risk_factors)
        
        # Anonymize
        # We can toggle mode here
        frame = anonymizer.anonymize_frame(frame, detection['poses'], mode='blur')
        
        # Draw bounding boxes
        for obj in detection['objects']:
            bbox = obj['bbox']
            cv2.rectangle(
                frame,
                (int(bbox[0]), int(bbox[1])),
                (int(bbox[2]), int(bbox[3])),
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                obj['class'],
                (int(bbox[0]), int(bbox[1]-10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        # Draw pose keypoints
        for pose in detection['poses']:
            keypoints = np.array(pose['keypoints'])
            for kpt in keypoints:
                cv2.circle(frame, tuple(kpt.astype(int)), 3, (0, 255, 255), -1)
        
        # Draw risk score panel
        panel_height = 120
        # Check if frame is big enough
        if height > 120:
            panel = np.zeros((panel_height, width, 3), dtype=np.uint8)
            
            # Risk score bar
            bar_width = int((risk_score / 100.0) * (width - 40))
            if bar_width < 0: bar_width = 0
            
            color = (0, 0, 255) if risk_score > 75 else (0, 165, 255) if risk_score > 50 else (0, 255, 0)
            cv2.rectangle(panel, (20, 20), (20 + bar_width, 40), color, -1)
            
            # Text
            cv2.putText(panel, f"Risk Score: {risk_score:.1f}", (20, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(panel, f"Alert Level: {alert['level']}", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Combine frame and panel (overlay panel on top-left or bottom? User guide said vstack)
            # vstack changes video height, which complicates VideoWriter if not planned.
            # User guide code: combined = np.vstack([frame, panel])
            # But VideoWriter initialized with (width, height).
            # If we vstack, height increases. We should have initialized VideoWriter with height + panel_height.
            # I will fix this logic.
            
            # Re-init video writer if first frame (hacky but safe for dynamic size)
            pass 
            
            # Better: Overlay panel on top of frame
            frame[0:panel_height, 0:width] = panel

        out.write(frame)
        
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")
    
    if cap:
        cap.release()
    out.release()
    
    print(f"✓ Demo video created: {output_video}")

if __name__ == "__main__":
    create_demo_video()
