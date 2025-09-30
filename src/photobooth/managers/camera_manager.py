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

    def __init__(
        self, cam_resolution, test_video_path=0, use_webcam=True, lighting_config=None
    ):
        self.cam_resolution = cam_resolution
        self.test_video_path = test_video_path
        self.use_webcam = use_webcam
        self.lighting_config = lighting_config or {}
        self.picam2 = None
        self.cap = None
        self.init_camera()

    def init_camera(self):
        # Prefer Picamera2 for Pi cameras (like Pi 2W setup)
        if PICAMERA2_AVAILABLE:
            try:
                print("[INFO] Initializing Picamera2 (preferred for Pi cameras)...")
                self.picam2 = Picamera2()

                # Create configuration with RGB888 format (like Pi 2W)
                cam_config = self.picam2.create_preview_configuration(
                    main={"size": self.cam_resolution, "format": "RGB888"}
                )
                print(f"[INFO] Picamera2 config: {cam_config}")

                self.picam2.configure(cam_config)

                # Set camera controls based on lighting configuration
                controls = {"AwbEnable": True}
                controls.update(self.lighting_config)

                lighting_mode = controls.get("_mode", "unknown")
                print(f"[INFO] Using camera settings for: {lighting_mode}")

                # Remove the mode indicator from controls (it's just for logging)
                controls.pop("_mode", None)

                self.picam2.start()

                # Apply controls after starting
                self.picam2.set_controls(controls)
                print(f"[INFO] Applied camera controls: {controls}")

                # Give camera time to initialize and adjust white balance
                time.sleep(3)

                # Test capture to ensure it's working
                test_frame = self.picam2.capture_array()
                if test_frame is not None:
                    print(f"[INFO] ✅ Picamera2 working! Frame: {test_frame.shape}")
                    return  # Success! Use Picamera2
                else:
                    raise RuntimeError("Picamera2 started but can't capture frames")

            except Exception as e:
                print(f"[ERROR] Picamera2 failed: {e}")
                print("[WARN] Falling back to OpenCV (not recommended for Pi cameras)")
                if self.picam2:
                    try:
                        self.picam2.stop()
                    except Exception:
                        pass
                self.picam2 = None
        if self.picam2 is None:
            src = self.test_video_path if self.use_webcam else self.test_video_path

            # Try V4L2 backend first for Pi cameras
            self.cap = cv2.VideoCapture(src, cv2.CAP_V4L2)

            if self.cap.isOpened():
                print(f"[INFO] Using V4L2 camera at /dev/video{src}")
                # Configure V4L2 settings for better Pi camera performance
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_resolution[1])
                self.cap.set(cv2.CAP_PROP_FPS, 15)  # Reasonable FPS for Pi
                # Try MJPG format for better performance
                self.cap.set(
                    cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G")
                )

                # Test if we can actually read frames
                print("[INFO] Testing camera capture...")
                for attempt in range(3):
                    ret, test_frame = self.cap.read()
                    if ret and test_frame is not None:
                        print(f"[INFO] Camera test successful: {test_frame.shape}")
                        break
                    else:
                        print(f"[WARN] Camera test attempt {attempt + 1} failed")
                        time.sleep(0.5)
                else:
                    # If V4L2 can't read frames, try fallback
                    print(
                        "[WARN] V4L2 camera opened but can't read frames, trying fallback"
                    )
                    self.cap.release()
                    self.cap = cv2.VideoCapture(src)  # Default backend
            else:
                # Fallback to default backend
                print("[WARN] V4L2 failed, trying default OpenCV backend")
                self.cap = cv2.VideoCapture(src)

            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Could not open camera at {src}. Check camera connection or TEST_VIDEO_PATH."
                )

    def get_frame(self):
        if self.picam2 is not None:
            frame = self.picam2.capture_array()
            if frame is not None:
                try:
                    # use module-level cv2 (avoid local import which makes cv2 a
                    # local variable and can cause UnboundLocalError later)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                except Exception:
                    pass
            return frame
        else:
            try:
                ok, frame = self.cap.read()
            except Exception as e:
                print(f"[WARN] cv2.VideoCapture.read() raised: {e}; reopening capture")
                try:
                    if self.cap is not None:
                        self.cap.release()
                except Exception:
                    pass
                # attempt to reopen device/source
                self.cap = cv2.VideoCapture(self.test_video_path)
                return None

            if not ok or frame is None:
                # Try reopening once if read failed/returned no frame
                try:
                    if self.cap is not None:
                        self.cap.release()
                except Exception:
                    pass
                self.cap = cv2.VideoCapture(self.test_video_path)
                return None

            return frame

    def set_white_balance_mode(self, mode):
        """
        Set white balance mode for Picamera2
        0=auto, 1=incandescent, 2=tungsten, 3=fluorescent, 4=indoor, 5=daylight, 6=cloudy
        """
        if self.picam2:
            self.picam2.set_controls({"AwbMode": mode})
            print(f"[INFO] Set white balance mode to: {mode}")

    def release(self):
        if self.cap is not None:
            self.cap.release()
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass
