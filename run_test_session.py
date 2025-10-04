#!/usr/bin/env python3
"""
Simple test runner that captures detailed file creation logging
Run this locally on the Pi where the display works
"""

import os
import sys
import logging
import subprocess
from datetime import datetime


def setup_test_logging():
    """Setup comprehensive logging for the test session"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"test_session_{timestamp}.log"

    # Configure logging to file only (since we'll run locally)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
        ],
    )

    return log_filename, logging.getLogger(__name__)


def check_local_videos():
    """Check what video files exist locally"""
    video_dir = "./local_videos"
    if os.path.exists(video_dir):
        files = []
        for f in os.listdir(video_dir):
            if f.endswith(".mp4"):
                filepath = os.path.join(video_dir, f)
                size = os.path.getsize(filepath)
                files.append(f"  {f} ({size} bytes)")
        return files
    return []


def check_network_videos():
    """Check what video files exist on network storage"""
    network_path = "/mnt/skynas/web/Halloween2025/media/videos"
    if os.path.exists(network_path):
        files = []
        for f in os.listdir(network_path):
            if f.endswith(".mp4"):
                filepath = os.path.join(network_path, f)
                size = os.path.getsize(filepath)
                files.append(f"  {f} ({size} bytes)")
        return files
    return []


def main():
    print("=== PhotoBooth File Creation Test ===")
    print("This will run the PhotoBooth with enhanced logging.")
    print("Press the button to trigger a session, then Ctrl+C to stop.")
    print()

    log_filename, logger = setup_test_logging()
    print(f"Logging to: {log_filename}")

    # Log initial state
    logger.info("=== TEST SESSION STARTED ===")
    logger.info(f"Working directory: {os.getcwd()}")

    # Check initial file states
    local_videos_before = check_local_videos()
    network_videos_before = check_network_videos()

    logger.info(f"Local videos before: {len(local_videos_before)} files")
    for f in local_videos_before:
        logger.info(f"BEFORE: {f}")

    logger.info(f"Network videos before: {len(network_videos_before)} files")
    for f in network_videos_before:
        logger.info(f"BEFORE: {f}")

    try:
        # Suppress ALSA errors by redirecting stderr
        print("Starting PhotoBooth... (ALSA errors will be suppressed)")
        logger.info("Starting PhotoBooth with stderr suppression")

        # Run the photobooth with stderr redirected to null
        with open("/dev/null", "w") as devnull:
            process = subprocess.Popen(
                [sys.executable, "photobooth.py"],
                stderr=devnull,
                stdout=subprocess.PIPE,
                text=True,
            )

            # Read stdout in real-time and log it
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    print(line)  # Show on console
                    logger.info(f"PHOTOBOOTH: {line}")

    except KeyboardInterrupt:
        print("\nStopping PhotoBooth...")
        logger.info("PhotoBooth stopped by user")
        if "process" in locals():
            process.terminate()
            process.wait()
    except Exception as e:
        logger.error(f"Error running PhotoBooth: {e}", exc_info=True)
        print(f"Error: {e}")

    # Check final file states
    print("\nChecking final file states...")
    logger.info("=== FINAL FILE CHECK ===")

    local_videos_after = check_local_videos()
    network_videos_after = check_network_videos()

    logger.info(f"Local videos after: {len(local_videos_after)} files")
    for f in local_videos_after:
        logger.info(f"AFTER: {f}")

    logger.info(f"Network videos after: {len(network_videos_after)} files")
    for f in network_videos_after:
        logger.info(f"AFTER: {f}")

    # Summary
    new_local = set(local_videos_after) - set(local_videos_before)
    new_network = set(network_videos_after) - set(network_videos_before)

    print("\nRESULTS:")
    print(f"New local videos: {len(new_local)}")
    for f in new_local:
        print(f"  NEW LOCAL: {f}")
    print(f"New network videos: {len(new_network)}")
    for f in new_network:
        print(f"  NEW NETWORK: {f}")

    logger.info(
        f"TEST COMPLETE - New local: {len(new_local)}, New network: {len(new_network)}"
    )
    logger.info("=== TEST SESSION ENDED ===")

    print(f"\nComplete log saved to: {log_filename}")


if __name__ == "__main__":
    main()
