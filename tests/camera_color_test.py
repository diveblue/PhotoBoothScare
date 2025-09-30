#!/usr/bin/env python3
"""
Camera color test - try different white balance modes to fix color issues
"""

import time
import cv2
from camera_manager import CameraManager

# White balance modes for Picamera2 - focused on night/artificial lighting
WB_MODES = {
    0: "Auto",
    1: "Incandescent",  # Best for warm porch lights/bulbs
    2: "Tungsten",  # Alternative for warm lighting
    3: "Fluorescent",  # For LED porch lights
    4: "Indoor",  # General indoor artificial lighting
}


def test_white_balance():
    print("=== Camera Color Test ===")
    print("Testing different white balance modes...")

    # Initialize camera
    camera = CameraManager((1280, 720), "/dev/video0", False)

    try:
        for mode, name in WB_MODES.items():
            print(f"\n--- Testing Mode {mode}: {name} ---")
            camera.set_white_balance_mode(mode)

            # Let camera adjust for 2 seconds
            time.sleep(2)

            # Capture a frame
            frame = camera.get_frame()
            if frame is not None:
                # Save test image
                filename = f"wb_test_mode_{mode}_{name.lower()}.jpg"
                cv2.imwrite(filename, frame)
                print(f"✅ Saved: {filename}")

                # Show frame for 3 seconds (if display available)
                try:
                    cv2.imshow(f"WB Mode {mode}: {name}", frame)
                    cv2.waitKey(3000)  # Show for 3 seconds
                    cv2.destroyAllWindows()
                except:
                    pass  # No display available
            else:
                print(f"❌ Failed to capture frame for mode {mode}")

    finally:
        camera.release()

    print("\n=== Test Complete ===")
    print("Check the saved wb_test_mode_*.jpg files to see which looks best!")
    print("Powder blue should look blue, not orange.")
    print(
        "\nTo use the best mode, note the number and I'll update the camera settings."
    )


if __name__ == "__main__":
    test_white_balance()
