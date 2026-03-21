#!/usr/bin/env python3
"""
Test Runner for Enhanced Fight Detection

Runs all property-based tests, unit tests, and integration tests.
Generates coverage reports and test summaries.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all test suites."""
    print("="*80)
    print("ENHANCED FIGHT DETECTION - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Test directories
    test_dirs = [
        "tests/property_based",
        "tests/unit",
        "tests/integration"
    ]
    
    all_passed = True
    results = {}
    
    for test_dir in test_dirs:
        print(f"\n{'='*80}")
        print(f"Running tests in: {test_dir}")
        print(f"{'='*80}\n")
        
        # Run pytest with coverage
        cmd = [
            "pytest",
            test_dir,
            "-v",
            "--tb=short",
            "--cov=models",
            "--cov=backend/services",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--html=test_report.html",
            "--self-contained-html"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            results[test_dir] = result.returncode == 0
            if result.returncode != 0:
                all_passed = False
        except Exception as e:
            print(f"Error running tests in {test_dir}: {e}")
            results[test_dir] = False
            all_passed = False
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}\n")
    
    for test_dir, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_dir}")
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
