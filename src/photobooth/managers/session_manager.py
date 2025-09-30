"""
session_manager.py
Manages photo booth session state and transitions
"""

import time
import random
from datetime import datetime
from ..utils.photobooth_state import PhotoBoothState


class SessionManager:
    def __init__(self, config, debug_log_func):
        self.config = config
        self.debug_log = debug_log_func

        # Session state
        self.state = PhotoBoothState()
        self.countdown_start_time = None
        self.gotcha_start_time = None
        self.qr_display_start = None
        self.countdown_beeped = set()
        self.smile_photos_taken = 0
        self.last_smile_time = 0
        self.last_countdown_number = None
        self.files_moved_to_network = False

        # Configuration
        self.countdown_seconds = config["COUNTDOWN_SECONDS"]
        self.qr_display_duration = config.get("QR_DISPLAY_SECONDS", 5.0)

    def start_countdown(self):
        """Start a new photo session countdown."""
        if (
            self.state.countdown_active
            or self.state.gotcha_active
            or self.qr_display_start is not None
        ):
            return  # Already in a session

        self.debug_log("timing", "🚀 BUTTON PRESSED - Starting countdown")
        self.state.start_countdown(self.countdown_seconds)
        self.countdown_start_time = time.time()
        self.countdown_beeped = set()
        self.smile_photos_taken = 0
        self.last_smile_time = 0
        self.last_countdown_number = None
        self.files_moved_to_network = False

    def update_countdown(self, now, audio_manager):
        """Update countdown state and handle audio cues."""
        if not self.state.countdown_active or self.countdown_start_time is None:
            return None

        elapsed = now - self.countdown_start_time
        remaining = self.countdown_seconds - elapsed

        if remaining <= 0:
            # Countdown finished - trigger gotcha
            self.debug_log("timing", "✅ Countdown finished - showing SMILE overlay")
            self.state.end_countdown()
            self.countdown_start_time = None
            return "gotcha"

        # Handle countdown beeps
        countdown_number = int(remaining) + 1
        if countdown_number != self.last_countdown_number:
            self.last_countdown_number = countdown_number
            if (
                countdown_number <= self.countdown_seconds
                and countdown_number not in self.countdown_beeped
            ):
                self.debug_log("timing", f"⏰ COUNTDOWN: {countdown_number}")
                self.debug_log("audio", "🔊 Playing beep sound")
                audio_manager.play_beep()
                self.countdown_beeped.add(countdown_number)

        return countdown_number

    def trigger_gotcha(self, now):
        """Trigger the gotcha/scare sequence."""
        if not self.state.gotcha_active:
            self.debug_log("timing", "📸 SMILE phase started")
            self.debug_log("audio", "🔊 Playing shutter sound")
            self.state.trigger_gotcha(10)
            self.gotcha_start_time = now

    def update_gotcha(self, now):
        """Update gotcha state and check for end."""
        if self.gotcha_start_time is None:
            return False

        if now - self.gotcha_start_time >= 10.0:
            self.debug_log("timing", "📱 GOTCHA ENDED - Showing QR code")
            self.state.end_gotcha()
            self.gotcha_start_time = None
            if self.qr_display_start is None:  # Only set once
                self.qr_display_start = time.time()
            return True
        return False

    def update_qr_display(self, now):
        """Update QR display and check for session end."""
        if self.qr_display_start is None:
            return False

        qr_elapsed = now - self.qr_display_start
        self.debug_log(
            "timing",
            f"🔄 QR display active for {qr_elapsed:.1f}s / {self.qr_display_duration:.1f}s",
        )

        if qr_elapsed >= self.qr_display_duration:
            self.debug_log("timing", "🏁 SESSION COMPLETE - Returning to IDLE state")
            self._reset_session()
            return True
        return False

    def _reset_session(self):
        """Reset all session state to idle."""
        self.state.countdown_active = False
        self.countdown_start_time = None
        self.gotcha_start_time = None
        self.countdown_beeped = set()
        self.smile_photos_taken = 0
        self.last_smile_time = 0
        self.last_countdown_number = None
        self.qr_display_start = None
        self.files_moved_to_network = False

    def increment_smile_photos(self):
        """Increment the count of smile photos taken."""
        self.smile_photos_taken += 1
        return self.smile_photos_taken

    def set_files_moved(self):
        """Mark files as moved to network."""
        self.files_moved_to_network = True

    def move_session_files(
        self,
        file_manager,
        local_photo_dir,
        local_video_dir,
        network_photo_dir,
        network_video_dir,
    ):
        """
        Move session files to network storage using the file manager.

        Returns:
            bool: True if files were moved successfully, False if already moved or failed
        """
        if self.files_moved_to_network:
            return True  # Already moved

        try:
            files_moved = file_manager.move_session_files_to_network(
                self.state.session_time,
                self.state.session_id,
                local_photo_dir,
                local_video_dir,
                network_photo_dir,
                network_video_dir,
            )

            if files_moved > 0:
                self.files_moved_to_network = True
                self.debug_log(
                    "timing",
                    f"✅ FILES MOVED to web server successfully ({files_moved} files)",
                )
                return True
            else:
                self.debug_log("timing", "ℹ️ No files to move")
                self.files_moved_to_network = True  # Mark as handled
                return True

        except Exception as e:
            self.debug_log("timing", f"❌ FILE MOVE failed: {e}")
            return False

    def is_idle(self):
        """Check if session is idle (no active countdown, gotcha, or QR display)."""
        return (
            not self.state.countdown_active
            and not self.state.gotcha_active
            and self.qr_display_start is None
        )

    def get_session_info(self):
        """Get current session information."""
        return {
            "session_id": self.state.session_id,
            "session_time": self.state.session_time,
            "is_countdown": self.state.countdown_active,
            "is_gotcha": self.state.gotcha_active,
            "is_qr_display": self.qr_display_start is not None,
            "smile_photos_taken": self.smile_photos_taken,
        }
