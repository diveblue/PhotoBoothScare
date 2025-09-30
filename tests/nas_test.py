#!/usr/bin/env python3
"""
nas_test.py
Quick test script to verify NAS connectivity and file transfer
"""

import os
import json
import time
import shutil
from pathlib import Path


def test_nas_connectivity():
    """Test NAS connectivity and file operations."""
    print("🔍 Testing NAS Connectivity...")

    # Load configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        photo_dir = config["PHOTO_DIR"]
        video_dir = config["VIDEO_DIR"]

        print(f"📁 Photo directory: {photo_dir}")
        print(f"🎬 Video directory: {video_dir}")

    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    # Test directories
    results = {}

    # Test photo directory
    print(f"\n📸 Testing photo directory: {photo_dir}")
    results["photo_dir"] = test_directory(photo_dir)

    # Test video directory
    print(f"\n🎬 Testing video directory: {video_dir}")
    results["video_dir"] = test_directory(video_dir)

    # Create test files and try to move them
    print(f"\n🧪 Testing file operations...")
    results["file_ops"] = test_file_operations(photo_dir, video_dir)

    # Summary
    print(f"\n" + "=" * 50)
    print("📊 SUMMARY:")
    print("=" * 50)

    all_good = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_good = False

    if all_good:
        print("\n🎉 All tests passed! NAS connectivity is working.")
    else:
        print("\n⚠️  Some tests failed. Check network connectivity and permissions.")

    return all_good


def test_directory(dir_path):
    """Test if directory exists and is writable."""
    try:
        # Check if path exists
        if not os.path.exists(dir_path):
            print(f"❌ Directory does not exist: {dir_path}")
            return False

        # Check if it's a directory
        if not os.path.isdir(dir_path):
            print(f"❌ Path is not a directory: {dir_path}")
            return False

        # Check if writable
        test_file = os.path.join(dir_path, f"test_write_{int(time.time())}.tmp")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ Directory is accessible and writable")
            return True
        except Exception as e:
            print(f"❌ Directory is not writable: {e}")
            return False

    except Exception as e:
        print(f"❌ Error testing directory: {e}")
        return False


def test_file_operations(photo_dir, video_dir):
    """Test actual file move operations like the photobooth does."""
    try:
        # Create test files
        session_id = f"TEST_{int(time.time())}"

        # Test photo file
        test_photo = f"photobooth_{session_id}_photo_123.jpg"
        with open(test_photo, "w") as f:
            f.write("fake photo content")

        # Test video file
        test_video = f"photobooth_{session_id}_video_456.mp4"
        with open(test_video, "w") as f:
            f.write("fake video content")

        print(f"📝 Created test files: {test_photo}, {test_video}")

        # Try to move them
        success = True

        # Move photo
        try:
            photo_dest = os.path.join(photo_dir, test_photo)
            shutil.move(test_photo, photo_dest)
            print(f"✅ Photo moved to: {photo_dest}")

            # Clean up
            os.remove(photo_dest)
            print(f"🧹 Cleaned up test photo")

        except Exception as e:
            print(f"❌ Failed to move photo: {e}")
            success = False
            # Clean up local file if move failed
            if os.path.exists(test_photo):
                os.remove(test_photo)

        # Move video
        try:
            video_dest = os.path.join(video_dir, test_video)
            shutil.move(test_video, video_dest)
            print(f"✅ Video moved to: {video_dest}")

            # Clean up
            os.remove(video_dest)
            print(f"🧹 Cleaned up test video")

        except Exception as e:
            print(f"❌ Failed to move video: {e}")
            success = False
            # Clean up local file if move failed
            if os.path.exists(test_video):
                os.remove(test_video)

        return success

    except Exception as e:
        print(f"❌ Error in file operations test: {e}")
        return False


def check_network_paths():
    """Check if network paths are mounted/accessible."""
    print("\n🌐 Checking network connectivity...")

    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)

    photo_dir = config["PHOTO_DIR"]
    video_dir = config["VIDEO_DIR"]

    # Check if these look like network paths
    if photo_dir.startswith("\\\\") or photo_dir.startswith("//"):
        print(f"📡 Detected Windows network path: {photo_dir}")
    elif photo_dir.startswith("/mnt/") or photo_dir.startswith("/media/"):
        print(f"🐧 Detected Linux mount point: {photo_dir}")
    else:
        print(f"💻 Local path detected: {photo_dir}")

    # Check mount status on Linux
    if os.name == "posix":
        try:
            result = os.popen("mount | grep skynas").read()
            if result:
                print(f"📁 NAS mount found: {result.strip()}")
            else:
                print(f"⚠️  No NAS mount found in /proc/mounts")
        except:
            pass


if __name__ == "__main__":
    print("🧪 PhotoBooth NAS Connectivity Test")
    print("=" * 40)

    check_network_paths()
    test_nas_connectivity()
