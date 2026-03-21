#!/usr/bin/env python3
"""
VideoLLaMA3 Mock Accuracy Test Script
Tests the model's ability to distinguish between fighting and normal videos
Uses mock classification when VideoLLaMA3 is not available
"""

import os
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

class VideoLLaMA3MockAccuracyTest:
    def __init__(self, data_dir: str = "data/sample_videos"):
        self.data_dir = Path(data_dir)
        self.fighting_dir = self.data_dir / "fightvideos"
        self.normal_dir = self.data_dir / "Normal_Videos_for_Event_Recognition"
        
        # Mock model settings (simulating different accuracy levels)
        self.mock_accuracy = {
            "fighting": 0.85,  # 85% accuracy for fighting videos
            "normal": 0.80     # 80% accuracy for normal videos
        }
        
        # Results storage
        self.results = {
            "fighting": {"correct": 0, "total": 0, "predictions": []},
            "normal": {"correct": 0, "total": 0, "predictions": []},
            "overall": {"accuracy": 0, "total_correct": 0, "total_videos": 0}
        }
        
    def get_video_files(self) -> Tuple[List[Path], List[Path]]:
        """Get all fighting and normal video files"""
        fighting_videos = list(self.fighting_dir.glob("*.mpeg"))
        normal_videos = list(self.normal_dir.glob("*.mp4"))
        
        print(f"Found {len(fighting_videos)} fighting videos")
        print(f"Found {len(normal_videos)} normal videos")
        
        return fighting_videos, normal_videos
    
    def classify_video_mock(self, video_path: Path) -> str:
        """
        Mock video classification simulating VideoLLaMA3 behavior
        Returns: 'fighting' or 'normal'
        """
        print(f"Classifying {video_path.name}...")
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Determine true category based on filename
        filename = video_path.name.lower()
        true_category = "fighting" if "fight" in filename else "normal"
        
        # Simulate model prediction with configurable accuracy
        accuracy = self.mock_accuracy[true_category]
        
        if random.random() < accuracy:
            # Correct prediction
            return true_category
        else:
            # Incorrect prediction
            return "normal" if true_category == "fighting" else "fighting"
    
    def test_single_video(self, video_path: Path, true_label: str) -> Dict:
        """Test a single video and return results"""
        predicted_label = self.classify_video_mock(video_path)
        
        is_correct = predicted_label == true_label
        
        result = {
            "video_path": str(video_path),
            "video_name": video_path.name,
            "true_label": true_label,
            "predicted_label": predicted_label,
            "correct": is_correct
        }
        
        return result
    
    def run_accuracy_test(self, sample_size: int = None) -> Dict:
        """Run the complete accuracy test"""
        print("Starting VideoLLaMA3 Mock Accuracy Test...")
        print("=" * 50)
        
        fighting_videos, normal_videos = self.get_video_files()
        
        # Optionally limit sample size for faster testing
        if sample_size:
            fighting_videos = fighting_videos[:sample_size]
            normal_videos = normal_videos[:sample_size]
            print(f"Using sample size: {len(fighting_videos)} fighting, {len(normal_videos)} normal")
        
        # Test fighting videos
        print("\n--- Testing Fighting Videos ---")
        for video_path in fighting_videos:
            result = self.test_single_video(video_path, "fighting")
            self.results["fighting"]["predictions"].append(result)
            self.results["fighting"]["total"] += 1
            if result["correct"]:
                self.results["fighting"]["correct"] += 1
        
        # Test normal videos
        print("\n--- Testing Normal Videos ---")
        for video_path in normal_videos:
            result = self.test_single_video(video_path, "normal")
            self.results["normal"]["predictions"].append(result)
            self.results["normal"]["total"] += 1
            if result["correct"]:
                self.results["normal"]["correct"] += 1
        
        # Calculate overall accuracy
        total_correct = self.results["fighting"]["correct"] + self.results["normal"]["correct"]
        total_videos = self.results["fighting"]["total"] + self.results["normal"]["total"]
        
        self.results["overall"]["total_correct"] = total_correct
        self.results["overall"]["total_videos"] = total_videos
        self.results["overall"]["accuracy"] = total_correct / total_videos if total_videos > 0 else 0
        
        return self.results
    
    def print_detailed_results(self):
        """Print detailed results"""
        print("\n" + "=" * 60)
        print("VIDEO LLAMA 3 MOCK ACCURACY TEST RESULTS")
        print("=" * 60)
        
        # Fighting videos results
        fighting_acc = (self.results["fighting"]["correct"] / 
                       self.results["fighting"]["total"] * 100 
                       if self.results["fighting"]["total"] > 0 else 0)
        
        print(f"\n🥊 Fighting Videos:")
        print(f"   Correct: {self.results['fighting']['correct']}/{self.results['fighting']['total']}")
        print(f"   Accuracy: {fighting_acc:.2f}%")
        print(f"   Expected: {self.mock_accuracy['fighting']*100:.1f}%")
        
        # Normal videos results
        normal_acc = (self.results["normal"]["correct"] / 
                     self.results["normal"]["total"] * 100 
                     if self.results["normal"]["total"] > 0 else 0)
        
        print(f"\n🚶 Normal Videos:")
        print(f"   Correct: {self.results['normal']['correct']}/{self.results['normal']['total']}")
        print(f"   Accuracy: {normal_acc:.2f}%")
        print(f"   Expected: {self.mock_accuracy['normal']*100:.1f}%")
        
        # Overall results
        overall_acc = self.results["overall"]["accuracy"] * 100
        expected_overall = ((self.mock_accuracy['fighting'] * self.results["fighting"]["total"] + 
                           self.mock_accuracy['normal'] * self.results["normal"]["total"]) / 
                          self.results["overall"]["total_videos"] * 100)
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Correct: {self.results['overall']['total_correct']}/{self.results['overall']['total_videos']}")
        print(f"   Overall Accuracy: {overall_acc:.2f}%")
        print(f"   Expected Accuracy: {expected_overall:.2f}%")
        
        # Print misclassified videos
        print(f"\n❌ Misclassified Videos:")
        print("-" * 40)
        
        all_predictions = (self.results["fighting"]["predictions"] + 
                          self.results["normal"]["predictions"])
        
        misclassified = [p for p in all_predictions if not p["correct"]]
        
        if misclassified:
            for pred in misclassified[:10]:  # Show first 10
                print(f"   {pred['video_name']}: {pred['true_label']} → {pred['predicted_label']}")
            if len(misclassified) > 10:
                print(f"   ... and {len(misclassified) - 10} more")
        else:
            print("   None! All videos classified correctly.")
    
    def save_results(self, output_file: str = "videollama3_mock_accuracy_results.json"):
        """Save results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {output_file}")
    
    def generate_report(self, output_file: str = "videollama3_accuracy_report.txt"):
        """Generate a text report"""
        with open(output_file, 'w') as f:
            f.write("VideoLLaMA3 Accuracy Test Report\n")
            f.write("=" * 40 + "\n\n")
            
            f.write(f"Dataset: {self.data_dir}\n")
            f.write(f"Fighting videos: {self.results['fighting']['total']}\n")
            f.write(f"Normal videos: {self.results['normal']['total']}\n")
            f.write(f"Total videos: {self.results['overall']['total_videos']}\n\n")
            
            fighting_acc = (self.results["fighting"]["correct"] / 
                           self.results["fighting"]["total"] * 100 
                           if self.results["fighting"]["total"] > 0 else 0)
            normal_acc = (self.results["normal"]["correct"] / 
                         self.results["normal"]["total"] * 100 
                         if self.results["normal"]["total"] > 0 else 0)
            overall_acc = self.results["overall"]["accuracy"] * 100
            
            f.write(f"Results:\n")
            f.write(f"Fighting accuracy: {fighting_acc:.2f}%\n")
            f.write(f"Normal accuracy: {normal_acc:.2f}%\n")
            f.write(f"Overall accuracy: {overall_acc:.2f}%\n")
        
        print(f"📄 Report saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Mock test VideoLLaMA3 accuracy on fighting vs normal videos")
    parser.add_argument("--data-dir", default="data/sample_videos", 
                       help="Path to video data directory")
    parser.add_argument("--sample-size", type=int, 
                       help="Limit number of videos from each category for faster testing")
    parser.add_argument("--output", default="videollama3_mock_accuracy_results.json",
                       help="Output file for results")
    
    args = parser.parse_args()
    
    # Initialize and run test
    tester = VideoLLaMA3MockAccuracyTest(args.data_dir)
    results = tester.run_accuracy_test(args.sample_size)
    
    # Print and save results
    tester.print_detailed_results()
    tester.save_results(args.output)
    tester.generate_report(args.output.replace('.json', '_report.txt'))

if __name__ == "__main__":
    main()
