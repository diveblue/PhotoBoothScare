#!/usr/bin/env python3
"""
Simple, isolated test to record a working video with Pi camera
This bypasses all the PhotoBooth complexity to test basic video recording
"""

import cv2
import time
import os


def test_simple_video_record():
    """Test basic video recording with minimal code"""
    print("Testing simple video recording...")

    # Try to open camera (Pi camera will be at index 0)
    print("Opening camera...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open camera")
        return False

    # Get camera frame properties
    ret, frame = cap.read()
    if not ret or frame is None:
        print("ERROR: Could not read frame from camera")
        cap.release()
        return False

    height, width = frame.shape[:2]
    print(f"Camera resolution: {width}x{height}")
    print(f"Frame shape: {frame.shape}")
    print(f"Frame dtype: {frame.dtype}")

    # Create video writer with exact camera dimensions
    output_path = "test_simple_record.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = 20.0

    print(
        f"Creating VideoWriter: {output_path}, codec=mp4v, fps={fps}, size=({width},{height})"
    )
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not writer.isOpened():
        print("ERROR: Could not open VideoWriter")
        cap.release()
        return False

    print("Recording 3 seconds of video...")
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < 3.0:
        ret, frame = cap.read()
        if ret and frame is not None:
            # NO RGB/BGR conversion - just write the frame as-is
            writer.write(frame)
            frame_count += 1

            if frame_count % 20 == 0:
                print(f"Recorded {frame_count} frames")

        time.sleep(0.05)  # ~20 FPS

    print(f"Recording complete. Total frames: {frame_count}")

    # Cleanup
    writer.release()
    cap.release()

    # Check file size
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"Video file size: {size} bytes")
        print(f"Video created: {output_path}")
        return True
    else:
        print("ERROR: Video file not created")
        return False


if __name__ == "__main__":
    success = test_simple_video_record()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
