"""
Real VideoLLaMA3 Test with Sample Videos
Tests VideoLLaMA3 model with actual fight and normal videos
"""
import os
import sys
from pathlib import Path

# Configure D: drive paths
os.environ['HF_HOME'] = r'D:\huggingface'
os.environ['TRANSFORMERS_CACHE'] = r'D:\huggingface\transformers'
os.environ['TORCH_HOME'] = r'D:\torch'
sys.path.insert(0, r'D:\python-packages')

print("=" * 80)
print("VideoLLaMA3 Real Test")
print("=" * 80)

try:
    import torch
    from transformers import AutoProcessor, AutoModelForVision2Seq
    from PIL import Image
    import cv2
    import numpy as np
    import json
    from datetime import datetime
    
    print(f"✓ PyTorch: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    
    # Load VideoLLaMA3 model
    print("\nLoading VideoLLaMA3 model...")
    model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
    
    processor = AutoProcessor.from_pretrained(
        model_name,
        cache_dir=os.environ['TRANSFORMERS_CACHE'],
        trust_remote_code=True
    )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForVision2Seq.from_pretrained(
        model_name,
        cache_dir=os.environ['TRANSFORMERS_CACHE'],
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True
    ).to(device)
    
    print(f"✓ Model loaded on {device}")
    
    def extract_frames(video_path, num_frames=8):
        """Extract evenly spaced frames from video"""
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames == 0:
            cap.release()
            return []
        
        # Extract frames evenly distributed
        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        frames = []
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
        
        cap.release()
        return frames
    
    def analyze_video_with_videollama(video_path, expected_type):
        """Analyze video with VideoLLaMA3"""
        print(f"\n{'=' * 80}")
        print(f"Video: {video_path.name}")
        print(f"Expected: {expected_type.upper()}")
        print("-" * 80)
        
        start_time = datetime.now()
        
        # Extract frames
        frames = extract_frames(video_path, num_frames=8)
        if not frames:
            print("✗ Failed to extract frames")
            return None
        
        print(f"✓ Extracted {len(frames)} frames")
        
        # Prepare prompt for violence detection
        prompt = """<|im_start|>system
You are a security AI analyzing surveillance video for violence detection.<|im_end|>
<|im_start|>user
<video>
Analyze this video sequence carefully. Determine if it shows violence, fighting, or aggressive behavior.

Provide your analysis in this EXACT format:
VIOLENCE_SCORE: [number 0-100]
SCENE_TYPE: [fight/normal/ambiguous]
CONFIDENCE: [low/medium/high]
REASONING: [brief explanation of what you see]

Focus on:
- Physical aggression or fighting between people
- Threatening gestures or behavior
- Rapid aggressive movements
- People in conflict or confrontation<|im_end|>
<|im_start|>assistant
"""
        
        try:
            # Process inputs
            inputs = processor(
                text=prompt,
                images=frames,
                return_tensors="pt",
                padding=True
            ).to(device)
            
            # Generate response
            print("Analyzing with VideoLLaMA3...")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    temperature=0.7,
                    top_p=0.9
                )
            
            # Decode response
            response = processor.batch_decode(outputs, skip_special_tokens=True)[0]
            
            # Extract assistant response
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1].strip()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'=' * 80}")
            print("VideoLLaMA3 Response:")
            print("-" * 80)
            print(response)
            print("-" * 80)
            print(f"Analysis time: {duration:.2f}s")
            print(f"Expected: {expected_type.upper()}")
            
            # Parse response for scoring
            violence_score = None
            scene_type = None
            confidence = None
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('VIOLENCE_SCORE:'):
                    try:
                        violence_score = int(''.join(filter(str.isdigit, line.split(':')[1])))
                    except:
                        pass
                elif line.startswith('SCENE_TYPE:'):
                    scene_type = line.split(':')[1].strip().lower()
                elif line.startswith('CONFIDENCE:'):
                    confidence = line.split(':')[1].strip().lower()
            
            result = {
                'video': video_path.name,
                'expected': expected_type,
                'violence_score': violence_score,
                'scene_type': scene_type,
                'confidence': confidence,
                'full_response': response,
                'frames_analyzed': len(frames),
                'duration_seconds': duration,
                'device': device
            }
            
            # Determine if correct
            if scene_type:
                if expected_type == 'fight' and scene_type == 'fight':
                    result['correct'] = True
                elif expected_type == 'normal' and scene_type == 'normal':
                    result['correct'] = True
                else:
                    result['correct'] = False
            else:
                result['correct'] = None
            
            return result
            
        except Exception as e:
            print(f"✗ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Find sample videos
    fight_dir = Path("data/sample_videos/fightvideos")
    normal_dir = Path("data/sample_videos/Normal_Videos_for_Event_Recognition")
    
    # Get 3 fight and 3 normal videos for testing
    fight_videos = sorted(list(fight_dir.glob("*.mpeg")))[:3] if fight_dir.exists() else []
    normal_videos = sorted(list(normal_dir.glob("*.mp4")))[:3] if normal_dir.exists() else []
    
    print(f"\nFound {len(fight_videos)} fight videos and {len(normal_videos)} normal videos")
    
    if not fight_videos and not normal_videos:
        print("✗ No videos found!")
        sys.exit(1)
    
    # Run tests
    results = []
    
    print("\n" + "=" * 80)
    print("TESTING FIGHT VIDEOS")
    print("=" * 80)
    
    for video in fight_videos:
        result = analyze_video_with_videollama(video, "fight")
        if result:
            results.append(result)
    
    print("\n" + "=" * 80)
    print("TESTING NORMAL VIDEOS")
    print("=" * 80)
    
    for video in normal_videos:
        result = analyze_video_with_videollama(video, "normal")
        if result:
            results.append(result)
    
    # Calculate accuracy
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    correct = sum(1 for r in results if r.get('correct') == True)
    total = len([r for r in results if r.get('correct') is not None])
    
    if total > 0:
        accuracy = (correct / total) * 100
        print(f"\nOverall Accuracy: {accuracy:.1f}% ({correct}/{total})")
    
    # Fight detection accuracy
    fight_results = [r for r in results if r['expected'] == 'fight' and r.get('correct') is not None]
    if fight_results:
        fight_correct = sum(1 for r in fight_results if r['correct'])
        fight_accuracy = (fight_correct / len(fight_results)) * 100
        print(f"Fight Detection: {fight_accuracy:.1f}% ({fight_correct}/{len(fight_results)})")
    
    # Normal detection accuracy
    normal_results = [r for r in results if r['expected'] == 'normal' and r.get('correct') is not None]
    if normal_results:
        normal_correct = sum(1 for r in normal_results if r['correct'])
        normal_accuracy = (normal_correct / len(normal_results)) * 100
        print(f"Normal Detection: {normal_accuracy:.1f}% ({normal_correct}/{len(normal_results)})")
    
    # Average analysis time
    avg_time = sum(r['duration_seconds'] for r in results) / len(results) if results else 0
    print(f"\nAverage Analysis Time: {avg_time:.2f}s per video")
    print(f"Device: {device}")
    
    # Save results
    output_file = "videollama3_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model': model_name,
            'device': device,
            'total_videos': len(results),
            'accuracy': accuracy if total > 0 else None,
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print("=" * 80)
    
except ImportError as e:
    print(f"\n✗ Import error: {e}")
    print("\nMissing dependencies. Install with:")
    print("pip install torch transformers pillow opencv-python")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
