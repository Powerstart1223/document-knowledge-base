#!/usr/bin/env python3
"""
Test Document Drafting Functionality
Simple test script for the document drafting pipeline
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path("src").absolute()))

def test_document_analysis():
    """Test document analysis and style learning"""
    print("🧪 Testing Document Analysis...")

    try:
        from document_analyzer import DocumentStyleAnalyzer, DocumentStyleLearner
        from langchain.schema import Document

        # Create test documents
        legal_doc = Document(
            page_content="""
SOFTWARE LICENSE AGREEMENT

This Software License Agreement ("Agreement") is entered into on [DATE] between [COMPANY NAME],
a [STATE] corporation ("Licensor"), and the party downloading or using the software ("Licensee").

WHEREAS, Licensor has developed certain software applications;
WHEREAS, Licensee desires to obtain a license to use such software;

THEREFORE, the parties agree as follows:

1. GRANT OF LICENSE
Licensor hereby grants to Licensee a non-exclusive, non-transferable license to use the Software.

2. RESTRICTIONS
Licensee shall not modify, reverse engineer, or distribute the Software without prior written consent.

3. TERMINATION
This Agreement may be terminated by either party with thirty (30) days written notice.
            """,
            metadata={"source": "software_license.docx", "file_type": ".docx"}
        )

        business_doc = Document(
            page_content="""
BUSINESS PROPOSAL FOR AI CONSULTING SERVICES

Dear Mr. Johnson,

We are pleased to submit this proposal for AI consulting services for your organization.
Our team has extensive experience in implementing AI solutions for businesses of all sizes.

Executive Summary:
Our proposed solution will help streamline your operations and increase efficiency by 40%.

Services Offered:
- AI Strategy Development
- Machine Learning Implementation
- Staff Training and Support
- Ongoing Maintenance

We believe this partnership will deliver significant value to your organization.

Sincerely,
[YOUR NAME]
AI Solutions Inc.
            """,
            metadata={"source": "ai_consulting_proposal.docx", "file_type": ".docx"}
        )

        # Test style analysis
        analyzer = DocumentStyleAnalyzer()
        learner = DocumentStyleLearner()

        # Analyze documents
        legal_analysis = analyzer.analyze_document_structure(legal_doc.page_content, legal_doc.metadata)
        business_analysis = analyzer.analyze_document_structure(business_doc.page_content, business_doc.metadata)

        print(f"✅ Legal document type detected: {legal_analysis['document_type']}")
        print(f"✅ Business document type detected: {business_analysis['document_type']}")

        # Learn from documents
        learning_result = learner.learn_from_documents([legal_doc, business_doc])

        print(f"✅ Learned {len(learning_result['style_templates'])} document styles")
        print(f"✅ Analyzed {learning_result['summary']['total_documents']} documents")

        return True

    except Exception as e:
        print(f"❌ Document analysis test failed: {e}")
        return False

def test_document_export():
    """Test document export functionality"""
    print("\n🧪 Testing Document Export...")

    try:
        from document_exporter import DocumentExporter

        exporter = DocumentExporter()

        # Test content
        test_content = """
TEST DOCUMENT

This is a test document for export functionality.

Key Features:
• Text formatting
• Bullet points
• Professional structure

Generated for testing purposes.
        """

        # Test TXT export (always available)
        result = exporter.export_document(test_content, "txt", "test_document.txt")

        if result["success"]:
            print(f"✅ TXT export successful: {result['filename']}")
        else:
            print(f"❌ TXT export failed: {result['error']}")
            return False

        # Test format availability
        formats = exporter.get_supported_formats()
        print(f"✅ {formats['available_count']}/{formats['total_count']} export formats available")

        for fmt, info in formats["supported_formats"].items():
            status = "✅" if info["available"] else "❌"
            print(f"  {status} {fmt.upper()}: {info['description']}")

        return True

    except Exception as e:
        print(f"❌ Document export test failed: {e}")
        return False

def test_basic_imports():
    """Test that all modules can be imported"""
    print("\n🧪 Testing Module Imports...")

    modules = [
        "document_analyzer",
        "document_drafter",
        "document_exporter"
    ]

    success = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ Successfully imported {module}")
        except Exception as e:
            print(f"❌ Failed to import {module}: {e}")
            success = False

    return success

def main():
    """Run all tests"""
    print("🚀 Testing Document Drafting System")
    print("=" * 50)

    tests = [
        ("Module Imports", test_basic_imports),
        ("Document Analysis", test_document_analysis),
        ("Document Export", test_document_export)
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
        print("\n🎉 All tests passed! Document drafting system is ready.")
        print("\n📝 Next steps:")
        print("1. Make sure you have an OpenAI API key configured")
        print("2. Upload some documents to learn from")
        print("3. Go to the Document Drafting tab and start creating!")
        return 0
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())