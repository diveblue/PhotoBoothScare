"""
countdown_manager.py
Handles countdown timing, beep coordination, and countdown state management.
"""

import time
import math


class CountdownManager:
    """Manages countdown timing, audio beeps, and number display logic."""

    def __init__(self, config, debug_log):
        self.config = config
        self.debug_log = debug_log
        self.countdown_seconds = config["COUNTDOWN_SECONDS"]

        # Internal state
        self.countdown_start_time = None
        self.countdown_beeped = set()
        self.last_countdown_number = None
        self.active = False

    def start_countdown(self, audio_manager, gpio_manager):
        """Start the countdown sequence with audio beeps and GPIO trigger."""
        if self.active:
            self.debug_log("timing", "Button press ignored - countdown already active")
            return False

        self.debug_log(
            "timing",
            f"🔘 BUTTON PRESSED - Starting {self.countdown_seconds}s countdown",
        )

        # Reset countdown state
        self.countdown_start_time = time.time()
        self.countdown_beeped = set()
        self.last_countdown_number = None
        self.active = True

        # Trigger the prop/LED immediately
        self.debug_log("gpio", "⚡ PROP TRIGGERED (scare relay activated)")
        gpio_manager.trigger_scare()

        return True

    def update(self, audio_manager):
        """Update countdown state and handle beeps. Returns countdown info."""
        if not self.active or self.countdown_start_time is None:
            return None

        now = time.time()
        elapsed = now - self.countdown_start_time
        seconds_left = int(math.ceil(self.countdown_seconds - elapsed))

        countdown_info = {
            "elapsed": elapsed,
            "seconds_left": seconds_left,
            "countdown_finished": elapsed >= self.countdown_seconds,
            "countdown_number": None,
        }

        if seconds_left > 0:
            countdown_info["countdown_number"] = seconds_left
            # Play beep if we haven't for this number yet
            if self.last_countdown_number != seconds_left:
                self.debug_log("timing", f"⏰ COUNTDOWN: {seconds_left}")
                self.debug_log("audio", "🔊 Playing beep sound")
                audio_manager.play_beep()
                self.last_countdown_number = seconds_left
        else:
            # Countdown finished
            if self.last_countdown_number is not None:
                self.debug_log(
                    "timing",
                    "✅ Countdown finished - showing SMILE overlay",
                )
                self.last_countdown_number = None

        return countdown_info

    def is_active(self):
        """Check if countdown is currently active."""
        return self.active

    def get_elapsed_time(self):
        """Get elapsed time since countdown started."""
        if not self.active or self.countdown_start_time is None:
            return 0.0
        return time.time() - self.countdown_start_time

    def is_finished(self):
        """Check if countdown has finished."""
        if not self.active or self.countdown_start_time is None:
            return False
        return self.get_elapsed_time() >= self.countdown_seconds

    def reset(self):
        """Reset countdown state."""
        self.countdown_start_time = None
        self.countdown_beeped = set()
        self.last_countdown_number = None
        self.active = False

    def cleanup(self):
        """Clean up countdown manager resources."""
        self.reset()
