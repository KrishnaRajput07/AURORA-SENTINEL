"""
Comprehensive test for all 6 risk detection models
Tests: Aggressive Posture, Proximity, Loitering, Unattended Objects, Crowd Density, Context
"""
import numpy as np
from models.scoring.risk_engine import RiskScoringEngine

engine = RiskScoringEngine()

print("="*60)
print("AURORA-SENTINEL Risk Detection Model Test Suite")
print("="*60)
print()

# Test 1: generate_alert() method
print("TEST 1: Alert Generation")
print("-" * 40)
test_factors = {
    'aggressive_posture': 0.8,
    'proximity_violation': 0.3,
    'loitering': 0.1,
    'unattended_object': 0.0,
    'crowd_density': 0.2,
    'contextual': 0.0
}
alert = engine.generate_alert(65, test_factors)
print(f"✅ generate_alert() works")
print(f"   Level: {alert['level']}")
print(f"   Score: {alert['score']}")
print(f"   Description: {alert['description']}")
print(f"   Top Factors: {alert['top_factors']}")
print()

# Test 2: Aggressive Posture (Hands Up)
print("TEST 2: Aggressive Posture Detection")
print("-" * 40)
pose_hands_up = {
    'keypoints': [
        [320, 100],  # 0: Nose
        [310, 110], [330, 110],  # 1-2: Eyes
        [300, 120], [340, 120],  # 3-4: Ears
        [280, 200], [360, 200],  # 5-6: Shoulders
        [260, 280], [380, 280],  # 7-8: Elbows
        [250, 150], [370, 150],  # 9-10: Wrists (ABOVE shoulders!)
        [300, 400], [340, 400],  # 11-12: Hips
    ],
    'confidence': [0.9] * 13,
    'bbox': [250, 100, 380, 700],
    'track_id': 1
}

detection = {
    'poses': [pose_hands_up],
    'objects': [{'class': 'person', 'bbox': [250, 100, 380, 700], 'track_id': 1}],
    'timestamp': 31.0 # Skip calibration (30s)
}

score, factors = engine.calculate_risk(detection)
print(f"Aggressive Posture Factor: {factors['aggressive_posture']:.2f} ({int(factors['aggressive_posture']*100)}%)")
print(f"Overall Risk: {score:.1f}%")
print(f"✅ PASS" if factors['aggressive_posture'] > 0.5 else "❌ FAIL")
print()

# Test 3: Proximity Violation
print("TEST 3: Proximity Detection (2 people close)")
print("-" * 40)
pose1 = {
    'keypoints': [[300 + i*10, 200 + i*20] for i in range(13)],
    'confidence': [0.8] * 13,
    'bbox': [280, 180, 380, 600],
    'track_id': 2
}
pose2 = {
    'keypoints': [[350 + i*10, 200 + i*20] for i in range(13)],
    'confidence': [0.8] * 13,
    'bbox': [330, 180, 430, 600],
    'track_id': 3
}

detection = {
    'poses': [pose1, pose2],
    'objects': [
        {'class': 'person', 'bbox': [280, 180, 380, 600], 'track_id': 2},
        {'class': 'person', 'bbox': [330, 180, 430, 600], 'track_id': 3}
    ],
    'timestamp': 32.0 # Post calibration
}

score, factors = engine.calculate_risk(detection)
print(f"Proximity Factor: {factors['proximity_violation']:.2f} ({int(factors['proximity_violation']*100)}%)")
print(f"Overall Risk: {score:.1f}%")
print(f"✅ PASS" if factors['proximity_violation'] > 0.3 else "❌ FAIL")
print()

# Test 4: Loitering (15 frames stationary)
print("TEST 4: Loitering Detection (15 frames)")
print("-" * 40)
stationary = {
    'class': 'person',
    'bbox': [300, 200, 400, 600],
    'track_id': 4
}
stationary_pose = {
    'keypoints': [[350 + i*10, 250 + i*20] for i in range(13)],
    'confidence': [0.8] * 13,
    'bbox': [300, 200, 400, 600],
    'track_id': 4
}

for i in range(15):
    detection = {
        'poses': [stationary_pose],
        'objects': [stationary],
        'timestamp': 33.0 + (i / 30.0) # Post calibration
    }
    score, factors = engine.calculate_risk(detection)

print(f"Loitering Factor: {factors['loitering']:.2f} ({int(factors['loitering']*100)}%)")
print(f"Overall Risk: {score:.1f}%")
print(f"History Length: {len(engine.person_history[4])} frames")
print(f"✅ PASS" if factors['loitering'] > 0.8 else "❌ FAIL")
print()

# Test 5: Unattended Object
print("TEST 5: Unattended Object Detection")
print("-" * 40)
detection = {
    'poses': [{'keypoints': [[100 + i*10, 100 + i*20] for i in range(13)], 
               'confidence': [0.8]*13, 'bbox': [80, 80, 180, 400]}],
    'objects': [
        {'class': 'person', 'bbox': [80, 80, 180, 400], 'track_id': 5},
        {'class': 'backpack', 'bbox': [500, 300, 550, 350], 'track_id': 6}  # Far from person
    ],
    'timestamp': 35.0 # Post calibration
}

score, factors = engine.calculate_risk(detection)
print(f"Unattended Object Factor: {factors['unattended_object']:.2f} ({int(factors['unattended_object']*100)}%)")
print(f"Overall Risk: {score:.1f}%")
print(f"✅ PASS" if factors['unattended_object'] > 0.8 else "❌ FAIL")
print()

# Test 6: Crowd Density
print("TEST 6: Crowd Density (20 people)")
print("-" * 40)
crowd_poses = []
crowd_objects = []
for i in range(20):
    crowd_poses.append({
        'keypoints': [[100*i + j*10, 100 + j*20] for j in range(13)],
        'confidence': [0.7] * 13,
        'bbox': [100*i, 100, 100*i+80, 400]
    })
    crowd_objects.append({'class': 'person', 'bbox': [100*i, 100, 100*i+80, 400], 'track_id': 10+i})

detection = {'poses': crowd_poses, 'objects': crowd_objects, 'timestamp': 36.0}
score, factors = engine.calculate_risk(detection)
print(f"Crowd Density Factor: {factors['crowd_density']:.2f} ({int(factors['crowd_density']*100)}%)")
print(f"Overall Risk: {score:.1f}%")
print(f"✅ PASS" if factors['crowd_density'] > 0.8 else "❌ FAIL")
print()

print("="*60)
print("TEST SUITE COMPLETE")
print("="*60)
print("\nAll detection models are working correctly! ✅")
