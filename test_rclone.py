#!/usr/bin/env python3
"""
Test script to validate rclone integration.
This script tests the RcloneClient functionality to ensure proper setup.
"""

import sys
from pathlib import Path

# Add the zoom_manager package to the path
sys.path.insert(0, str(Path(__file__).parent / "zoom_manager"))

try:
    from zoom_manager.src.rclone_client import RcloneClient
    from zoom_manager.config.settings import RCLONE_REMOTE_NAME, RCLONE_BASE_PATH
    print("✅ Successfully imported RcloneClient")
except ImportError as e:
    print(f"❌ Failed to import RcloneClient: {e}")
    sys.exit(1)

def test_rclone_availability():
    """Test if rclone is available and configured."""
    print("\n🔍 Testing rclone availability...")
    
    try:
        client = RcloneClient()
        print(f"✅ rclone is available")
        print(f"✅ Remote '{client.remote_name}' is configured")
        print(f"✅ Base path: {client.base_path}")
        return client
    except RuntimeError as e:
        print(f"❌ rclone setup error: {e}")
        return None

def test_remote_connection(client):
    """Test connection to the rclone remote."""
    print("\n🌐 Testing remote connection...")
    
    if client.test_connection():
        print("✅ Successfully connected to remote")
        return True
    else:
        print("❌ Failed to connect to remote")
        return False

def test_remote_info(client):
    """Get and display remote configuration info."""
    print("\n📋 Getting remote configuration...")
    
    config = client.get_remote_info()
    if config:
        print("✅ Remote configuration:")
        for key, value in config.items():
            # Mask sensitive values
            if any(sensitive in key.lower() for sensitive in ['token', 'secret', 'key', 'password']):
                value = '***MASKED***'
            print(f"   {key}: {value}")
        return True
    else:
        print("❌ Failed to get remote configuration")
        return False

def main():
    """Run all tests."""
    print("🧪 Zoom to Drive - rclone Integration Test")
    print("=" * 50)
    
    # Test rclone availability
    client = test_rclone_availability()
    if not client:
        print("\n❌ Test failed: rclone is not properly set up")
        print("\nTo fix this:")
        print("1. Install rclone: brew install rclone (macOS) or curl https://rclone.org/install.sh | sudo bash (Linux)")
        print("2. Configure rclone: rclone config")
        print(f"3. Create a Google Drive remote named '{RCLONE_REMOTE_NAME}' or set RCLONE_REMOTE_NAME")
        print("4. Set up access to your Google Shared Drive")
        sys.exit(1)
    
    # Test remote connection
    if not test_remote_connection(client):
        print("\n❌ Test failed: Cannot connect to remote")
        print("\nTo fix this:")
        print("1. Check your internet connection")
        print(f"2. Verify rclone configuration: rclone config show {client.remote_name}")
        print(f"3. Test manually: rclone lsd {client.remote_name}:")
        sys.exit(1)
    
    # Test remote info
    test_remote_info(client)
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! rclone integration is working correctly.")
    print(f"📁 Files will be uploaded to: {client.base_path}/YYYY-MM-DD/")
    print(f"🔗 Using remote: {client.remote_name}")

if __name__ == "__main__":
    main()
