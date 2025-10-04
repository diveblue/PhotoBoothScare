"""
VideoRenderer - Pure video frame rendering and display

This class handles:
- Getting camera frames
- Reading current display state from ThreadSafeDisplayState
- Rendering overlays based on state
- Displaying frames in OpenCV window
- Returning keyboard input for quit detection

This is extracted from ActionHandler to create clean separation of concerns.
"""

import cv2
import time
from typing import Optional


class VideoRenderer:
    """
    Pure video rendering class that reads shared state and displays frames.

    No business logic - just renders what the current state tells it to render.
    """

    def __init__(
        self,
        display_state,
        camera_manager,
        overlay_renderer,
        config,
        camera_controls=None,
        settings_overlay=None,
        input_handler=None,
    ):
        self.display_state = display_state
        self.camera_manager = camera_manager
        self.overlay_renderer = overlay_renderer
        self.config = config
        self.camera_controls = camera_controls
        self.settings_overlay = settings_overlay
        self.input_handler = input_handler

        # Window configuration
        self.window_name = config.get("PREVIEW_WINDOW", "PhotoBooth Preview")
        self.preview_enabled = config.get("PREVIEW_ENABLED", True)

    def render_frame(self) -> Optional[str]:
        """
        Render one frame: get camera frame, apply overlays, display window.

        Returns:
            str: Key pressed ('q' for quit, 'space' for button, etc.) or None
        """
        if not self.preview_enabled:
            return None

        # Get camera frame
        frame = self.camera_manager.get_frame()
        if frame is None:
            return None

        # Flip frame horizontally (mirror effect)
        frame = cv2.flip(frame, 1)

        # Get current display state (thread-safe)
        current_state = self.display_state.get_current_state()

        # Convert display state to overlay format
        overlay_state = self._convert_state_to_overlay_format(current_state)

        # Render overlay on frame
        rendered_frame = self.overlay_renderer.draw_overlay(frame, overlay_state)

        # Apply settings overlay if available
        if self.settings_overlay:
            rendered_frame = self.settings_overlay.draw_overlay(rendered_frame)

        # Display frame
        cv2.imshow(self.window_name, rendered_frame)

        # Check for keyboard input (non-blocking) and delegate to InputHandler
        key = cv2.waitKey(1) & 0xFF
        if key != 255:  # Key was pressed
            self._handle_key_press(key, current_state)

        return None  # VideoRenderer no longer returns key events

    def _convert_state_to_overlay_format(self, state):
        """
        Convert ThreadSafeDisplayState format to overlay renderer format.

        This bridges the gap between our new state format and the existing
        overlay renderer expectations.
        """
        overlay_state = {
            "phase": state.phase,
            "countdown_active": state.phase == "countdown",
            "gotcha_active": state.gotcha_active,
            "countdown_number": state.countdown_number or 0,
            "qr_url": state.qr_data,
        }

        # Debug output
        if state.phase != "idle":
            print(
                f"🎨 VideoRenderer: phase={state.phase}, countdown={state.countdown_number}, gotcha={state.gotcha_active}"
            )

        return overlay_state

    def _handle_key_press(self, key, current_state):
        """Handle keyboard input by delegating to appropriate handlers."""
        if key == ord("q"):
            if self.input_handler:
                self.input_handler.handle_key_input("quit")
        elif key == ord(" "):  # Spacebar
            if self.input_handler:
                self.input_handler.handle_key_input("button")
        elif key == ord("s"):
            if self.input_handler:
                self.input_handler.handle_key_input("status")
        else:
            # Handle camera control keys (only when idle)
            if self.camera_controls and self._is_idle_state(current_state):
                self.camera_controls.handle_key(key)

    def _is_idle_state(self, state):
        """Check if system is in idle state (ready for camera controls)."""
        return (
            state.phase == "idle"
            and not state.gotcha_active
            and not state.qr_data  # No QR being displayed
        )

    def cleanup(self):
        """Clean up OpenCV windows"""
        cv2.destroyAllWindows()

    def run_continuous_loop(self):
        """
        Continuous rendering loop - runs until quit signal.

        This can be used for threading or standalone operation.
        """
        print("🎬 VideoRenderer: Starting continuous loop")
        try:
            while True:
                key_pressed = self.render_frame()
                if key_pressed == "quit":
                    print("🎬 VideoRenderer: Quit requested")
                    break
                elif key_pressed:
                    print(f"🎬 VideoRenderer: Key pressed: {key_pressed}")
        except KeyboardInterrupt:
            print("🎬 VideoRenderer: Interrupted")
        finally:
            self.cleanup()
