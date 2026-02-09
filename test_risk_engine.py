"""
Quick test to verify aggressive posture and loitering detection
"""
import numpy as np
from models.scoring.risk_engine import RiskScoringEngine

# Initialize engine
engine = RiskScoringEngine()

print("=== Risk Engine Configuration ===")
print(f"History buffer size: {engine.person_history.default_factory().maxlen}")
print(f"Loitering threshold: {engine.loitering_time_threshold} frames")
print(f"Weights: {engine.weights}")
print()

# Test 1: Aggressive Posture (Hands Up, Stationary)
print("=== Test 1: Aggressive Posture Detection ===")
pose_hands_up = {
    'keypoints': [
        [320, 100],  # 0: Nose
        [310, 110], [330, 110],  # 1-2: Eyes
        [300, 120], [340, 120],  # 3-4: Ears
        [280, 200], [360, 200],  # 5-6: Shoulders
        [260, 280], [380, 280],  # 7-8: Elbows
        [250, 150], [370, 150],  # 9-10: Wrists (ABOVE shoulders - hands up!)
        [300, 400], [340, 400],  # 11-12: Hips
        [290, 600], [350, 600],  # 13-14: Knees
        [285, 700], [355, 700],  # 15-16: Ankles
    ],
    'confidence': [0.9] * 17,
    'bbox': [250, 100, 380, 700],  # Height = 600px
    'track_id': 1
}

detection_data = {
    'poses': [pose_hands_up],
    'objects': [{'class': 'person', 'bbox': [250, 100, 380, 700], 'track_id': 1}],
    'timestamp': 0
}

score, factors = engine.calculate_risk(detection_data)
print(f"Risk Score: {score:.1f}%")
print(f"Aggressive Posture Factor: {factors['aggressive_posture']:.2f}")
print()

# Test 2: Loitering (Simulate 80 frames of stationary person)
print("=== Test 2: Loitering Detection ===")
stationary_person = {
    'class': 'person',
    'bbox': [300, 200, 400, 600],
    'track_id': 2
}

stationary_pose = {
    'keypoints': [[350, 250]] + [[350 + i*10, 250 + i*20] for i in range(16)],
    'confidence': [0.8] * 17,
    'bbox': [300, 200, 400, 600],
    'track_id': 2
}

# Simulate 80 frames
for i in range(80):
    detection_data = {
        'poses': [stationary_pose],
        'objects': [stationary_person],
        'timestamp': i / 30.0
    }
    score, factors = engine.calculate_risk(detection_data)

print(f"After 80 frames (~2.6 seconds):")
print(f"Risk Score: {score:.1f}%")
print(f"Loitering Factor: {factors['loitering']:.2f}")
print(f"History length for track 2: {len(engine.person_history[2])}")
print()

print("=== Tests Complete ===")
print("If aggressive_posture > 0.5 and loitering > 0.8, detections are working!")
