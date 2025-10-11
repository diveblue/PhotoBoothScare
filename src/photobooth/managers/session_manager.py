"""
SessionManager
----------------

Responsibilities:
    - Central authority for all session state and transitions in the photobooth system.
    - Coordinates session lifecycle: idle, countdown, recording, gotcha, QR display, and reset.
    - Prevents overlapping sessions and enforces correct session timing.
    - Publishes events to trigger hardware and UI actions (camera, audio, video, overlay, GPIO) via an event bus or dispatcher.
    - Integrates with ConfigManager for runtime configuration and uses standard Python logging for diagnostics.


Key Methods:
    - is_idle(): Returns True if booth is ready for a new session.
    - start_countdown(): Initiates countdown and transitions to recording state.
    - update(): Advances session state machine; should be called regularly from main loop.
    - stop_session(): Forces session to end and resets state.
    - get_state(): Returns current session state (enum or string).
    - emit_event(event): Publishes an event to the system event bus for decoupled action handling.

Architecture:
    - Event-driven: publishes events to an event bus/dispatcher for all hardware and UI actions; does not call other managers directly.
    - Accepts a config object (from ConfigManager) and a logger instance in the constructor.
    - All session state is managed internally; other managers must not duplicate session logic.
    - Uses dependency injection for event bus or dispatcher if required.
    - All debug/info output is via the provided logger (no debug_log or print statements).
    - Designed for single-responsibility and testability; no direct hardware or UI code.
"""

import logging
import time
import random
from datetime import datetime
from ..utils.photobooth_state import PhotoBoothState
from ..utils.session_action import SessionAction


