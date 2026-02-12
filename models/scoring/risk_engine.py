import numpy as np
from collections import deque, defaultdict
import math

class RiskScoringEngine:
    """
    Advanced Multi-Factor Risk Scoring Engine
    Combines behavioral signals, context, and temporal tracking
    to calculate a unified threat score.
    """
    def __init__(self, fps=30, bypass_calibration=False):
        # Track person positions over time for behavior analysis
        self.person_history = defaultdict(lambda: deque(maxlen=300))  # 10 seconds at 30fps
        self.person_last_seen = {} # {tid: timestamp}
        
        # Track risk scores for temporal validation
        self.risk_history = deque(maxlen=30)
        
        # Performance/Context Settings
        self.fps = fps
        self.calibration_duration = 30 # seconds to learn "normal"
        self.start_time = None
        self.is_calibrated = bypass_calibration # If bypassed, we start calibrated
        self.bypass_calib = bypass_calibration
        self.baseline = {
            'avg_crowd': 0,
            'max_crowd': 0,
            'samples': 0,
            'proximity_median': 0
        }
        
        # Balanced weights (Sum = 1.0) as per Innovation Spec
        self.weights = {
            'weapon_detection': 0.45,   # High priority
            'aggressive_posture': 0.15,
            'proximity_violation': 0.10,
            'unattended_object': 0.15,
            'loitering': 0.05,
            'crowd_density': 0.05,
            'contextual': 0.05
        }
        
        # Time-Based Thresholds (Seconds)
        self.thresholds = {
            'loitering_time': 5.0,      # 5 seconds
            'unattended_time': 10.0,    # 10 seconds
            'crowd_multiplier': 2.0     # Alert if 2x more than baseline
        }
        
        self.crowd_limit = 15 # Default fallback
        
    def calculate_risk(self, detection_data, context=None):
        """
        Main pipeline: Detection -> Factor Analysis -> Multi-Signal Validation -> Score
        """
        # 0. Calibration Phase
        import time
        # Prefer context timestamp (from video), fallback to detection timestamp, then system time
        current_time = context.get('timestamp') if context else detection_data.get('timestamp', time.time())
        self._current_timestamp = current_time # Internal state for helpers
        if self.start_time is None: self.start_time = current_time
        
        elapsed = current_time - self.start_time
        if elapsed < self.calibration_duration and not self.is_calibrated:
            self._update_calibration(detection_data)
            # Return zeroed dictionary to avoid KeyErrors in callers
            zero_factors = {k: 0.0 for k in self.weights.keys()}
            return 0.0, zero_factors
        elif elapsed >= self.calibration_duration and not self.is_calibrated:
            self.is_calibrated = True
            self._finalize_calibration()

        # Update history
        self._update_history(detection_data['poses'])
        
        factors = {}
        
        # 1. Analyze Individual Factors
        factors['weapon_detection'] = self._analyze_weapons(
            detection_data.get('weapons', []), 
            detection_data.get('objects', [])
        )
        factors['aggressive_posture'] = self._analyze_aggression(detection_data['poses'])
        factors['proximity_violation'] = self._check_proximity(detection_data['poses'])
        factors['loitering'] = self._detect_loitering(detection_data['objects'])
        factors['unattended_object'] = self._detect_unattended_objects(detection_data['objects'], detection_data['poses'])
        factors['crowd_density'] = self._analyze_crowd_density(detection_data['poses'])
        
        if context:
            factors['contextual'] = self._apply_context(context)
        else:
            factors['contextual'] = 0.0
            
        # 2. Multi-Signal Validation
        # If a weapon is detected, we always want high risk, regardless of other factors
        if factors['weapon_detection'] > 0.5:
            suppression_factor = 1.0
        else:
            high_risk_count = sum(1 for v in factors.values() if v > 0.5)
            
            # If we have a VERY high signal in aggression, avoid suppression
            if factors.get('aggressive_posture', 0) > 0.75:
                suppression_factor = 1.0
            elif high_risk_count < 2 and factors['unattended_object'] < 0.5:
                suppression_factor = 0.7  
            else:
                suppression_factor = 1.0
            
        # 3. Calculate Weighted Sum
        raw_score = sum(factors[k] * self.weights.get(k, 0) for k in factors)
        
        # WEAPON ESCALATION (NEW): 
        # If a weapon is detected, we want to skip standard weighing and 
        # immediately escalate to a critical level.
        if factors.get('weapon_detection', 0) > 0.3:
            # Ensure at least 80% risk if a weapon is even slightly visible
            # Scales to 100% with weapon confidence
            print(f"DEBUG: Weapon Detected! Confidence: {factors['weapon_detection']:.2f}, Escalating Score...")
            raw_score = max(raw_score, 0.8 + (factors['weapon_detection'] * 0.2))
            suppression_factor = 1.0 # Never suppress a weapon threat
        
        # Apply suppression
        final_risk_score = raw_score * suppression_factor
        
        # 4. Temporal Smoothing (avoid flickering)
        # CRITICAL FIX: If weapon detected, bypass smoothing for INSTANT alert
        if factors.get('weapon_detection', 0) > 0.3:
             # Fill history with current score to maintain high alert state
             for _ in range(self.risk_history.maxlen):
                 self.risk_history.append(final_risk_score)
             smoothed_score = final_risk_score
        else:
             self.risk_history.append(final_risk_score)
             smoothed_score = np.mean(self.risk_history)
        
        # Return percentage (0-100)
        return min(100.0, smoothed_score * 100), factors

    def _analyze_weapons(self, weapons, objects=None):
        """Analyze weapon detections for risk impact"""
        max_conf = 0.0
        
        # 1. Check Custom Model Detections (Guns, etc.)
        if weapons:
            max_conf = max([w['confidence'] for w in weapons])
            
        # 2. Check Standard Model Detections (Knives, Bats)
        if objects:
            weapon_types = ['knife', 'baseball bat', 'scissors']
            for obj in objects:
                if obj.get('class') in weapon_types:
                    # Boost confidence slightly for these explicit threats being present
                    max_conf = max(max_conf, obj.get('confidence', 0.5))
                    
        return max_conf

    def _update_history(self, poses):
        """Update movement history for tracked persons"""
        current_ids = set()
        current_time = self._current_timestamp or 0
        
        for pose in poses:
            if 'track_id' in pose and pose['track_id'] != -1:
                tid = pose['track_id']
                center = self._get_bbox_center(pose['bbox'])
                # Store position with timestamp
                self.person_history[tid].append((center, current_time))
                current_ids.add(tid)
        
        # Cleanup old IDs
        for tid in list(self.person_history.keys()):
            if tid not in current_ids:
                # Keep history briefly or remove? Remove for now to save memory
                if len(self.person_history[tid]) > 0:
                     # Keep strict cleanup for demo
                     pass 

    def _analyze_aggression(self, poses):
        """
        Detect aggressive/fighting stance using YOLO pose estimation.
        Analyzes keypoint positions and confidence for behavioral patterns.
        """
        if not poses:
            return 0.0
            
        scores = []
        for pose in poses:
            kpts = np.array(pose['keypoints'])
            conf = np.array(pose['confidence'])
            
            # YOLO pose has 17 keypoints, require at least 11 for analysis
            if len(kpts) < 11 or np.mean(conf) < 0.35:
                continue
                
            aggression = 0.0
            
            # Context: Is person moving?
            is_moving = self._is_person_moving(pose)
            
            # Get person height for scale-invariant thresholds
            person_height = pose['bbox'][3] - pose['bbox'][1] if 'bbox' in pose else 100
            
            # Feature 1: Raised Arms (Wrists above Shoulders)
            # 5: L-Shldr, 6: R-Shldr, 9: L-Wrist, 10: R-Wrist
            left_wrist_up = kpts[9][1] < kpts[5][1]
            right_wrist_up = kpts[10][1] < kpts[6][1]
            
            if left_wrist_up or right_wrist_up:
                if is_moving:
                    aggression += 0.2 # Could be running, but still notable
                else:
                    aggression += 0.6 # Stationary hands up is very suspicious
            
            # Feature 2: Hands near head (Defensive/Fighting)
            # Use height-based threshold instead of fixed pixels
            nose = np.array(kpts[0])
            wrist_l = np.array(kpts[9])
            wrist_r = np.array(kpts[10])
            shoulder_l = np.array(kpts[5])
            shoulder_r = np.array(kpts[6])

            head_proximity_threshold = person_height * 0.25  # 25% of body height
            
            if np.linalg.norm(wrist_l - nose) < head_proximity_threshold or \
               np.linalg.norm(wrist_r - nose) < head_proximity_threshold:
                if not is_moving:
                    aggression += 0.7 # High threat if stationary with hands near head
                else:
                    aggression += 0.3 # Moving with hands up (could be running scared)
            
            # Feature 3: Strike Detection (Extended Arm)
            # Detect if arm is fully extended (wrist far from shoulder)
            # Index 5-9 (L-Shldr, L-Wrist), 6-10 (R-Shldr, R-Wrist)
            left_arm_ext = np.linalg.norm(wrist_l - shoulder_l) > (person_height * 0.4)
            right_arm_ext = np.linalg.norm(wrist_r - shoulder_r) > (person_height * 0.4)
            
            if left_arm_ext or right_arm_ext:
                aggression += 0.4 # Potential punch or strike
            
            # Feature 4: Widened Stance (Fighting/Defensive posture)
            # 15: L-Ankle, 16: R-Ankle
            if len(kpts) > 16:
                ankle_dist = abs(kpts[15][0] - kpts[16][0])
                if ankle_dist > (person_height * 0.4): # Feet spread wide
                    aggression += 0.3
            
            # Temporal weighting: High aggression must be sustained or rapid
            scores.append(min(1.0, aggression))
            
        return np.max(scores) if scores else 0.0

    def _check_proximity(self, poses):
        """
        Enhanced proximity check with person-to-person interaction validation.
        """
        if len(poses) < 2:
            return 0.0
            
        violations = 0
        total_pairs = 0
        
        # Calculate individual aggression scores first for interaction validation
        aggression_scores = {}
        for i, pose in enumerate(poses):
            aggression_scores[i] = self._analyze_aggression([pose])

        for i in range(len(poses)):
            for j in range(i+1, len(poses)):
                p1, p2 = poses[i], poses[j]
                
                c1 = np.array(self._get_bbox_center(p1['bbox']))
                c2 = np.array(self._get_bbox_center(p2['bbox']))
                dist = np.linalg.norm(c1 - c2)
                
                h1 = p1['bbox'][3] - p1['bbox'][1]
                h2 = p2['bbox'][3] - p2['bbox'][1]
                avg_height = (h1 + h2) / 2
                
                if dist < (avg_height * 0.5):
                    # INTERACTION VALIDATION: If both are aggressive and close, it's a fight
                    if aggression_scores[i] > 0.5 and aggression_scores[j] > 0.5:
                        violations += 3.0 # triple-weight confirmed interaction
                    else:
                        violations += 1.0
                
                total_pairs += 1
                
        if total_pairs == 0: return 0.0
        
        ratio = violations / total_pairs
        return min(1.0, ratio * 2.0)

    def _detect_loitering(self, objects):
        """
        Detect loitering using TIME-BASED displacement.
        """
        loiter_count = 0
        p_count = 0
        
        for obj in objects:
            if obj['class'] != 'person' or 'track_id' not in obj:
                continue
            
            p_count += 1
            tid = obj['track_id']
            history = self.person_history[tid]
            
            # Use timestamps instead of frame count for loitering duration
            if len(history) < 2: continue
            history_seconds = history[-1][1] - history[0][1]
            if history_seconds < self.thresholds['loitering_time']:
                continue
            
            # Calculate displacement relative to person scale
            box = obj['bbox']
            height = box[3] - box[1]
            
            # Displacement between start and end of loitering window using timestamps
            start_pos = np.array(history[0][0])
            end_pos = np.array(history[-1][0])
            displacement = np.linalg.norm(end_pos - start_pos)
            
            # Scale-invariant movement check: If moved < 25% of height over the window
            if displacement < (height * 0.25):
                loiter_count += 1
                
        if p_count == 0: return 0.0
        return min(1.0, loiter_count / p_count)

    def _update_calibration(self, det):
        """Record baseline environment stats during learning phase"""
        num_persons = len(det['poses'])
        self.baseline['avg_crowd'] += num_persons
        self.baseline['max_crowd'] = max(self.baseline['max_crowd'], num_persons)
        self.baseline['samples'] += 1

    def _finalize_calibration(self):
        """Set thresholds based on observed environment"""
        if self.baseline['samples'] > 0:
            avg = self.baseline['avg_crowd'] / self.baseline['samples']
            # Adaptive crowd limit: 3x average or minimum 5
            self.crowd_limit = max(5, int(avg * self.thresholds['crowd_multiplier']))
            print(f"DEBUG: Calibration complete. Baseline Avg Crowd: {avg:.1f}, New Limit: {self.crowd_limit}")

    def _get_factor_confidence(self, name, data):
        """
        Calculate confidence (0-1) for a specific detection.
        Example: Aggression confidence increases with more keypoints.
        """
        if name == 'aggressive_posture':
            # Mean confidence of key hand/arm keypoints
            if not data: return 0.0
            kpt_confs = data[0].get('confidence', [])
            if len(kpt_confs) < 11: return 0.3
            arm_idxs = [5, 6, 7, 8, 9, 10] # Shoulder to hand
            relevant_confs = [kpt_confs[i] for i in arm_idxs if i < len(kpt_confs)]
            return np.mean(relevant_confs) if relevant_confs else 0.5
        
        return 1.0 # Default fallback

    def _detect_unattended_objects(self, objects, poses):
        """
        Detect bags far from any person.
        """
        bags = [o for o in objects if o['class'] in ['backpack', 'suitcase', 'handbag']]
        if not bags: return 0.0
        
        if not poses: return 1.0 # Bags but no people = Risk
        
        person_centers = [np.array(self._get_bbox_center(p['bbox'])) for p in poses]
        
        unattended = 0
        for bag in bags:
            bag_center = np.array(self._get_center(bag['bbox']))
            bag_height = bag['bbox'][3] - bag['bbox'][1]
            
            # Distance to nearest person
            dists = [np.linalg.norm(bag_center - p) for p in person_centers]
            min_dist = min(dists)
            
            # Threshold: 2x Bag Height
            if min_dist > (bag_height * 3.0): 
                unattended += 1
                
        return unattended / len(bags)

    def _analyze_crowd_density(self, poses):
        count = len(poses)
        return min(1.0, count / self.crowd_limit)

    def _apply_context(self, context):
        score = 0.0
        if context.get('hour', 12) > 22 or context.get('hour', 12) < 5:
            score += 0.4
        return min(1.0, score)

    def _is_person_moving(self, pose):
        """Check if track ID has significant movement history (scale-invariant)"""
        if 'track_id' not in pose or pose['track_id'] == -1:
            return False  # Assume static if no track info
            
        tid = pose['track_id']
        history = self.person_history[tid]
        
        if len(history) < 5:
            return False
        
        # Calculate displacement relative to height over the buffer
        person_height = pose['bbox'][3] - pose['bbox'][1] if 'bbox' in pose else 100
        movement_threshold = person_height * 0.2 # 20% of height displacement
        
        start_pos = np.array(history[0][0])
        end_pos = np.array(history[-1][0])
        recent_movement = np.linalg.norm(end_pos - start_pos)
        
        return recent_movement > movement_threshold

    @staticmethod
    def _get_bbox_center(bbox):
        return [(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2]

    @staticmethod
    def _get_center(bbox):
        return [(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2]
    
    def generate_alert(self, risk_score, risk_factors):
        """
        Generate alert dictionary from risk score and contributing factors.
        Used by both live feed and video processing.
        """
        # Determine alert level based on risk score
        if risk_score >= 75:
            level = 'critical'
        elif risk_score >= 50:
            level = 'high'
        elif risk_score >= 25:
            level = 'medium'
        else:
            level = 'low'
        
        # Get top 3 contributing factors (sorted by impact)
        sorted_factors = sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)
        top_factors = [f"{k.replace('_', ' ').title()}: {int(v*100)}%" for k, v in sorted_factors[:3] if v > 0.1]
        
        return {
            'level': level,
            'score': risk_score,
            'top_factors': top_factors,
            'all_factors': risk_factors,
            'description': self._generate_threat_description(risk_factors, risk_score)
        }
    
    def _generate_threat_description(self, factors, score):
        """
        Generate human-readable threat description based on active factors.
        """
        active_threats = []
        
        if factors.get('weapon_detection', 0) > 0.5:
            active_threats.append('WEAPON DETECTED')
        if factors.get('aggressive_posture', 0) > 0.5:
            active_threats.append('aggressive behavior detected')
        if factors.get('proximity_violation', 0) > 0.5:
            active_threats.append('people in close proximity')
        if factors.get('loitering', 0) > 0.5:
            active_threats.append('suspicious loitering')
        if factors.get('unattended_object', 0) > 0.5:
            active_threats.append('unattended objects')
        if factors.get('crowd_density', 0) > 0.7:
            active_threats.append('high crowd density')
        
        if not active_threats:
            return 'Low risk situation'
        
        if factors.get('weapon_detection', 0) > 0.5:
            return f"CRITICAL THREAT: {', '.join(active_threats)}"
        elif score >= 75:
            return f"CRITICAL: {', '.join(active_threats)}"
        elif score >= 50:
            return f"HIGH RISK: {', '.join(active_threats)}"
        else:
            return f"Elevated risk: {', '.join(active_threats)}"
    
    def detect_motion_patterns(self, poses):
        """
        Detect aggressive motion vectors (sudden movements, direction changes).
        Optimized for high-activity environments like airports.
        """
        patterns = []
        
        for pose in poses:
            if 'track_id' not in pose or pose['track_id'] == -1:
                continue
                
            tid = pose['track_id']
            history = self.person_history[tid]
            
            # Require at least 1s of history for quality analysis
            if len(history) < 2 or (history[-1][1] - history[0][1]) < 1.0:
                continue
            
            # Get current person scale for normalization
            height = pose['bbox'][3] - pose['bbox'][1] if 'bbox' in pose else 100
            
            # 1. Analyze Acceleration
            velocities = []
            for i in range(1, len(history)):
                # history[i] is (pos, time)
                dist = np.linalg.norm(np.array(history[i][0]) - np.array(history[i-1][0]))
                dt = history[i][1] - history[i-1][1]
                if dt > 0:
                    velocities.append(dist / dt)
            
            if len(velocities) >= 5:
                recent_vel = np.mean(velocities[-3:])
                prev_vel = np.mean(velocities[-10:-3]) if len(velocities) > 10 else velocities[0]
                
                # Strict check: 3x speed increase AND velocity > 50% of height per second
                if recent_vel > prev_vel * 3.0 and recent_vel > (height * 0.5):
                    patterns.append(f"Rapid acceleration detected (Track {tid})")
            
            # 2. Analyze Direction (Filter out normal walking jitter)
            if len(history) >= 10:
                directions = []
                for i in range(1, len(history)):
                    dx = history[i][0][0] - history[i-1][0][0]
                    dy = history[i][0][1] - history[i-1][0][1]
                    
                    if abs(dx) > (height * 0.05) or abs(dy) > (height * 0.05):
                        angle = np.arctan2(dy, dx)
                        directions.append(angle)
                
                if len(directions) >= 6:
                    reversals = 0
                    for i in range(1, len(directions)):
                        angle_diff = abs(directions[i] - directions[i-1])
                        if angle_diff > np.pi:
                            angle_diff = 2 * np.pi - angle_diff
                        
                        # Look for clear reversals (> 110 degrees)
                        if angle_diff > (np.pi * 0.6): 
                            reversals += 1
                    
                    # Require 3 clear reversals for "erratic" label
                    if reversals >= 3:
                        patterns.append(f"Erratic movement pattern (Track {tid})")
        
        return patterns
