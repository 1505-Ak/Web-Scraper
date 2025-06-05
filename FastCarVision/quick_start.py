#!/usr/bin/env python3
"""
FastCarVision Quick Start

This script installs dependencies and performs a basic functionality test.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description, ignore_errors=False):
    """Run a command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠️  {description} had issues but continuing...")
            return False
        else:
            print(f"❌ {description} failed: {e.stderr}")
            return False

def test_basic_imports():
    """Test if basic imports work"""
    print("🧪 Testing basic imports...")
    
    try:
        import numpy
        print("  ✅ numpy")
    except ImportError as e:
        print(f"  ❌ numpy: {e}")
        return False
    
    try:
        import PIL
        print("  ✅ PIL (Pillow)")
    except ImportError as e:
        print(f"  ❌ PIL: {e}")
        return False
    
    try:
        import cv2
        print("  ✅ OpenCV")
    except ImportError as e:
        print(f"  ❌ OpenCV: {e}")
        return False
    
    try:
        import torch
        print("  ✅ PyTorch")
    except ImportError as e:
        print(f"  ❌ PyTorch: {e}")
        return False
    
    try:
        import fastapi
        print("  ✅ FastAPI")
    except ImportError as e:
        print(f"  ❌ FastAPI: {e}")
        return False
    
    try:
        import streamlit
        print("  ✅ Streamlit")
    except ImportError as e:
        print(f"  ❌ Streamlit: {e}")
        return False
    
    return True

def main():
    """Main quick start function"""
    print("🚗 FastCarVision Quick Start")
    print("=" * 50)
    
    # First, try to install dependencies
    print("\n📦 Installing core dependencies...")
    
    # Install in order to avoid conflicts
    deps = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install numpy==1.23.5", "Installing numpy"),
        ("pip install Pillow==9.5.0", "Installing Pillow"),
        ("pip install opencv-python==4.7.0.72", "Installing OpenCV"),
        ("pip install torch==1.13.1 torchvision==0.14.1", "Installing PyTorch"),
        ("pip install fastapi==0.68.0 uvicorn[standard]==0.15.0", "Installing FastAPI"),
        ("pip install streamlit==1.25.0", "Installing Streamlit"),
        ("pip install ultralytics==8.0.20", "Installing YOLOv8"),
        ("pip install pydantic==1.10.12 python-dotenv==0.20.0", "Installing utilities"),
        ("pip install beautifulsoup4==4.12.2 requests==2.28.1 aiohttp==3.8.1", "Installing web scraping tools"),
        ("pip install python-multipart==0.0.5", "Installing multipart"),
    ]
    
    for cmd, desc in deps:
        run_command(cmd, desc, ignore_errors=True)
    
    # Test imports
    print("\n🧪 Testing imports...")
    if test_basic_imports():
        print("✅ All basic imports working!")
    else:
        print("⚠️  Some imports failed, but basic functionality should still work")
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    dirs = ["data", "logs", "backend/app"]
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}/")
    
    # Create .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        with open(env_file, "w") as f:
            f.write("""# FastCarVision Configuration
DEBUG=false
CUDA_AVAILABLE=false
CAR_DETECTION_MODEL=yolov8n.pt
CLIP_MODEL=ViT-B/32
ENABLE_AUTOTRADER=true
ENABLE_CARS_COM=true
""")
        print("  ✅ Created .env file")
    
    print("\n🎉 Quick start completed!")
    print("\n🚀 To start the application:")
    print("1. Backend: python run_backend.py")
    print("2. Frontend: python run_frontend.py")
    print("3. Visit: http://localhost:8501")
    
    print("\n🔍 If you encounter issues:")
    print("- Check that all dependencies installed correctly")
    print("- Make sure ports 8000 and 8501 are available")
    print("- Check the logs for specific error messages")

if __name__ == "__main__":
    main() 