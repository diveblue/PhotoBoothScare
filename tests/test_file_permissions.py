#!/usr/bin/env python3
"""
Test file permissions for PhotoBooth NAS setup
Run this on the Pi to diagnose file permission issues
"""

import os
import stat
import subprocess
import tempfile
import json
from pathlib import Path


def get_mount_info():
    """Get mount information for debugging"""
    try:
        result = subprocess.run(["mount"], capture_output=True, text=True)
        mounts = result.stdout
        print("=== MOUNT INFO ===")
        for line in mounts.split("\n"):
            if (
                "skynas" in line.lower()
                or "cifs" in line.lower()
                or "smb" in line.lower()
            ):
                print(f"📁 {line}")
        print()
    except Exception as e:
        print(f"❌ Could not get mount info: {e}")


def check_directory_permissions(path, desc):
    """Check directory permissions and ownership"""
    print(f"=== {desc.upper()}: {path} ===")

    if not os.path.exists(path):
        print(f"❌ Directory does not exist: {path}")
        return False

    try:
        # Get directory stats
        st = os.stat(path)
        mode = stat.filemode(st.st_mode)
        uid = st.st_uid
        gid = st.st_gid

        print(f"📁 Exists: YES")
        print(f"📁 Permissions: {mode}")
        print(f"📁 Owner UID: {uid}")
        print(f"📁 Group GID: {gid}")

        # Try to get user/group names
        try:
            import pwd
            import grp

            user_name = pwd.getpwuid(uid).pw_name
            group_name = grp.getgrgid(gid).gr_name
            print(f"📁 Owner: {user_name}")
            print(f"📁 Group: {group_name}")
        except:
            pass

        # Test write permissions
        test_file = os.path.join(path, ".permission_test")
        try:
            with open(test_file, "w") as f:
                f.write("permission test")
            os.remove(test_file)
            print(f"✅ Write test: PASSED")
            return True
        except Exception as e:
            print(f"❌ Write test: FAILED - {e}")
            return False

    except Exception as e:
        print(f"❌ Error checking {path}: {e}")
        return False
    finally:
        print()


def test_file_operations(local_dir, network_dir, desc):
    """Test the actual file move operations"""
    print(f"=== TESTING {desc.upper()} FILE OPERATIONS ===")

    # Create test file in local directory
    test_filename = "test_photobooth_file.txt"
    local_file = os.path.join(local_dir, test_filename)
    network_file = os.path.join(network_dir, test_filename)

    try:
        # Create local test file
        with open(local_file, "w") as f:
            f.write(f"Test file created at {os.getctime(local_file)}")
        print(f"✅ Created local test file: {local_file}")

        # Test move operation
        import shutil

        shutil.move(local_file, network_file)
        print(f"✅ Moved file to network: {network_file}")

        # Verify file exists at destination
        if os.path.exists(network_file):
            print(f"✅ File verified at destination")

            # Read file content
            with open(network_file, "r") as f:
                content = f.read()
            print(f"✅ File content readable: {len(content)} chars")

            # Clean up
            os.remove(network_file)
            print(f"✅ Cleanup successful")
            return True
        else:
            print(f"❌ File not found at destination after move")
            return False

    except Exception as e:
        print(f"❌ File operation failed: {e}")

        # Try to clean up any remaining files
        for cleanup_file in [local_file, network_file]:
            try:
                if os.path.exists(cleanup_file):
                    os.remove(cleanup_file)
            except:
                pass
        return False
    finally:
        print()


def main():
    print("🔍 PhotoBooth File Permission Diagnostic Tool")
    print("=" * 50)

    # Load config to get paths
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        print("✅ Loaded config.json")
    except Exception as e:
        print(f"❌ Could not load config.json: {e}")
        return

    # Get current user info
    current_user = os.getenv("USER", "unknown")
    current_uid = os.getuid()
    current_gid = os.getgid()
    print(f"👤 Running as: {current_user} (UID:{current_uid}, GID:{current_gid})")
    print()

    # Get mount info
    get_mount_info()

    # Define paths (replicate the logic from main.py)
    local_media_base = os.environ.get("LOCAL_MEDIA_DIR", "/home/pi/photobooth_media")
    local_photo_dir = os.path.join(local_media_base, "photos")
    local_video_dir = os.path.join(local_media_base, "videos")

    # Network paths with conversion logic
    network_photo_dir = config.get("PHOTO_DIR", "./local_photos")
    network_video_dir = config.get("VIDEO_DIR", "./local_videos")

    # Convert UNC paths to mount points if needed
    if network_photo_dir.startswith(r"\\"):
        network_photo_dir = network_photo_dir.replace(
            r"\\SKYNAS\web", "/mnt/skynas"
        ).replace("\\", "/")
    if network_video_dir.startswith(r"\\"):
        network_video_dir = network_video_dir.replace(
            r"\\SKYNAS\web", "/mnt/skynas"
        ).replace("\\", "/")

    print(f"📁 Paths being tested:")
    print(f"   Local photos:   {local_photo_dir}")
    print(f"   Local videos:   {local_video_dir}")
    print(f"   Network photos: {network_photo_dir}")
    print(f"   Network videos: {network_video_dir}")
    print()

    # Check all directories
    results = {}
    results["local_photos"] = check_directory_permissions(
        local_photo_dir, "Local Photos"
    )
    results["local_videos"] = check_directory_permissions(
        local_video_dir, "Local Videos"
    )
    results["network_photos"] = check_directory_permissions(
        network_photo_dir, "Network Photos"
    )
    results["network_videos"] = check_directory_permissions(
        network_video_dir, "Network Videos"
    )

    # Test file operations if directories are accessible
    if results["local_photos"] and results["network_photos"]:
        results["photo_operations"] = test_file_operations(
            local_photo_dir, network_photo_dir, "Photo"
        )
    else:
        print("⚠️  Skipping photo file operations test (directory issues)")

    if results["local_videos"] and results["network_videos"]:
        results["video_operations"] = test_file_operations(
            local_video_dir, network_video_dir, "Video"
        )
    else:
        print("⚠️  Skipping video file operations test (directory issues)")

    # Summary
    print("=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)

    all_good = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test.replace('_', ' ').title()}")
        if not passed:
            all_good = False

    if all_good:
        print("\n🎉 All tests passed! File operations should work correctly.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        print("\n🔧 Common fixes:")
        print(
            "   - Check NAS is mounted: sudo mount -t cifs //SKYNAS/web /mnt/skynas -o ..."
        )
        print("   - Check mount permissions: mount | grep skynas")
        print("   - Check user is in correct groups: groups $USER")
        print("   - Try chmod 755 on network directories")
        print("   - Check umask and mount options (uid=, gid=, file_mode=, dir_mode=)")


if __name__ == "__main__":
    main()
