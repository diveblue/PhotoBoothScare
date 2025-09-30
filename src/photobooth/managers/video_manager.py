"""
video_manager.py
Handles video recording and RTSP streaming
"""

import cv2
import os
from .rtsp_camera_manager import RTSPCameraManager


class VideoManager:
    def __init__(self, config, debug_log_func):
        self.config = config
        self.debug_log = debug_log_func

        # Video recording
        self.video_writer = None
        self.recording = False
        self.rtsp_manager = None

        # Configuration
        self.video_dir = config["VIDEO_DIR"]
        self.rtsp_url = config["RTSP_URL"]
        self.rtsp_fps = config.get("RTSP_VIDEO_FPS", 20.0)

        # Ensure video directory exists
        os.makedirs(self.video_dir, exist_ok=True)

        # Initialize RTSP manager
        self._init_rtsp()

    def _init_rtsp(self):
        """Initialize RTSP camera manager."""
        try:
            self.rtsp_manager = RTSPCameraManager(
                self.rtsp_url, self.config["RTSP_USER"], self.config["RTSP_PASS"]
            )
            print("[RTSP] Secondary RTSP stream started.")
        except Exception as e:
            print(f"[WARN] RTSP initialization failed: {e}")
            self.rtsp_manager = None

    def start_recording(self, session_id, session_time, frame_size):
        """Start video recording for a session."""
        if self.recording:
            return

        try:
            # Main video file
            video_filename = f"{session_time}_{session_id}_booth.mp4"
            video_path = os.path.join(self.video_dir, video_filename)

            # Use mp4v codec (MPEG-4 part 2) - same as working videos from 9/25 and earlier
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, frame_size)

            if self.video_writer.isOpened():
                self.recording = True
                self._video_size = frame_size  # Store video size for frame resizing
                self.debug_log(
                    "timing", f"🎥 VIDEO RECORDING STARTED: {video_filename}"
                )
            else:
                print(f"[ERROR] Failed to open video writer: {video_path}")
                self.video_writer = None
                return

            # RTSP secondary recording
            if self.rtsp_manager:
                try:
                    rtsp_filename = f"{session_time}_{session_id}_rtsp_secondary.mp4"
                    rtsp_path = os.path.join(self.video_dir, rtsp_filename)
                    self.rtsp_manager.start(rtsp_path)
                    self.debug_log(
                        "timing", f"📡 RTSP SECONDARY RECORDING STARTED: {rtsp_path}"
                    )
                except Exception as e:
                    print(f"[WARN] RTSP recording start failed: {e}")

        except Exception as e:
            print(f"[ERROR] Video recording start failed: {e}")
            self.recording = False

    def write_frame(self, frame):
        """Write a frame to the video file."""
        if self.recording and self.video_writer:
            try:
                # Debug frame properties
                if hasattr(self, "_frame_count"):
                    self._frame_count += 1
                else:
                    self._frame_count = 1
                    print(
                        f"[DEBUG] First frame shape: {frame.shape}, dtype: {frame.dtype}"
                    )
                    print(f"[DEBUG] Video size: {self._video_size}")

                # Simple approach: just write the frame as-is (like successful test)
                # No resizing, no RGB/BGR conversion - just use frame directly
                self.video_writer.write(frame)

                # Log every 30 frames to avoid spam
                if self._frame_count % 30 == 0:
                    print(f"[DEBUG] Written {self._frame_count} frames to video")

            except Exception as e:
                print(f"[ERROR] Video frame write failed: {e}")
                print(
                    f"[ERROR] Frame shape: {frame.shape}, Video recording: {self.recording}"
                )
                import traceback

                traceback.print_exc()

    def stop_recording(self):
        """Stop video recording."""
        if not self.recording:
            return

        try:
            if self.video_writer:
                # Debug info before stopping
                frame_count = getattr(self, "_frame_count", 0)
                print(
                    f"[DEBUG] Stopping video recording with {frame_count} frames written"
                )

                self.video_writer.release()
                self.video_writer = None
                self._frame_count = 0  # Reset frame count
                self.debug_log("timing", "🎬 VIDEO RECORDING STOPPED")

            # Stop RTSP recording
            if self.rtsp_manager:
                try:
                    self.rtsp_manager.stop()
                    self.debug_log("timing", "📡 RTSP SECONDARY RECORDING STOPPED")
                except Exception as e:
                    print(f"[WARN] RTSP recording stop failed: {e}")

        except Exception as e:
            print(f"[ERROR] Video recording stop failed: {e}")
        finally:
            self.recording = False

    def cleanup(self):
        """Cleanup video resources."""
        self.stop_recording()
        if self.rtsp_manager:
            try:
                self.rtsp_manager.cleanup()
            except Exception:
                pass
