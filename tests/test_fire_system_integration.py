import cv2
import numpy as np
import os
import sys
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.detection.detector import UnifiedDetector
from models.scoring.risk_engine import RiskScoringEngine

def test_fire_system_integration():
    """
    Test the entire pipeline: 
    Detector (Fire) -> Detection Data -> Risk Engine -> Risk Score
    """
    print("--- AURORA FIRE SYSTEM INTEGRATION TEST ---")
    
    # 1. Initialize System Components
    print("[1/4] Initializing Detector and Risk Engine...")
    detector = UnifiedDetector()
    # Use bypass_calibration to get immediate results
    risk_engine = RiskScoringEngine(bypass_calibration=True)
    
    if detector.fire_model is None:
        print("[ERROR] Fire model (fir.pt) could not be loaded. Test aborted.")
        return

    # 2. Create Synthetic Fire Scene
    print("[2/4] Creating synthetic fire scene (Red circle test)...")
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    # Draw a large red circle to simulate fire
    cv2.circle(frame, (320, 320), 120, (0, 0, 255), -1) 
    cv2.putText(frame, "SYSTEM INTEGRATION TEST: FIRE", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # 3. Step 1: Run Detection
    print("[3/4] Running Detection Pipeline...")
    detection_data = detector.process_frame(frame)
    
    fire_count = len(detection_data.get('fire', []))
    print(f"      - Detector found {fire_count} fire/smoke entities.")

    # 4. Step 2: Run Risk Scoring
    print("[4/4] Running Risk Scoring Pipeline...")
    risk_score, factors = risk_engine.calculate_risk(detection_data)
    
    # 5. Report Results
    print("\n--- TEST RESULTS ---")
    print(f"Final Risk Score: {risk_score:.2f}%")
    print("Risk Factors Breakdown:")
    for factor, value in factors.items():
        if value > 0:
            print(f"  - {factor}: {value:.4f}")
    
    # Validation logic
    fire_factor = factors.get('fire_smoke', 0)
    if fire_factor > 0:
        print("\n[SUCCESS] Fire detected and factored into risk score!")
        if risk_score > 40:
            print("[SUCCESS] Risk score is significantly elevated due to fire.")
        else:
            print("[WARNING] Fire detected but risk score remains low. Check weights.")
    else:
        print("\n[FAILURE] Fire model detected it, but Risk Engine ignored it or factor was 0.")

    # Save output for review
    os.makedirs("storage", exist_ok=True)
    cv2.imwrite("storage/system_fire_test.jpg", frame)
    print(f"\nSaved test visualization to 'storage/system_fire_test.jpg'")

if __name__ == "__main__":
    test_fire_system_integration()
