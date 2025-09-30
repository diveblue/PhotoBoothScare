"""
rtsp_camera_manager.py
FFmpeg-backed RTSP recorder with OpenCV fallback.

Public API:
- RTSPCameraManager(rtsp_url, video_output_path, fps)
- start(video_output_path=None)
- stop()
- is_recording()

Also exposes get_rtsp_url_onvif(camera_ip, username, password)
"""

import os
import threading
import subprocess
import time

try:
    import cv2
except Exception:
    cv2 = None


def get_rtsp_url_onvif(camera_ip, username, password):
    """
    Fetches the current RTSP stream URI from an ONVIF-compatible camera (e.g., Tethys).
    Returns the full RTSP URL (with token) or None if failed.
    """
    try:
        from onvif2 import ONVIFCamera

        cam = ONVIFCamera(camera_ip, 80, username, password)
        media_service = cam.create_media_service()
        profiles = media_service.GetProfiles()
        # Use the first profile
        token = profiles[0].token
        stream_uri = media_service.GetStreamUri(
            {
                "StreamSetup": {
                    "Stream": "RTP-Unicast",
                    "Transport": {"Protocol": "RTSP"},
                },
                "ProfileToken": token,
            }
        )
        return stream_uri.Uri
    except Exception as e:
        print(f"[ONVIF] Failed to fetch RTSP URL: {e}")
        return None


class RTSPCameraManager:
    def __init__(self, rtsp_url, video_output_path, fps=15.0):
        self.rtsp_url = rtsp_url
        self.video_output_path = video_output_path
        self.fps = fps
        self.proc = None
        self.thread = None
        self.recording = False
        self.stop_event = threading.Event()
        self.cap = None

    def start(self, video_output_path=None):
        if video_output_path:
            self.video_output_path = video_output_path
        # Try ffmpeg first
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-rtsp_transport",
            "tcp",
            "-i",
            self.rtsp_url,
            "-c",
            "copy",
            self.video_output_path,
        ]
        try:
            # Spawn ffmpeg; it will exit on network error, so monitor thread will restart or expose status
            self.proc = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
            )
            self.recording = True
            self.stop_event.clear()
            # Start a monitor thread to read stderr to avoid blocking and log basic info
            self.thread = threading.Thread(target=self._monitor_ffmpeg, daemon=True)
            self.thread.start()
            print(
                f"[RTSP-FFMPEG] Started ffmpeg recorder for {self.rtsp_url} -> {self.video_output_path}"
            )
            return
        except FileNotFoundError:
            # ffmpeg not installed; fall back to cv2
            print("[RTSP-FFMPEG] ffmpeg not found, falling back to OpenCV capture")
        except Exception as e:
            print(f"[RTSP-FFMPEG] Failed to start ffmpeg: {e}")

        # Fallback: OpenCV-based recording (if cv2 available)
        if cv2 is None:
            raise RuntimeError(
                "Neither ffmpeg nor OpenCV are available to record RTSP stream"
            )

        self.cap = cv2.VideoCapture(self.rtsp_url)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open RTSP stream: {self.rtsp_url}")

        self.recording = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._record_loop_cv2, daemon=True)
        self.thread.start()

    def _monitor_ffmpeg(self):
        # Consume stderr to keep process running and expose events
        try:
            assert self.proc is not None
            while not self.stop_event.is_set():
                line = self.proc.stderr.readline()
                if line == "":
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                # Optionally parse line for errors
                # print(f"[ffmpeg] {line.strip()}")
            # Wait for process to exit
            self.proc.wait(timeout=1)
        except Exception:
            pass
        finally:
            self.recording = False

    def _record_loop_cv2(self):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        writer = cv2.VideoWriter(
            self.video_output_path, fourcc, self.fps, (width, height)
        )
        while self.recording and not self.stop_event.is_set():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                writer.write(frame)
            except Exception:
                time.sleep(0.1)
                continue
        try:
            writer.release()
        except Exception:
            pass
        try:
            self.cap.release()
        except Exception:
            pass
        self.recording = False

    def stop(self):
        # Stop either ffmpeg or cv2 capture
        self.recording = False
        self.stop_event.set()
        if self.proc:
            try:
                # Attempt graceful termination
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=3)
                except Exception:
                    self.proc.kill()
            except Exception:
                pass
            self.proc = None
        if self.thread:
            try:
                self.thread.join(timeout=4)
            except Exception:
                pass
            self.thread = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.recording = False

    def is_recording(self):
        return self.recording
