#!/usr/bin/env python3
"""
pi_nas_test.py
Test NAS connectivity on Raspberry Pi
"""

import os
import json
import subprocess
import time


def check_skynas_mount():
    """Check if SKYNAS is properly mounted on Pi."""
    print("🔍 Checking SKYNAS mount status...")

    try:
        # Check current mounts
        result = subprocess.run(["mount"], capture_output=True, text=True)
        skynas_mounts = [
            line for line in result.stdout.split("\n") if "skynas" in line.lower()
        ]

        if skynas_mounts:
            print("✅ SKYNAS mounts found:")
            for mount in skynas_mounts:
                print(f"   📁 {mount}")
            return True
        else:
            print("❌ No SKYNAS mounts found")
            return False

    except Exception as e:
        print(f"❌ Error checking mounts: {e}")
        return False


def suggest_mount_commands():
    """Suggest mount commands for SKYNAS."""
    print("\n💡 To mount SKYNAS, try these commands:")
    print("=" * 50)
    print("# Create mount points:")
    print("sudo mkdir -p /mnt/skynas/web/Halloween2025/media/photos")
    print("sudo mkdir -p /mnt/skynas/web/Halloween2025/media/videos")
    print()
    print("# Mount SKYNAS (replace with your actual IP/credentials):")
    print("sudo mount -t cifs //SKYNAS_IP/web /mnt/skynas/web \\")
    print("  -o username=YOUR_USERNAME,password=YOUR_PASSWORD,uid=pi,gid=pi")
    print()
    print("# Or add to /etc/fstab for permanent mounting:")
    print(
        "//SKYNAS_IP/web /mnt/skynas/web cifs username=USER,password=PASS,uid=pi,gid=pi 0 0"
    )


def test_file_operations():
    """Test file operations in current directory and suggest paths."""
    print("\n🧪 Testing local file operations...")

    try:
        # Test in current directory
        test_file = f"test_{int(time.time())}.txt"
        with open(test_file, "w") as f:
            f.write("test content")

        print(f"✅ Can write to current directory: {os.getcwd()}")
        os.remove(test_file)

        # Check if we can create photos/videos directories locally
        os.makedirs("local_photos", exist_ok=True)
        os.makedirs("local_videos", exist_ok=True)

        # Test writing to local directories
        test_photo = "local_photos/test_photo.jpg"
        test_video = "local_videos/test_video.mp4"

        with open(test_photo, "w") as f:
            f.write("fake photo")
        with open(test_video, "w") as f:
            f.write("fake video")

        print("✅ Created local test directories:")
        print(f"   📸 {os.path.abspath('local_photos')}")
        print(f"   🎬 {os.path.abspath('local_videos')}")

        # Clean up
        os.remove(test_photo)
        os.remove(test_video)

        return True

    except Exception as e:
        print(f"❌ Local file operations failed: {e}")
        return False


def update_config_for_pi():
    """Update config.json with Pi-appropriate paths."""
    print("\n🔧 Updating config for Pi...")

    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        # Show current paths
        print(f"Current PHOTO_DIR: {config['PHOTO_DIR']}")
        print(f"Current VIDEO_DIR: {config['VIDEO_DIR']}")

        # Suggest new paths
        suggested_paths = {
            "local_fallback": {
                "PHOTO_DIR": "./local_photos",
                "VIDEO_DIR": "./local_videos",
            },
            "nas_mounted": {
                "PHOTO_DIR": "/mnt/skynas/web/Halloween2025/media/photos",
                "VIDEO_DIR": "/mnt/skynas/web/Halloween2025/media/videos",
            },
        }

        print("\n💡 Suggested path options:")
        print("1. Local fallback (for testing):")
        print(f"   PHOTO_DIR: {suggested_paths['local_fallback']['PHOTO_DIR']}")
        print(f"   VIDEO_DIR: {suggested_paths['local_fallback']['VIDEO_DIR']}")

        print("\n2. NAS mounted (for production):")
        print(f"   PHOTO_DIR: {suggested_paths['nas_mounted']['PHOTO_DIR']}")
        print(f"   VIDEO_DIR: {suggested_paths['nas_mounted']['VIDEO_DIR']}")

        # For now, let's update to local paths for testing
        config["PHOTO_DIR"] = suggested_paths["local_fallback"]["PHOTO_DIR"]
        config["VIDEO_DIR"] = suggested_paths["local_fallback"]["VIDEO_DIR"]

        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

        print("\n✅ Updated config.json with local fallback paths for testing")
        return True

    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False


def main():
    print("🍓 Pi NAS Connectivity Test")
    print("=" * 30)

    # Check current system
    print(f"🖥️  System: {os.uname().sysname} {os.uname().release}")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USER', 'unknown')}")

    # Check SKYNAS mount
    skynas_mounted = check_skynas_mount()

    if not skynas_mounted:
        suggest_mount_commands()

    # Test local file operations
    local_works = test_file_operations()

    if local_works:
        print("\n🎯 RECOMMENDATION:")
        print(
            "1. For immediate testing: Use local directories (./local_photos, ./local_videos)"
        )
        print("2. For production: Mount SKYNAS and update paths")

        # Update config for local testing
        update_config_for_pi()

    print(f"\n{'=' * 50}")
    print("🏁 Next steps:")
    print("1. Run: python nas_test.py  (to test with new paths)")
    print("2. Take a test photo to verify file saving works")
    print("3. Set up SKYNAS mount for production use")


if __name__ == "__main__":
    main()
