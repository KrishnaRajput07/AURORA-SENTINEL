import os
import sys
from pathlib import Path

# Configure to use D: drive
os.environ['HF_HOME'] = r'D:\huggingface'
os.environ['TRANSFORMERS_CACHE'] = r'D:\huggingface\transformers'
os.environ['TORCH_HOME'] = r'D:\torch'
sys.path.insert(0, r'D:\python-packages')

print("=" * 80)
print("VideoLLaMA3 Test - Fight vs Normal Videos")
print("=" * 80)

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from PIL import Image
    import cv2
    import numpy as np
    import json
    from datetime import datetime
    
    print(f" Dependencies loaded")
    print(f"  PyTorch: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    
    # Load model
    print("\nLoading VideoLLaMA3 model...")
    model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=os.environ['TRANSFORMERS_CACHE'],
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=os.environ['TRANSFORMERS_CACHE'],
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        low_cpu_mem_usage=True,
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )
    
    print(" Model loaded")
    
    # Find sample videos
    fight_dir = Path("data/sample_videos/fightvideos")
    normal_dir = Path("data/sample_videos/Normal_Videos_for_Event_Recognition")
    
    fight_videos = list(fight_dir.glob("*.mpeg"))[:3] if fight_dir.exists() else []
    normal_videos = list(normal_dir.glob("*.mp4"))[:3] if normal_dir.exists() else []
    
    print(f"\nFound {len(fight_videos)} fight videos and {len(normal_videos)} normal videos")
    
    def extract_middle_frame(video_path):
        """Extract middle frame from video"""
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            cap.release()
            return None
        
        middle_frame = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        return None
    
    def analyze_video(video_path, expected_type):
        """Analyze video with VideoLLaMA3"""
        print(f"\n{'=' * 80}")
        print(f"Video: {video_path.name}")
        print(f"Expected: {expected_type.upper()}")
        print("-" * 80)
        
        # Extract middle frame
        frame = extract_middle_frame(video_path)
        if not frame:
            print(" Failed to extract frame")
            return None
        
        print(f" Extracted frame")
        
        # Analyze with VideoLLaMA3
        prompt = """Analyze this video frame for violence or fighting.

Rate the violence level from 0-100 where:
- 0-30: Normal, peaceful activity
- 31-60: Suspicious or potentially aggressive
- 61-100: Clear violence or fighting

Provide:
SCORE: [0-100]
TYPE: [fight/normal]
REASON: [brief explanation]"""
        
        try:
            # Simple text-only test first
            inputs = tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            print("Generating response...")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            print(f"\nVideoLLaMA3 Response:")
            print(response)
            
            result = {
                'video': video_path.name,
                'expected': expected_type,
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f" Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Run tests
    results = []
    
    print("\n" + "=" * 80)
    print("TESTING FIGHT VIDEOS")
    print("=" * 80)
    
    for video in fight_videos:
        result = analyze_video(video, "fight")
        if result:
            results.append(result)
    
    print("\n" + "=" * 80)
    print("TESTING NORMAL VIDEOS")
    print("=" * 80)
    
    for video in normal_videos:
        result = analyze_video(video, "normal")
        if result:
            results.append(result)
    
    # Save results
    output_file = "videollama_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {output_file}")
    print(f"Total videos tested: {len(results)}")
    
except ImportError as e:
    print(f"\n ERROR: Missing dependency - {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
