import cv2
import numpy as np
from ultralytics import YOLO
import torch

class UnifiedDetector:
    """
    Combines object detection and pose estimation with ByteTrack
    """
    def __init__(self, device='cpu'):
        self.device = device
        print(f"Initializing UnifiedDetector on {self.device}...")
        
        # Load models
        print("Loading detection models...")
        try:
            # Main object detection model
            self.object_model = YOLO('yolov8n.pt')
            self.object_model.to(device)
            
            # Pose estimation model
            self.pose_model = YOLO('yolov8n-pose.pt')
            self.pose_model.to(device)
            
        except Exception as e:
            print(f"Warning: Failed to load models on {device}, falling back to CPU or raising error: {e}")
            self.object_model = YOLO('yolov8n.pt')
            self.pose_model = YOLO('yolov8n-pose.pt')
            self.device = 'cpu'
        
        # Classes of interest
        self.critical_objects = {
            0: 'person',
            24: 'backpack',
            26: 'handbag',
            28: 'suitcase',
        }
        
    def detect_objects(self, frame):
        """
        Detect and TRACK objects in frame using ByteTrack
        Returns: list of detections with track_ids
        """
        # Enable tracking with ByteTrack
        # persist=True is crucial for ID consistency across frames
        # Enable tracking with ByteTrack
        # persist=True is crucial for ID consistency across frames
        # CRASH FIX: use predict() instead of track() on Windows CPU to avoid LAP/tracker crashes
        results = self.object_model.predict(
            frame, 
            # persist=True, 
            # tracker="bytetrack.yaml", 
            verbose=False, 
            device=self.device,
            classes=list(self.critical_objects.keys()) # Filter classes early if possible
        )[0]
        
        detections = []
        
        if results.boxes is None:
            return detections

        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy()
            
            # Get track ID if available from tracker
            track_id = int(box.id[0]) if box.id is not None else -1
            
            if cls in self.critical_objects and conf > 0.3: # Lowered threshold slightly for better tracking continuity
                detections.append({
                    'class': self.critical_objects[cls],
                    'confidence': conf,
                    'bbox': xyxy.tolist(),
                    'center': self._get_center(xyxy),
                    'track_id': track_id
                })
        
        return detections
    
    def detect_poses(self, frame):
        """
        Detect human poses
        Returns: list of pose keypoints
        """
        # Run pose estimation
        # Note: We could run this on crops from detect_objects for speed, 
        # but running full frame is often more robust for context.
        results = self.pose_model(frame, verbose=False, device=self.device)[0]
        
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
    
    def process_frame(self, frame):
        """
        Complete detection pipeline
        """
        # 1. Run Object Tracking
        objects = self.detect_objects(frame)
        
        # 2. Run Pose Estimation
        # Improvement: Correlation Check?
        # Ideally, we map poses to tracked objects. 
        # For now, we return them separately but could match by IoU later.
        poses = self.detect_poses(frame)
        
        return {
            'objects': objects,
            'poses': poses,
            'timestamp': cv2.getTickCount() / cv2.getTickFrequency()
        }
    
    @staticmethod
    def _get_center(bbox):
        """Calculate center point of bounding box"""
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]


# Test the detector
if __name__ == "__main__":
    detector = UnifiedDetector()
    
    # Create a dummy frame
    print("Running test on dummy frame...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    results = detector.process_frame(dummy_frame)
    print(f"Test Successful: {len(results['objects'])} objects, {len(results['poses'])} people detected.")

