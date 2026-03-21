
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Quick VLM Test - Verify the system is working
"""
import sys
import os
from PIL import Image
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("Loading VLM Service...")
from backend.services.vlm_service import vlm_service

# Create test image
print("Creating test image...")
test_image = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))

# Test analysis
print("\nTesting VLM analysis...")
print("=" * 60)

result = vlm_service.analyze_scene(
    frame_pil=test_image,
    prompt="Describe what you see in this image.",
    risk_score=50
)

print("\nRESULT:")
print(f"  Provider: {result.get('provider', 'unknown')}")
print(f"  Description: {result.get('description', 'N/A')[:200]}...")
print(f"  Risk Score: {result.get('risk_score', 0)}")
print(f"  Latency: {result.get('latency', 0):.2f}s")
print(f"  Ensemble Size: {result.get('ensemble_size', 0)}")

print("\n" + "=" * 60)
if result.get('provider') != 'none':
    print("✓ VLM SYSTEM IS WORKING!")
    print(f"  Using provider: {result.get('provider')}")
else:
    print("✗ VLM SYSTEM NOT WORKING")
    print("  Check the error messages above")
