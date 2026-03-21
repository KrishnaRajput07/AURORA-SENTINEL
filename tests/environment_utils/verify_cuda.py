import torch
import sys

def verify():
    print(f"Python Version: {sys.version}")
    print(f"PyTorch Version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    if cuda_available:
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"Current Device: {torch.cuda.current_device()}")
    else:
        print("WARNING: CUDA is NOT available. The system will fall back to CPU.")

if __name__ == "__main__":
    verify()
