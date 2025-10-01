#!/usr/bin/env python3
"""
Setup script for Document Knowledge Base
This script helps you get started with the application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_environment():
    """Set up environment file"""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if env_example.exists():
        print("\n⚙️ Setting up environment file...")
        env_content = env_example.read_text()
        env_file.write_text(env_content)
        print("✅ Created .env file from template")
        print("📝 Please edit .env file and add your OpenAI API key")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["data", "uploads", "vectordb"]
    print("\n📁 Creating directories...")

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created/verified directory: {directory}")

def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")

    try:
        # Test imports
        sys.path.append("src")
        from config import Config
        from document_processor import DocumentProcessor
        from vector_store import VectorStore

        print("✅ All imports successful")

        # Test document processor
        processor = DocumentProcessor()
        print("✅ Document processor initialized")

        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Document Knowledge Base")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        return 1

    # Install requirements
    if not install_requirements():
        return 1

    # Setup environment
    if not setup_environment():
        return 1

    # Create directories
    create_directories()

    # Run tests
    if not run_tests():
        print("\n⚠️ Some tests failed, but setup may still work")

    print("\n" + "=" * 40)
    print("🎉 Setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run: streamlit run src/app.py")
    print("3. Upload documents and start asking questions!")

    return 0

if __name__ == "__main__":
    sys.exit(main())