import torch
import sys

print(f"Python: {sys.version}")
print(f"Torch: {torch.__version__}")
try:
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Current Device: {torch.cuda.current_device()}")
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA NOT Available")
        
except Exception as e:
    print(f"Error checking CUDA: {e}")