class SessionManager:
    """
    Central orchestrator for photobooth session state management.

    This class follows SOLID principles by being the single source of truth
    for session state transitions while delegating execution to main.py.
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Session state
        self.state = PhotoBoothState()
        self.state.phase = "idle"

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
        self.gotcha_recording_extend = config.get(3.0)
        self.prop_trigger_at_countdown = config.get(1)

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

        # PHASE STATE MACHINE
        phase = getattr(self.state, "phase", None)

        if phase == "idle":
            if (
                not hasattr(self, "_last_idle_debug")
                or now - self._last_idle_debug > 2.0
            ):
                print("😴 SessionManager: IDLE state - waiting for button press")
                self._last_idle_debug = now
            return action
        elif phase == "countdown":
            return self._handle_countdown_state(
                action, now, frame_dimensions, video_recording
            )
        elif phase == "smile":
            return self._handle_smile_state(action, now)
        elif phase == "gotcha":
            return self._handle_gotcha_state(
                action, now, video_recording, video_finalized
            )
        return action

    def _handle_smile_state(self, action, now):
        """
        Handle smile phase: show smile overlay for a fixed duration, then transition to gotcha.
        """
        SMILE_DURATION = self.config.get("SMILE_SECONDS", 2.0)
        if not hasattr(self, "smile_start_time") or self.smile_start_time is None:
            self.smile_start_time = now
            self.logger.debug("😊 SMILE phase started")

        elapsed = now - self.smile_start_time
        action.smile_action = {"show_display": True}
        if elapsed >= SMILE_DURATION:
            self.logger.debug("😊 SMILE phase complete, transitioning to GOTCHA")
            self.state.phase = "gotcha"
            self.smile_start_time = None
        return action

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
            self.logger.debug(
                f"🚀 COUNTDOWN STARTED at {self.current_countdown_number}"
            )

            # No display_state: all state is now in self.state

            # Start video recording at beginning
            if not video_recording and frame_dimensions:
                action.start_video = True
                action.video_dimensions = frame_dimensions
                self.logger.debug("🎥 VIDEO RECORDING STARTED with countdown")

        # Calculate which countdown number we should be showing based on elapsed time
        elapsed = now - self.countdown_start_time
        expected_number = self.countdown_seconds - int(elapsed)  # 3-0, 3-1, 3-2 = 3,2,1

        # Ensure we don't go below 1 (countdown stops at 1, not 0)
        if expected_number < 1:
            # Countdown finished - transition to smile
            self.logger.debug("✅ Countdown finished - transitioning to SMILE")
            self.state.countdown_number = None
            self.state.end_countdown()
            #            self.state.trigger_gotcha(10)
            #            self.gotcha_start_time = now
            self.countdown_start_time = None
            self.current_countdown_number = None

            #            # Start smile phase with coordinated actions
            #           action.smile_action = {
            #                "show_display": True,
            #                "play_shutter": True,
            #                "capture_photo": True,
            #            }
            #            self.logger.debug("📸 SMILE PHASE started")
            return action

        # Check if we need to trigger a new countdown number
        if expected_number != self.current_countdown_number:
            self.current_countdown_number = expected_number
            self.state.countdown_number = expected_number

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
                self.logger.debug(
                    f"⚡ PROP TRIGGERED at countdown {self.current_countdown_number}"
                )

            self.logger.debug(
                "timing",
                f"⏰ COUNTDOWN: {self.current_countdown_number} (beep + display)",
            )
        else:
            # Same number, just update display (no beep)
            self.state.countdown_number = self.current_countdown_number
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
                self.logger.debug(
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

                self.logger.debug(
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
            self.logger.debug("👻 GOTCHA PHASE started - display scare + QR")

        # Always show gotcha with integrated QR code
        action.gotcha_action = {
            "show_display": True,
            "qr_url": f"http://192.168.86.23/session.php?id={self.state.session_id}",
        }

        # Check if gotcha display time is finished
        gotcha_display_seconds = self.config.get(8.0)
        if (
            now - self.gotcha_display_start >= gotcha_display_seconds
            and not self.gotcha_cleanup_done
        ):
            # Time to cleanup - stop video and move files
            self.logger.debug("🎬 GOTCHA FINISHED - starting cleanup")

            action.stop_video = True
            self.video_stopped = True
            self.gotcha_cleanup_done = True
            self.logger.debug("🎬 VIDEO RECORDING STOPPED")

        # Try file movement when video is finalized and we've started cleanup
        if video_finalized and not self.files_moved_to_network and self.video_stopped:
            action.move_files = True
            self.files_moved_to_network = True
            self.logger.debug("📁 FILES MOVED TO NETWORK")

        # Session complete when files are moved or after reasonable timeout
        cleanup_timeout = gotcha_display_seconds + 5.0  # Extra time for file operations
        if self.files_moved_to_network or (
            now - self.gotcha_display_start >= cleanup_timeout
        ):
            completion_reason = (
                "files moved" if self.files_moved_to_network else "timeout"
            )
            self.logger.debug(
                "timing",
                f"✅ SESSION COMPLETE - returning to idle ({completion_reason})",
            )
            action.session_complete = True
            action.cleanup_session = True
            self._reset_session()

        return action

    def start_countdown(self):
        """Start a new photo session countdown. Called by button press."""
        # Use a single phase string for clarity: 'idle', 'countdown', 'smile', 'gotcha'
        phase = getattr(self.state, "phase", None)

        if phase != "idle":
            self.logger.error(f"start_countdown called in invalid phase: {phase}")
            return False

        self.logger.debug("🚀 BUTTON PRESSED - Starting countdown")
        # Explicitly set phase to 'countdown'
        self.state.phase = "countdown"
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
            self.logger.debug("✅ Countdown finished - showing SMILE overlay")
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
                self.logger.debug(f"⏰ COUNTDOWN: {countdown_number}")
                self.logger.debug("🔊 Playing beep sound")
                audio_manager.play_beep()
                self.countdown_beeped.add(countdown_number)

                # Trigger prop at configured countdown number
                prop_trigger_at = self.config.get(1)
                if countdown_number == prop_trigger_at and gpio_manager is not None:
                    self.logger.debug(
                        "gpio", f"⚡ PROP TRIGGERED at countdown {countdown_number}"
                    )
                    gpio_manager.trigger_scare()

        return countdown_number

    def trigger_gotcha(self, now):
        """Trigger the gotcha/scare sequence."""
        if self.state.phase != "smile":
            self.logger.error(
                f"trigger_gotcha called in invalid phase: {self.state.phase}"
            )
            return
        else:
            self.logger.debug("📸 Gotcha phase started")
            self.state.phase = "gotcha"
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
        self.logger.debug(
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
        self.logger.debug("📱 QR CODE DISPLAY started with gotcha overlay")

    def update_gotcha_qr_phase(self, now):
        """Update the combined gotcha+QR phase. Only end when files are moved."""
        if self.gotcha_start_time is None:
            return False

        # Stay in gotcha+QR phase until files are moved
        if self.files_moved_to_network:
            self.logger.debug(
                "timing", "✅ FILES MOVED - Session complete, returning to idle"
            )
            self.state.end_gotcha()
            self.gotcha_start_time = None
            self.qr_started = False
            return True

        # Debug: Show why we're still waiting
        elapsed = now - self.gotcha_start_time
        if elapsed > 10.0:  # After 10 seconds, start logging why we're waiting
            self.logger.debug(
                "timing",
                f"⏳ Still in QR phase after {elapsed:.1f}s - files_moved: {self.files_moved_to_network}, video_stopped: {self.video_stopped}",
            )

        return False

    def _reset_session(self):
        """Reset all session state to idle."""
        self.state.phase = "idle"
        self.state.countdown_active = False
        # gotcha_active removed: only use phase
        self.state.session_id = None
        self.state.session_time = None
        self.countdown_start_time = None
        self.gotcha_start_time = None
        self.countdown_beeped = set()
        self.smile_photos_taken = 0
        self.last_smile_time = 0
        self.last_countdown_number = None
        self.files_moved_to_network = False
        self.video_stopped = False
        self.qr_started = False
        self.current_countdown_number = None
        self.last_beep_time = None
        self.current_smile_seconds = None
        self.gotcha_display_start = None
        self.gotcha_cleanup_done = False
        self.prop_triggered = False

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
                self.logger.debug(
                    "timing",
                    f"✅ FILES MOVED to web server successfully ({files_moved} files)",
                )
                return True
            else:
                self.logger.debug("ℹ️ No files to move")
                self.files_moved_to_network = True  # Mark as handled
                return True

        except Exception as e:
            self.logger.debug(f"❌ FILE MOVE failed: {e}")
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
            self.logger.debug(
                "timing", "⏳ Video still processing - waiting for completion"
            )
            return False

        # Verify the final video file exists and has reasonable size (not just stub)
        import os

        final_video_path = f"{local_video_dir}/{self.state.session_time}_{self.state.session_id}_booth.mp4"

        if os.path.exists(final_video_path):
            file_size = os.path.getsize(final_video_path)
            if file_size > 1000:  # File has actual content (not just 48-byte stub)
                self.logger.debug(
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
                self.logger.debug(
                    "timing",
                    f"⏳ Video file too small ({file_size} bytes) - waiting for completion",
                )
                return False
        else:
            self.logger.debug("⏳ Final video file not ready - waiting")
            return False

    def is_idle(self):
        """Check if session is idle (phase == 'idle')."""
        return getattr(self.state, "phase", None) == "idle"

    def get_session_info(self):
        """Get current session information."""
        return {
            "session_id": self.state.session_id,
            "session_time": self.state.session_time,
            "phase": getattr(self.state, "phase", None),
            "is_qr_display": getattr(self.state, "phase", None) == "gotcha",
            "smile_photos_taken": getattr(self, "smile_photos_taken", 0),
        }
