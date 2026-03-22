import cv2
import numpy as np
import os
from ultralytics import YOLO
import torch
from concurrent.futures import ThreadPoolExecutor
import time

class UnifiedDetector:
    """
    Combines object detection and pose estimation with ByteTrack
    """
    def __init__(self, device=None):
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True
            
        print(f"Initializing UnifiedDetector on {self.device}...")
        
        # Load models
        print("Loading detection models...")
        try:
            # Main object detection model
            self.object_model = YOLO('yolov8n.pt')
            self.object_model.to(self.device)
            
            # Pose estimation model
            self.pose_model = YOLO('yolov8n-pose.pt')
            self.pose_model.to(self.device)
            
            # Weapon detection model (NEW) - Fix misspelling and use available yolov8s.pt if possible
            weapon_model_file = 'yolov8s.pt' if os.path.exists('yolov8s.pt') else 'yolov8n.pt'
            self.weapon_model = YOLO(weapon_model_file)
            self.weapon_model.to(self.device)
            
        except Exception as e:
            print(f"Warning: Failed to load models on {self.device}, falling back to CPU or raising error: {e}")
            self.object_model = YOLO('yolov8n.pt')
            self.pose_model = YOLO('yolov8n-pose.pt')
            weapon_model_file = 'yolov8s.pt' if os.path.exists('yolov8s.pt') else 'yolov8n.pt'
            self.weapon_model = YOLO(weapon_model_file)
            self.device = 'cpu'
        
        # Critical objects from COCO (standard models like yolov8n/s)
        self.critical_objects = {
            0: 'person',
            24: 'backpack',
            26: 'handbag',
            28: 'suitcase',
            34: 'baseball bat',
            43: 'knife',
            76: 'scissors',
            # Add gun if the model supports it (standard COCO doesn't have 'gun' usually, it has 'cell phone' often misidentified)
        }
        
        # Specific classes to be treated as WEAPONS
        self.weapon_class_names = ['knife', 'baseball bat', 'scissors']
        
        # Initialize Simple Tracker (Fallback since YOLO track crashes on Windows)
        self.tracker = SimpleTracker()
        
        # Parallel Execution Pool
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.use_half = self.device == 'cuda'
        
        # Disable half precision to avoid dtype mismatch issues
        # FP16 can cause "expected mat1 and mat2 to have the same dtype" errors
        self.use_half = False
        print("[INFO] Using FP32 (Full Precision) for stability.")
        
    def _check_blur(self, frame):
        """Innovation #16: Blur Detection using Laplacian Variance"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance < 100 

    def detect_objects(self, frame):
        """
        Detect and TRACK objects in frame using SimpleTracker
        """
        is_blurry = self._check_blur(frame)
        
        # Run standard prediction
        results = self.object_model.predict(
            frame, 
            verbose=False, 
            device=self.device,
            classes=list(self.critical_objects.keys()),
            half=self.use_half
        )[0]
        
        raw_boxes = []
        
        if results.boxes is not None:
            for box in results.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                
                if cls in self.critical_objects and conf > 0.3:
                    raw_boxes.append({
                        'class': self.critical_objects[cls],
                        'confidence': conf,
                        'bbox': xyxy.tolist(),
                        'is_blurry': is_blurry
                    })
                
        # Update Tracker
        tracked_objects = self.tracker.update(raw_boxes)
        
        return tracked_objects
    
    def detect_poses(self, frame):
        """
        Detect human poses
        Returns: list of pose keypoints
        """
        # Run pose estimation
        # Note: We could run this on crops from detect_objects for speed, 
        # but running full frame is often more robust for context.
        results = self.pose_model(frame, verbose=False, device=self.device, half=self.use_half)[0]
        
        poses = []
        if results.keypoints is not None:
            # Handle standard 8.0+ output
            for i, keypoints in enumerate(results.keypoints):
                # .xy is the coordinates (x, y)
                if hasattr(keypoints, 'xy'):
                    kpts = keypoints.xy[0].cpu().numpy()
                    conf = keypoints.conf[0].cpu().numpy() if keypoints.conf is not None else np.ones(len(kpts))
                elif hasattr(keypoints, 'data'):
                     # Fallback
                     data = keypoints.data[0].cpu().numpy()
                     kpts = data[:, :2]
                     conf = data[:, 2] if data.shape[1] > 2 else np.ones(len(kpts))
                else:
                    continue

                # Get corresponding box if available
                bbox = [0, 0, 0, 0]
                if results.boxes is not None and i < len(results.boxes):
                    bbox = results.boxes[i].xyxy[0].cpu().numpy().tolist()

                poses.append({
                    'keypoints': kpts.tolist(),
                    'confidence': conf.tolist(),
                    'bbox': bbox
                })
        
        return poses
    
    def detect_weapons(self, frame):
        """
        Detect weapons in frame using the specialized weapon model if it has specific classes.
        Since we found that standard YOLO models misidentify everything, we strictly filter here.
        """
        # If weapon_model is just a general YOLO model, we use it to look for specific COCO weapon classes
        results = self.weapon_model.predict(
            frame, 
            verbose=False, 
            device=self.device,
            conf=0.4, # Higher confidence for weapons
            half=self.use_half
        )[0]
        
        weapons = []
        if results.boxes is not None:
            # Check what classes this model actually has
            names = results.names
            
            for box in results.boxes:
                cls_id = int(box.cls[0])
                cls_name = names.get(cls_id, 'unknown').lower()
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                
                # CRITICAL: Only accept if it's explicitly a weapon class
                # Also check for 'handgun' or 'pistol' specifically
                is_valid_weapon = any(w in cls_name for w in ['gun', 'weapon', 'pistol', 'rifle', 'knife', 'machete'])
                
                if (is_valid_weapon or cls_id in [43, 34, 76]) and conf > 0.60:
                    weapons.append({
                        'class': 'weapon',
                        'sub_class': cls_name if cls_name != 'unknown' else 'unidentified_threat',
                        'confidence': conf,
                        'bbox': xyxy.tolist()
                    })
        
        return weapons

    def process_frame(self, frame):
        """
        Complete detection pipeline - Sequential for VRAM Stability (Innovation #7-10)
        Parallel threads often choke single-GPU laptops (RTX 4050).
        """
        # 1. Run inference sequentially to protect VRAM
        objects = self.detect_objects(frame)
        poses = self.detect_poses(frame)
        weapons = self.detect_weapons(frame)
        
        # 4. Match Poses to Tracked Objects (Critical for Risk Engine)
        self._assign_tracks_to_poses(objects, poses)
        
        return {
            'objects': objects,
            'poses': poses,
            'weapons': weapons,
            'timestamp': time.time()
        }

    def warmup(self):
        """Run dummy frames through models to initialize CUDA/weights"""
        print("Warming up models...")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        for _ in range(3):
            self.process_frame(dummy)
        print("Model warmup complete.")
        
    def _assign_tracks_to_poses(self, objects, poses):
        """
        Match detected poses to tracked person objects using IoU/Distance
        Adds 'track_id' to pose dict if matched
        """
        if not objects or not poses:
            return
            
        # Filter for person objects only
        persons = [obj for obj in objects if obj['class'] == 'person' and 'track_id' in obj]
        
        for pose in poses:
            if 'bbox' not in pose or not pose['bbox']:
                continue
                
            pose_box = pose['bbox']
            best_match = None
            max_iou = 0.0
            
            for person in persons:
                # Calculate IoU
                iou = self._calculate_iou(pose_box, person['bbox'])
                if iou > max_iou:
                    max_iou = iou
                    best_match = person
            
            # If good match found, assign track ID
            if best_match and max_iou > 0.5:
                pose['track_id'] = best_match['track_id']
                
    def _calculate_iou(self, boxA, boxB):
        # determine the (x, y)-coordinates of the intersection rectangle
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        # compute the area of intersection rectangle
        interArea = max(0, xB - xA) * max(0, yB - yA)

        # compute the area of both the prediction and ground-truth
        # rectangles
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        # compute the intersection over union by taking the intersection
        # area and dividing it by the sum of prediction + ground-truth
        # areas - the interesection area
        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
        return iou
    
    @staticmethod
    def _get_center(bbox):
        """Calculate center point of bounding box"""
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]


# Test the detector


class SimpleTracker:
    def __init__(self):
        self.tracks = {} # id -> box
        self.next_id = 0
        self.max_age = 30 # Lost frames before deleting
        self.track_age = {} # id -> age

    def update(self, detections):
        if not detections:
            self._increment_ages()
            return []

        current_dets = []
        for det in detections:
            det['center'] = self._get_center(det['bbox'])
            det['track_id'] = -1
            current_dets.append(det)

        matched_tracks = set()
        
        for det in current_dets:
            best_iou = 0
            best_tid = -1
            
            for tid, track_box in self.tracks.items():
                if tid in matched_tracks: continue
                
                iou = self._calculate_iou(det['bbox'], track_box)
                
                # Calculate center distance for fallback
                track_center = self._get_center(track_box)
                dist = np.linalg.norm(np.array(det['center']) - np.array(track_center))
                h = track_box[3] - track_box[1]
                
                # Match if IoU is good OR if center is very close (fallback for fast movement)
                if (iou > 0.3 and iou > best_iou) or (iou <= 0.3 and dist < h * 0.8):
                    best_iou = iou if iou > 0.3 else 0.31 # slightly prefer IoU matches
                    best_tid = tid
            
            if best_tid != -1:
                det['track_id'] = best_tid
                # Update box with momentum? No, just use current.
                self.tracks[best_tid] = det['bbox']
                self.track_age[best_tid] = 0
                matched_tracks.add(best_tid)
            else:
                det['track_id'] = self.next_id
                self.tracks[self.next_id] = det['bbox']
                self.track_age[self.next_id] = 0
                self.next_id += 1
        
        for tid in list(self.tracks.keys()):
            if tid not in matched_tracks:
                self.track_age[tid] += 1
                if self.track_age[tid] > self.max_age:
                    del self.tracks[tid]
                    del self.track_age[tid]
                    
        return current_dets

    def _increment_ages(self):
        for tid in list(self.tracks.keys()):
            self.track_age[tid] += 1
            if self.track_age[tid] > self.max_age:
                del self.tracks[tid]
                del self.track_age[tid]

    def _get_center(self, bbox):
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]

    def _calculate_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-6)


# Test the detector
if __name__ == "__main__":
    detector = UnifiedDetector()
    
    # Create a dummy frame
    print("Running test on dummy frame...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    results = detector.process_frame(dummy_frame)
    print(f"Test Successful: {len(results['objects'])} objects, {len(results['poses'])} people detected.")

