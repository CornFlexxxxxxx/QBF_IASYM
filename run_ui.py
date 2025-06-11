#!/usr/bin/env python3
"""
QBF Logic System Launcher
Quick launcher script for the web UI
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        return False
    print("✅ Python version OK")
    
    # Check if in conda environment
    if 'CONDA_DEFAULT_ENV' in os.environ:
        print(f"✅ Conda environment: {os.environ['CONDA_DEFAULT_ENV']}")
    else:
        print("⚠️ Not in conda environment (recommended: conda activate qbf-logic)")
    
    # Check JAR file
    jar_path = Path("org.tweetyproject.logics.qbf-1.28-with-dependencies.jar")
    if jar_path.exists():
        print("✅ TweetyProject JAR found")
    else:
        print("❌ TweetyProject JAR not found")
        return False
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print("✅ Environment configuration found")
    else:
        print("⚠️ .env file not found (API key required for LLM features)")
    
    # Check Java
    try:
        result = subprocess.run(["java", "-version"], capture_output=True)
        if result.returncode == 0:
            print("✅ Java available")
        else:
            print("❌ Java not available")
            return False
    except FileNotFoundError:
        print("❌ Java not found")
        return False
    
    return True

def install_streamlit():
    """Install streamlit if not available"""
    try:
        import streamlit
        return True
    except ImportError:
        print("📦 Installing Streamlit...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "pandas", "plotly"])
            print("✅ Streamlit installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Streamlit")
            return False

def launch_ui():
    """Launch the Streamlit UI"""
    print("\n🚀 Launching QBF Logic System UI...")
    print("📱 Opening in your default browser...")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "qbf_ui.py",
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--theme.base", "light"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 QBF Logic System stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error launching UI: {e}")

def main():
    """Main launcher function"""
    print("🧠 QBF Logic System Launcher")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix the issues above.")
        print("\nQuick setup guide:")
        print("1. conda activate qbf-logic")
        print("2. Copy .env.template to .env and add your API key")
        print("3. Ensure Java is installed")
        return 1
    
    # Install Streamlit if needed
    if not install_streamlit():
        print("\n❌ Could not install required packages.")
        return 1
    
    # Launch UI
    launch_ui()
    return 0

if __name__ == "__main__":
    sys.exit(main())