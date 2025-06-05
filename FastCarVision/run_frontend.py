#!/usr/bin/env python3
"""
FastCarVision Frontend Runner

This script starts the FastCarVision Streamlit frontend application.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Start the FastCarVision frontend application"""
    print("🌐 Starting FastCarVision Frontend...")
    print("=" * 50)
    
    frontend_dir = Path(__file__).parent / "frontend"
    app_file = frontend_dir / "app.py"
    
    if not app_file.exists():
        print(f"❌ Frontend app not found at {app_file}")
        sys.exit(1)
    
    try:
        # Change to frontend directory
        os.chdir(frontend_dir)
        
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 