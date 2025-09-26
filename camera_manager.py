"""
camera_manager.py
Handles camera initialization and frame capture for both Picamera2 and OpenCV sources.
"""

import os
import time
import cv2

try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except Exception:
    Picamera2 = None
    PICAMERA2_AVAILABLE = False


class CameraManager:
    """
    Abstracts camera access for both Raspberry Pi (Picamera2) and generic webcams (OpenCV).
    """

    def __init__(self, cam_resolution, test_video_path=0, use_webcam=True):
        self.cam_resolution = cam_resolution
        self.test_video_path = test_video_path
        self.use_webcam = use_webcam
        self.picam2 = None
        self.cap = None
        self.init_camera()

    def init_camera(self):
        if PICAMERA2_AVAILABLE:
            try:
                self.picam2 = Picamera2()
                cam_config = self.picam2.create_preview_configuration(
                    main={"size": self.cam_resolution}
                )
                self.picam2.configure(cam_config)
                self.picam2.start()
                time.sleep(0.5)
                print(f"[INFO] Using PiCam via Picamera2 @ {self.cam_resolution}")
            except Exception as e:
                print(
                    f"[WARN] Picamera2 init failed: {e}; falling back to OpenCV capture"
                )
                self.picam2 = None
        if self.picam2 is None:
            src = self.test_video_path if self.use_webcam else self.test_video_path
            self.cap = cv2.VideoCapture(src)
            if not self.cap.isOpened():
                raise RuntimeError(
                    "Could not open camera/video. Check camera connection or TEST_VIDEO_PATH."
                )

    def get_frame(self):
        if self.picam2 is not None:
            frame = self.picam2.capture_array()
            if frame is not None:
                try:
                    import cv2

                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                except Exception:
                    pass
            return frame
        else:
            ok, frame = self.cap.read()
            if not ok:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self.cap.read()
            return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass
