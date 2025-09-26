"""
rtsp_camera_manager.py
Handles RTSP camera initialization and video capture for secondary camera angles.
"""

import cv2
import threading


class RTSPCameraManager:
    """
    Manages an RTSP camera for video capture (no display).
    All configuration is passed in from the main app/config.
    """

    def __init__(self, rtsp_url, video_output_path, fps):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.recording = False
        self.video_writer = None
        self.video_output_path = video_output_path
        self.fps = fps
        self.thread = None
        self.stop_event = threading.Event()

    def start(self, video_output_path=None):
        if video_output_path:
            self.video_output_path = video_output_path
        self.cap = cv2.VideoCapture(self.rtsp_url)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open RTSP stream: {self.rtsp_url}")
        self.recording = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def _record_loop(self):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.video_writer = cv2.VideoWriter(
            self.video_output_path, fourcc, self.fps, (width, height)
        )
        while self.recording and not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                continue
            self.video_writer.write(frame)
        self.video_writer.release()
        self.cap.release()

    def stop(self):
        self.recording = False
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        self.thread = None

    def is_recording(self):
        return self.recording
