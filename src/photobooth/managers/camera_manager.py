"""
CameraManager - Hardware Abstraction for Camera Operations

RESPONSIBILITIES:
- Manages camera initialization and frame capture across different hardware
- Provides unified interface for Picamera2 (Raspberry Pi) and OpenCV (webcam) backends
- Handles camera failures with automatic recovery and fallback mechanisms
- Maintains camera settings and provides consistent RGB888 frame format

KEY METHODS:
- init_camera(): Initialize camera with appropriate backend (Picamera2 preferred)
- get_frame(): Capture single frame with error recovery
- release(): Clean shutdown of camera resources
- set_camera_setting(): Adjust camera parameters (brightness, contrast, etc.)

BACKEND SUPPORT:
- Picamera2: Primary backend for Raspberry Pi cameras (IMX708 sensor)
- OpenCV: Fallback for webcams and development environments
- Test Video: File-based input for testing without camera hardware

ARCHITECTURE:
- Hardware abstraction following Dependency Inversion principle
- Encapsulates camera complexity from higher-level managers
- Provides consistent interface regardless of underlying camera system
"""

import os
import time
import cv2
import platform

try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except Exception:
    Picamera2 = None
    PICAMERA2_AVAILABLE = False

# Platform detection for better logging
IS_RASPBERRY_PI = platform.machine().startswith("arm") or os.path.exists(
    "/boot/config.txt"
)


class CameraManager:
    """
    Hardware abstraction layer for camera operations.

    Provides unified interface for different camera backends while handling
    initialization, frame capture, and recovery from camera failures.
    """

    def __init__(self, config):
        if config["CAM_RESOLUTION"] == "CAM_RESOLUTION_HIGH":
            self.cam_resolution = config["CAM_RESOLUTION_HIGH"]
        else:
            self.cam_resolution = config["CAM_RESOLUTION_LOW"]

        self.test_video_path = config.get("TEST_VIDEO_PATH", 0)
        self.use_webcam = config.get("USE_WEBCAM", True)
        self.lighting_config = config.get("LIGHTING_CONFIG", {})
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
            print(
                f"[DEBUG] CameraManager.get_frame (picam2): shape={getattr(frame, 'shape', None)}, dtype={getattr(frame, 'dtype', None)}"
            )
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

            print(
                f"[DEBUG] CameraManager.get_frame (opencv): shape={getattr(frame, 'shape', None)}, dtype={getattr(frame, 'dtype', None)} min={getattr(frame, 'min', lambda: None)()} max={getattr(frame, 'max', lambda: None)()}"
            )
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
