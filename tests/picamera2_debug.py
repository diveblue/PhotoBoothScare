#!/usr/bin/env python3
"""
Quick Picamera2 test to debug camera issues
"""

try:
    from picamera2 import Picamera2
    import time

    print("✅ Picamera2 imported successfully")

    # Try to initialize
    picam2 = Picamera2()
    print("✅ Picamera2 object created")

    # List available cameras
    cameras = Picamera2.global_camera_info()
    print(f"📷 Available cameras: {cameras}")

    # Try to configure
    config = picam2.create_preview_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )
    print(f"✅ Configuration created: {config}")

    picam2.configure(config)
    print("✅ Camera configured")

    picam2.start()
    print("✅ Camera started")

    time.sleep(2)

    # Try to capture
    frame = picam2.capture_array()
    print(f"✅ Frame captured: {frame.shape if frame is not None else 'None'}")

    picam2.stop()
    print("✅ Camera stopped - Test complete!")

except ImportError as e:
    print(f"❌ Picamera2 not available: {e}")
except Exception as e:
    print(f"❌ Picamera2 test failed: {e}")
    import traceback

    traceback.print_exc()
