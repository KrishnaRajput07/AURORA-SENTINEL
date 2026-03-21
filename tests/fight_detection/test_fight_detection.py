"""
Diagnostic script to test fight detection on stored videos
"""
import cv2
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path


from models.detection.detector import UnifiedDetector
from models.scoring.risk_engine import RiskScoringEngine

def analyze_video(video_path, output_path=None):
    """Analyze a video and report detection results"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {os.path.basename(video_path)}")
    print(f"{'='*80}")
    
    # Initialize detector and risk engine
    detector = UnifiedDetector()
    risk_engine = RiskScoringEngine(fps=30, bypass_calibration=True)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Could not open video {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"Video Info: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s duration")
    
    # Statistics
    frame_count = 0
    high_risk_frames = 0
    max_risk = 0
    max_risk_frame = 0
    total_persons = 0
    total_weapons = 0
    aggressive_frames = 0
    proximity_frames = 0
    
    risk_scores = []
    factor_summary = {
        'weapon_detection': [],
        'aggressive_posture': [],
        'proximity_violation': [],
        'loitering': [],
        'unattended_object': [],
        'crowd_density': []
    }
    
    # Process every 5th frame for speed
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 5 == 0:  # Sample every 5th frame
            # Run detection
            detection = detector.process_frame(frame)
            
            # Calculate risk
            timestamp = frame_count / fps
            risk_score, factors = risk_engine.calculate_risk(
                detection, 
                context={'timestamp': timestamp, 'hour': 14, 'sensitivity': 1.0}
            )
            
            risk_scores.append(risk_score)
            
            # Track factors
            for key in factor_summary:
                if key in factors:
                    factor_summary[key].append(factors[key])
            
            # Statistics
            total_persons += len(detection.get('poses', []))
            total_weapons += len(detection.get('weapons', []))
            
            if risk_score > 50:
                high_risk_frames += 1
            
            if risk_score > max_risk:
                max_risk = risk_score
                max_risk_frame = frame_count
            
            if factors.get('aggressive_posture', 0) > 0.4:
                aggressive_frames += 1
            
            if factors.get('proximity_violation', 0) > 0.4:
                proximity_frames += 1
            
            # Print progress every 30 frames
            if frame_count % 150 == 0:
                print(f"  Frame {frame_count}/{total_frames} - Current Risk: {risk_score:.1f}%")
        
        frame_count += 1
    
    cap.release()
    
    # Report results
    print(f"\n{'='*80}")
    print("DETECTION RESULTS:")
    print(f"{'='*80}")
    print(f"Frames Analyzed: {len(risk_scores)}")
    print(f"Average Risk Score: {np.mean(risk_scores):.1f}%")
    print(f"Max Risk Score: {max_risk:.1f}% (at frame {max_risk_frame}, {max_risk_frame/fps:.1f}s)")
    print(f"High Risk Frames (>50%): {high_risk_frames} ({high_risk_frames/len(risk_scores)*100:.1f}%)")
    print(f"\nDetection Stats:")
    print(f"  Total Person Detections: {total_persons}")
    print(f"  Total Weapon Detections: {total_weapons}")
    print(f"  Aggressive Posture Frames: {aggressive_frames}")
    print(f"  Proximity Violation Frames: {proximity_frames}")
    
    print(f"\nAverage Factor Scores:")
    for key, values in factor_summary.items():
        if values:
            avg = np.mean(values)
            max_val = np.max(values)
            print(f"  {key}: avg={avg:.3f}, max={max_val:.3f}")
    
    # Diagnosis
    print(f"\n{'='*80}")
    print("DIAGNOSIS:")
    print(f"{'='*80}")
    
    if max_risk < 30:
        print("⚠️  LOW DETECTION: Max risk is below 30%")
        print("   Possible issues:")
        print("   - Pose detection not capturing fighting stances")
        print("   - Proximity thresholds too strict")
        print("   - Temporal validation suppressing alerts")
    elif max_risk < 50:
        print("⚠️  MODERATE DETECTION: Max risk is 30-50%")
        print("   Detection is working but may need tuning")
    else:
        print("✓  GOOD DETECTION: Max risk above 50%")
    
    if total_persons == 0:
        print("❌ CRITICAL: No persons detected in video!")
        print("   Check if YOLOv8 pose model is working")
    
    if aggressive_frames == 0 and max_risk > 0:
        print("⚠️  No aggressive postures detected")
        print("   Pose-based aggression detection may need adjustment")
    
    if proximity_frames == 0 and total_persons > len(risk_scores):
        print("⚠️  No proximity violations detected")
        print("   Multiple people present but not flagged as close")
    
    return {
        'max_risk': max_risk,
        'avg_risk': np.mean(risk_scores),
        'high_risk_frames': high_risk_frames,
        'total_persons': total_persons,
        'total_weapons': total_weapons
    }

if __name__ == "__main__":
    # Test videos in storage/temp
    video_dir = "storage/temp"
    
    if not os.path.exists(video_dir):
        print(f"ERROR: Directory {video_dir} not found")
        sys.exit(1)
    
    videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    
    if not videos:
        print(f"No videos found in {video_dir}")
        sys.exit(1)
    
    print(f"Found {len(videos)} videos to analyze")
    
    results = {}
    for video_file in videos:
        video_path = os.path.join(video_dir, video_file)
        try:
            result = analyze_video(video_path)
            results[video_file] = result
        except Exception as e:
            print(f"ERROR analyzing {video_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY OF ALL VIDEOS:")
    print(f"{'='*80}")
    for video_file, result in results.items():
        is_boxing = "boxing" in video_file.lower() or "scr9" in video_file.lower()
        expected = "LOW risk (boxing)" if is_boxing else "HIGH risk (fight)"
        actual = "HIGH" if result['max_risk'] > 50 else "MODERATE" if result['max_risk'] > 30 else "LOW"
        status = "✓" if (is_boxing and actual == "LOW") or (not is_boxing and actual == "HIGH") else "⚠️"
        
        print(f"{status} {video_file}")
        print(f"   Expected: {expected}, Actual: {actual} ({result['max_risk']:.1f}%)")
        print(f"   Persons: {result['total_persons']}, Weapons: {result['total_weapons']}")
