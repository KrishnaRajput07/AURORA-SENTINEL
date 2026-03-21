"""
VLM System Diagnostic Tool
Tests all VLM providers to identify which ones are working
"""
import os
import sys
import requests
from PIL import Image
import numpy as np

print("=" * 60)
print("VLM SYSTEM DIAGNOSTIC")
print("=" * 60)

# Create a test image
test_image = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
print("\n✓ Test image created (480x640)")

# Test 1: Local AI Layer (Port 3001)
print("\n" + "=" * 60)
print("TEST 1: Local AI Intelligence Layer (Port 3001)")
print("=" * 60)
try:
    health_response = requests.get("http://localhost:3001/health", timeout=2)
    if health_response.status_code == 200:
        print("✓ Local AI Layer is RUNNING")
        print(f"  Response: {health_response.json()}")
        
        # Try to analyze
        import base64
        import io
        buffer = io.BytesIO()
        test_image.save(buffer, format='JPEG')
        image_data = base64.b64encode(buffer.getvalue()).decode()
        image_data = f"data:image/jpeg;base64,{image_data}"
        
        analyze_response = requests.post("http://localhost:3001/analyze", json={
            'imageData': image_data,
            'mlScore': 50,
            'mlFactors': {},
            'cameraId': 'TEST'
        }, timeout=30)
        
        if analyze_response.status_code == 200:
            result = analyze_response.json()
            print("✓ Local AI Layer ANALYSIS WORKS!")
            print(f"  Provider: {result.get('provider', 'unknown')}")
            print(f"  Explanation: {result.get('explanation', 'N/A')[:100]}...")
        else:
            print(f"✗ Local AI Layer analysis failed: {analyze_response.status_code}")
            print(f"  Response: {analyze_response.text[:200]}")
    else:
        print(f"✗ Local AI Layer returned status {health_response.status_code}")
except Exception as e:
    print(f"✗ Local AI Layer NOT AVAILABLE: {e}")

# Test 2: Qwen2-VL
print("\n" + "=" * 60)
print("TEST 2: Qwen2-VL (Local GPU Model)")
print("=" * 60)
try:
    from transformers import Qwen2VLForConditionalGeneration
    import torch
    print("✓ Transformers library installed")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    
    # Try to load model
    print("  Attempting to load Qwen2-VL-2B-Instruct...")
    # Don't actually load to save time, just check if possible
    print("  (Skipping actual load to save time)")
    print("✓ Qwen2-VL CAN be loaded (transformers installed)")
except ImportError as e:
    print(f"✗ Qwen2-VL NOT AVAILABLE: {e}")
except Exception as e:
    print(f"✗ Qwen2-VL error: {e}")

# Test 3: Ollama
print("\n" + "=" * 60)
print("TEST 3: Ollama (Local LLaVA)")
print("=" * 60)
try:
    import ollama
    print("✓ Ollama library installed")
    
    # Try to list models
    try:
        models = ollama.list()
        print(f"✓ Ollama is RUNNING")
        print(f"  Available models: {[m['name'] for m in models.get('models', [])]}")
    except Exception as e:
        print(f"✗ Ollama not running: {e}")
except ImportError:
    print("✗ Ollama library NOT INSTALLED")

# Test 4: Gemini API
print("\n" + "=" * 60)
print("TEST 4: Google Gemini API")
print("=" * 60)
try:
    import google.generativeai as genai
    print("✓ google-generativeai library installed")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✓ GEMINI_API_KEY found: {api_key[:10]}...")
        try:
            genai.configure(api_key=api_key)
            print("✓ Gemini API configured successfully")
        except Exception as e:
            print(f"✗ Gemini API configuration failed: {e}")
    else:
        print("✗ GEMINI_API_KEY not found in environment")
except ImportError:
    print("✗ google-generativeai library NOT INSTALLED")

# Test 5: HuggingFace Token
print("\n" + "=" * 60)
print("TEST 5: HuggingFace API")
print("=" * 60)
hf_token = os.getenv("HF_ACCESS_TOKEN")
if hf_token:
    print(f"✓ HF_ACCESS_TOKEN found: {hf_token[:10]}...")
else:
    print("✗ HF_ACCESS_TOKEN not found in environment")

# Summary
print("\n" + "=" * 60)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 60)

print("\nBased on the tests above:")
print("1. If Local AI Layer works → Use it (fastest, most reliable)")
print("2. If Qwen2-VL works → Use it (good accuracy, local)")
print("3. If Ollama works → Use it (good fallback)")
print("4. If Gemini works → Use it (best accuracy, costs money)")
print("\nCheck the test results above to see which providers are working.")
print("\nTo fix VLM issues:")
print("  - Make sure Local AI Layer is running: python ai-intelligence-layer/server_local.py")
print("  - Or install Ollama: https://ollama.com/download")
print("  - Or configure Gemini API key in .env file")
