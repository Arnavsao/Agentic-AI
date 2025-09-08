#!/usr/bin/env python3
"""
Installation script for GAIL RAG Chatbot System
Handles Python 3.13 compatibility issues
"""
import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    if version.major == 3 and version.minor == 13:
        print("⚠️  Python 3.13 detected - using compatible package versions")
        return "py313"
    else:
        print("✅ Python version is compatible")
        return "standard"


def install_packages(requirements_file):
    """Install packages from requirements file."""
    print(f"Installing packages from {requirements_file}...")
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], 
                      check=True)
        
        # Install requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                      check=True)
        
        print("✅ Packages installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ["logs", "static/css", "static/js", "templates", "chroma_db"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")


def create_env_file():
    """Create .env file if it doesn't exist."""
    if not Path(".env").exists():
        env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Web Scraping Configuration
USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
REQUEST_DELAY=1
MAX_RETRIES=3

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("📝 Created .env file - please add your OpenAI API key")


def main():
    """Main installation function."""
    print("🚀 GAIL RAG Chatbot System - Installation")
    print("=" * 50)
    
    # Check Python version
    python_type = check_python_version()
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install packages
    if python_type == "py313":
        requirements_file = "requirements-py313.txt"
    else:
        requirements_file = "requirements.txt"
    
    success = install_packages(requirements_file)
    
    if success:
        print("\n🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file and add your OpenAI API key")
        print("2. Run: python main.py --full-pipeline")
        print("3. Open http://localhost:8000 in your browser")
    else:
        print("\n❌ Installation failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
