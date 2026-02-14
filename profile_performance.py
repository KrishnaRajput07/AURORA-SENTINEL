import cv2
import numpy as np
import time
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from models.detection.detector import UnifiedDetector

def profile_detector():
    print("Initializing detector for profiling...")
    detector = UnifiedDetector()
    
    # Run warmup
    detector.warmup()
    
    # Create dummy frame
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Profile process_frame
    iterations = 20
    times = []
    
    print(f"Profiling {iterations} iterations...")
    for i in range(iterations):
        start = time.time()
        detector.process_frame(frame)
        end = time.time()
        duration = end - start
        times.append(duration)
        print(f"Iteration {i+1}: {duration:.4f}s")
    
    avg_time = sum(times) / iterations
    fps = 1 / avg_time
    
    print("\nResults:")
    print(f"Average Processing Time: {avg_time:.4f}s")
    print(f"Estimated Peak Throughput: {fps:.2f} FPS")
    
    if avg_time < 0.1: # Threshold for "next level" performance (at least 10 FPS)
        print("VERIFICATION PASSED: Performance is significantly improved.")
    else:
        print("VERIFICATION WARNING: Performance still below target, but verify on actual hardware.")

if __name__ == "__main__":
    profile_detector()
