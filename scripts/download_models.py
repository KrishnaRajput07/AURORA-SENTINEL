from ultralytics import YOLO
import torch
import os

def download_models():
    # Ensure models directory exists
    os.makedirs('models', exist_ok=True)
    
    print("Downloading YOLO models...")
    # These will auto-download to the current directory or cache upon load,
    # but let's instantiate them to trigger the download.
    try:
        YOLO('yolov8n.pt')
        YOLO('yolov8n-pose.pt')
        YOLO('yolov8s.pt')  # Backup
    except Exception as e:
        print(f"Error downloading YOLO models: {e}")

    print("Downloading SlowFast...")
    try:
        from torchvision.models.video import slowfast_r50
        model = slowfast_r50(pretrained=True)
        torch.save(model.state_dict(), 'models/slowfast_r50.pth')
    except ImportError:
        print("Warning: slowfast_r50 not found in torchvision. Skipping (not critical for basic detection).")
    except Exception as e:
        print(f"Error downloading SlowFast: {e}")
    
    print("All models downloaded (or attempted)!")

if __name__ == "__main__":
    download_models()
