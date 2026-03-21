#!/usr/bin/env python3
"""
Install transformers to D drive manually
Bypasses C drive space issues
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

def install_transformers_to_d_drive():
    """Download and install transformers to D drive"""
    print("🔄 Installing transformers to D drive...")
    
    # Set target directory
    target_dir = Path("d:/python-packages")
    target_dir.mkdir(exist_ok=True)
    
    # Add to Python path
    if str(target_dir) not in sys.path:
        sys.path.insert(0, str(target_dir))
    
    transformers_dir = target_dir / "transformers"
    
    if transformers_dir.exists():
        print("✅ Transformers already installed in D drive")
        return str(target_dir)
    
    try:
        # Download transformers wheel
        print("📥 Downloading transformers...")
        url = "https://files.pythonhosted.org/packages/9c/7b/17c4b4da1f5c1bc5d6b9d4dc3d1e7c4a5c4b4d4d4d4d4d4d4d4d4d4d4d4d4d4/transformers-4.30.0-py3-none-any.whl"
        wheel_path = target_dir / "transformers-4.30.0-py3-none-any.whl"
        
        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\r📥 Downloading: {percent:.1f}%", end="", flush=True)
        
        urllib.request.urlretrieve(url, wheel_path, progress_hook)
        print("\n✅ Download complete")
        
        # Extract wheel
        print("📦 Extracting transformers...")
        with zipfile.ZipFile(wheel_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # Clean up wheel file
        wheel_path.unlink()
        
        print("✅ Transformers installed to D drive successfully!")
        return str(target_dir)
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return None

def test_transformers_import():
    """Test if transformers can be imported"""
    try:
        import transformers
        print(f"✅ Transformers imported successfully! Version: {transformers.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    # Install to D drive
    target_path = install_transformers_to_d_drive()
    
    if target_path:
        # Test import
        print("\n🧪 Testing import...")
        if test_transformers_import():
            print(f"\n🎉 Success! Transformers is available at: {target_path}")
            print("You can now run the VideoLLaMA3 accuracy test!")
        else:
            print("\n⚠️ Installation succeeded but import failed")
    else:
        print("\n❌ Installation failed")
