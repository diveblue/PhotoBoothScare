"""
KeyboardInputManager - User Input Processing and Camera Controls

RESPONSIBILITIES:
- Processes keyboard input for both pygame and OpenCV display modes
- Handles camera control shortcuts (brightness, contrast, white balance, etc.)
- Manages system controls (quit, help, button simulation)
- Coordinates with SessionManager for session state awareness

KEY METHODS:
- handle_pygame_events(): Process pygame keyboard events with session state checking
- handle_opencv_key(): Process OpenCV waitKey input with camera controls
- handle_pygame_key(): Direct pygame key processing for cleaner input handling
- cleanup(): Clean shutdown of input resources

INPUT CATEGORIES:
- System: Q/ESC (quit), F11 (quit), H (help display)
- Session: SPACE (simulate button press with session state validation)
- Camera: W(white balance), B(brightness), C(contrast), S(saturation), E(exposure), G(gain)
- Settings: N(noise reduction), R(reset defaults)

ARCHITECTURE:
- Centralizes all keyboard input processing following Single Responsibility
- Integrates with CameraControls for settings management
- Respects session state through SessionManager coordination
- Provides unified interface regardless of display backend (pygame vs OpenCV)
"""

import pygame


class KeyboardInputManager:
    """
    Manages keyboard input and camera controls for photobooth interface.

    Processes user input while respecting session state and providing
    unified interface across different display backends.
    """

    def __init__(self, camera_controls, debug_log, session_manager):
        self.camera_controls = camera_controls
        self.debug_log = debug_log
        self.session_manager = session_manager

    def handle_pygame_events(self, state):
        """Handle pygame keyboard events. Returns True to quit, False to continue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                self.debug_log(
                    "input",
                    f"[PYGAME] Keydown: key={event.key} mods={pygame.key.get_mods()}",
                )
                # System controls
                if event.key in (pygame.K_q, pygame.K_ESCAPE, pygame.K_F11):
                    return True

                # Button simulation
                if event.key == pygame.K_SPACE:
                    self.debug_log("gpio", "⌨️  SPACE KEY pressed (simulating button)")
                    # Check session state before calling callback (same as hardware button)
                    if not self._is_idle_state(state):
                        self.debug_log("gpio", "⌨️  SPACE KEY ignored (session active)")
                    else:
                        start_countdown_callback()
                    continue

                # Camera control shortcuts (only when idle)
                if self._is_idle_state(state):
                    key_char = self._pygame_key_to_char(event.key)
                    if key_char:
                        self.camera_controls.handle_key(ord(key_char))

        return False

    def handle_opencv_key(self, key, state):
        """Handle OpenCV keyboard input. Returns True to quit, False to continue."""
        key = key & 0xFF
        if key == 255:  # No key pressed
            return False

        self.debug_log(
            "input",
            f"[OPENCV] Keypress: key={key} char={chr(key) if 32 <= key <= 126 else None}",
        )

        # System controls
        if key == ord("q"):
            return True

        # Button simulation
        if key == ord(" "):
            self.debug_log("gpio", "⌨️  SPACE KEY pressed (simulating button)")
            # Check session state before calling callback (same as hardware button)
            if not self._is_idle_state(state):
                self.debug_log("gpio", "⌨️  SPACE KEY ignored (session active)")
            else:
                self.session_manager.start_countdown()
            return False

        # Camera control shortcuts (only when idle)
        if self._is_idle_state(state):
            key_char = chr(key) if 32 <= key <= 126 else None
            if key_char:
                self.camera_controls.handle_key(key)

        return False

    def _is_idle_state(self, state):
        """Check if system is in idle state (ready for camera controls)."""
        # Use a single phase string for clarity: 'idle', 'countdown', 'smile', 'gotcha'
        # Accepts either a dict or object with .phase attribute
        phase = None
        if isinstance(state, dict):
            phase = state.get("phase")
        else:
            phase = getattr(state, "phase", None)
        return phase == "idle"

    def _pygame_key_to_char(self, pygame_key):
        """Convert pygame key to character for camera controls."""
        # Get modifier state
        mods = pygame.key.get_pressed()
        shift_pressed = mods[pygame.K_LSHIFT] or mods[pygame.K_RSHIFT]

        # Map pygame keys to characters
        key_map = {
            pygame.K_w: "w",
            pygame.K_b: "B" if shift_pressed else "b",
            pygame.K_c: "C" if shift_pressed else "c",
            pygame.K_s: "S" if shift_pressed else "s",
            pygame.K_e: "E" if shift_pressed else "e",
            pygame.K_g: "G" if shift_pressed else "g",
            pygame.K_n: "n",
            pygame.K_r: "r",
            pygame.K_h: "h",
        }

        return key_map.get(pygame_key)

    def cleanup(self):
        """Clean up keyboard input manager resources."""
        pass

    def run(self, session_manager=None):
        """Main input loop: listens for quit key (OpenCV backend)."""
        import cv2
        import time

        while True:
            key = cv2.waitKey(1)
            # Dummy state and qr_manager for now
            state = (
                session_manager.get_state()
                if session_manager and hasattr(session_manager, "get_state")
                else type(
                    "Dummy", (), {"countdown_active": False, "gotcha_active": False}
                )()
            )

            class DummyQR:
                def is_active(self):
                    return False

            qr_manager = DummyQR()

            def dummy_start():
                pass

            if self.handle_opencv_key(key, state, qr_manager, dummy_start):
                break
            time.sleep(0.01)
