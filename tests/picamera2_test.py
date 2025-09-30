#!/usr/bin/env python3
"""
Test Picamera2 setup exactly like Pi 2W worked
"""

import time
import sys

print("Testing Picamera2 (Pi camera preferred method)")
print("=" * 50)

try:
    from picamera2 import Picamera2

    print("✅ Picamera2 imported successfully")
except ImportError as e:
    print(f"❌ Picamera2 import failed: {e}")
    print("Install with: sudo apt install python3-picamera2")
    sys.exit(1)

try:
    # Initialize camera
    print("Initializing Picamera2...")
    picam2 = Picamera2()

    # Show available sensors and modes
    print(f"Camera sensors: {picam2.sensor_modes}")

    # Use configuration similar to Pi 2W setup
    print("Creating preview configuration...")
    config = picam2.create_preview_configuration(
        main={"size": (960, 540), "format": "RGB888"}
    )
    print(f"Config: {config}")

    print("Configuring camera...")
    picam2.configure(config)

    print("Starting camera...")
    picam2.start()

    # Wait for camera to stabilize
    time.sleep(2)
    print("Camera started, capturing test frames...")

    # Capture test frames
    for i in range(10):
        try:
            frame = picam2.capture_array()
            if frame is not None:
                print(f"✅ Frame {i + 1}: {frame.shape}, dtype: {frame.dtype}")
            else:
                print(f"❌ Frame {i + 1}: None")
        except Exception as e:
            print(f"❌ Frame {i + 1} error: {e}")
        time.sleep(0.5)

    print("Stopping camera...")
    picam2.stop()
    print("✅ Picamera2 test completed successfully!")

    print("\n" + "=" * 50)
    print("🎯 RECOMMENDATION: Use Picamera2 in your photobooth")
    print("   - Better performance than OpenCV")
    print("   - Direct hardware access")
    print("   - Designed for Pi cameras")

except Exception as e:
    print(f"❌ Picamera2 test failed: {e}")
    print("\nDebugging info:")
    print("- Check camera connection: lsusb or dmesg | grep -i camera")
    print("- Check camera enabled: sudo raspi-config -> Interface Options -> Camera")
    print("- Check libcamera: libcamera-hello --list-cameras")
    sys.exit(1)
