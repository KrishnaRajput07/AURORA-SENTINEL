import sys
import os

# Add root to sys.path to ensure models can be imported
sys.path.append(os.getcwd())

try:
    from models.detection.detector import UnifiedDetector
    from models.scoring.risk_engine import RiskScoringEngine
    from models.privacy.anonymizer import PrivacyAnonymizer
except ImportError:
    print("Warning: Could not import machine learning models.")
    UnifiedDetector = None
    RiskScoringEngine = None
    PrivacyAnonymizer = None

class MLService:
    _instance = None
    
    def __init__(self):
        self.detector = None
        self.risk_engine = None
        self.anonymizer = None
        self.loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self):
        if self.loaded:
            return
        
        print("Loading ML Models...")
        try:
            if UnifiedDetector:
                self.detector = UnifiedDetector()
                self.detector.warmup() # NEW: Initialize CUDA and weights
                self.risk_engine = RiskScoringEngine()
                self.anonymizer = PrivacyAnonymizer()
                self.loaded = True
                print("ML Models loaded successfully.")
            else:
                print("ML dependencies missing, running in mock mode.")
        except Exception as e:
            print(f"Error loading ML models: {e}")
            self.detector = None
            self.risk_engine = None
            self.anonymizer = None

ml_service = MLService.get_instance()
