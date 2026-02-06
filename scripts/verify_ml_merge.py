import sys
import os
import numpy as np
import cv2

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from models.detection.detector import UnifiedDetector
    from models.scoring.risk_engine import RiskScoringEngine
    
    print("Initializing models...")
    detector = UnifiedDetector()
    risk_engine = RiskScoringEngine()
    
    print("Models initialized successfully.")
    
    # Create a dummy frame
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Simulate a sequence of frames
    print("Running simulation on 5 frames...")
    for i in range(5):
        # 1. Detection & Tracking
        detection_data = detector.process_frame(frame)
        
        # Check structure
        objects = detection_data.get('objects', [])
        poses = detection_data.get('poses', [])
        
        print(f"[Frame {i}] Objects: {len(objects)}, Poses: {len(poses)}")
        
        if objects:
            print(f"   First Object Track ID: {objects[0].get('track_id')}")
            
        # 2. Risk Scoring
        risk_score, risk_factors = risk_engine.calculate_risk(detection_data)
        print(f"   Risk Score: {risk_score:.2f}")
        
    print("\n✅ Verification Simulation Complete!")

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Ensure you are running this from the project root or scripts directory correctly.")
except Exception as e:
    print(f"❌ Runtime Error: {e}")
    import traceback
    traceback.print_exc()
