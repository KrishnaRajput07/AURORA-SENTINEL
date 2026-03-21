#!/usr/bin/env python3
"""
Test VideoLLaMA3 model access
"""

import sys
sys.path.insert(0, r'd:\python-packages')

try:
    import transformers
    print(f"✅ Transformers version: {transformers.__version__}")
    
    from transformers import AutoModelForCausalLM, AutoProcessor
    print("✅ AutoModel classes imported")
    
    print("\n🔄 Testing VideoLLaMA3 model access...")
    model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
    
    try:
        # Test model info access first
        from huggingface_hub import model_info
        info = model_info(model_name)
        print(f"✅ Model info found: {info.modelId}")
        print(f"   Files: {len(info.siblings)}")
        print(f"   Tags: {info.tags}")
        
        # Try to load processor
        print("\n🔄 Testing processor access...")
        processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        print("✅ Processor loaded successfully")
        
        # Try to load model (this might take time)
        print("\n🔄 Testing model loading (may take a while)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype="auto",
            device_map="auto"
        )
        print("✅ VideoLLaMA3 model loaded successfully!")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Parameters: {sum(p.numel() for p in model.parameters())}")
        
    except Exception as e:
        print(f"❌ Model access failed: {e}")
        print("\n🔧 Possible solutions:")
        print("1. Check internet connection")
        print("2. Verify HuggingFace token if required")
        print("3. Try alternative model name")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
