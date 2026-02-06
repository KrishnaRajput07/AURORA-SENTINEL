import numpy as np
from scipy.spatial.distance import euclidean
from collections import deque
import math

class RiskScoringEngine:
    """
    Multi-factor risk scoring system
    """
    def __init__(self, history_length=30):
        self.history = deque(maxlen=history_length)  # 1 second at 30fps
        
        # Risk weights (tunable)
        self.weights = {
            'aggressive_posture': 0.35, # Fighting stance, hands up
            'proximity_violation': 0.25, # People too close (fighting/stealing)
            'loitering': 0.20,           # Staying in one spot too long
            'unattended_object': 0.30,   # Bags left alone
            'crowd_density': 0.15,       # Potential stampede/chaos
            'contextual': 0.10           # Time of day, location
        }
        
        # Thresholds
        self.loitering_threshold = 300  # 10 seconds at 30fps implies history needs to be longer for real loitering? 
                                        # User guide said history_length=30 but loitering_threshold=300. 
                                        # logic in _detect_loitering checks len(self.history) < self.loitering_threshold.
                                        # So we need to increase history_length or adjust logic.
                                        # For now, I'll increase history_length default or just accept it might not trigger until history fills up if I used a larger deque.
                                        # Actually, maintaining 300 frames in memory might be heavy if full frames.
                                        # The history stores 'detection_data' (dicts), which is lightweight.
                                        # So I will increase the default history_length to coverage loitering, or handle it.
        self.history = deque(maxlen=300) # Increased to support loitering check
        
        self.proximity_threshold = 50   # pixels
        self.crowd_density_high = 15    # people per frame
        
    def calculate_risk(self, detection_data, context=None):
        """
        Main risk calculation
        
        Args:
            detection_data: Output from UnifiedDetector
            context: Dict with time, location, weather, etc.
        
        Returns:
            risk_score (0-100), risk_factors dict
        """
        self.history.append(detection_data)
        
        risk_factors = {}
        
        # 1. Aggressive posture analysis
        risk_factors['aggressive_posture'] = self._analyze_aggression(
            detection_data['poses']
        )
        
        # 2. Proximity violations
        risk_factors['proximity_violation'] = self._check_proximity(
            detection_data['poses']
        )
        
        # 3. Loitering detection
        risk_factors['loitering'] = self._detect_loitering(
            detection_data['objects']
        )
        
        # 4. Unattended objects
        risk_factors['unattended_object'] = self._detect_unattended_objects(
            detection_data['objects'],
            detection_data['poses']
        )
        
        # 5. Crowd density
        risk_factors['crowd_density'] = self._analyze_crowd_density(
            detection_data['poses']
        )
        
        # 6. Contextual factors
        if context:
            risk_factors['contextual'] = self._apply_context(context)
        else:
            risk_factors['contextual'] = 0
        
        # Calculate weighted score
        # Note: Normalize weights sum if they exceed 1.0, or just clamp.
        # User guide weights sum > 1 (0.35+0.25+0.20+0.30+0.15+0.10 = 1.35).
        # This means total score can exceed 1.0 before *100.
        total_score = sum(
            risk_factors.get(k, 0) * self.weights.get(k, 0)
            for k in self.weights.keys()
        )
        
        # Normalize to 0-100
        # If max theoretical score is 1.35, we clamp at 1.0 then * 100? or just clamp at 100.
        risk_score = min(100.0, total_score * 100)
        
        return risk_score, risk_factors
    
    def _analyze_aggression(self, poses):
        """
        Detect aggressive body postures
        Based on joint angles and body dynamics
        """
        if not poses:
            return 0.0
        
        aggression_score = 0.0
        
        for pose in poses:
            kpts = np.array(pose['keypoints'])
            conf = np.array(pose['confidence'])
            
            # Need basic upper body keypoints
            if len(kpts) < 11: 
                continue

            # Only process if enough keypoints are visible
            if np.mean(conf) < 0.4:
                continue
            
            # Check for raised arms (potential fighting)
            # 5: L-Shoulder, 6: R-Shoulder, 9: L-Wrist, 10: R-Wrist
            if len(kpts) >= 11:
                left_shoulder, right_shoulder = kpts[5], kpts[6]
                left_wrist, right_wrist = kpts[9], kpts[10]
                
                # Arms raised above shoulders (y is smaller when higher)
                if (left_wrist[1] < left_shoulder[1] or 
                    right_wrist[1] < right_shoulder[1]):
                    aggression_score += 0.3
            
            # Check for wide stance (aggressive posture)
            if len(kpts) >= 17:  # Need ankles (15, 16)
                left_ankle, right_ankle = kpts[15], kpts[16]
                stance_width = euclidean(left_ankle, right_ankle)
                
                # Compare to shoulder width
                shoulder_width = euclidean(left_shoulder, right_shoulder)
                # Avoid division by zero
                if shoulder_width > 0 and stance_width > shoulder_width * 2.5:
                    aggression_score += 0.2
        
        return min(1.0, aggression_score / max(len(poses), 1))
    
    def _check_proximity(self, poses):
        """
        Check if people are too close (potential conflict)
        """
        if len(poses) < 2:
            return 0.0
        
        proximity_violations = 0
        total_pairs = 0
        
        # Check all pairs
        for i in range(len(poses)):
            for j in range(i + 1, len(poses)):
                bbox1 = poses[i]['bbox']
                bbox2 = poses[j]['bbox']
                
                center1 = self._get_bbox_center(bbox1)
                center2 = self._get_bbox_center(bbox2)
                
                distance = euclidean(center1, center2)
                
                if distance < self.proximity_threshold:
                    proximity_violations += 1
                
                total_pairs += 1
        
        return proximity_violations / total_pairs if total_pairs > 0 else 0.0
    
    def _detect_loitering(self, objects):
        """
        Detect if a person has been stationary for too long
        """
        # If history isn't full enough to detect long-term loitering, return 0
        if len(self.history) < self.history.maxlen: # Wait for full history window
        # Note: default history might be short (30), for loitering we might want longer.
        # But assuming the deque catches enough frames.
            if len(self.history) < 30: # Minimum frames to check
                return 0.0
        
        # Look at the oldest frame in our window vs current
        oldest_frame = self.history[0]
        current_frame_objects = objects
        
        # Filter for persons
        old_persons = [obj for obj in oldest_frame['objects'] if obj['class'] == 'person']
        curr_persons = [obj for obj in current_frame_objects if obj['class'] == 'person']
        
        if not old_persons or not curr_persons:
            return 0.0
            
        stationary_count = 0
        
        # Method A: Match by Track ID (Superior)
        # Create dict for fast lookup
        old_map = {obj.get('track_id', -1): obj for obj in old_persons if obj.get('track_id', -1) != -1}
        
        for curr in curr_persons:
            tid = curr.get('track_id', -1)
            mapped_old = None
            
            if tid != -1 and tid in old_map:
                mapped_old = old_map[tid]
            else:
                # Method B: Fallback to Distance Matching (if tracking fails or not present)
                curr_center = self._get_center(curr['bbox'])
                best_dist = float('inf')
                for old in old_persons:
                    # Skip if this old person was already matched via ID (to avoid double counting? optional)
                    if old.get('track_id', -1) != -1 and old.get('track_id') in [p.get('track_id') for p in curr_persons]:
                        continue
                        
                    dist = euclidean(curr_center, self._get_center(old['bbox']))
                    if dist < best_dist:
                        best_dist = dist
                        if dist < 50: # Match threshold
                            mapped_old = old
                
            if mapped_old:
                # Check movement
                p1 = self._get_center(mapped_old['bbox'])
                p2 = self._get_center(curr['bbox'])
                
                if euclidean(p1, p2) < 50: # Moved less than 50 pixels in the history window
                    stationary_count += 1

        return min(1.0, stationary_count / max(len(curr_persons), 1))
    
    def _detect_unattended_objects(self, objects, poses):
        """
        Detect bags/objects not near any person
        """
        bags = [obj for obj in objects 
                if obj['class'] in ['backpack', 'handbag', 'suitcase']]
        
        if not bags:
            return 0.0
            
        if not poses:
            # Bags exist but no people? Definitely unattended
            return 1.0
        
        person_positions = [self._get_bbox_center(pose['bbox']) 
                           for pose in poses]
        
        unattended_count = 0
        for bag in bags:
            bag_center = self._get_center(bag['bbox'])
            
            # Check distance to nearest person
            min_distance = min(
                euclidean(bag_center, person_pos)
                for person_pos in person_positions
            )
            
            # If bag is far from all people
            if min_distance > 150:  # 150 pixels threshold
                unattended_count += 1
        
        return unattended_count / max(len(bags), 1)
    
    def _analyze_crowd_density(self, poses):
        """
        Calculate crowd density risk
        """
        person_count = len(poses)
        
        if person_count < 5:
            return 0.0
        elif person_count < self.crowd_density_high:
            return 0.3
        else:
            return min(1.0, person_count / 25)  # Saturate at 25 people
    
    def _apply_context(self, context):
        """
        Apply contextual factors (time, location, events)
        """
        score = 0.0
        
        # Time of day (higher risk at night)
        if 'hour' in context:
            if 22 <= context['hour'] or context['hour'] <= 5:
                score += 0.3
        
        # High-risk location
        if context.get('location_risk') == 'high':
            score += 0.4
        
        # Special events
        if context.get('event_nearby'):
            score += 0.2
        
        return min(1.0, score)
    
    @staticmethod
    def _get_bbox_center(bbox):
        """Get center of bounding box"""
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
    
    @staticmethod
    def _get_center(bbox):
        # Same as above but used for objects
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
    
    def generate_alert(self, risk_score, risk_factors):
        """
        Generate alert based on risk score
        """
        if risk_score >= 75:
            level = 'CRITICAL'
            color = 'red'
        elif risk_score >= 50:
            level = 'HIGH'
            color = 'orange'
        elif risk_score >= 25:
            level = 'MEDIUM'
            color = 'yellow'
        else:
            level = 'LOW'
            color = 'green'
        
        # Find top contributing factors
        top_factors = sorted(
            risk_factors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            'level': level,
            'color': color,
            'score': round(risk_score, 2),
            'top_factors': [
                {
                    'name': factor[0].replace('_', ' ').title(),
                    'score': round(factor[1] * 100, 2)
                }
                for factor in top_factors
            ],
            'timestamp': None  # Will be added by API
        }

