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

import threading

class MLService:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.detector = None
        self.risk_engine = None
        self.anonymizer = None
        self.loaded = False
        self.load_error = None
        self.device_in_use = None
        self.models_ready = threading.Event()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self):
        if self.loaded:
            self.models_ready.set()
            return
        # Load synchronously — must complete before accepting WebSocket connections
        self._load_models_internal()

    def load_models_async(self):
        """Non-blocking load for cases where background loading is acceptable."""
        if self.loaded:
            return
        self.load_error = None
        self.models_ready.clear()
        thread = threading.Thread(target=self._load_models_internal)
        thread.daemon = True
        thread.start()

    def wait_until_ready(self, timeout=120):
        """Block until models are loaded or timeout is reached. Returns True if ready."""
        return self.models_ready.wait(timeout=timeout)

    def _load_models_internal(self):
        print("=" * 50)
        print("Loading ML Models...")
        try:
            if UnifiedDetector:
                import torch
                preferred_device = 'cuda' if torch.cuda.is_available() else 'cpu'
                print(f"  Device: {preferred_device.upper()}")

                try:
                    print("  Loading YOLO detector...")
                    self.detector = UnifiedDetector(device=preferred_device)
                    self.device_in_use = preferred_device
                except Exception as gpu_exc:
                    # If GPU init fails (OOM/driver), fall back to CPU.
                    if preferred_device == 'cuda':
                        print(f"  Warning: CUDA detector init failed, falling back to CPU. Error: {gpu_exc}")
                        self.detector = UnifiedDetector(device='cpu')
                        self.device_in_use = 'cpu'
                    else:
                        raise

                print("  Warming up models...")
                self.detector.warmup()
                print("  Loading Risk Engine...")
                self.risk_engine = RiskScoringEngine()
                print("  Loading Anonymizer...")
                self.anonymizer = PrivacyAnonymizer()
                self.loaded = True
                self.load_error = None
                self.models_ready.set()
                print(f"ML Models loaded successfully (device={self.device_in_use}).")
                print("=" * 50)
            else:
                print("WARNING: ML dependencies missing — running in mock mode (0% scores expected).")
                print("Install: pip install ultralytics torch")
                self.loaded = False
                self.load_error = "ML dependencies missing (UnifiedDetector import failed)"
                self.models_ready.set()
                print("=" * 50)
        except Exception as e:
            import traceback
            print(f"ERROR loading ML models: {e}")
            traceback.print_exc()
            self.detector = None
            self.risk_engine = None
            self.anonymizer = None
            self.loaded = False
            self.device_in_use = None
            self.load_error = str(e)
            self.models_ready.set()  # Unblock waiters even on failure
            print("=" * 50)

ml_service = MLService.get_instance()
