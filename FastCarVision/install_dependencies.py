#!/usr/bin/env python3
"""
FastCarVision Dependency Installer

This script installs dependencies in the correct order to avoid conflicts.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_pip_command(command, description):
    """Run a pip command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Install dependencies in correct order"""
    print("🚗 FastCarVision Dependency Installer")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Upgrade pip first
    run_pip_command("pip install --upgrade pip", "Upgrading pip")
    
    # Install core dependencies first
    core_deps = [
        "numpy==1.23.5",
        "Pillow==9.5.0", 
        "opencv-python==4.7.0.72",
        "torch==1.13.1",
        "torchvision==0.14.1"
    ]
    
    for dep in core_deps:
        run_pip_command(f"pip install {dep}", f"Installing {dep}")
    
    # Install remaining dependencies
    remaining_deps = [
        "fastapi==0.68.0",
        "uvicorn[standard]==0.15.0",
        "python-multipart==0.0.5",
        "ultralytics==8.0.20",
        "transformers==4.21.0",
        "faiss-cpu==1.7.4",
        "beautifulsoup4==4.12.2",
        "requests==2.28.1",
        "aiohttp==3.8.1",
        "pandas==1.5.3",
        "pydantic==1.10.12",
        "streamlit==1.25.0",
        "python-dotenv==0.20.0"
    ]
    
    for dep in remaining_deps:
        run_pip_command(f"pip install {dep}", f"Installing {dep}")
    
    # Try to install CLIP (optional)
    print("🔄 Installing CLIP (optional)...")
    clip_success = run_pip_command(
        "pip install git+https://github.com/openai/CLIP.git", 
        "Installing CLIP"
    )
    
    if not clip_success:
        print("⚠️  CLIP installation failed, but the app will work with reduced functionality")
    
    print("\n🎉 Dependency installation completed!")
    print("📝 Note: If you see any warnings about package conflicts, they should not affect basic functionality.")
    print("\n📖 Next steps:")
    print("1. Run: python run_backend.py")
    print("2. In another terminal: python run_frontend.py") 

if __name__ == "__main__":
    main() 