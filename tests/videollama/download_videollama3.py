"""
Download VideoLLaMA3 model to D: drive
This script downloads the VideoLLaMA3-7B model (~14 GB) to D:\huggingface\transformers
"""
import os
import sys

# Configure to use D: drive
os.environ['HF_HOME'] = r'D:\huggingface'
os.environ['TRANSFORMERS_CACHE'] = r'D:\huggingface\transformers'
os.environ['TORCH_HOME'] = r'D:\torch'

# Add D: drive packages to path
sys.path.insert(0, r'D:\python-packages')

print("=" * 60)
print("VideoLLaMA3 Model Download")
print("=" * 60)
print(f"Cache directory: {os.environ['TRANSFORMERS_CACHE']}")
print(f"Model: DAMO-NLP-SG/VideoLLaMA3-7B")
print(f"Size: ~14 GB")
print("=" * 60)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    
    print("\n✓ PyTorch and Transformers loaded successfully")
    print(f"  PyTorch version: {torch.__version__}")
    
    model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
    
    print(f"\nDownloading model: {model_name}")
    print("This will take 10-20 minutes depending on your internet speed...")
    print("You can interrupt (Ctrl+C) and resume later - downloads resume automatically.\n")
    
    # Download tokenizer
    print("Step 1/2: Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=os.environ['TRANSFORMERS_CACHE'],
        trust_remote_code=True
    )
    print("✓ Tokenizer downloaded")
    
    # Download model
    print("\nStep 2/2: Downloading model (this is the large part)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=os.environ['TRANSFORMERS_CACHE'],
        trust_remote_code=True,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    print("✓ Model downloaded")
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS: VideoLLaMA3 model downloaded successfully!")
    print("=" * 60)
    print(f"Location: {os.environ['TRANSFORMERS_CACHE']}")
    print("\nNext step: Run 'python test_videollama_standalone.py' to test the model")
    
except ImportError as e:
    print(f"\n✗ ERROR: Missing dependencies")
    print(f"  {e}")
    print("\nPlease ensure PyTorch and Transformers are installed on D: drive")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nIf download was interrupted, you can run this script again to resume.")
    sys.exit(1)
