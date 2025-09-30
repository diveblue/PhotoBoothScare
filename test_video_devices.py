#!/usr/bin/env python3
"""
Test which video device works for the Pi camera
"""

import cv2


def test_video_devices():
    """Test video devices to find working one"""
    print("Testing video devices...")

    for device_id in [0, 1, 10, 11, 12, 13, 14, 15, 16]:
        print(f"\nTesting /dev/video{device_id}...")
        cap = cv2.VideoCapture(device_id)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(
                    f"SUCCESS: Device {device_id} - {width}x{height}, shape: {frame.shape}"
                )
                cap.release()
                return device_id
            else:
                print(f"Device {device_id}: opened but no frame")
        else:
            print(f"Device {device_id}: failed to open")

        cap.release()

    print("No working video device found")
    return None


if __name__ == "__main__":
    working_device = test_video_devices()
    if working_device is not None:
        print(f"\nWorking device: /dev/video{working_device}")
    else:
        print("\nNo working camera device found")
