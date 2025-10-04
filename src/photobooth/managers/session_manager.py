"""
SessionManager - Central Orchestrator for PhotoBooth Sessions

RESPONSIBILITIES:
- Single source of truth for all session state transitions (SOLID principle)
- Orchestrates countdown → smile → gotcha → QR → idle flow
- Controls timing of audio, video, GPIO, and photo capture actions
- Coordinates with all other managers through main.py via SessionAction commands

KEY METHODS:
- update(): Main orchestration method called every frame by main.py
- is_idle(): Check if system is ready for new session
- start_countdown(): Begin new photobooth session
- _handle_countdown_state(): Manage countdown phase with beeps and GPIO trigger
- _handle_gotcha_state(): Control scare activation and video recording
- _handle_qr_state(): Manage QR code display and file operations

ARCHITECTURE:
- Returns SessionAction objects that tell main.py exactly what to execute
- Never directly calls other managers - maintains loose coupling
- All business logic contained within this class following Single Responsibility
"""

import time
import random
from datetime import datetime
from ..utils.photobooth_state import PhotoBoothState
from ..utils.session_action import SessionAction
from ..utils.thread_safe_display_state import ThreadSafeDisplayState


class SessionManager:
    """
    Central orchestrator for photobooth session state management.

    This class follows SOLID principles by being the single source of truth
    for session state transitions while delegating execution to main.py.
    """

    def __init__(self, config, debug_log_func, display_state: ThreadSafeDisplayState):
        self.config = config
        self.debug_log = debug_log_func
        self.display_state = display_state

        # Session state
        self.state = PhotoBoothState()

        # Initialize shared display state to idle
        self.display_state.update_phase("idle")

        # Coordinated timing variables
        self.current_countdown_number = None  # Current countdown display: 3, 2, 1
        self.countdown_start_time = None  # When countdown began

        # Smile phase tracking
        self.current_smile_seconds = None  # Which photo number (0-based)

        # Simple gotcha tracking
        self.gotcha_display_start = None
        self.gotcha_cleanup_done = False

        # Session phases
        self.files_moved_to_network = False
        self.video_stopped = False
        self.prop_triggered = False  # Configuration
        self.countdown_seconds = config["COUNTDOWN_SECONDS"]
        self.gotcha_recording_extend = config.get("GOTCHA_RECORDING_SECONDS", 3.0)
        self.prop_trigger_at_countdown = config.get("PROP_TRIGGER_AT_COUNTDOWN", 1)

    def update(
        self, now, frame_dimensions=None, video_recording=False, video_finalized=False
    ):
        """
        SOLID ORCHESTRATION METHOD

        This is the single method that handles ALL session state transitions.
        Main.py calls this and executes the returned actions.

        Args:
            now: Current timestamp
            frame_dimensions: (width, height) for video recording
            video_recording: Whether video is currently recording
            video_finalized: Whether video processing is complete

        Returns:
            SessionAction object with actions for main.py to execute
        """
        action = SessionAction()

        # Set session info for all states
        if self.state.session_id:
            action.session_id = self.state.session_id
            action.session_time = self.state.session_time

        # IDLE STATE - waiting for button press
        if not self.state.countdown_active and not self.state.gotcha_active:
            # Update shared display state to idle
            self.display_state.update_phase("idle")

            # Debug: Only print occasionally to avoid spam
            if (
                not hasattr(self, "_last_idle_debug")
                or now - self._last_idle_debug > 2.0
            ):
                print("😴 SessionManager: IDLE state - waiting for button press")
                self._last_idle_debug = now
            return action  # No actions needed in idle

        # COUNTDOWN STATE
        if self.state.countdown_active:
            return self._handle_countdown_state(
                action, now, frame_dimensions, video_recording
            )

        # GOTCHA STATE (includes smile, scare, and QR phases)
        if self.state.gotcha_active:
            return self._handle_gotcha_state(
                action, now, video_recording, video_finalized
            )

        return action

    def _handle_countdown_state(self, action, now, frame_dimensions, video_recording):
        """
        Handle countdown phase with coordinated timing.
        Flow: 3-beep → 2-beep → 1-beep → SMILE
        Each number shows for exactly 1 second with beep at start.
        """

        # Initialize countdown if just starting
        if self.current_countdown_number is None:
            self.current_countdown_number = self.countdown_seconds  # Start at 3
            self.countdown_start_time = now
            self.debug_log(
                "timing", f"🚀 COUNTDOWN STARTED at {self.current_countdown_number}"
            )

            # Update shared display state for countdown
            self.display_state.update_phase("countdown")
            self.display_state.update_countdown(self.current_countdown_number)

            # Start video recording at beginning
            if not video_recording and frame_dimensions:
                action.start_video = True
                action.video_dimensions = frame_dimensions
                self.debug_log("timing", "🎥 VIDEO RECORDING STARTED with countdown")

        # Calculate which countdown number we should be showing based on elapsed time
        elapsed = now - self.countdown_start_time
        expected_number = self.countdown_seconds - int(elapsed)  # 3-0, 3-1, 3-2 = 3,2,1

        # Ensure we don't go below 1 (countdown stops at 1, not 0)
        if expected_number < 1:
            # Countdown finished - transition to smile
            self.debug_log("timing", "✅ Countdown finished - transitioning to SMILE")
            self.state.end_countdown()
            self.state.trigger_gotcha(10)
            self.gotcha_start_time = now
            self.countdown_start_time = None
            self.current_countdown_number = None

            # Start smile phase with coordinated actions
            action.smile_action = {
                "show_display": True,
                "play_shutter": True,
                "capture_photo": True,
            }
            self.debug_log("timing", "📸 SMILE PHASE started")
            return action

        # Check if we need to trigger a new countdown number
        if expected_number != self.current_countdown_number:
            self.current_countdown_number = expected_number

            # COORDINATED ACTION: Show number + beep + prop trigger (if needed)
            action.countdown_update = {
                "number": self.current_countdown_number,
                "play_beep": True,  # Always beep on number change
                "show_display": True,
                "trigger_prop": (
                    self.current_countdown_number == self.prop_trigger_at_countdown
                    and not self.prop_triggered
                ),
            }

            # Trigger prop if needed
            if (
                self.current_countdown_number == self.prop_trigger_at_countdown
                and not self.prop_triggered
            ):
                self.prop_triggered = True
                self.debug_log(
                    "gpio",
                    f"⚡ PROP TRIGGERED at countdown {self.current_countdown_number}",
                )

            self.debug_log(
                "timing",
                f"⏰ COUNTDOWN: {self.current_countdown_number} (beep + display)",
            )
        else:
            # Same number, just update display (no beep)
            action.countdown_update = {
                "number": self.current_countdown_number,
                "play_beep": False,
                "show_display": True,
                "trigger_prop": False,
            }

        return action

    def _handle_gotcha_state(self, action, now, video_recording, video_finalized):
        """
        Handle smile + gotcha phases with coordinated timing.
        Flow: smile-pic-shutter → smile-pic-shutter → ... → GOTCHA display
        """
        if not self.gotcha_start_time:
            return action

        elapsed_gotcha = now - self.gotcha_start_time
        smile_duration = self.config.get(
            "SMILE_SECONDS", 5.0
        )  # 5 photos, one per second

        # PHASE 1: SMILE - coordinated photo capture
        if elapsed_gotcha < smile_duration:
            # Calculate which photo we should be taking (0-based)
            expected_photo = int(
                elapsed_gotcha
            )  # 0.0-0.99 = photo 0, 1.0-1.99 = photo 1, etc.

            # Initialize smile if just starting
            if self.current_smile_seconds is None:
                self.current_smile_seconds = 0
                self.debug_log(
                    "timing", f"😊 SMILE PHASE started - {int(smile_duration)} photos"
                )

            # Check if we need to take a new photo
            if (
                expected_photo != self.current_smile_seconds
                and expected_photo < smile_duration
            ):
                self.current_smile_seconds = expected_photo

                # COORDINATED ACTION: Display + Photo + Shutter sound
                action.smile_action = {
                    "show_display": True,
                    "capture_photo": True,
                    "play_shutter": True,
                }

                self.debug_log(
                    "timing",
                    f"📸 SMILE photo {expected_photo + 1}/{int(smile_duration)} taken",
                )
            else:
                # Same photo interval, just show smile display
                action.smile_action = {
                    "show_display": True,
                    "capture_photo": False,
                    "play_shutter": False,
                }

            return action

        # PHASE 2: GOTCHA - coordinated scare display
        # Initialize gotcha phase if just starting
        if self.gotcha_display_start is None:
            self.gotcha_display_start = now
            self.debug_log("timing", "👻 GOTCHA PHASE started - display scare + QR")

        # Always show gotcha with integrated QR code
        action.gotcha_action = {
            "show_display": True,
            "qr_url": f"http://192.168.86.23/session.php?id={self.state.session_id}",
        }

        # Check if gotcha display time is finished
        gotcha_display_seconds = self.config.get("GOTCHA_DISPLAY_SECONDS", 8.0)
        if (
            now - self.gotcha_display_start >= gotcha_display_seconds
            and not self.gotcha_cleanup_done
        ):
            # Time to cleanup - stop video and move files
            self.debug_log("timing", "🎬 GOTCHA FINISHED - starting cleanup")

            action.stop_video = True
            self.video_stopped = True
            self.gotcha_cleanup_done = True
            self.debug_log("timing", "🎬 VIDEO RECORDING STOPPED")

        # Try file movement when video is finalized and we've started cleanup
        if video_finalized and not self.files_moved_to_network and self.video_stopped:
            action.move_files = True
            self.files_moved_to_network = True
            self.debug_log("timing", "📁 FILES MOVED TO NETWORK")

        # Session complete when files are moved or after reasonable timeout
        cleanup_timeout = gotcha_display_seconds + 5.0  # Extra time for file operations
        if self.files_moved_to_network or (
            now - self.gotcha_display_start >= cleanup_timeout
        ):
            completion_reason = (
                "files moved" if self.files_moved_to_network else "timeout"
            )
            self.debug_log(
                "timing",
                f"✅ SESSION COMPLETE - returning to idle ({completion_reason})",
            )
            action.session_complete = True
            action.cleanup_session = True
            self._reset_session()

        return action

    def _reset_session(self):
        """Reset all session state to idle."""
        self.state.countdown_active = False
        self.state.gotcha_active = False
        self.state.session_id = None
        self.state.session_time = None

        # Reset simple countdown tracking
        self.current_countdown_number = None
        self.last_beep_time = None
        self.countdown_start_time = None

        # Reset simple smile tracking
        self.current_smile_seconds = None

        # Reset simple gotcha tracking
        self.gotcha_display_start = None
        self.gotcha_cleanup_done = False

        # Reset session phases
        self.files_moved_to_network = False
        self.video_stopped = False
        self.prop_triggered = False

    def start_countdown(self):
        """Start a new photo session countdown. Called by button press."""
        if self.state.countdown_active or self.state.gotcha_active:
            self.debug_log("timing", "⚠️ Session already active - ignoring button press")
            return False

        self.debug_log("timing", "🚀 BUTTON PRESSED - Starting countdown")
        self.state.start_countdown(self.countdown_seconds)
        self.countdown_start_time = time.time()
        self._reset_session_tracking()
        return True

    def _reset_session_tracking(self):
        """Reset tracking variables for new session."""
        self.countdown_beeped = set()
        self.smile_photos_taken = 0
        self.last_smile_time = 0
        self.last_countdown_number = None
        self.files_moved_to_network = False
        self.video_stopped = False
        self.qr_started = False
        self.prop_triggered = False

    def update_countdown(self, now, audio_manager, gpio_manager=None):
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

        # Handle countdown beeps and prop trigger
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

                # Trigger prop at configured countdown number
                prop_trigger_at = self.config.get("PROP_TRIGGER_AT_COUNTDOWN", 1)
                if countdown_number == prop_trigger_at and gpio_manager is not None:
                    self.debug_log(
                        "gpio", f"⚡ PROP TRIGGERED at countdown {countdown_number}"
                    )
                    gpio_manager.trigger_scare()

        return countdown_number

    def trigger_gotcha(self, now):
        """Trigger the gotcha/scare sequence."""
        if not self.state.gotcha_active:
            self.debug_log("timing", "📸 SMILE phase started")
            self.debug_log("audio", "🔊 Playing shutter sound")
            self.state.trigger_gotcha(10)
            self.gotcha_start_time = now

    def should_stop_video_recording(self, now):
        """Check if video recording should stop (after gotcha_recording_extend seconds into gotcha)."""
        if self.gotcha_start_time is None or self.video_stopped:
            return False

        gotcha_elapsed = now - self.gotcha_start_time
        return gotcha_elapsed >= self.gotcha_recording_extend

    def mark_video_stopped(self):
        """Mark that video recording has been stopped."""
        self.video_stopped = True
        self.debug_log(
            "timing",
            f"📹 VIDEO STOPPED after {self.gotcha_recording_extend}s into gotcha",
        )

    def should_start_qr_display(self, now):
        """Check if QR display should start (immediately when gotcha begins)."""
        if self.gotcha_start_time is None or self.qr_started:
            return False
        # Start QR immediately when gotcha starts
        return True

    def mark_qr_started(self):
        """Mark that QR display has started."""
        self.qr_started = True
        self.debug_log("timing", "📱 QR CODE DISPLAY started with gotcha overlay")

    def update_gotcha_qr_phase(self, now):
        """Update the combined gotcha+QR phase. Only end when files are moved."""
        if self.gotcha_start_time is None:
            return False

        # Stay in gotcha+QR phase until files are moved
        if self.files_moved_to_network:
            self.debug_log(
                "timing", "✅ FILES MOVED - Session complete, returning to idle"
            )
            self.state.end_gotcha()
            self.gotcha_start_time = None
            self.qr_started = False
            return True

        # Debug: Show why we're still waiting
        elapsed = now - self.gotcha_start_time
        if elapsed > 10.0:  # After 10 seconds, start logging why we're waiting
            self.debug_log(
                "timing",
                f"⏳ Still in QR phase after {elapsed:.1f}s - files_moved: {self.files_moved_to_network}, video_stopped: {self.video_stopped}",
            )

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
        self.files_moved_to_network = False
        self.video_stopped = False
        self.qr_started = False

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

    def try_async_file_movement(
        self,
        video_manager,
        file_manager,
        local_photo_dir,
        local_video_dir,
        network_photo_dir,
        network_video_dir,
    ):
        """Try to move files if video processing is complete."""
        if self.files_moved_to_network:
            return True  # Already moved

        # Only attempt file movement if video has been stopped
        if not self.video_stopped:
            return False

        # Check if video processing is complete
        if video_manager.is_finalizing():
            self.debug_log(
                "timing", "⏳ Video still processing - waiting for completion"
            )
            return False

        # Verify the final video file exists and has reasonable size (not just stub)
        import os

        final_video_path = f"{local_video_dir}/{self.state.session_time}_{self.state.session_id}_booth.mp4"

        if os.path.exists(final_video_path):
            file_size = os.path.getsize(final_video_path)
            if file_size > 1000:  # File has actual content (not just 48-byte stub)
                self.debug_log(
                    "timing", f"🎬 Video finalized ({file_size} bytes) - moving files"
                )
                return self.move_session_files(
                    file_manager,
                    local_photo_dir,
                    local_video_dir,
                    network_photo_dir,
                    network_video_dir,
                )
            else:
                self.debug_log(
                    "timing",
                    f"⏳ Video file too small ({file_size} bytes) - waiting for completion",
                )
                return False
        else:
            self.debug_log("timing", "⏳ Final video file not ready - waiting")
            return False

    def is_idle(self):
        """Check if session is idle (no active countdown, gotcha, or QR display)."""
        return not self.state.countdown_active and not self.state.gotcha_active

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
