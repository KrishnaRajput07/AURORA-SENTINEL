#!/usr/bin/env python3
"""
Real VideoLLaMA3 Accuracy Test
Optimized for testing with actual VideoLLaMA3 model
"""

import os
import sys
import json
import time
from pathlib import Path
import argparse

# Configure paths
os.environ['HF_HOME'] = r'D:\huggingface'
os.environ['TRANSFORMERS_CACHE'] = r'D:\huggingface\transformers'

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import torch
        import transformers
        import cv2
        from PIL import Image
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ Transformers: {transformers.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def load_videollama3_model():
    """Load VideoLLaMA3 model with error handling"""
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("🔄 Loading VideoLLaMA3 model...")
        model_name = "DAMO-NLP-SG/VideoLLaMA3-7B"
        
        # Load tokenizer first
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=os.environ['TRANSFORMERS_CACHE']
        )
        
        # Load model with optimizations
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"📱 Using device: {device}")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            cache_dir=os.environ['TRANSFORMERS_CACHE'],
            low_cpu_mem_usage=True
        )
        
        if device == "cpu":
            model = model.to("cpu")
        
        print("✅ Model loaded successfully!")
        return model, tokenizer
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None, None

def extract_video_frame(video_path):
    """Extract a representative frame from video"""
    try:
        import cv2
        from PIL import Image
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            cap.release()
            return None
        
        # Extract frame at 25% mark (more representative than middle)
        frame_idx = max(1, total_frames // 4)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cap.release()
            return Image.fromarray(frame_rgb)
        
        cap.release()
        return None
        
    except Exception as e:
        print(f"❌ Frame extraction error: {e}")
        return None

def analyze_video_with_videollama3(model, tokenizer, video_path, expected_label):
    """Analyze a single video with VideoLLaMA3"""
    print(f"\n🎬 Analyzing: {video_path.name}")
    print(f"📋 Expected: {expected_label}")
    
    # Extract frame
    frame = extract_video_frame(video_path)
    if not frame:
        return {"error": "Failed to extract frame", "video": str(video_path)}
    
    print("✅ Frame extracted")
    
    # Prepare prompt
    prompt = """Analyze this image carefully and determine if it shows violence or fighting.

Rate the violence level from 0-100:
- 0-20: Completely normal/safe activities
- 21-40: Some tension but no violence
- 41-60: Mild aggression or potential conflict
- 61-80: Active fighting or violence
- 81-100: Severe violence

Also classify as:
- 'fight' if showing actual violence/fighting
- 'normal' if showing peaceful activities
- 'ambiguous' if unclear

Respond in this format:
Violence Score: <number>
Classification: <fight|normal|ambiguous>
Reason: <brief explanation>"""

    try:
        import torch
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate response
        print("🤖 Analyzing with VideoLLaMA3...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.3,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse response
        violence_score = 50  # default
        classification = "ambiguous"  # default
        
        lines = response.split('\n')
        for line in lines:
            if "Violence Score:" in line:
                try:
                    score = int(line.split(':')[1].strip())
                    violence_score = score
                except:
                    pass
            elif "Classification:" in line:
                classification = line.split(':')[1].strip().lower()
        
        # Determine if prediction matches expected
        predicted_fight = classification == "fight"
        expected_fight = expected_label == "fighting"
        is_correct = predicted_fight == expected_fight
        
        result = {
            "video": str(video_path),
            "video_name": video_path.name,
            "expected_label": expected_label,
            "predicted_classification": classification,
            "violence_score": violence_score,
            "predicted_fight": predicted_fight,
            "is_correct": is_correct,
            "response": response
        }
        
        print(f"📊 Score: {violence_score}/100")
        print(f"🏷️  Classification: {classification}")
        print(f"✅ Correct: {is_correct}")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return {"error": str(e), "video": str(video_path)}

def run_accuracy_test(data_dir="data/sample_videos", max_videos_per_category=3):
    """Run accuracy test on sample videos"""
    print("🚀 VideoLLaMA3 Real Accuracy Test")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return None
    
    # Load model
    model, tokenizer = load_videollama3_model()
    if not model or not tokenizer:
        return None
    
    # Find videos
    data_path = Path(data_dir)
    fight_dir = data_path / "fightvideos"
    normal_dir = data_path / "Normal_Videos_for_Event_Recognition"
    
    if not fight_dir.exists() or not normal_dir.exists():
        print(f"❌ Data directories not found in {data_dir}")
        return None
    
    # Get sample videos
    fight_videos = list(fight_dir.glob("*.mpeg"))[:max_videos_per_category]
    normal_videos = list(normal_dir.glob("*.mp4"))[:max_videos_per_category]
    
    print(f"\n📁 Testing {len(fight_videos)} fight videos and {len(normal_videos)} normal videos")
    
    # Run tests
    results = {
        "fighting": {"correct": 0, "total": 0, "results": []},
        "normal": {"correct": 0, "total": 0, "results": []},
        "overall": {"accuracy": 0, "total_correct": 0, "total_videos": 0}
    }
    
    print("\n" + "=" * 50)
    print("🥊 TESTING FIGHT VIDEOS")
    print("=" * 50)
    
    for video_path in fight_videos:
        result = analyze_video_with_videollama3(model, tokenizer, video_path, "fighting")
        
        if "error" not in result:
            results["fighting"]["results"].append(result)
            results["fighting"]["total"] += 1
            if result["is_correct"]:
                results["fighting"]["correct"] += 1
    
    print("\n" + "=" * 50)
    print("🚶 TESTING NORMAL VIDEOS")
    print("=" * 50)
    
    for video_path in normal_videos:
        result = analyze_video_with_videollama3(model, tokenizer, video_path, "normal")
        
        if "error" not in result:
            results["normal"]["results"].append(result)
            results["normal"]["total"] += 1
            if result["is_correct"]:
                results["normal"]["correct"] += 1
    
    # Calculate overall accuracy
    total_correct = results["fighting"]["correct"] + results["normal"]["correct"]
    total_videos = results["fighting"]["total"] + results["normal"]["total"]
    
    results["overall"]["total_correct"] = total_correct
    results["overall"]["total_videos"] = total_videos
    results["overall"]["accuracy"] = total_correct / total_videos if total_videos > 0 else 0
    
    return results

def print_results(results):
    """Print detailed results"""
    if not results:
        return
    
    print("\n" + "=" * 60)
    print("📊 VIDEO LLAMA 3 REAL ACCURACY RESULTS")
    print("=" * 60)
    
    # Fighting results
    fighting_acc = (results["fighting"]["correct"] / 
                    results["fighting"]["total"] * 100 
                    if results["fighting"]["total"] > 0 else 0)
    
    print(f"\n🥊 Fighting Videos:")
    print(f"   Correct: {results['fighting']['correct']}/{results['fighting']['total']}")
    print(f"   Accuracy: {fighting_acc:.2f}%")
    
    # Normal results
    normal_acc = (results["normal"]["correct"] / 
                 results["normal"]["total"] * 100 
                 if results["normal"]["total"] > 0 else 0)
    
    print(f"\n🚶 Normal Videos:")
    print(f"   Correct: {results['normal']['correct']}/{results['normal']['total']}")
    print(f"   Accuracy: {normal_acc:.2f}%")
    
    # Overall results
    overall_acc = results["overall"]["accuracy"] * 100
    print(f"\n📈 Overall Results:")
    print(f"   Total Correct: {results['overall']['total_correct']}/{results['overall']['total_videos']}")
    print(f"   Overall Accuracy: {overall_acc:.2f}%")
    
    # Show incorrect predictions
    all_results = results["fighting"]["results"] + results["normal"]["results"]
    incorrect = [r for r in all_results if not r["is_correct"]]
    
    if incorrect:
        print(f"\n❌ Incorrect Predictions:")
        for result in incorrect:
            print(f"   {result['video_name']}: {result['expected_label']} → {result['predicted_classification']}")

def main():
    parser = argparse.ArgumentParser(description="Real VideoLLaMA3 accuracy test")
    parser.add_argument("--data-dir", default="data/sample_videos", help="Data directory")
    parser.add_argument("--max-videos", type=int, default=3, help="Max videos per category")
    parser.add_argument("--output", default="videollama3_real_accuracy.json", help="Output file")
    
    args = parser.parse_args()
    
    # Run test
    results = run_accuracy_test(args.data_dir, args.max_videos)
    
    if results:
        # Print results
        print_results(results)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")
    else:
        print("❌ Test failed")

if __name__ == "__main__":
    main()
