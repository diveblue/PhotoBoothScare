#!/usr/bin/env python3
"""
camera_local_test.py

Quick non-GUI test for a local camera. Attempts to open the camera (index or
/dev/video path), capture a single good frame, save it as test_frame.jpg and
print diagnostics. Useful when pygame/OpenCV highgui aren't available.

Usage:
  python3 camera_local_test.py [source]

Examples:
  python3 camera_local_test.py         # use camera index 0
  python3 camera_local_test.py 1       # use camera index 1
  python3 camera_local_test.py /dev/video0
"""

import sys
import time
import argparse
import cv2
import os
from datetime import datetime


def parse_source(s):
    if s is None:
        return 0
    try:
        return int(s)
    except Exception:
        return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "source", nargs="?", default="0", help="camera index or /dev/video path"
    )
    args = p.parse_args()

    src = parse_source(args.source)

    print(f"[INFO] Opening source: {src}")

    cap = cv2.VideoCapture(src)

    start = time.time()
    # Wait up to 5 seconds for the capture to become available
    while not cap.isOpened() and (time.time() - start) < 5.0:
        time.sleep(0.2)

    if not cap.isOpened():
        print(
            "[ERROR] Could not open capture. Check camera connection and permissions."
        )
        sys.exit(2)

    # Try to read frames for up to 5 seconds, accept the first non-empty frame
    frame = None
    start = time.time()
    attempts = 0
    while (time.time() - start) < 5.0:
        attempts += 1
        try:
            ok, f = cap.read()
        except Exception as e:
            print(f"[WARN] read() raised: {e}")
            ok = False
            f = None

        if ok and f is not None:
            frame = f
            break
        time.sleep(0.1)

    if frame is None:
        print(f"[ERROR] No frame captured after {attempts} attempts.")
        cap.release()
        sys.exit(3)

    # Save frame to file
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"test_frame_{now}.jpg"
    try:
        ok = cv2.imwrite(out_name, frame)
    except Exception as e:
        print(f"[ERROR] Failed to write image: {e}")
        ok = False

    h, w = frame.shape[:2]
    print(f"[OK] Captured frame {w}x{h}, saved: {out_name if ok else '(save failed)'}")

    cap.release()

    # Print a short tip for next steps
    print(
        "[TIP] If this fails, run: ls /dev/video*  and v4l2-ctl --list-devices  (install v4l-utils)"
    )


if __name__ == "__main__":
    main()
