#!/usr/bin/env python3
"""
Test using the actual PhotoBooth camera manager to understand the frame format issue
"""

import sys
import os
import cv2
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(""), "src"))


def test_photobooth_camera():
    """Test the actual PhotoBooth camera manager"""
    try:
        from photobooth.managers.camera_manager import CameraManager

        print("Testing PhotoBooth camera manager...")

        # Use the same config as PhotoBooth
        config = {
            "test_video_path": 0,
            "CAM_RESOLUTION_HIGH": [1280, 720],
            "CAM_RESOLUTION_LOW": [960, 540],
        }

        # Initialize camera manager like PhotoBooth does
        cam_resolution = config["CAM_RESOLUTION_HIGH"]  # [1280, 720]
        camera_manager = CameraManager(
            cam_resolution=cam_resolution,
            test_video_path=config.get("test_video_path", 0),
            use_webcam=True,
        )

        # Get a frame
        print("Getting frame from camera manager...")
        frame = camera_manager.get_frame()

        if frame is None:
            print("ERROR: No frame from camera manager")
            return False

        print(f"Frame shape: {frame.shape}")
        print(f"Frame dtype: {frame.dtype}")
        print(f"Frame min/max: {frame.min()}/{frame.max()}")

        # Check if frame is RGB or BGR
        height, width = frame.shape[:2]
        print(f"Dimensions: {width}x{height}")

        # Test video recording with this frame
        output_path = "test_photobooth_camera.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, 20.0, (width, height))

        if not writer.isOpened():
            print("ERROR: VideoWriter failed to open")
            # camera_manager.cleanup()  # Method doesn't exist
            return False

        print("Recording 3 seconds with PhotoBooth camera frames...")
        start_time = time.time()
        frame_count = 0

        while time.time() - start_time < 3.0:
            frame = camera_manager.get_frame()
            if frame is not None:
                # Test both with and without RGB->BGR conversion
                if frame_count < 20:
                    # First 20 frames: no conversion
                    writer.write(frame)
                else:
                    # Next frames: with RGB->BGR conversion
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    writer.write(frame_bgr)

                frame_count += 1
                if frame_count % 20 == 0:
                    print(f"Recorded {frame_count} frames")

            time.sleep(0.05)

        writer.release()
        # camera_manager.cleanup()  # Method doesn't exist

        # Check file
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"Video created: {output_path} ({size} bytes)")
            return True
        else:
            print("ERROR: Video file not created")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_photobooth_camera()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
