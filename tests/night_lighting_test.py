#!/usr/bin/env python3
"""
Quick night lighting test - optimized for dimly lit porch
"""

import time
import cv2
from camera_manager import CameraManager


def night_test():
    print("=== Night Porch Lighting Test ===")
    print("Testing optimized settings for dimly lit porch...")

    # Initialize camera with night-optimized settings
    camera = CameraManager((1280, 720), "/dev/video0", False)

    # Wait for camera to adjust to low light
    print("Waiting 5 seconds for camera to adjust to low light...")
    time.sleep(5)

    try:
        for i in range(3):
            print(f"Capturing test photo {i + 1}/3...")
            frame = camera.get_frame()

            if frame is not None:
                filename = f"night_test_{i + 1}.jpg"
                cv2.imwrite(filename, frame)
                print(f"✅ Saved: {filename}")

                # Brief display if available
                try:
                    cv2.imshow("Night Test", frame)
                    cv2.waitKey(2000)  # 2 seconds
                    cv2.destroyAllWindows()
                except Exception:
                    pass

            time.sleep(1)  # Brief pause between shots

    finally:
        camera.release()

    print("\n=== Test Complete ===")
    print("Check the night_test_*.jpg files.")
    print("Your powder blue shirt should now look more blue and less orange!")
    print("Colors should be more accurate under porch lighting.")


if __name__ == "__main__":
    night_test()
