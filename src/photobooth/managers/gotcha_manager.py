"""
gotcha_manager.py
Handles "gotcha" scare sequence timing and state management.
"""

import time


class GotchaManager:
    """Manages the gotcha scare sequence with proper timing and state tracking."""

    def __init__(self, config, debug_log):
        self.config = config
        self.debug_log = debug_log
        self.gotcha_duration = 10.0  # Default 10 second gotcha duration

        # Internal state
        self.gotcha_start_time = None
        self.active = False

    def should_trigger_gotcha(
        self, photo_manager, countdown_elapsed, countdown_seconds
    ):
        """Check if gotcha should be triggered based on photo completion and timing."""
        if self.active or self.gotcha_start_time is not None:
            return False

        smile_pause = 3.0  # Pause after countdown before gotcha
        return (
            photo_manager.is_complete()
            and countdown_elapsed >= countdown_seconds + smile_pause
        )

    def trigger_gotcha(self, state, duration=10.0):
        """Start the gotcha scare sequence."""
        if self.active:
            return False

        self.debug_log("timing", "👻 GOTCHA TRIGGERED! (scare sequence)")
        self.gotcha_start_time = time.time()
        self.gotcha_duration = duration
        self.active = True

        # Update the photobooth state
        state.trigger_gotcha(duration)

        return True

    def update(self, state):
        """Update gotcha state and check for completion. Returns gotcha info."""
        if not self.active or self.gotcha_start_time is None:
            return None

        now = time.time()
        elapsed = now - self.gotcha_start_time

        gotcha_info = {
            "elapsed": elapsed,
            "duration": self.gotcha_duration,
            "active": True,
            "completed": elapsed >= self.gotcha_duration,
        }

        # Check if gotcha should end
        if elapsed >= self.gotcha_duration:
            self.debug_log("timing", "📱 GOTCHA ENDED - Ready for QR code")
            state.end_gotcha()
            self.gotcha_start_time = None
            self.active = False
            gotcha_info["active"] = False

        return gotcha_info

    def is_active(self):
        """Check if gotcha is currently active."""
        return self.active

    def get_elapsed_time(self):
        """Get elapsed time since gotcha started."""
        if not self.active or self.gotcha_start_time is None:
            return 0.0
        return time.time() - self.gotcha_start_time

    def is_complete(self):
        """Check if gotcha has completed."""
        if not self.active or self.gotcha_start_time is None:
            return False
        return self.get_elapsed_time() >= self.gotcha_duration

    def reset(self):
        """Reset gotcha state."""
        self.gotcha_start_time = None
        self.active = False

    def cleanup(self):
        """Clean up gotcha manager resources."""
        self.reset()
