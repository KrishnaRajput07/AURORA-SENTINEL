import cv2
import numpy as np

class PrivacyAnonymizer:
    """
    Anonymize faces and sensitive information
    """
    def __init__(self):
        # Load face detection model (faster than YOLO for this)
        # We'll use the builtin haar cascade for simplicity/speed as per guide
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except Exception as e:
            print(f"Error loading face cascade: {e}")
            self.face_cascade = None
        
    def detect_faces(self, frame):
        """Detect faces and return bounding boxes"""
        if self.face_cascade is None:
            return []
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30)
        )
        return faces

    def anonymize_frame(self, frame, poses=None, mode='blur', face_rects=None):
        """
        Apply privacy protection to frame
        
        Args:
            frame: Input frame
            poses: Optional pose data for skeleton extraction
            mode: 'blur', 'pixelate', or 'skeleton'
            face_rects: Optional pre-detected face rectangles [x, y, w, h] to avoid re-detection
        
        Returns:
            Anonymized frame
        """
        if mode == 'skeleton' and poses:
            return self._extract_skeleton(frame, poses)
        elif mode == 'blur':
            return self._blur_faces(frame, face_rects)
        elif mode == 'pixelate':
            return self._pixelate_faces(frame)
        else:
            return frame
    
    def _blur_faces(self, frame, face_rects=None):
        """Gaussian blur on faces"""
        if self.face_cascade is None and face_rects is None:
            return frame
            
        # Detect if not provided
        if face_rects is None:
            face_rects = self.detect_faces(frame)
        
        result = frame.copy()
        for (x, y, w, h) in face_rects:
            # Clamp coordinates
            h_img, w_img = frame.shape[:2]
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)
            
            if w <= 0 or h <= 0: continue

            # Extract face region
            face_region = result[y:y+h, x:x+w]
            
            # Apply strong Gaussian blur
            # Kernel size must be odd
            ksize = (99, 99)
            if w < 100 or h < 100:
                ksize = (int(w/2)*2+1, int(h/2)*2+1) # dynamic kernel size
            
            try:
                blurred = cv2.GaussianBlur(face_region, ksize, 30)
                result[y:y+h, x:x+w] = blurred
            except:
                pass
        
        return result
    
    def _pixelate_faces(self, frame):
        """Pixelate detected faces"""
        if self.face_cascade is None:
            return frame
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        
        result = frame.copy()
        for (x, y, w, h) in faces:
            # Extract face region
            face_region = result[y:y+h, x:x+w]
            
            # Resize down and back up for pixelation
            small = cv2.resize(face_region, (16, 16), interpolation=cv2.INTER_LINEAR)
            pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            
            result[y:y+h, x:x+w] = pixelated
        
        return result
    
    def _extract_skeleton(self, frame, poses):
        """
        Create skeleton-only visualization
        Preserves behavior information while removing identity
        """
        # Create black background
        skeleton_frame = np.zeros_like(frame)
        
        # COCO keypoint connections
        connections = [
            (5, 6),   # Shoulders
            (5, 7),   # Left shoulder to elbow
            (7, 9),   # Left elbow to wrist
            (6, 8),   # Right shoulder to elbow
            (8, 10),  # Right elbow to wrist
            (5, 11),  # Left shoulder to hip
            (6, 12),  # Right shoulder to hip
            (11, 12), # Hips
            (11, 13), # Left hip to knee
            (13, 15), # Left knee to ankle
            (12, 14), # Right hip to knee
            (14, 16), # Right knee to ankle
        ]
        
        for pose in poses:
            keypoints = np.array(pose['keypoints'])
            confidence = np.array(pose['confidence'])
            
            # Keypoints are typically 17x2 or 17x3
            # If we just have data [17, 2], careful with indexing
            if len(keypoints) < 17:
                continue

            # Draw skeleton
            for connection in connections:
                pt1_idx, pt2_idx = connection
                
                if (confidence[pt1_idx] > 0.5 and 
                    confidence[pt2_idx] > 0.5):
                    
                    pt1 = tuple(keypoints[pt1_idx].astype(int))
                    pt2 = tuple(keypoints[pt2_idx].astype(int))
                    
                    cv2.line(skeleton_frame, pt1, pt2, (0, 255, 0), 2)
            
            # Draw keypoints
            for i, (kpt, conf) in enumerate(zip(keypoints, confidence)):
                if conf > 0.5:
                    cv2.circle(
                        skeleton_frame,
                        tuple(kpt.astype(int)),
                        4,
                        (0, 255, 0),
                        -1
                    )
        
        return skeleton_frame
