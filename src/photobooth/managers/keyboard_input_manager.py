"""
keyboard_input_manager.py
Handles keyboard input for both pygame and OpenCV display modes.
Consolidates camera control shortcuts and system controls.
"""

import pygame


class KeyboardInputManager:
    """Manages keyboard input for both pygame and OpenCV display modes."""

    def __init__(self, camera_controls, debug_log):
        self.camera_controls = camera_controls
        self.debug_log = debug_log

    def handle_pygame_events(self, state, qr_manager, start_countdown_callback):
        """Handle pygame keyboard events. Returns True to quit, False to continue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                # System controls
                if event.key in (pygame.K_q, pygame.K_ESCAPE, pygame.K_F11):
                    return True

                # Button simulation
                if event.key == pygame.K_SPACE:
                    self.debug_log("gpio", "⌨️  SPACE KEY pressed (simulating button)")
                    start_countdown_callback()
                    continue

                # Camera control shortcuts (only when idle)
                if self._is_idle_state(state, qr_manager):
                    key_char = self._pygame_key_to_char(event.key)
                    if key_char:
                        self.camera_controls.handle_key(ord(key_char))

        return False

    def handle_opencv_key(self, key, state, qr_manager, start_countdown_callback):
        """Handle OpenCV keyboard input. Returns True to quit, False to continue."""
        key = key & 0xFF

        # System controls
        if key == ord("q"):
            return True

        # Button simulation
        if key == ord(" "):
            self.debug_log("gpio", "⌨️  SPACE KEY pressed (simulating button)")
            start_countdown_callback()
            return False

        # Camera control shortcuts (only when idle)
        if self._is_idle_state(state, qr_manager):
            key_char = chr(key) if 32 <= key <= 126 else None
            if key_char:
                self.camera_controls.handle_key(key)

        return False

    def _is_idle_state(self, state, qr_manager):
        """Check if system is in idle state (ready for camera controls)."""
        return (
            not state.countdown_active
            and not state.gotcha_active
            and not qr_manager.is_active()
        )

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
