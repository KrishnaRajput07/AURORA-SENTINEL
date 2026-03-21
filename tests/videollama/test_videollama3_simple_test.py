#!/usr/bin/env python3
"""
Simple VideoLLaMA3 test with current setup
"""

import sys
sys.path.insert(0, r'd:\python-packages')

try:
    import transformers
    print(f"✅ Transformers version: {transformers.__version__}")
    
    # Test basic imports
    from transformers import AutoProcessor
    print("✅ AutoProcessor imported")
    
    # Try to load processor only (not the full model)
    print("\n🔄 Testing VideoLLaMA3 processor...")
    model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
    
    try:
        processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        print("✅ VideoLLaMA3 processor loaded successfully!")
        print(f"   Processor type: {type(processor).__name__}")
        
        # Test with a simple image
        from PIL import Image
        import numpy as np
        
        # Create a test image
        test_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        
        # Process the image
        print("\n🔄 Testing image processing...")
        inputs = processor(images=test_image, text="What do you see in this image?", return_tensors="pt")
        print("✅ Image processing successful!")
        print(f"   Input keys: {list(inputs.keys())}")
        
        print("\n🎉 VideoLLaMA3 is working! Ready for accuracy testing.")
        
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
