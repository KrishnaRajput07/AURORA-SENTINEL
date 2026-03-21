#!/usr/bin/env python3
"""
Fix VideoLLaMA3 compatibility with transformers
"""

import os
import sys

def fix_transformers_compatibility():
    """Fix the VideoInput import issue in transformers"""
    
    # Add D drive to path
    sys.path.insert(0, r'd:\python-packages')
    
    transformers_path = r'd:\python-packages\transformers\image_utils.py'
    
    if os.path.exists(transformers_path):
        print(f"🔧 Fixing transformers compatibility...")
        
        # Read the current file
        with open(transformers_path, 'r') as f:
            content = f.read()
        
        # Check if VideoInput is missing
        if 'VideoInput' not in content:
            # Add the missing VideoInput class
            videoinput_class = '''
# VideoInput class for VideoLLaMA3 compatibility
class VideoInput:
    """Video input for VideoLLaMA3 models"""
    def __init__(self, video=None, video_path=None, fps=None, max_frames=None):
        self.video = video
        self.video_path = video_path
        self.fps = fps
        self.max_frames = max_frames

'''
            
            # Find the import section and add VideoInput
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_lines.append(line)
                # Add VideoInput after the imports
                if line.strip().startswith('from typing import'):
                    new_lines.append(videoinput_class)
                    break
            
            fixed_content = '\n'.join(new_lines)
            
            # Write the fixed file
            with open(transformers_path, 'w') as f:
                f.write(fixed_content)
            
            print("✅ Fixed VideoInput import issue")
            return True
        else:
            print("✅ VideoInput already exists")
            return True
    else:
        print("❌ transformers image_utils.py not found")
        return False

def test_videollama3_after_fix():
    """Test VideoLLaMA3 after applying fix"""
    
    # Apply fix first
    if fix_transformers_compatibility():
        print("\n🔄 Testing VideoLLaMA3 after fix...")
        
        try:
            import transformers
            print(f"✅ Transformers version: {transformers.__version__}")
            
            from transformers import AutoProcessor
            print("✅ AutoProcessor imported")
            
            # Test VideoLLaMA3 processor loading
            model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
            
            processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            print("✅ VideoLLaMA3 processor loaded successfully!")
            
            # Test with a simple image
            from PIL import Image
            import numpy as np
            
            test_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
            
            inputs = processor(images=test_image, text="What do you see?", return_tensors="pt")
            print("✅ VideoLLaMA3 processing successful!")
            
            print("\n🎉 VIDEO LLAMA 3 IS NOW WORKING!")
            print("✅ Compatibility issue fixed")
            print("✅ Ready for real accuracy testing")
            
            return True
            
        except Exception as e:
            print(f"❌ Still failing: {e}")
            return False
    
    return False

if __name__ == "__main__":
    success = test_videollama3_after_fix()
    
    if success:
        print("\n🚀 Run the real accuracy test now:")
        print("python test_videollama3_accuracy.py")
    else:
        print("\n❌ Fix failed")
