#!/usr/bin/env python3
"""
Test script to simulate a full PhotoBooth session video creation
to verify RGB/BGR conversion is working properly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from photobooth.managers.camera_manager import CameraManager
from photobooth.managers.video_manager import VideoManager
import time


def test_session_video():
    """Test creating a video like a real PhotoBooth session"""
    print("Testing session video creation...")

    # Initialize camera and video manager
    camera_manager = CameraManager(config={"test_video_path": 0})  # Use webcam
    video_manager = VideoManager()

    # Start video recording
    session_id = f"2025-09-29_test_session_{int(time.time())}"
    video_path = f"local_videos/{session_id}_booth.mp4"

    print(f"Starting video recording: {video_path}")

    if not video_manager.start_recording(video_path, (640, 480)):
        print("Failed to start recording!")
        return False

    # Record for 3 seconds with real camera frames
    print("Recording frames...")
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < 3.0:
        frame = camera_manager.get_frame()
        if frame is not None:
            if video_manager.write_frame(frame):
                frame_count += 1
                if frame_count % 10 == 0:
                    print(f"Recorded {frame_count} frames")
        time.sleep(0.05)  # ~20 FPS

    # Stop recording
    video_manager.stop_recording()
    camera_manager.cleanup()

    print(f"Recording complete! {frame_count} frames written")
    print(f"Video saved to: {video_path}")

    # Check file size
    if os.path.exists(video_path):
        size = os.path.getsize(video_path)
        print(f"Video file size: {size} bytes")
        if size < 50000:  # Less than 50KB suggests problem
            print("WARNING: Video file seems too small!")
        return True
    else:
        print("ERROR: Video file was not created!")
        return False


if __name__ == "__main__":
    # Ensure local_videos directory exists
    os.makedirs("local_videos", exist_ok=True)
    test_session_video()
