#!/usr/bin/env python3
"""
Debug test to check what camera dimensions we're getting
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from photobooth.managers.camera_manager import CameraManager


def test_camera_dimensions():
    """Test what dimensions the camera provides"""
    print("Testing camera dimensions...")

    # Initialize camera manager
    camera_manager = CameraManager(config={"test_video_path": 0})

    # Get a few frames to see dimensions
    for i in range(3):
        frame = camera_manager.get_frame()
        if frame is not None:
            height, width = frame.shape[:2]
            print(f"Frame {i + 1}: {width}x{height} (WxH), shape: {frame.shape}")
        else:
            print(f"Frame {i + 1}: None")

    camera_manager.cleanup()


if __name__ == "__main__":
    test_camera_dimensions()
