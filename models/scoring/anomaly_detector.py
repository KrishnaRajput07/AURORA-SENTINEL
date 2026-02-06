import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os

class AnomalyDetector:
    """
    Detect unusual patterns using unsupervised learning
    """
    def __init__(self, model_path=None):
        self.model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def extract_features(self, detection_data):
        """
        Extract feature vector from detection data
        """
        features = []
        
        # Number of people
        features.append(len(detection_data.get('poses', [])))
        
        # Number of objects
        features.append(len(detection_data.get('objects', [])))
        
        # Spatial distribution (variance of positions)
        if detection_data.get('poses'):
            # Flatten lists of bboxes to get all coordinates
            # But we need positions (centers)
            # Assuming 'poses' has bbox
            positions = []
            for pose in detection_data['poses']:
                bbox = pose['bbox'] 
                # bbox is [x1, y1, x2, y2]
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                positions.append([cx, cy])
            
            positions = np.array(positions)
            
            if len(positions) > 1:
                features.append(np.var(positions[:, 0]))  # X variance
                features.append(np.var(positions[:, 1]))  # Y variance
            else:
                features.extend([0, 0])
        else:
            features.extend([0, 0])
        
        # Average confidence scores
        if detection_data.get('poses'):
            # poses[i]['confidence'] is a list of keypoint confidences
            # We want overall pose confidence? or average keypoint conf
            avg_conf = np.mean([
                np.mean(pose['confidence'])
                for pose in detection_data['poses']
            ])
            features.append(avg_conf)
        else:
            features.append(0)
        
        # Object diversity (number of unique object types)
        if detection_data.get('objects'):
            unique_objects = len(set(
                obj['class'] for obj in detection_data['objects']
            ))
            features.append(unique_objects)
        else:
            features.append(0)
        
        return np.array(features).reshape(1, -1)
    
    def train(self, detection_history):
        """
        Train on normal surveillance footage
        
        Args:
            detection_history: List of detection_data dicts
        """
        features_list = [
            self.extract_features(data).flatten()
            for data in detection_history
        ]
        
        if not features_list:
            print("No data to train on!")
            return
            
        X = np.vstack(features_list)
        self.model.fit(X)
        self.is_trained = True
        
        print(f"Anomaly detector trained on {len(detection_history)} samples")
    
    def predict(self, detection_data):
        """
        Predict if current frame is anomalous
        
        Returns:
            is_anomaly (bool), anomaly_score (float 0 to 1)
        """
        if not self.is_trained:
            # Not trained yet, assume normal
            return False, 0.0
        
        features = self.extract_features(detection_data)
        
        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.model.predict(features)[0]
        
        # Get anomaly score (lower = more anomalous in raw sklearn, but score_samples returns negative offset)
        # decision_function returns negative for outliers, positive for inliers.
        # score_samples returns anomaly score. 
        # For IsolationForest, "The lower, the more abnormal." (closer to -1?)
        # Read docs: "The anomaly score of the input samples. The lower, the more abnormal."
        score = self.model.score_samples(features)[0]
        
        is_anomaly = (prediction == -1)
        
        # Normalize score to 0-1 (0 = normal, 1 = anomaly)
        # Isolation forest scores are typically around -0.5 to 0.5
        # We can just map it roughly or Use decision function
        
        normalized_score = max(0, min(1, 1 - (score + 0.5)*2 )) # Rough heuristic
        
        return is_anomaly, normalized_score
    
    def save_model(self, path):
        """Save trained model"""
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"Model saved to {path}")
    
    def load_model(self, path):
        """Load trained model"""
        with open(path, 'rb') as f:
            self.model = pickle.load(f)
        self.is_trained = True
        print(f"Model loaded from {path}")
