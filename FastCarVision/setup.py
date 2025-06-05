#!/usr/bin/env python3
"""
FastCarVision Setup Script

This script helps install dependencies and set up the FastCarVision application.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚗 FastCarVision Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("⚠️  Some dependencies may have failed to install. Check the output above.")
        
    # Create necessary directories
    print("📁 Creating necessary directories...")
    directories = ["data", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ Created {directory}/ directory")
    
    # Make run scripts executable
    print("🔧 Setting up run scripts...")
    scripts = ["run_backend.py", "run_frontend.py"]
    for script in scripts:
        if Path(script).exists():
            os.chmod(script, 0o755)
            print(f"   ✅ Made {script} executable")
    
    # Create environment file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if not env_file.exists() and env_example.exists():
        print("📋 Creating .env file from example...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("   ✅ Created .env file")
        print("   ⚠️  Please review and modify .env file as needed")
    
    print("\n🎉 Setup completed!")
    print("\n📖 Next steps:")
    print("1. Review and modify .env file if needed")
    print("2. Start the backend server: python run_backend.py")
    print("3. Start the frontend: python run_frontend.py")
    print("4. Open your browser to http://localhost:8501")
    print("\n🔗 API Documentation will be available at: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 