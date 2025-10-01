#!/usr/bin/env python3
"""
Test script for Document Knowledge Base
This script tests the core functionality without requiring a full setup
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_document_processing():
    """Test document processing functionality"""
    print("🧪 Testing document processing...")

    try:
        from document_processor import DocumentProcessor

        processor = DocumentProcessor()

        # Test with sample document
        sample_file = Path("data/sample_document.txt")
        if sample_file.exists():
            documents = processor.process_document(str(sample_file))
            print(f"✅ Processed {len(documents)} chunks from sample document")
            return True
        else:
            print("❌ Sample document not found")
            return False

    except Exception as e:
        print(f"❌ Document processing test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("🧪 Testing configuration...")

    try:
        from config import Config

        # Test config values
        print(f"✅ Chunk size: {Config.CHUNK_SIZE}")
        print(f"✅ Chunk overlap: {Config.CHUNK_OVERLAP}")
        print(f"✅ Use local model: {Config.USE_LOCAL_MODEL}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_vector_store_init():
    """Test vector store initialization (without API key)"""
    print("🧪 Testing vector store initialization...")

    try:
        # Set local model to avoid API key requirement
        os.environ['USE_LOCAL_MODEL'] = 'true'

        from vector_store import VectorStore

        # This should work with local embeddings
        vector_store = VectorStore()
        stats = vector_store.get_collection_stats()

        print(f"✅ Vector store initialized")
        print(f"✅ Collection stats: {stats}")

        return True

    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        print("ℹ️ This might fail if dependencies aren't installed")
        return False

def test_imports():
    """Test all module imports"""
    print("🧪 Testing imports...")

    modules = [
        "config",
        "document_processor",
        "vector_store",
        "rag_pipeline"
    ]

    success = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ Imported {module}")
        except Exception as e:
            print(f"❌ Failed to import {module}: {e}")
            success = False

    return success

def main():
    """Run all tests"""
    print("🚀 Testing Document Knowledge Base System")
    print("=" * 50)

    tests = [
        ("Configuration", test_configuration),
        ("Imports", test_imports),
        ("Document Processing", test_document_processing),
        ("Vector Store", test_vector_store_init),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("-" * 20)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! System appears to be working correctly.")
        print("\n📝 Next steps:")
        print("1. Set up your .env file with OpenAI API key")
        print("2. Run: streamlit run src/app.py")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
        print("You may need to install dependencies: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())