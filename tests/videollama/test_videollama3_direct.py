#!/usr/bin/env python3
"""
Direct VideoLLaMA3 Test - Bypassing transformers import issues
Works with existing VideoLLaMA3 installation
"""

import os
import sys
import json
import time
from pathlib import Path

def test_videollama3_direct():
    """Test VideoLLaMA3 using direct approach"""
    print("🚀 Direct VideoLLaMA3 Test")
    print("=" * 50)
    
    # Check if we can import basic dependencies
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ CUDA: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch not available")
        return
    
    try:
        import cv2
        from PIL import Image
        print("✅ OpenCV & PIL available")
    except ImportError:
        print("❌ OpenCV/PIL not available")
        return
    
    # Try to import VideoLLaMA3 integration
    try:
        
        from videoLLaMA_integration import VideoLLaMAAnalyzer
        print("✅ VideoLLaMA3 integration loaded")
    except ImportError as e:
        print(f"❌ VideoLLaMA3 integration failed: {e}")
        print("Trying alternative approach...")
        return test_alternative_approach()
    
    # Initialize analyzer
    try:
        print("\n🔄 Initializing VideoLLaMA3 analyzer...")
        analyzer = VideoLLaMAAnalyzer()
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Analyzer initialization failed: {e}")
        return
    
    # Test with sample videos
    data_dir = Path("data/sample_videos")
    fight_dir = data_dir / "fightvideos"
    normal_dir = data_dir / "Normal_Videos_for_Event_Recognition"
    
    if not fight_dir.exists() or not normal_dir.exists():
        print(f"❌ Data directories not found")
        return
    
    # Get sample videos (2 from each category)
    fight_videos = list(fight_dir.glob("*.mpeg"))[:2]
    normal_videos = list(normal_dir.glob("*.mp4"))[:2]
    
    print(f"\n📁 Testing {len(fight_videos)} fight videos and {len(normal_videos)} normal videos")
    
    results = []
    
    # Test fighting videos
    print("\n🥊 Testing Fighting Videos:")
    print("-" * 40)
    
    for video_path in fight_videos:
        try:
            print(f"\n🎬 {video_path.name}")
            result = analyzer.analyze_video_file(str(video_path), fps=1, max_frames=16)
            
            # Determine if prediction is correct
            scene_type = result.get('sceneType', 'normal').lower()
            is_fight = scene_type in ['real_fight', 'fight']
            expected_fight = True  # Since this is fight directory
            is_correct = is_fight == expected_fight
            
            test_result = {
                'video': str(video_path),
                'name': video_path.name,
                'expected': 'fighting',
                'predicted': scene_type,
                'ai_score': result.get('aiScore', 0),
                'confidence': result.get('confidence', 0),
                'is_correct': is_correct,
                'explanation': result.get('explanation', '')[:100]
            }
            
            results.append(test_result)
            
            print(f"  📊 Score: {test_result['ai_score']}/100")
            print(f"  🏷️  Predicted: {scene_type}")
            print(f"  ✅ Correct: {is_correct}")
            print(f"  💬 {test_result['explanation']}...")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'video': str(video_path),
                'name': video_path.name,
                'error': str(e)
            })
    
    # Test normal videos
    print("\n🚶 Testing Normal Videos:")
    print("-" * 40)
    
    for video_path in normal_videos:
        try:
            print(f"\n🎬 {video_path.name}")
            result = analyzer.analyze_video_file(str(video_path), fps=1, max_frames=16)
            
            # Determine if prediction is correct
            scene_type = result.get('sceneType', 'normal').lower()
            is_fight = scene_type in ['real_fight', 'fight']
            expected_fight = False  # Since this is normal directory
            is_correct = is_fight == expected_fight
            
            test_result = {
                'video': str(video_path),
                'name': video_path.name,
                'expected': 'normal',
                'predicted': scene_type,
                'ai_score': result.get('aiScore', 0),
                'confidence': result.get('confidence', 0),
                'is_correct': is_correct,
                'explanation': result.get('explanation', '')[:100]
            }
            
            results.append(test_result)
            
            print(f"  📊 Score: {test_result['ai_score']}/100")
            print(f"  🏷️  Predicted: {scene_type}")
            print(f"  ✅ Correct: {is_correct}")
            print(f"  💬 {test_result['explanation']}...")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'video': str(video_path),
                'name': video_path.name,
                'error': str(e)
            })
    
    # Calculate and display results
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    valid_results = [r for r in results if 'error' not in r]
    correct_count = sum(1 for r in valid_results if r['is_correct'])
    total_count = len(valid_results)
    
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"Overall Accuracy: {accuracy:.1f}% ({correct_count}/{total_count})")
        
        # Breakdown by category
        fight_results = [r for r in valid_results if r['expected'] == 'fighting']
        normal_results = [r for r in valid_results if r['expected'] == 'normal']
        
        fight_correct = sum(1 for r in fight_results if r['is_correct'])
        normal_correct = sum(1 for r in normal_results if r['is_correct'])
        
        print(f"Fighting Videos: {fight_correct}/{len(fight_results)} ({(fight_correct/len(fight_results)*100):.1f}%)" if fight_results else "Fighting Videos: N/A")
        print(f"Normal Videos: {normal_correct}/{len(normal_results)} ({(normal_correct/len(normal_results)*100):.1f}%)" if normal_results else "Normal Videos: N/A")
        
        # Show incorrect predictions
        incorrect = [r for r in valid_results if not r['is_correct']]
        if incorrect:
            print(f"\n❌ Incorrect Predictions:")
            for r in incorrect:
                print(f"  {r['name']}: {r['expected']} → {r['predicted']}")
    else:
        print("❌ No valid results")
    
    # Save results
    output_file = "videollama3_direct_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_tested': total_count,
                'correct': correct_count,
                'accuracy': accuracy if total_count > 0 else 0
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")

def test_alternative_approach():
    """Alternative approach when direct integration fails"""
    print("\n🔄 Trying alternative VideoLLaMA3 approach...")
    
    # Try to use the existing simple test
    try:
        print("Attempting to run existing simple test...")
        exec(open('test_videollama3_simple.py').read())
    except Exception as e:
        print(f"Alternative approach also failed: {e}")
        print("\n📝 Suggestion:")
        print("1. Check if VideoLLaMA3 is properly installed")
        print("2. Verify transformers library installation")
        print("3. Try using the mock test for demonstration:")
        print("   python test_videollama3_mock.py --sample-size 5")

if __name__ == "__main__":
    test_videollama3_direct()
