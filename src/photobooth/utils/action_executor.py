"""
ActionExecutor - Executes actions returned by SessionManager

This class handles:
- Executing audio commands (play_beep, play_shutter)
- Executing video commands (start/stop recording)
- Executing GPIO commands (trigger_scare)
- Executing photo commands (capture_photo)
- Pure execution - no business logic

This bridges the gap between SessionManager (returns actions) and hardware managers.
"""

import time


class ActionExecutor:
    """
    Executes actions returned by SessionManager.

    Takes SessionAction objects and executes the requested operations
    using the appropriate managers.
    """

    def __init__(
        self,
        audio_manager=None,
        video_manager=None,
        gpio_manager=None,
        photo_manager=None,
    ):
        self.audio_manager = audio_manager
        self.video_manager = video_manager
        self.gpio_manager = gpio_manager
        self.photo_manager = photo_manager

    def execute_action(
        self, action, frame=None, session_time=None, session_id=None, now=None
    ):
        """
        Execute all actions specified in the SessionAction object.

        Args:
            action: SessionAction object from SessionManager
            frame: Current camera frame (for photo capture)
            session_time: Current session timestamp
            session_id: Current session ID
            now: Current time
        """
        if action is None:
            return

        # Handle coordinated countdown actions
        if hasattr(action, "countdown_update") and action.countdown_update:
            self._execute_countdown_update(action.countdown_update)

        # Handle coordinated smile actions
        if hasattr(action, "smile_action") and action.smile_action:
            self._execute_smile_action(
                action.smile_action, frame, session_time, session_id, now
            )

        # Handle coordinated gotcha actions
        if hasattr(action, "gotcha_action") and action.gotcha_action:
            self._execute_gotcha_action(action.gotcha_action)

        # Handle individual audio actions
        if hasattr(action, "play_beep") and action.play_beep and self.audio_manager:
            print("🔊 ActionExecutor: Playing beep")
            self.audio_manager.play_beep()

        if (
            hasattr(action, "play_shutter")
            and action.play_shutter
            and self.audio_manager
        ):
            print("📸 ActionExecutor: Playing shutter sound")
            self.audio_manager.play_shutter()

        # Handle video actions
        if hasattr(action, "start_video") and action.start_video and self.video_manager:
            print("🎥 ActionExecutor: Starting video recording")
            if hasattr(action, "session_id") and hasattr(action, "video_dimensions"):
                self.video_manager.start_recording(
                    action.session_id, session_time or now, action.video_dimensions
                )

        if hasattr(action, "stop_video") and action.stop_video and self.video_manager:
            print("🛑 ActionExecutor: Stopping video recording")
            self.video_manager.stop_recording()

        # Handle GPIO actions
        if (
            hasattr(action, "trigger_scare")
            and action.trigger_scare
            and self.gpio_manager
        ):
            print("💀 ActionExecutor: Triggering scare!")
            self.gpio_manager.trigger_scare()

        # Handle photo actions
        if (
            hasattr(action, "capture_photo")
            and action.capture_photo
            and self.photo_manager
            and frame is not None
        ):
            print("📷 ActionExecutor: Capturing photo")
            self.photo_manager.capture_photo(frame, session_time, session_id, now)

    def _execute_countdown_update(self, countdown_data):
        """Execute coordinated countdown actions (beep + display + prop trigger)"""
        if countdown_data.get("play_beep") and self.audio_manager:
            print(
                f"🔊 ActionExecutor: Playing countdown beep for {countdown_data.get('number')}"
            )
            self.audio_manager.play_beep()

        if countdown_data.get("trigger_prop") and self.gpio_manager:
            print(
                f"💀 ActionExecutor: Triggering prop at countdown {countdown_data.get('number')}"
            )
            self.gpio_manager.trigger_scare()

        # Display update handled by SessionManager updating shared state
        print(f"⏰ ActionExecutor: Countdown {countdown_data.get('number')} executed")

    def _execute_smile_action(self, smile_data, frame, session_time, session_id, now):
        """Execute coordinated smile actions (shutter + photo)"""
        if smile_data.get("play_shutter") and self.audio_manager:
            print("📸 ActionExecutor: Playing shutter sound")
            self.audio_manager.play_shutter()

        if smile_data.get("capture_photo") and self.photo_manager and frame is not None:
            print("📷 ActionExecutor: Capturing photo")
            self.photo_manager.capture_photo(frame, session_time, session_id, now)

        print("📸 ActionExecutor: Smile action executed")

    def _execute_gotcha_action(self, gotcha_data):
        """Execute coordinated gotcha actions"""
        print(
            f"👻 ActionExecutor: Gotcha action executed (duration: {gotcha_data.get('duration', 0):.1f}s)"
        )

    def cleanup(self):
        """Clean up resources"""
        print("🔧 ActionExecutor: Cleanup complete")
