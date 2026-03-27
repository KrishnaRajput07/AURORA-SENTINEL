import numpy as np
from collections import deque, defaultdict
import math
import yaml
import os
from pathlib import Path

class RiskScoringEngine:
    """
    Advanced Multi-Factor Risk Scoring Engine
    Combines behavioral signals, context, and temporal tracking
    to calculate a unified threat score.
    """
    def __init__(self, fps=30, bypass_calibration=False, config_path=None):
        """
        Initialize Risk Scoring Engine.
        
        Args:
            fps: Frames per second of video
            bypass_calibration: Skip calibration phase
            config_path: Path to YAML config file (optional)
        """
        # Track person positions over time for behavior analysis
        self.person_history = defaultdict(lambda: deque(maxlen=300))  # 10 seconds at 30fps
        self.person_last_seen = {} # {tid: timestamp}
        
        # Track risk scores for temporal validation (enhanced: 20-frame window)
        self.risk_history = deque(maxlen=20)
        
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
        
        # Load thresholds from config file or use defaults
        self.thresholds = self._load_thresholds(config_path)
        
        # Log loaded thresholds
        print(f"Risk Engine initialized with thresholds:")
        print(f"  Temporal: {self.thresholds['temporal_validation_ratio']*100:.0f}% ratio, "
              f"{self.thresholds['temporal_window_size']} frames, "
              f"{self.thresholds['temporal_suppression_max']} max suppression")
        print(f"  Proximity: {self.thresholds['proximity_distance']*100:.0f}% distance, "
              f"{self.thresholds['proximity_escalation']}x escalation")
        print(f"  Aggression: raised_arms={self.thresholds['aggression_raised_arms']}, "
              f"strike={self.thresholds['aggression_strike']}, "
              f"fighting_stance={self.thresholds['aggression_fighting_stance']}")
        
        # Per-person keypoint velocity tracking for strike detection
        self.keypoint_history = defaultdict(lambda: {
            'wrists': deque(maxlen=10),
            'ankles': deque(maxlen=10)
        })
        
        # Grappling state tracking
        self.grappling_history = defaultdict(int)  # {(tid1, tid2): frame_count}
        
        # Balanced weights (Sum = 1.0) as per Innovation Spec
        self.weights = {
            'weapon_detection': 0.40,   # Adjusted down slightly to accommodate fire
            # Reduced to limit noisy "overfire" from combat-like pose jitter.
            'aggressive_posture': 0.20,
            'fire_smoke': 0.45,         # High weight for fire/smoke
            'proximity_violation': 0.15,
            'unattended_object': 0.15,
            'loitering': 0.10,
            'crowd_density': 0.05,
            'contextual': 0.05
        }
        
        # Immediate-threat handling for deterministic detectors (fire/weapon).
        # These thresholds are intentionally conservative to avoid under-reacting
        # to clear hazards while still filtering weak/noisy detections.
        self.fire_threat_thresholds = {
            'moderate': 0.50,
            'high': 0.65,
            'critical': 0.80,
        }
        self.weapon_threat_thresholds = {
            'high': 0.50,
            'critical': 0.70,
        }
        self.instant_threat_confidence_floor = 0.85
        
        self.strict_mode = True # Always on for this request
        
        self.crowd_limit = 15 # Default fallback
    
    def _load_thresholds(self, config_path=None):
        """
        Load thresholds from YAML config file or use defaults.
        
        Args:
            config_path: Path to YAML config file (optional)
            
        Returns:
            Dict of threshold values
        """
        # Default thresholds (enhanced for fight detection)
        defaults = {
            'temporal_validation_ratio': 0.30,
            'temporal_window_size': 20,
            'temporal_suppression_max': 0.4,
            'proximity_distance': 0.40,
            'proximity_escalation': 3.0,
            'strike_velocity': 0.40,
            'grappling_distance': 0.40,
            'grappling_overlap': 0.60,
            'aggression_raised_arms': 0.7,
            'aggression_strike': 0.5,
            'aggression_fighting_stance': 0.6,
            'loitering_time': 15.0,
            'unattended_time': 8.0,
            'crowd_multiplier': 1.2,
            'proximity_alert': 0.45,
        }
        
        # Try to load from config file
        if config_path is None:
            # Try default location
            config_path = Path(__file__).parent.parent.parent / 'config' / 'risk_thresholds.yaml'
        
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Extract values from nested structure
                thresholds = defaults.copy()
                
                if 'temporal' in config:
                    thresholds['temporal_validation_ratio'] = config['temporal'].get('validation_ratio', defaults['temporal_validation_ratio'])
                    thresholds['temporal_window_size'] = config['temporal'].get('window_size', defaults['temporal_window_size'])
                    thresholds['temporal_suppression_max'] = config['temporal'].get('suppression_max', defaults['temporal_suppression_max'])
                
                if 'proximity' in config:
                    thresholds['proximity_distance'] = config['proximity'].get('distance', defaults['proximity_distance'])
                    thresholds['proximity_escalation'] = config['proximity'].get('escalation', defaults['proximity_escalation'])
                
                if 'strike' in config:
                    thresholds['strike_velocity'] = config['strike'].get('velocity', defaults['strike_velocity'])
                
                if 'grappling' in config:
                    thresholds['grappling_distance'] = config['grappling'].get('distance', defaults['grappling_distance'])
                    thresholds['grappling_overlap'] = config['grappling'].get('overlap', defaults['grappling_overlap'])
                
                if 'aggression' in config:
                    thresholds['aggression_raised_arms'] = config['aggression'].get('raised_arms', defaults['aggression_raised_arms'])
                    thresholds['aggression_strike'] = config['aggression'].get('strike', defaults['aggression_strike'])
                    thresholds['aggression_fighting_stance'] = config['aggression'].get('fighting_stance', defaults['aggression_fighting_stance'])
                
                # Validate thresholds
                self._validate_thresholds(thresholds)
                
                print(f"Loaded thresholds from: {config_path}")
                return thresholds
                
            except Exception as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")
                print("Using default thresholds")
                return defaults
        else:
            print(f"Config file not found at {config_path}, using defaults")
            return defaults
    
    def _validate_thresholds(self, thresholds):
        """
        Validate that threshold values are within acceptable ranges.
        
        Args:
            thresholds: Dict of threshold values
            
        Raises:
            ValueError if any threshold is out of range
        """
        # Score values should be 0.0-1.0
        score_params = [
            'temporal_validation_ratio', 'temporal_suppression_max',
            'proximity_distance', 'strike_velocity', 'grappling_distance',
            'grappling_overlap', 'aggression_raised_arms', 'aggression_strike',
            'aggression_fighting_stance'
        ]
        
        for param in score_params:
            if param in thresholds:
                value = thresholds[param]
                if not (0.0 <= value <= 1.0):
                    raise ValueError(f"Threshold '{param}' must be between 0.0 and 1.0, got {value}")
        
        # Distance/multiplier values should be positive
        positive_params = [
            'proximity_escalation', 'temporal_window_size',
            'loitering_time', 'unattended_time', 'crowd_multiplier'
        ]
        
        for param in positive_params:
            if param in thresholds:
                value = thresholds[param]
                if value <= 0:
                    raise ValueError(f"Threshold '{param}' must be positive, got {value}")
        
    def calculate_risk(self, detection_data, context=None):
        """
        Main pipeline: Detection -> Factor Analysis -> Multi-Signal Validation -> Score
        """
        # 0. Calibration Phase
        import time
        # Prefer context timestamp (from video), fallback to detection timestamp, then system time
        current_time = context.get('timestamp') if (context and context.get('timestamp') is not None) else detection_data.get('timestamp', time.time())
        self._current_timestamp = current_time # Internal state for helpers
        if self.start_time is None: self.start_time = current_time
        
        elapsed = current_time - self.start_time
        if elapsed < self.calibration_duration and not self.is_calibrated:
            self._update_calibration(detection_data)

            # Do not suppress clear hazards during calibration.
            fire_conf_now = self._analyze_fire(detection_data.get('fire', []))
            weapon_conf_now = self._analyze_weapons(
                detection_data.get('weapons', []),
                detection_data.get('objects', []),
            )
            emergency_score = self._estimate_immediate_threat_score(fire_conf_now, weapon_conf_now)
            if emergency_score > 0:
                emergency_factors = {k: 0.0 for k in self.weights.keys()}
                emergency_factors['fire_smoke'] = fire_conf_now
                emergency_factors['weapon_detection'] = weapon_conf_now
                self.risk_history.append(emergency_score)
                return min(100.0, emergency_score * 100), emergency_factors

            # Return zeroed dictionary to avoid KeyErrors in callers
            zero_factors = {k: 0.0 for k in self.weights.keys()}
            return 0.0, zero_factors
        elif elapsed >= self.calibration_duration and not self.is_calibrated:
            self.is_calibrated = True
            self._finalize_calibration()

        # Update history
        self._update_history(detection_data['poses'])
        self._update_keypoint_history(detection_data['poses'])
        
        factors = {}
        
        # 1. Analyze Individual Factors
        factors['weapon_detection'] = self._analyze_weapons(
            detection_data.get('weapons', []), 
            detection_data.get('objects', [])
        )
        factors['aggressive_posture'] = self._analyze_aggression(detection_data['poses'])
        factors['fire_smoke'] = self._analyze_fire(detection_data.get('fire', []))
        factors['proximity_violation'] = self._check_proximity(detection_data['poses'])
        factors['loitering'] = self._detect_loitering(detection_data['objects'])
        factors['unattended_object'] = self._detect_unattended_objects(detection_data['objects'], detection_data['poses'])
        factors['crowd_density'] = self._analyze_crowd_density(detection_data['poses'])
        
        if context:
            factors['contextual'] = self._apply_context(context)
        else:
            factors['contextual'] = 0.0
            
        # 2. Sensitivity Adjustment (NEW)
        # Apply user-defined sensitivity if provided in context
        sensitivity = context.get('sensitivity', 1.0) if context else 1.0
        # Sensitivity 0.5 = 50% risk, Sensitivity 2.0 = 200% risk (capped)
        
        # 3. ENHANCED Multi-Signal Validation with Suppression Factor Bypass
        # Bypass suppression for high-confidence combat indicators
        aggression = factors.get('aggressive_posture', 0) or 0
        weapon_conf = factors.get('weapon_detection', 0) or 0
        fire_conf = factors.get('fire_smoke', 0) or 0
        
        if weapon_conf > 0.4 or fire_conf >= self.fire_threat_thresholds['moderate']:
            suppression_factor = 1.0  # Deterministic detector bypass
        elif aggression > 0.7:
            suppression_factor = 1.0  # High aggression bypasses suppression
        else:
            high_risk_count = sum(1 for v in factors.values() if v is not None and v > 0.4)
            
            # Enhanced: If aggression > 0.5 but < 0.6, apply max 0.8 suppression (not 0.6)
            if aggression > 0.5:
                suppression_factor = 0.8
            elif high_risk_count < 1:
                suppression_factor = 0.6
            else:
                suppression_factor = 1.0
            
        # 4. Calculate Weighted Sum (Aggressive normalization)
        raw_score = sum((factors[k] or 0) * self.weights.get(k, 0) for k in factors)
        
        # Apply Sensitivity
        raw_score *= (sensitivity * 1.2) # Multiplier for "Smarter/Stricter" request
        
        # WEAPON ESCALATION: 
        weapon_conf = factors.get('weapon_detection', 0) or 0
        if weapon_conf >= self.weapon_threat_thresholds['critical']: # Hardened to prevent false COCO triggers
            raw_score = max(raw_score, 0.88) # Immediate Serious Alert
            suppression_factor = 1.0 
        elif weapon_conf >= self.weapon_threat_thresholds['high']:
            raw_score = max(raw_score, 0.65)
            suppression_factor = 1.0

        # FIRE ESCALATION:
        fire_conf = factors.get('fire_smoke', 0) or 0
        if fire_conf >= self.fire_threat_thresholds['critical']:
            raw_score = max(raw_score, 0.92)
            suppression_factor = 1.0
        elif fire_conf >= self.fire_threat_thresholds['high']:
            raw_score = max(raw_score, 0.78)
            suppression_factor = 1.0
        elif fire_conf >= self.fire_threat_thresholds['moderate']:
            raw_score = max(raw_score, 0.60)
            suppression_factor = 1.0
        
        # ENHANCED FIGHT DETECTION: Aggression + Proximity Escalation
        aggression = factors.get('aggressive_posture', 0) or 0
        proximity = factors.get('proximity_violation', 0) or 0
        
        # Minimum 70% only for higher-confirmed aggression + close proximity.
        if aggression > 0.7 and proximity > 0.35:
            raw_score = max(raw_score, 0.70)
            suppression_factor = 1.0
            print(f"DEBUG: High aggression ({aggression:.2f}) + proximity detected. Escalating to 70%+")
        
        # Strike + Proximity Escalation: Add a smaller bump only for strong strike velocity.
        strike_indicators = self._detect_strike_velocity(detection_data['poses'])
        if len(strike_indicators) > 0 and proximity > 0.3:
            max_velocity = max((v.get('velocity', 0.0) or 0.0) for v in strike_indicators.values())
            if max_velocity > (self.thresholds['strike_velocity'] * 1.25):
                raw_score += 0.2
                print(f"DEBUG: Strike motion + proximity detected. Escalating by 0.2")
        
        # 4. Enhanced Grappling Detection
        grappling_score = self._detect_grappling(detection_data['poses'])
        if grappling_score > 0:
            factors['grappling'] = grappling_score
            raw_score = max(raw_score, 0.65)  # Minimum 65% for grappling
            suppression_factor = 1.0
            print(f"DEBUG: Grappling/Clinching detected (score: {grappling_score:.2f}). Escalating...")

        # Check for Chasing/Following Patterns
        poses = detection_data['poses']
        chase_score = self._detect_chasing(poses)
        if chase_score > 0.5:
            factors['chasing'] = chase_score
            raw_score = max(raw_score, 0.5 + (chase_score * 0.3))

        # 4. Contradiction Detection (Innovation #23: Safety through Skepticism)
        # High aggression (fast) + High loitering (static) = CONTRADICTION
        if factors.get('aggressive_posture', 0) > 0.7 and factors.get('loitering', 0) > 0.6:
            print("DEBUG: Contradiction detected (High Aggression + High Loitering). Reducing scores.")
            factors['aggressive_posture'] *= 0.5
            factors['loitering'] *= 0.5
            raw_score *= 0.7 # Global dampening for contradictory signals

        # 4.5 Confidence Scoring & Decay (Innovation #5 / #24)
        # Higher agreement between signals = higher confidence
        is_blurry = any(det.get('is_blurry', False) for det in detection_data.get('objects', []))
        quality_multiplier = 0.7 if is_blurry else 1.0
        if is_blurry:
             print("DEBUG: Forensic Confidence Decay active (Blurry Frame).")

        # Ensure all factor values are numbers (not None)
        agreement_bonus = sum(1 for v in factors.values() if v is not None and v > 0.4) * 0.1
        temporal_bonus = (len(self.risk_history) / self.risk_history.maxlen) * 0.2
        confidence_score = min(1.0, (0.5 + agreement_bonus + temporal_bonus) * quality_multiplier)

        instant_threat_detected = (
            weapon_conf >= self.weapon_threat_thresholds['high']
            or fire_conf >= self.fire_threat_thresholds['moderate']
        )
        critical_instant_threat = (
            weapon_conf >= self.weapon_threat_thresholds['critical']
            or fire_conf >= self.fire_threat_thresholds['critical']
        )
        if instant_threat_detected:
            confidence_score = max(confidence_score, self.instant_threat_confidence_floor)
        
        # Apply confidence to final risk
        final_risk_score = raw_score * suppression_factor * confidence_score
        
        # 5. Temporal Validation (Enhanced: 20-frame window, 30% ratio, 0.4 max suppression)
        self.risk_history.append(final_risk_score)
        
        # Require sustained risk for validation (20 frames minimum)
        # Enhanced thresholds for better fight detection
        if len(self.risk_history) >= self.thresholds['temporal_window_size']:
             # Calculate percentage of frames in history that were high risk (> 0.4)
             high_risk_frames = sum(1 for r in self.risk_history if r > 0.4)
             validation_ratio = high_risk_frames / len(self.risk_history)
             
             if final_risk_score > 0.75:
                 # Critical deterministic threats bypass temporal suppression.
                 if (not critical_instant_threat) and validation_ratio < self.thresholds['temporal_validation_ratio']:
                     final_risk_score *= self.thresholds['temporal_suppression_max']  # Max 0.4 suppression (was 0.6)
             elif final_risk_score > 0.4:
                 # Medium threats need 30% support.
                 if (not instant_threat_detected) and validation_ratio < self.thresholds['temporal_validation_ratio']:
                     final_risk_score *= 0.7
                     
        # Use mean for smoothed output
        smoothed_score = np.mean(self.risk_history)
        if instant_threat_detected:
            # Keep smoothing but avoid masking active high-confidence hazards.
            smoothed_score = max(smoothed_score, final_risk_score * 0.9)
        
        # Return percentage (0-100)
        return min(100.0, smoothed_score * 100), factors

    def _analyze_weapons(self, weapons, objects=None):
        """Analyze weapon detections for risk impact with strict validation"""
        max_conf = 0.0
        
        # 1. Check Specialized Model Detections (Guns, etc.)
        # Only trust if confidence is high (> 0.5 for automatic escalation)
        if weapons:
            max_conf = max([w['confidence'] for w in weapons])
            
        # 2. Check Standard Model Detections (Knives, Bats, Scissors)
        if objects:
            weapon_types = ['knife', 'baseball bat', 'scissors']
            for obj in objects:
                if obj.get('class') in weapon_types:
                    obj_conf = obj.get('confidence', 0)
                    if obj_conf > 0.45:  # Lower threshold — knives/scissors are real threats
                        # No multiplier penalty: treat COCO knife/scissors at full confidence
                        max_conf = max(max_conf, obj_conf)
                    
        return max_conf

    def _analyze_fire(self, fire_detections):
        """Analyze fire and smoke for risk impact."""
        if not fire_detections:
            return 0.0
        
        # We prioritize 'fire' detections over 'smoke'
        max_fire_conf = 0.0
        for det in fire_detections:
            conf = det.get('confidence', 0)
            if det.get('class') == 'fire':
                max_fire_conf = max(max_fire_conf, conf)
            elif det.get('class') == 'smoke':
                # Smoke has 60% relative impact of fire
                max_fire_conf = max(max_fire_conf, conf * 0.6)
            else:
                # Other classes (unknown) have 40% impact
                max_fire_conf = max(max_fire_conf, conf * 0.4)
                
        return max_fire_conf

    def _estimate_immediate_threat_score(self, fire_conf, weapon_conf):
        """
        Estimate emergency raw risk (0-1) for deterministic hazards.
        Used during calibration and as a shared policy baseline.
        """
        threat_score = 0.0

        if weapon_conf >= self.weapon_threat_thresholds['critical']:
            threat_score = max(threat_score, 0.88)
        elif weapon_conf >= self.weapon_threat_thresholds['high']:
            threat_score = max(threat_score, 0.65)

        if fire_conf >= self.fire_threat_thresholds['critical']:
            threat_score = max(threat_score, 0.92)
        elif fire_conf >= self.fire_threat_thresholds['high']:
            threat_score = max(threat_score, 0.78)
        elif fire_conf >= self.fire_threat_thresholds['moderate']:
            threat_score = max(threat_score, 0.60)

        return min(1.0, threat_score)

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
    
    def _update_keypoint_history(self, poses):
        """
        Update per-keypoint velocity history for strike detection.
        Tracks wrist and ankle positions per person using track_id.
        """
        for pose in poses:
            if 'track_id' not in pose or pose['track_id'] == -1:
                continue
                
            tid = pose['track_id']
            kpts = np.array(pose['keypoints'])
            conf = np.array(pose['confidence'])
            
            # YOLO pose keypoints: 9=L-Wrist, 10=R-Wrist, 15=L-Ankle, 16=R-Ankle
            if len(kpts) < 17:
                continue
                
            # Get person height for normalization
            person_height = pose['bbox'][3] - pose['bbox'][1] if 'bbox' in pose else 100
            
            # Store normalized wrist positions
            if conf[9] > 0.3:  # L-Wrist confidence check
                normalized_pos = kpts[9] / person_height
                self.keypoint_history[tid]['wrists'].append(('left', normalized_pos, self._current_timestamp))
                
            if conf[10] > 0.3:  # R-Wrist confidence check
                normalized_pos = kpts[10] / person_height
                self.keypoint_history[tid]['wrists'].append(('right', normalized_pos, self._current_timestamp))
                
            # Store normalized ankle positions
            if len(kpts) > 15 and conf[15] > 0.3:  # L-Ankle
                normalized_pos = kpts[15] / person_height
                self.keypoint_history[tid]['ankles'].append(('left', normalized_pos, self._current_timestamp))
                
            if len(kpts) > 16 and conf[16] > 0.3:  # R-Ankle
                normalized_pos = kpts[16] / person_height
                self.keypoint_history[tid]['ankles'].append(('right', normalized_pos, self._current_timestamp))
    
    def _detect_strike_velocity(self, poses):
        """
        Detect strike motion by analyzing rapid limb movements.
        Returns dict of {track_id: {'has_strike': bool, 'velocity': float, 'limb': str}}
        """
        strike_indicators = {}
        # Same-frame left/right samples get appended back-to-back to the shared deque.
        # To avoid "velocity" computed from limb switching, we require a small time delta.
        min_strike_dt_sec = 0.01
        
        for pose in poses:
            if 'track_id' not in pose or pose['track_id'] == -1:
                continue
                
            tid = pose['track_id']
            person_height = pose['bbox'][3] - pose['bbox'][1] if 'bbox' in pose else 100
            
            # Check wrist velocity
            wrist_history = self.keypoint_history[tid]['wrists']
            if len(wrist_history) >= 2:
                recent = wrist_history[-1]
                recent_side = recent[0]
                # Find the most recent previous sample for the SAME side with enough dt.
                previous = None
                for i in range(len(wrist_history) - 2, -1, -1):
                    cand = wrist_history[i]
                    if cand[0] != recent_side:
                        continue
                    if (recent[2] - cand[2]) <= min_strike_dt_sec:
                        continue
                    previous = cand
                    break

                if previous is not None:
                    displacement = np.linalg.norm(recent[1] - previous[1])
                    if displacement > self.thresholds['strike_velocity']:
                        strike_indicators[tid] = {
                            'has_strike': True,
                            'velocity': displacement,
                            'limb': 'wrist',
                            'side': recent_side  # 'left' or 'right'
                        }
                        continue
            
            # Check ankle velocity (kicks)
            ankle_history = self.keypoint_history[tid]['ankles']
            if len(ankle_history) >= 2:
                recent = ankle_history[-1]
                recent_side = recent[0]
                previous = None
                for i in range(len(ankle_history) - 2, -1, -1):
                    cand = ankle_history[i]
                    if cand[0] != recent_side:
                        continue
                    if (recent[2] - cand[2]) <= min_strike_dt_sec:
                        continue
                    previous = cand
                    break

                if previous is not None:
                    displacement = np.linalg.norm(recent[1] - previous[1])
                    if displacement > self.thresholds['strike_velocity']:
                        strike_indicators[tid] = {
                            'has_strike': True,
                            'velocity': displacement,
                            'limb': 'ankle',
                            'side': recent_side
                        }
        
        return strike_indicators

    def _analyze_aggression(self, poses):
        """
        ENHANCED FIGHT DETECTION: Aggressive pose detection with NO discrimination.
        Detects ALL combat-like behavior (boxing, sparring, real fights) equally.
        The AI intelligence layer will handle smart discrimination.
        
        OPTIMIZED: Reduced redundant calculations, cached values.
        """
        if not poses:
            return 0.0
        
        # Get strike indicators once (cached)
        strike_indicators = self._detect_strike_velocity(poses)
        
        scores = []
        for pose in poses:
            kpts = np.array(pose['keypoints'])
            conf = np.array(pose['confidence'])
            
            # YOLO pose has 17 keypoints, require at least 11 for analysis
            if len(kpts) < 11 or np.mean(conf) < 0.35:
                continue
                
            aggression = 0.0
            tid = pose.get('track_id')
            
            # Get person height once (cached)
            person_height = pose['bbox'][3] - pose['bbox'][1] if 'bbox' in pose else 100
            
            # Pre-calculate commonly used values
            ankle_dist = abs(kpts[15][0] - kpts[16][0]) if len(kpts) > 16 else 0
            wide_stance = ankle_dist > (person_height * 0.3)
            
            # FEATURE 1: Raised Arms + Widened Stance (Score: 0.7)
            left_wrist_up = kpts[9][1] < kpts[5][1]
            right_wrist_up = kpts[10][1] < kpts[6][1]
            
            # Both arms raised + wide stance = 0.7 (AGGRESSIVE - no discrimination)
            if left_wrist_up and right_wrist_up and wide_stance:
                aggression += self.thresholds['aggression_raised_arms']  # 0.7
            elif (left_wrist_up or right_wrist_up) and wide_stance:
                aggression += 0.5  # One arm raised + stance
            elif left_wrist_up and right_wrist_up:
                aggression += 0.6  # Both arms raised
            
            # FEATURE 2: Fighting Stance (Hands near head + wide feet) (Score: 0.6)
            nose = kpts[0]
            wrist_l = kpts[9]
            wrist_r = kpts[10]
            
            head_proximity_threshold = person_height * 0.25  # 25% of body height
            hands_near_head = (np.linalg.norm(wrist_l - nose) < head_proximity_threshold or 
                             np.linalg.norm(wrist_r - nose) < head_proximity_threshold)
            
            if hands_near_head and wide_stance:
                aggression += self.thresholds['aggression_fighting_stance']  # 0.6
            elif hands_near_head:
                aggression += 0.4  # Hands near head only
            
            # FEATURE 3: Strike Motion Detection (Score: 0.5 + 0.4 if extended)
            if tid in strike_indicators:
                aggression += self.thresholds['aggression_strike']  # 0.5 base for strike
                
                # Check if arm is extended during strike (cached calculation)
                shoulder_l = kpts[5]
                shoulder_r = kpts[6]
                left_arm_ext = np.linalg.norm(wrist_l - shoulder_l) > (person_height * 0.4)
                right_arm_ext = np.linalg.norm(wrist_r - shoulder_r) > (person_height * 0.4)
                
                if left_arm_ext or right_arm_ext:
                    aggression += 0.4  # Additional score for extended arm during strike
            else:
                # FEATURE 4: Extended Arms (Potential strike/push) - only if no strike detected
                shoulder_l = kpts[5]
                shoulder_r = kpts[6]
                left_arm_ext = np.linalg.norm(wrist_l - shoulder_l) > (person_height * 0.4)
                right_arm_ext = np.linalg.norm(wrist_r - shoulder_r) > (person_height * 0.4)
                
                if left_arm_ext and right_arm_ext:
                    aggression += 0.5  # Both arms extended (shoving/double punch)
                elif left_arm_ext or right_arm_ext:
                    aggression += 0.3  # Single arm extended
            
            # FEATURE 5: Wide Stance alone (defensive/ready position)
            if wide_stance and aggression < 0.3:  # Only if not already counted
                aggression += 0.3
            
            # Accumulate scores up to maximum of 1.0
            scores.append(min(1.0, aggression))
            
        return np.max(scores) if scores else 0.0

    def _check_proximity(self, poses):
        """
        ENHANCED FIGHT DETECTION: Proximity check with 40% threshold and escalation.
        Detects close combat situations and escalates when combined with aggression.
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
                
                # Calculate distance between persons
                dist = self._calculate_distance(p1, p2)
                
                h1 = p1['bbox'][3] - p1['bbox'][1]
                h2 = p2['bbox'][3] - p2['bbox'][1]
                avg_height = (h1 + h2) / 2
                
                # ENHANCED: 40% of average height threshold (reduced from 60%)
                if dist < (avg_height * self.thresholds['proximity_distance']):
                    # ESCALATION: If either person shows aggression > 0.3, apply 3.0x weight
                    if aggression_scores[i] > 0.3 or aggression_scores[j] > 0.3:
                        violations += self.thresholds['proximity_escalation']  # 3.0
                    else:
                        violations += 1.5  # Baseline weight for close proximity
                
                total_pairs += 1
                
        if total_pairs == 0: return 0.0
        
        # Return proportional score
        ratio = violations / total_pairs
        return min(1.0, ratio)
    
    def _detect_grappling(self, poses):
        """
        ENHANCED FIGHT DETECTION: Detect grappling/clinching using distance + bbox overlap.
        Returns grappling factor score (0.8 when detected) and updates grappling history.
        """
        if len(poses) < 2:
            return 0.0
        
        grappling_detected = False
        max_grappling_score = 0.0
        
        for i in range(len(poses)):
            for j in range(i+1, len(poses)):
                p1, p2 = poses[i], poses[j]
                
                # Calculate distance
                dist = self._calculate_distance(p1, p2)
                
                h1 = p1['bbox'][3] - p1['bbox'][1]
                h2 = p2['bbox'][3] - p2['bbox'][1]
                avg_height = (h1 + h2) / 2
                
                # Check if distance < 40% of average height
                if dist < (avg_height * self.thresholds['grappling_distance']):
                    # Calculate bounding box overlap (IoU approximation)
                    bbox1 = p1['bbox']
                    bbox2 = p2['bbox']
                    
                    # Calculate intersection
                    x1 = max(bbox1[0], bbox2[0])
                    y1 = max(bbox1[1], bbox2[1])
                    x2 = min(bbox1[2], bbox2[2])
                    y2 = min(bbox1[3], bbox2[3])
                    
                    if x2 > x1 and y2 > y1:
                        intersection = (x2 - x1) * (y2 - y1)
                        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
                        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
                        
                        # Calculate overlap ratio (intersection / smaller bbox)
                        overlap_ratio = intersection / min(area1, area2)
                        
                        # Grappling detected when overlap > 60%
                        if overlap_ratio > self.thresholds['grappling_overlap']:
                            grappling_detected = True
                            
                            # Track grappling persistence
                            tid1 = p1.get('track_id', -1)
                            tid2 = p2.get('track_id', -1)
                            if tid1 != -1 and tid2 != -1:
                                pair_key = tuple(sorted([tid1, tid2]))
                                self.grappling_history[pair_key] += 1
                                
                                # If grappling persists > 10 frames, maintain elevated score
                                if self.grappling_history[pair_key] > 10:
                                    max_grappling_score = max(max_grappling_score, 0.9)
                                else:
                                    max_grappling_score = max(max_grappling_score, 0.8)
                            else:
                                max_grappling_score = max(max_grappling_score, 0.8)
        
        return max_grappling_score

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
            
            # Scale-invariant movement check: require "mostly stationary" to count as loitering.
            if displacement < (height * 0.4):
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
        
        # 1. Time-based context
        hour = context.get('hour', 12)
        if hour > 22 or hour < 5:
            score += 0.4
            
        # 2. Location-based context (NEW)
        location_type = context.get('location_type', 'public')
        if location_type == 'secure_facility':
            score += 0.5
        elif location_type == 'private_property':
            score += 0.3
            
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

    def _calculate_distance(self, p1, p2):
        """
        Calculate Euclidean distance between two persons' centers.
        """
        c1 = self._get_bbox_center(p1['bbox'])
        c2 = self._get_bbox_center(p2['bbox'])
        return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

    def _detect_chasing(self, poses):
        """
        Detect if one person is chasing another by analyzing velocity vectors.
        """
        if len(poses) < 2: return 0.0
        
        max_chase = 0.0
        for i, p1 in enumerate(poses):
            tid1 = p1.get('track_id')
            if not tid1 or len(self.person_history[tid1]) < 5: continue
            
            # Vector of P1
            h1 = self.person_history[tid1]
            vec1 = np.array(h1[-1][0]) - np.array(h1[0][0])
            
            for j, p2 in enumerate(poses):
                if i == j: continue
                tid2 = p2.get('track_id')
                if not tid2 or len(self.person_history[tid2]) < 5: continue
                
                # Check if P1 is moving TOWARD P2
                p2_pos = np.array(self._get_bbox_center(p2['bbox']))
                p1_pos = np.array(self._get_bbox_center(p1['bbox']))
                to_target = p2_pos - p1_pos
                
                # Cosine similarity between P1 movement and vector to P2
                mag1 = np.linalg.norm(vec1)
                mag_to = np.linalg.norm(to_target)
                
                if mag1 > 20 and mag_to > 0: # Significant movement
                    similarity = np.dot(vec1, to_target) / (mag1 * mag_to)
                    if similarity > 0.8: # Moving >80% directly toward them
                         # Check if distance is closing
                         d_start = np.linalg.norm(np.array(h1[0][0]) - np.array(self.person_history[tid2][0][0]))
                         d_end = np.linalg.norm(p1_pos - p2_pos)
                         if d_end < d_start * 0.7: # Distance closed by 30%
                             max_chase = max(max_chase, 0.7)
                             
        return max_chase

    def _get_bbox_center(self, bbox):
        return [(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2]

    def _get_center(self, bbox):
        return self._get_bbox_center(bbox)
    
    def generate_alert(self, risk_score, risk_factors):
        """
        Generate alert dictionary from risk score and contributing factors.
        Used by both live feed and video processing.
        """
        # Determine alert level based on risk score
        if risk_score >= 60:
            level = 'critical'
        elif risk_score >= 35:
            level = 'high'
        elif risk_score >= 15:
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
