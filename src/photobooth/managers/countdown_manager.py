"""
CountdownManager - Countdown Phase Timing and Audio Coordination

RESPONSIBILITIES:
- Manages countdown timing from configured seconds down to zero
- Coordinates audio beep playback at each second interval
- Controls GPIO prop trigger timing (typically at countdown=1)
- Provides countdown number display logic for overlay rendering

KEY METHODS:
- start_countdown(): Initialize countdown sequence with audio and GPIO coordination
- update(): Process countdown state and return current countdown number
- should_trigger_prop(): Determine if GPIO prop should be triggered at current count
- is_complete(): Check if countdown has finished and session should progress

TIMING COORDINATION:
- Plays beep sound at each countdown second (via AudioManager)
- Triggers GPIO prop at configured countdown number (default: 1 second)
- Manages countdown display state for OverlayRenderer
- Coordinates with SessionManager for phase transitions

ARCHITECTURE:
- Encapsulates countdown logic following Single Responsibility principle
- Integrates with AudioManager and GPIOManager through main.py coordination
- Maintains internal timing state while providing external status interface
- Clean separation between countdown logic and audio/GPIO execution
"""

import time
import math


class CountdownManager:
    """
    Manages countdown phase timing, audio coordination, and prop triggering.

    Handles the countdown sequence from start to completion with proper
    timing for beeps, GPIO triggers, and display updates.
    """

    def __init__(self, config, debug_log):
        self.config = config
        self.debug_log = debug_log
        self.countdown_seconds = config["COUNTDOWN_SECONDS"]
        self.prop_trigger_at_countdown = config.get("PROP_TRIGGER_AT_COUNTDOWN", 1)

        # Internal state
        self.countdown_start_time = None
        self.countdown_beeped = set()
        self.last_countdown_number = None
        self.prop_triggered = False
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
        self.prop_triggered = False
        self.active = True

        self.debug_log(
            "timing",
            f"⚡ PROP will trigger at countdown {self.prop_trigger_at_countdown}",
        )

        return True

    def update(self, audio_manager, gpio_manager=None):
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

                # Trigger prop at configured countdown number
                if (
                    seconds_left == self.prop_trigger_at_countdown
                    and not self.prop_triggered
                    and gpio_manager is not None
                ):
                    self.debug_log(
                        "gpio", f"⚡ PROP TRIGGERED at countdown {seconds_left}"
                    )
                    gpio_manager.trigger_scare()
                    self.prop_triggered = True
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
