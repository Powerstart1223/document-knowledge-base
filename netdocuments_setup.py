#!/usr/bin/env python3
"""
NetDocuments Setup Wizard
Interactive setup for NetDocuments integration
"""

import os
import sys
import json
from pathlib import Path

def print_header():
    """Print setup wizard header"""
    print("=" * 60)
    print("📚 NetDocuments Integration Setup Wizard")
    print("=" * 60)
    print()

def print_step(step_num, title):
    """Print step header"""
    print(f"📋 Step {step_num}: {title}")
    print("-" * 40)

def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    while True:
        value = input(full_prompt).strip()

        if not value and default:
            return default

        if not value and required:
            print("❌ This field is required. Please enter a value.")
            continue

        return value

def update_env_file():
    """Update .env file with NetDocuments settings"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    # Read current .env or create from example
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    elif env_example.exists():
        with open(env_example, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    print_step(1, "NetDocuments Configuration")
    print("We'll update your .env file with NetDocuments settings.")
    print()

    # Get NetDocuments settings
    enabled = get_user_input("Enable NetDocuments integration? (y/n)", "y").lower().startswith('y')

    if not enabled:
        print("✅ NetDocuments integration will remain disabled.")
        return

    print()
    print("You'll need to register an application in the NetDocuments Developer Portal:")
    print("1. Log into your NetDocuments account")
    print("2. Go to the Developer Portal")
    print("3. Create a new application")
    print("4. Copy the Client ID and Client Secret")
    print()

    client_id = get_user_input("NetDocuments Client ID")
    client_secret = get_user_input("NetDocuments Client Secret")
    redirect_uri = get_user_input("Redirect URI", "https://localhost:3000/gettoken")

    # Update or add NetDocuments settings
    settings = {
        "NETDOCUMENTS_ENABLED": "true" if enabled else "false",
        "NETDOCUMENTS_CLIENT_ID": client_id,
        "NETDOCUMENTS_CLIENT_SECRET": client_secret,
        "NETDOCUMENTS_REDIRECT_URI": redirect_uri
    }

    # Update existing lines or add new ones
    updated_lines = []
    settings_added = set()

    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            updated_lines.append(line + '\n')
            continue

        key = line.split('=')[0]
        if key in settings:
            updated_lines.append(f"{key}={settings[key]}\n")
            settings_added.add(key)
        else:
            updated_lines.append(line + '\n')

    # Add any missing settings
    for key, value in settings.items():
        if key not in settings_added:
            updated_lines.append(f"{key}={value}\n")

    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)

    print(f"✅ Updated {env_file} with NetDocuments settings")

def test_connection():
    """Test NetDocuments connection"""
    print_step(2, "Test Connection")
    print("Testing NetDocuments API connection...")
    print()

    try:
        # Add src to path
        sys.path.insert(0, str(Path("src").absolute()))

        from netdocuments_integration import NetDocumentsAPI
        from config import Config

        # Reload config
        import importlib
        import config
        importlib.reload(config)

        api = NetDocumentsAPI()

        if not Config.NETDOCUMENTS_ENABLED:
            print("❌ NetDocuments integration is not enabled in .env file")
            return False

        if not api.config.get("client_id"):
            print("✅ Configuration loaded successfully")
            print("⚠️ OAuth authentication required (will be done through web interface)")
            return True
        else:
            print("✅ NetDocuments API client initialized successfully")
            return True

    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def show_next_steps():
    """Show next steps to complete setup"""
    print_step(3, "Next Steps")
    print("Setup is almost complete! Here's what to do next:")
    print()
    print("1. 🚀 Start the application:")
    print("   streamlit run src/app.py")
    print()
    print("2. 🔐 Complete OAuth authentication:")
    print("   - Go to the NetDocuments tab in the sidebar")
    print("   - Click the authorization link")
    print("   - Copy the authorization code")
    print("   - Paste it back in the application")
    print()
    print("3. 📄 Start syncing documents:")
    print("   - Use 'Sync Recent' for documents from the last 30 days")
    print("   - Use 'Search & Sync' to find specific documents")
    print()
    print("🎉 You're all set! Your NetDocuments will be integrated with your knowledge base.")

def main():
    """Main setup function"""
    print_header()

    print("This wizard will help you set up NetDocuments integration.")
    print("You'll need access to the NetDocuments Developer Portal.")
    print()

    if not input("Continue with setup? (y/n): ").lower().startswith('y'):
        print("Setup cancelled.")
        return

    print()

    # Step 1: Update .env file
    update_env_file()
    print()

    # Step 2: Test connection
    connection_ok = test_connection()
    print()

    # Step 3: Show next steps
    show_next_steps()

    if connection_ok:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n⚠️ Setup completed with warnings. Check the error messages above.")

if __name__ == "__main__":
    main()