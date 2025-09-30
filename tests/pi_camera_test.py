#!/usr/bin/env python3
"""
Quick test script for Pi 4 camera via OpenCV and Picamera2
"""

import cv2
import sys
import time


def test_opencv_camera():
    """Test OpenCV capture from /dev/video0"""
    print("Testing OpenCV capture from /dev/video0...")

    cap = cv2.VideoCapture(0)  # /dev/video0

    if not cap.isOpened():
        print("❌ Failed to open /dev/video0 with OpenCV")
        return False

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("✅ Camera opened successfully")

    # Try to capture 5 frames
    for i in range(5):
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✅ Frame {i + 1}: {frame.shape}")
        else:
            print(f"❌ Frame {i + 1}: Failed to capture")
            cap.release()
            return False
        time.sleep(0.1)

    cap.release()
    return True


def test_picamera2():
    """Test Picamera2 capture"""
    print("\nTesting Picamera2...")

    try:
        from picamera2 import Picamera2

        picam2 = Picamera2()
        cam_config = picam2.create_preview_configuration(main={"size": (1280, 720)})
        picam2.configure(cam_config)
        picam2.start()
        time.sleep(0.5)

        print("✅ Picamera2 started successfully")

        # Try to capture 5 frames
        for i in range(5):
            frame = picam2.capture_array()
            if frame is not None:
                print(f"✅ Frame {i + 1}: {frame.shape}")
            else:
                print(f"❌ Frame {i + 1}: Failed to capture")
                picam2.stop()
                return False
            time.sleep(0.1)

        picam2.stop()
        return True

    except ImportError:
        print("❌ Picamera2 not available")
        return False
    except Exception as e:
        print(f"❌ Picamera2 error: {e}")
        return False


if __name__ == "__main__":
    print("Pi 4 Camera Test")
    print("================")

    opencv_ok = test_opencv_camera()
    picamera2_ok = test_picamera2()

    print("\nResults:")
    print(f"OpenCV: {'✅ Working' if opencv_ok else '❌ Failed'}")
    print(f"Picamera2: {'✅ Working' if picamera2_ok else '❌ Failed'}")

    if opencv_ok or picamera2_ok:
        print("\n✅ At least one camera method is working!")
        sys.exit(0)
    else:
        print("\n❌ Both camera methods failed")
        sys.exit(1)
