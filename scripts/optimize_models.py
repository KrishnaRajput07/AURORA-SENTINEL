try:
    from ultralytics import YOLO
    import onnx
    import onnxruntime as ort
except ImportError as e:
    print(f"Missing dependencies for optimization: {e}")
    print("Please install: pip install onnx onnxruntime-gpu")
    exit(1)

import os

def optimize_yolo_to_onnx():
    """Convert YOLO models to ONNX for faster inference"""
    print("Optimizing YOLO models...")
    
    models = ['yolov8n.pt', 'yolov8n-pose.pt']
    
    # Ensure models dir
    os.makedirs('models', exist_ok=True)
    
    for model_name in models:
        print(f"\nConverting {model_name}...")
        try:
            # Check if exists, else download
            model = YOLO(model_name) 
            
            # Export to ONNX
            # Ultralytics export handles downloading if needed
            onnx_path = model.export(format='onnx', simplify=True)
            
            print(f"✓ Saved to {onnx_path}")
            
            # Verify
            if os.path.exists(onnx_path):
                onnx_model = onnx.load(onnx_path)
                onnx.checker.check_model(onnx_model)
                
                # Benchmark check
                # session = ort.InferenceSession(onnx_path)
                print(f"  ONNX Export verified")
        except Exception as e:
            print(f"Optimization failed for {model_name}: {e}")

def benchmark_inference():
    """Benchmark inference speeds"""
    import cv2
    import time
    
    print("\nBenchmarking PyTorch Inference...")
    try:
        detector = YOLO('yolov8n.pt')
        
        # Load test frame
        frame = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Warm-up
        for _ in range(5):
            _ = detector(frame, verbose=False)
        
        # Benchmark
        start = time.time()
        for _ in range(50):
            _ = detector(frame, verbose=False)
        end = time.time()
        
        avg_time = (end - start) / 50
        fps = 1 / avg_time
        
        print(f"\n{'='*50}")
        print(f"Inference Benchmark (PyTorch)")
        print(f"{'='*50}")
        print(f"Average time: {avg_time*1000:.1f}ms")
        print(f"FPS: {fps:.1f}")
        print(f"{'='*50}")
    except Exception as e:
        print(f"Benchmark failed: {e}")

if __name__ == "__main__":
    import numpy as np
    optimize_yolo_to_onnx()
    benchmark_inference()
