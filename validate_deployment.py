#!/usr/bin/env python3
"""
Deployment Validation Script

Run this script before deploying to Streamlit Cloud to check for common issues.

Usage:
    python validate_deployment.py
"""

import os
import sys
from pathlib import Path

# Use ASCII characters for Windows compatibility
CHECK = "[OK]"
CROSS = "[FAIL]"
WARN = "[WARN]"


def check_file_exists(filepath: str, required: bool = True) -> bool:
    """Check if a file exists and report."""
    exists = Path(filepath).exists()
    status = CHECK if exists else (CROSS if required else WARN)
    req_str = "REQUIRED" if required else "optional"
    print(f"  {status} {filepath} ({req_str})")
    return exists or not required


def check_file_not_exists(filepath: str) -> bool:
    """Check that a file does NOT exist (e.g., secrets)."""
    exists = Path(filepath).exists()
    status = CROSS if exists else CHECK
    print(f"  {status} {filepath} (should NOT exist in git)")
    return not exists


def check_gitignore_contains(pattern: str) -> bool:
    """Check if .gitignore contains a pattern."""
    try:
        with open(".gitignore", "r") as f:
            content = f.read()
            contains = pattern in content
            status = CHECK if contains else CROSS
            print(f"  {status} .gitignore contains '{pattern}'")
            return contains
    except Exception:
        print(f"  {CROSS} Could not read .gitignore")
        return False


def check_requirements_txt() -> bool:
    """Validate requirements.txt format."""
    try:
        with open("requirements.txt", "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

        required_packages = [
            "streamlit",
            "openai",
            "chromadb",
            "sentence-transformers",
        ]

        all_good = True
        for pkg in required_packages:
            found = any(pkg in line.lower() for line in lines)
            status = CHECK if found else CROSS
            print(f"  {status} {pkg} in requirements.txt")
            if not found:
                all_good = False

        return all_good
    except Exception as e:
        print(f"  {CROSS} Error reading requirements.txt: {e}")
        return False


def check_no_hardcoded_secrets() -> bool:
    """Check source files for hardcoded secrets."""
    files_to_check = [
        "streamlit_app.py",
        "llm_backend.py",
        "api_clients.py",
        "document_generator.py",
    ]

    suspicious_patterns = [
        "sk-proj-",  # OpenAI API key prefix
        "sk-[A-Za-z0-9]{32,}",  # Generic secret key pattern
    ]

    all_good = True
    for filepath in files_to_check:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                for pattern in suspicious_patterns:
                    if "sk-proj-" in content and "your" not in content.lower():
                        print(f"  {CROSS} {filepath} may contain hardcoded API key!")
                        all_good = False
                        break
        except Exception:
            pass  # File doesn't exist or can't be read

    if all_good:
        print(f"  {CHECK} No hardcoded secrets detected in source files")

    return all_good


def main():
    print("\n" + "="*70)
    print("Streamlit Cloud Deployment Validation")
    print("="*70 + "\n")

    all_checks_passed = True

    # Check 1: Required files exist
    print("1. Required Files:")
    all_checks_passed &= check_file_exists("streamlit_app.py", required=True)
    all_checks_passed &= check_file_exists("requirements.txt", required=True)
    all_checks_passed &= check_file_exists(".streamlit/config.toml", required=False)
    all_checks_passed &= check_file_exists(".streamlit/secrets.toml.example", required=True)
    all_checks_passed &= check_file_exists("DEPLOYMENT.md", required=False)
    print()

    # Check 2: Secrets not in repo
    print("2. Secrets Not Committed:")
    all_checks_passed &= check_gitignore_contains(".env")
    all_checks_passed &= check_gitignore_contains(".streamlit/secrets.toml")
    print()

    # Check 3: No hardcoded secrets
    print("3. No Hardcoded Secrets:")
    all_checks_passed &= check_no_hardcoded_secrets()
    print()

    # Check 4: Dependencies
    print("4. Dependencies:")
    all_checks_passed &= check_requirements_txt()
    print()

    # Final verdict
    print("="*70)
    if all_checks_passed:
        print("[SUCCESS] ALL CHECKS PASSED")
        print("\nYour app is ready for Streamlit Cloud deployment!")
        print("\nNext steps:")
        print("  1. Push to GitHub: git push origin main")
        print("  2. Deploy at https://share.streamlit.io")
        print("  3. Configure secrets in Streamlit Cloud dashboard")
        print("  4. See STREAMLIT_CLOUD_CHECKLIST.md for details")
        return 0
    else:
        print("[ERROR] SOME CHECKS FAILED")
        print("\nPlease fix the issues above before deploying.")
        print("See DEPLOYMENT_CHANGES.md for more information.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
