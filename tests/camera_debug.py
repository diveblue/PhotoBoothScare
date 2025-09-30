#!/usr/bin/env python3
"""
Debug camera initialization for Pi 4
"""

import cv2
import time


def test_opencv_with_settings():
    """Test OpenCV with better V4L2 settings for Pi camera"""

    print("Testing OpenCV with Pi camera settings...")

    # Try different video devices
    for device in [0, 1, 10, 13]:
        print(f"\nTrying /dev/video{device}...")

        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

        if not cap.isOpened():
            print(f"❌ Could not open /dev/video{device}")
            continue

        # Set buffer size to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

        # Set FPS
        cap.set(cv2.CAP_PROP_FPS, 15)

        # Set pixel format to MJPG (often faster)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))

        print(f"✅ Opened /dev/video{device}")

        # Try to read a few frames
        success_count = 0
        for i in range(5):
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ Frame {i + 1}: {frame.shape}")
                success_count += 1
            else:
                print(f"❌ Frame {i + 1}: Failed")
            time.sleep(0.1)

        cap.release()

        if success_count > 0:
            print(f"✅ /dev/video{device} works! Got {success_count}/5 frames")
            return device
        else:
            print(f"❌ /dev/video{device} opened but no frames")

    return None


def test_picamera2():
    """Test Picamera2 directly"""

    print("\nTesting Picamera2...")

    try:
        from picamera2 import Picamera2

        picam2 = Picamera2()

        # List available configurations
        print("Available camera configurations:")
        for i, config in enumerate(picam2.sensor_modes):
            print(f"  {i}: {config}")

        # Use a simple configuration
        config = picam2.create_preview_configuration(
            main={"size": (960, 540), "format": "RGB888"}
        )
        print(f"Using config: {config}")

        picam2.configure(config)
        picam2.start()
        time.sleep(1)

        print("✅ Picamera2 started successfully")

        # Capture a few frames
        for i in range(5):
            frame = picam2.capture_array()
            if frame is not None:
                print(f"✅ Frame {i + 1}: {frame.shape}")
            else:
                print(f"❌ Frame {i + 1}: Failed")
            time.sleep(0.1)

        picam2.stop()
        print("✅ Picamera2 test completed")
        return True

    except ImportError:
        print("❌ Picamera2 not available")
        return False
    except Exception as e:
        print(f"❌ Picamera2 failed: {e}")
        return False


if __name__ == "__main__":
    print("Pi 4 Camera Debug")
    print("=" * 40)

    # Test Picamera2 first (preferred)
    picamera2_works = test_picamera2()

    # Test OpenCV as fallback
    working_device = test_opencv_with_settings()

    print("\n" + "=" * 40)
    print("Results:")
    print(f"Picamera2: {'✅ Working' if picamera2_works else '❌ Failed'}")
    print(
        f"OpenCV: {'✅ Working on /dev/video' + str(working_device) if working_device is not None else '❌ Failed'}"
    )

    if picamera2_works:
        print("\n🎯 Recommendation: Use Picamera2 (better performance)")
    elif working_device is not None:
        print(f"\n🎯 Recommendation: Use OpenCV with /dev/video{working_device}")
    else:
        print("\n❌ No camera methods working!")
