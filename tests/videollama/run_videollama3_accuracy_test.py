#!/usr/bin/env python3
"""
VideoLLaMA3 Accuracy Test Runner
Comprehensive testing script that works with both real and mock VideoLLaMA3
"""

import os
import sys
import json
from pathlib import Path

def check_videollama_availability():
    """Check if VideoLLaMA3 dependencies are available"""
    try:
        import torch
        import transformers
        import cv2
        from PIL import Image
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        return False

def run_real_test(data_dir="data/sample_videos"):
    """Run test with real VideoLLaMA3 model"""
    print("🚀 Running VideoLLaMA3 Real Model Test")
    print("=" * 50)
    
    try:
        # Import and run the real test
        from test_videollama3_accuracy import VideoLLaMA3AccuracyTest
        
        tester = VideoLLaMA3AccuracyTest(data_dir)
        results = tester.run_accuracy_test()
        tester.print_results()
        tester.save_results("videollama3_real_accuracy_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Real test failed: {e}")
        return None

def run_mock_test(data_dir="data/sample_videos", sample_size=None):
    """Run mock test for demonstration"""
    print("🎭 Running VideoLLaMA3 Mock Test")
    print("=" * 50)
    
    from test_videollama3_mock import VideoLLaMA3MockAccuracyTest
    
    tester = VideoLLaMA3MockAccuracyTest(data_dir)
    results = tester.run_accuracy_test(sample_size)
    tester.print_detailed_results()
    tester.save_results("videollama3_mock_accuracy_results.json")
    
    return results

def generate_summary_report(real_results=None, mock_results=None):
    """Generate a summary report comparing results"""
    report = {
        "test_summary": {
            "timestamp": str(Path.cwd()),
            "total_videos_tested": 0,
            "real_model_available": real_results is not None,
            "mock_test_run": mock_results is not None
        }
    }
    
    if real_results:
        report["real_results"] = {
            "overall_accuracy": real_results["overall"]["accuracy"] * 100,
            "fighting_accuracy": (real_results["fighting"]["correct"] / 
                                real_results["fighting"]["total"] * 100 
                                if real_results["fighting"]["total"] > 0 else 0),
            "normal_accuracy": (real_results["normal"]["correct"] / 
                              real_results["normal"]["total"] * 100 
                              if real_results["normal"]["total"] > 0 else 0),
            "total_videos": real_results["overall"]["total_videos"]
        }
        report["test_summary"]["total_videos_tested"] = real_results["overall"]["total_videos"]
    
    if mock_results:
        report["mock_results"] = {
            "overall_accuracy": mock_results["overall"]["accuracy"] * 100,
            "fighting_accuracy": (mock_results["fighting"]["correct"] / 
                                mock_results["fighting"]["total"] * 100 
                                if mock_results["fighting"]["total"] > 0 else 0),
            "normal_accuracy": (mock_results["normal"]["correct"] / 
                              mock_results["normal"]["total"] * 100 
                              if mock_results["normal"]["total"] > 0 else 0),
            "total_videos": mock_results["overall"]["total_videos"]
        }
        
        if not real_results:
            report["test_summary"]["total_videos_tested"] = mock_results["overall"]["total_videos"]
    
    # Save summary report
    with open("videollama3_test_summary.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    print("🎬 VideoLLaMA3 Accuracy Test Suite")
    print("=" * 40)
    
    # Check data directory
    data_dir = "data/sample_videos"
    if not Path(data_dir).exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Check VideoLLaMA3 availability
    videollama_available = check_videollama_availability()
    
    print(f"📦 VideoLLaMA3 dependencies available: {'Yes' if videollama_available else 'No'}")
    print(f"📁 Test data directory: {data_dir}")
    
    real_results = None
    mock_results = None
    
    if videollama_available:
        print("\n" + "="*50)
        choice = input("Run real VideoLLaMA3 test? (y/n): ").lower().strip()
        
        if choice == 'y':
            real_results = run_real_test(data_dir)
    
    # Always run mock test for comparison
    print("\n" + "="*50)
    choice = input("Run mock test for comparison? (y/n): ").lower().strip()
    
    if choice == 'y':
        sample_choice = input("Use sample size for faster testing? (enter number or 'all'): ").strip()
        
        if sample_choice.lower() == 'all':
            sample_size = None
        else:
            try:
                sample_size = int(sample_choice)
            except ValueError:
                sample_size = 5  # default
        
        mock_results = run_mock_test(data_dir, sample_size)
    
    # Generate summary
    print("\n" + "="*50)
    print("📊 Generating Summary Report...")
    summary = generate_summary_report(real_results, mock_results)
    
    print("\n✅ Test Suite Complete!")
    print(f"📄 Summary report saved to: videollama3_test_summary.json")
    
    if real_results:
        print(f"📄 Real test results: videollama3_real_accuracy_results.json")
    if mock_results:
        print(f"📄 Mock test results: videollama3_mock_accuracy_results.json")

if __name__ == "__main__":
    main()
