import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from models.scoring.risk_engine import RiskScoringEngine

def test_weapon_escalation():
    engine = RiskScoringEngine(bypass_calibration=True)
    
    # CASE 1: Knife Detection (Standard Object)
    print("Testing Knife Detection...")
    detection_knife = {
        'objects': [{'class': 'knife', 'confidence': 0.9, 'bbox': [100, 100, 200, 200], 'track_id': 1}],
        'poses': [{'keypoints': [], 'confidence': [], 'bbox': [100, 100, 200, 200], 'track_id': 1}],
        'weapons': []
    }
    
    score_knife, factors_knife = engine.calculate_risk(detection_knife)
    print(f"Knife Risk Score: {score_knife:.2f}%")
    print(f"Knife Factors: {factors_knife}")
    
    if score_knife < 80:
        print("FAILED: Knife risk score too low!")
    else:
        print("PASSED: Knife triggered critical risk.")
        
    print("-" * 30)

    # CASE 2: Gun Detection (Custom Weapon Model)
    print("Testing Gun Detection...")
    detection_gun = {
        'objects': [{'class': 'person', 'confidence': 0.9, 'bbox': [100, 100, 200, 200], 'track_id': 1}],
        'poses': [{'keypoints': [], 'confidence': [], 'bbox': [100, 100, 200, 200], 'track_id': 1}],
        'weapons': [{'class': 'weapon', 'confidence': 0.85, 'bbox': [100, 100, 200, 200]}]
    }
    
    score_gun, factors_gun = engine.calculate_risk(detection_gun)
    print(f"Gun Risk Score: {score_gun:.2f}%")
    print(f"Gun Factors: {factors_gun}")
    
    if score_gun < 80:
        print("FAILED: Gun risk score too low!")
    else:
        print("PASSED: Gun triggered critical risk.")

if __name__ == "__main__":
    test_weapon_escalation()