if __name__ == "__main__":
    import sys
    import os
    # Add project root to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    import cv2
    from models.detection.detector import UnifiedDetector
    
    print("Testing RiskScoringEngine...")
    try:
        detector = UnifiedDetector()
        risk_engine = RiskScoringEngine()
        
        # Test 1: Dummy Data
        print("\nTest 1: Dummy Interaction")
        dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
        detection = detector.process_frame(dummy_frame)
        risk_score, factors = risk_engine.calculate_risk(detection)
        print(f"Risk Score (Empty): {risk_score}")
        
        # Test 2: Sample Video (if exists)
        video_path = 'data/sample_videos/aggressive_behavior.mp4'
        import os
        if os.path.exists(video_path):
            print(f"\nTest 2: Processing {video_path}...")
            cap = cv2.VideoCapture(video_path)
            for i in range(30): # Process first second
                ret, frame = cap.read()
                if not ret: break
                
                det = detector.process_frame(frame)
                score, facts = risk_engine.calculate_risk(det)
                if i % 10 == 0:
                    print(f"Frame {i}: Score {score:.1f}")
            cap.release()
            print("Risk Engine Video Test Complete!")
        else:
            print(f"Skipping video test: {video_path} not found")
            
        print("\n✓ Risk Engine Verified")
            
    except Exception as e:
        print(f"Risk Engine Test Failed: {e}")
