import cv2
import numpy as np
import os
import sys
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.detection.detector import UnifiedDetector

def test_fire_model(image_path=None):
    """
    Test the fire/smoke detection logic in UnifiedDetector.
    """
    print("Initializing UnifiedDetector (Fire Mode)...")
    detector = UnifiedDetector()
    
    if detector.fire_model is None:
        print("[ERROR] Fire model (fir.pt) could not be loaded. Check paths or LFS status.")
        return

    # 1. Prepare Frame
    if image_path and os.path.exists(image_path):
        print(f"Loading image: {image_path}")
        frame = cv2.imread(image_path)
    else:
        print("No image provided, generating synthetic test frame with red (fire-like) circle...")
        # Create a black image with a bright red circle to simulate 'fire'
        frame = np.zeros((640, 640, 3), dtype=np.uint8)
        cv2.circle(frame, (320, 320), 100, (0, 0, 255), -1) # Bright red circle
        cv2.putText(frame, "SIMULATED FIRE", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # 2. Run Fire Detection Specifically
    print("Running detect_fire()...")
    start_time = time.time()
    fire_results = detector.detect_fire(frame)
    duration = time.time() - start_time
    
    # 3. Analyze Results
    print(f"\nDetection Results (took {duration:.3f}s):")
    if not fire_results:
        print("[-] No fire or smoke detected.")
    else:
        print(f"[+] Detected {len(fire_results)} fire/smoke indicators:")
        for i, det in enumerate(fire_results):
            cls = det['class']
            conf = det['confidence']
            bbox = [int(x) for x in det['bbox']]
            print(f"    {i+1}. Label: {cls}, Confidence: {conf:.2f}, Box: {bbox}")

    # 4. Optional: Save result for visual inspection
    if fire_results:
        for det in fire_results:
            x1, y1, x2, y2 = map(int, det['bbox'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 3) # Orange for fire
            cv2.putText(frame, f"{det['class']} {det['confidence']:.2f}", (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        
        output_path = "storage/fire_test_result.jpg"
        os.makedirs("storage", exist_ok=True)
        cv2.imwrite(output_path, frame)
        print(f"\n[INFO] Saved visualization to: {output_path}")

if __name__ == "__main__":
    # Check if user passed an image path as argument
    target_img = sys.argv[1] if len(sys.argv) > 1 else None
    test_fire_model(target_img)
