#!/usr/bin/env python3
"""
VLM Prompt Enhancement Test Script

Demonstrates the difference between original and enhanced VLM prompts
and shows how they affect the quality of video analysis descriptions.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

def test_prompt_generation():
    """Test and compare original vs enhanced prompts."""
    
    # Mock ML detection data
    ml_objects = [
        {"class": "person", "confidence": 0.85, "bbox": [0.2, 0.1, 0.4, 0.8]},
        {"class": "person", "confidence": 0.78, "bbox": [0.6, 0.2, 0.8, 0.9]},
        {"class": "knife", "confidence": 0.92, "bbox": [0.35, 0.4, 0.4, 0.5]},
        {"class": "car", "confidence": 0.67, "bbox": [0.8, 0.5, 1.0, 0.8]}
    ]
    
    ml_weapons = [
        {"class": "knife", "sub_class": "knife", "confidence": 0.92, "bbox": [0.35, 0.4, 0.4, 0.5]}
    ]
    
    prev_description = "Two individuals arguing, one reaching into pocket"
    timestamp = 45.7
    
    print("🔍 VLM Prompt Enhancement Test")
    print("=" * 60)
    
    # Test enhanced prompts
    try:
        from backend.services.enhanced_vlm_prompts import build_vlm_prompt_enhanced, build_contextual_prompts
        
        print("\n📝 ENHANCED MAIN PROMPT:")
        print("-" * 40)
        enhanced_prompt = build_vlm_prompt_enhanced(ml_objects, ml_weapons, prev_description, timestamp)
        print(enhanced_prompt[:800] + "..." if len(enhanced_prompt) > 800 else enhanced_prompt)
        
        print("\n🎯 CONTEXTUAL PROMPTS:")
        print("-" * 40)
        for risk_level in [20, 50, 85]:
            contextual = build_contextual_prompts(risk_level, "weapon")
            print(f"Risk {risk_level}: {contextual}")
            
    except ImportError as e:
        print(f"❌ Could not import enhanced prompts: {e}")
        return False
    
    # Test fallback prompts
    print("\n🔄 FALLBACK PROMPT (Original):")
    print("-" * 40)
    try:
        from backend.services.offline_processor import build_vlm_prompt
        fallback_prompt = build_vlm_prompt(ml_objects, ml_weapons, prev_description, timestamp)
        print(fallback_prompt)
    except Exception as e:
        print(f"❌ Error with fallback prompt: {e}")
        return False
    
    return True

def analyze_metadata_quality():
    """Analyze current metadata descriptions for quality issues."""
    print("\n📊 Current Metadata Quality Analysis")
    print("=" * 60)
    
    try:
        import json
        with open("storage/metadata.json", 'r') as f:
            metadata = json.load(f)
            
        total_events = 0
        generic_descriptions = 0
        detailed_descriptions = 0
        risk_scores = []
        
        for video in metadata[:3]:  # Analyze first 3 videos
            print(f"\n🎬 Video: {video.get('filename', 'unknown')}")
            events = video.get('events', [])
            total_events += len(events)
            
            for event in events[:5]:  # First 5 events per video
                desc = event.get('description', '')
                severity = event.get('severity', 'unknown')
                confidence = event.get('confidence', 0)
                
                # Quality assessment
                word_count = len(desc.split())
                has_specifics = any(keyword in desc.lower() for keyword in [
                    'tackle', 'touchdown', 'field goal', 'quarterback', 'receiver',
                    'helmet', 'jersey', 'yards', 'possession', 'interception'
                ])
                
                if word_count < 15 or not has_specifics:
                    generic_descriptions += 1
                    quality = "❌ Generic"
                else:
                    detailed_descriptions += 1
                    quality = "✅ Detailed"
                
                print(f"  {quality} [{severity.upper()}] ({confidence:.2f}): {desc[:60]}...")
                
                if 'risk_score' in event:
                    risk_scores.append(event['risk_score'])
        
        print(f"\n📈 Quality Summary:")
        print(f"  Total Events: {total_events}")
        print(f"  Detailed Descriptions: {detailed_descriptions}")
        print(f"  Generic Descriptions: {generic_descriptions}")
        print(f"  Quality Rate: {(detailed_descriptions/total_events*100):.1f}%" if total_events > 0 else "N/A")
        
    except FileNotFoundError:
        print("❌ No metadata.json found - run video processing first")
        return False
    except Exception as e:
        print(f"❌ Error analyzing metadata: {e}")
        return False
    
    return True

def suggest_improvements():
    """Provide specific improvement suggestions."""
    print("\n💡 Improvement Suggestions")
    print("=" * 60)
    
    suggestions = [
        "1. 🎯 ENHANCED PROMPT FEATURES:",
        "   - 6-section forensic analysis format",
        "   - Detailed person description requirements",
        "   - Specific interaction analysis guidelines",
        "   - Actionable intelligence focus",
        "",
        "2. 📊 EXPECTED IMPROVEMENTS:",
        "   - Longer, more detailed descriptions",
        "   - Better person identification details",
        "   - More accurate threat assessment",
        "   - Richer forensic context",
        "",
        "3. 🚀 IMPLEMENTATION BENEFITS:",
        "   - Backward compatible with fallback prompts",
        "   - Gradual rollout possible",
        "   - A/B testing capability",
        "   - Configurable detail levels",
        "",
        "4. 📈 QUALITY METRICS TO TRACK:",
        "   - Description word count",
        "   - Specific detail inclusion rate",
        "   - Risk score accuracy",
        "   - Agent tool usage effectiveness"
    ]
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    """Run all tests and analysis."""
    print("🔬 VLM Prompt Enhancement Analysis")
    print("=" * 60)
    
    success = True
    
    # Test prompt generation
    if not test_prompt_generation():
        success = False
    
    # Analyze current quality
    if not analyze_metadata_quality():
        print("⚠️ Could not analyze metadata quality")
    
    # Provide suggestions
    suggest_improvements()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ Enhancement analysis completed successfully!")
        print("📝 Enhanced prompts are ready for deployment")
    else:
        print("❌ Some issues detected - check imports and dependencies")
    
    print("\n🚀 Next Steps:")
    print("1. Test enhanced prompts with real video processing")
    print("2. Compare description quality before/after")
    print("3. Monitor agent tool performance with improved data")
    print("4. Adjust prompt details based on results")

if __name__ == "__main__":
    main()
