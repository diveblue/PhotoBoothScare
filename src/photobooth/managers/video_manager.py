"""
VideoManager - Enhanced Video Recording with Audio Support

RESPONSIBILITIES:
- Records video sessions with synchronized audio using pyaudio and ffmpeg
- Manages video file lifecycle from recording to network storage
- Provides clean separation between recording and file movement phases
- Handles RTSP secondary camera integration when available

KEY METHODS:
- start_recording(): Begin video+audio recording with session ID and timing
- stop_recording(): End recording and prepare for file operations
- write_frame(): Add frame to active video recording
- cleanup(): Clean shutdown of video and audio resources

AUDIO FEATURES:
- Real-time audio capture via pyaudio (when available)
- Synchronized audio/video muxing using ffmpeg
- Graceful fallback to video-only when audio hardware unavailable
- Optimized for Raspberry Pi 4 audio capabilities

CRITICAL TIMING:
- Video recording MUST stop before file movement to prevent corruption
- Uses RGB888 format directly from camera (no conversion needed)
- Stops recording during gotcha phase, before QR display begins

ARCHITECTURE:
- Follows Single Responsibility by only handling video+audio operations
- Coordinates with SessionManager through main.py for timing
- Delegates RTSP management to specialized RTSPCameraManager
- Ensures video integrity through proper lifecycle management
"""

import cv2
import os
import subprocess
import threading
import time

import logging

try:
    import pyaudio
    import wave

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

from .rtsp_camera_manager import RTSPCameraManager


class VideoManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Video recording
        self.video_writer = None
        self.recording = False

        # Audio recording
        self.audio_enabled = AUDIO_AVAILABLE and config.get("ENABLE_AUDIO", True)
        self.audio_thread = None
        self.audio_recording = False
        self.audio_file = None

        # Audio settings from config
        self.audio_format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        self.audio_channels = config.get("AUDIO_CHANNELS", 1)
        self.audio_rate = config.get("AUDIO_SAMPLE_RATE", 48000)
        self.audio_device_index = config.get("AUDIO_DEVICE_INDEX", None)
        self.audio_chunk = 1024

        # Configuration
        self.video_dir = config["VIDEO_DIR"]
        self.rtsp_url = config["RTSP_URL"]
        self.rtsp_fps = config.get("RTSP_VIDEO_FPS", 20.0)

        # Ensure video directory exists
        os.makedirs(self.video_dir, exist_ok=True)

        if self.audio_enabled:
            print("[AUDIO] Audio recording enabled")
        else:
            print("[AUDIO] Audio recording disabled (pyaudio not available)")

    def start_recording(self, session_id, session_time, frame_size):
        """Start video and audio recording for a session."""
        if self.recording:
            return False

        try:
            # Main video file (without audio initially)
            self.video_filename = f"{session_time}_{session_id}_booth"
            self.video_path = os.path.join(
                self.video_dir, f"{self.video_filename}_temp.mp4"
            )
            self.final_path = os.path.join(self.video_dir, f"{self.video_filename}.mp4")

            # Start video recording
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(
                self.video_path, fourcc, 20.0, frame_size
            )

            if not self.video_writer.isOpened():
                print(f"[ERROR] Failed to open video writer: {self.video_path}")
                return False

            self.recording = True
            self._video_size = frame_size
            self.logger.debug(
                "timing", f"🎥 VIDEO RECORDING STARTED: {self.video_filename}.mp4"
            )

            # Start audio recording in parallel
            if self.audio_enabled:
                self._start_audio_recording(session_time, session_id)

            return True

        except Exception as e:
            print(f"[ERROR] Failed to start recording: {e}")
            return False

    def _start_audio_recording(self, session_time, session_id):
        """Start audio recording in a separate thread."""
        try:
            self.audio_file = os.path.join(
                self.video_dir, f".{session_time}_{session_id}_audio_temp.wav"
            )
            self.audio_recording = True

            self.audio_thread = threading.Thread(
                target=self._record_audio_thread, daemon=True
            )
            self.audio_thread.start()
            self.logger.debug(f"🎤 AUDIO RECORDING STARTED: {self.audio_file}")

        except Exception as e:
            print(f"[ERROR] Failed to start audio recording: {e}")
            self.audio_enabled = False

    def _record_audio_thread(self):
        """Audio recording thread function."""
        if not AUDIO_AVAILABLE:
            return

        p = pyaudio.PyAudio()
        frames = []

        try:
            # Suppress ALSA warnings during device enumeration
            import os

            os.environ["ALSA_PCM_CARD"] = "2"  # Force use of our specific device
            os.environ["ALSA_PCM_DEVICE"] = "0"

            stream = p.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                input=True,
                input_device_index=self.audio_device_index,  # Explicitly specify device
                frames_per_buffer=self.audio_chunk,
            )

            print("[DEBUG] Audio recording thread started")

            while self.audio_recording:
                data = stream.read(self.audio_chunk, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()

            # Save audio file
            wf = wave.open(self.audio_file, "wb")
            wf.setnchannels(self.audio_channels)
            wf.setsampwidth(p.get_sample_size(self.audio_format))
            wf.setframerate(self.audio_rate)
            wf.writeframes(b"".join(frames))
            wf.close()

            print(f"[DEBUG] Audio saved to: {self.audio_file}")

        except Exception as e:
            print(f"[ERROR] Audio recording failed: {e}")
        finally:
            p.terminate()

    def write_frame(self, frame):
        """Write a frame to the video file."""
        if self.recording and self.video_writer:
            try:
                if hasattr(self, "_frame_count"):
                    self._frame_count += 1
                else:
                    self._frame_count = 1
                    print(
                        f"[DEBUG] First frame shape: {frame.shape}, dtype: {frame.dtype}"
                    )
                    print(f"[DEBUG] Video size: {self._video_size}")

                # Simple approach: just write the frame as-is
                self.video_writer.write(frame)

                # Log every 30 frames to avoid spam
                if self._frame_count % 30 == 0:
                    print(f"[DEBUG] Written {self._frame_count} frames to video")

            except Exception as e:
                print(f"[ERROR] Video frame write failed: {e}")
                import traceback

                traceback.print_exc()

    def stop_recording(self):
        """Stop video and audio recording immediately, schedule async audio/video combination."""
        if not self.recording:
            return

        try:
            # Mark as not recording immediately
            self.recording = False

            # Stop video recording
            if self.video_writer:
                frame_count = getattr(self, "_frame_count", 0)
                print(
                    f"[DEBUG] Stopping video recording with {frame_count} frames written"
                )

                self.video_writer.release()
                self.video_writer = None
                self._frame_count = 0
                self.logger.debug("🎬 VIDEO RECORDING STOPPED")

            # Stop audio recording
            if self.audio_enabled and self.audio_recording:
                self.audio_recording = False
                if self.audio_thread:
                    self.audio_thread.join(timeout=2.0)  # Wait max 2 seconds
                self.logger.debug("🎤 AUDIO RECORDING STOPPED")

            # Start async audio/video combination
            if self.audio_enabled and os.path.exists(self.audio_file):
                # Start background thread for ffmpeg processing
                import threading

                self.mux_thread = threading.Thread(
                    target=self._combine_audio_video_async
                )
                self.mux_thread.daemon = True
                self.mux_thread.start()
                self.logger.debug("🎵 AUDIO/VIDEO MUXING STARTED (async)")
            else:
                # No audio, just rename video file to final name immediately
                if os.path.exists(self.video_path):
                    os.rename(self.video_path, self.final_path)
                    self.logger.debug(f"✅ VIDEO READY: {self.final_path}")

        except Exception as e:
            print(f"[ERROR] Video recording stop failed: {e}")
            self.recording = False

    def is_finalizing(self):
        """Check if video finalization is still in progress."""
        return (
            hasattr(self, "mux_thread")
            and self.mux_thread
            and self.mux_thread.is_alive()
        )

    def wait_for_finalization(self, timeout=5.0):
        """Wait for any background video processing to complete."""
        if (
            hasattr(self, "mux_thread")
            and self.mux_thread
            and self.mux_thread.is_alive()
        ):
            self.logger.debug(
                "timing", f"⏳ Waiting for video finalization (max {timeout}s)..."
            )
            self.mux_thread.join(timeout=timeout)
            if self.mux_thread.is_alive():
                self.logger.debug(
                    "timing", "⚠️ Video finalization timeout - proceeding anyway"
                )
                return False
            else:
                self.logger.debug("✅ Video finalization complete")
                return True
        return True  # No muxing thread, already complete

    def _combine_audio_video_async(self):
        """Async version: Combine video and audio files using ffmpeg in background."""
        try:
            cmd = [
                "ffmpeg",
                "-y",  # -y to overwrite output file
                "-i",
                self.video_path,  # Input video
                "-i",
                self.audio_file,  # Input audio
                "-c:v",
                "libx264",  # Re-encode video for better compatibility
                "-preset",
                "fast",  # Fast encoding preset
                "-crf",
                "23",  # Good quality/size balance
                "-c:a",
                "aac",  # Encode audio as AAC
                "-b:a",
                "128k",  # Audio bitrate
                "-ar",
                "48000",  # Audio sample rate
                "-movflags",
                "+faststart",  # Enable fast start for web playback
                "-shortest",  # Stop when shortest stream ends
                self.final_path,
            ]

            print(f"[DEBUG] Combining audio/video: {' '.join(cmd)}")

            # Determine the working directory - use the parent directory of the video files
            work_dir = (
                os.path.dirname(self.video_path)
                if os.path.dirname(self.video_path)
                else "."
            )
            print(f"[DEBUG] FFmpeg working directory: {work_dir}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=work_dir
            )

            if result.returncode == 0:
                # Verify the final file actually exists and has content
                if os.path.exists(self.final_path):
                    file_size = os.path.getsize(self.final_path)
                    self.logger.debug(
                        "timing",
                        f"✅ AUDIO/VIDEO COMBINED: {self.final_path} ({file_size} bytes)",
                    )
                    print(
                        f"[DEBUG] Final video file created: {self.final_path} ({file_size} bytes)"
                    )
                else:
                    print(
                        f"[ERROR] ffmpeg succeeded but final file missing: {self.final_path}"
                    )

                # Clean up temporary files after a delay to allow file manager to complete
                import time

                time.sleep(2.0)  # Wait for file manager to complete
                try:
                    if os.path.exists(self.video_path):
                        os.remove(self.video_path)
                        print(f"[DEBUG] Removed temp video: {self.video_path}")
                    if os.path.exists(self.audio_file):
                        os.remove(self.audio_file)
                        print(f"[DEBUG] Removed temp audio: {self.audio_file}")
                    self.logger.debug("🧹 TEMP FILES CLEANED UP")
                except Exception as e:
                    print(f"[DEBUG] Temp file cleanup failed: {e}")
            else:
                print(f"[ERROR] ffmpeg failed: {result.stderr}")
                # Fallback: just use video file
                if os.path.exists(self.video_path):
                    os.rename(self.video_path, self.final_path)
                    file_size = (
                        os.path.getsize(self.final_path)
                        if os.path.exists(self.final_path)
                        else 0
                    )
                    self.logger.debug(
                        "timing",
                        f"⚠️ AUDIO FAILED, VIDEO READY: {self.final_path} ({file_size} bytes)",
                    )
                    print(
                        f"[DEBUG] Fallback video file: {self.final_path} ({file_size} bytes)"
                    )

        except Exception as e:
            print(f"[ERROR] Audio/video combination failed: {e}")
            # Fallback: just use video file
            if os.path.exists(self.video_path):
                os.rename(self.video_path, self.final_path)
                file_size = (
                    os.path.getsize(self.final_path)
                    if os.path.exists(self.final_path)
                    else 0
                )
                self.logger.debug(
                    "timing",
                    f"⚠️ AUDIO FAILED, VIDEO READY: {self.final_path} ({file_size} bytes)",
                )
                print(
                    f"[DEBUG] Exception fallback video file: {self.final_path} ({file_size} bytes)"
                )

    def _combine_audio_video(self):
        """Legacy sync version - kept for compatibility."""
        self._combine_audio_video_async()

    def cleanup(self):
        """Cleanup video resources."""
        self.stop_recording()
