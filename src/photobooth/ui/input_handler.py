"""
InputHandler - Pure input event processing

This class handles:
- Keyboard input detection (spacebar, quit keys, etc.)
- GPIO button events (when connected)
- Converting input events to SessionManager method calls
- No business logic - just translates events to actions

This is extracted from ActionHandler/main.py to create clean separation.
"""

import time
from typing import Optional, Callable


class InputHandler:
    """
    Pure input handling class that converts events to SessionManager calls.

    No business logic - just translates user input to session manager methods.
    """

    def __init__(self, session_manager, gpio_manager=None):
        self.session_manager = session_manager
        self.gpio_manager = gpio_manager

        # Debouncing for button presses
        self.last_button_time = 0
        self.button_debounce_seconds = 2.0

        # Set up GPIO callback if available
        if self.gpio_manager:
            self.gpio_manager.add_event_detect(self._on_gpio_button_press)

    def handle_key_event(self, key_pressed: str) -> bool:
        """
        Handle a key event from VideoRenderer.

        Args:
            key_pressed: The key that was pressed ('button', 'quit', 'status', etc.)

        Returns:
            bool: True if should quit application, False otherwise
        """
        if key_pressed == "quit":
            print("🛑 InputHandler: Quit requested")
            return True

        elif key_pressed == "button":
            print("🔘 InputHandler: Button press detected (SPACE key)")
            self._handle_button_press()

        elif key_pressed == "status":
            print("📊 InputHandler: Status requested")
            self._handle_status_request()

        return False

    def _handle_button_press(self):
        """Handle button press event with debouncing"""
        current_time = time.time()

        # Debounce button presses
        if current_time - self.last_button_time < self.button_debounce_seconds:
            print(
                f"🔘 InputHandler: Button debounced (too soon: {current_time - self.last_button_time:.1f}s)"
            )
            return

        # Check if system is ready for new session
        if not self.session_manager.is_idle():
            print("🔘 InputHandler: Button ignored (session already active)")
            return

        self.last_button_time = current_time
        print("🔘 InputHandler: Starting countdown via SessionManager")
        self.session_manager.start_countdown()

    def _handle_status_request(self):
        """Handle status request"""
        try:
            # Get status from session manager's display state
            if hasattr(self.session_manager, "display_state"):
                status = self.session_manager.display_state.debug_state()
                print(f"📊 Current Status: {status}")
            else:
                print("📊 Status: SessionManager has no display_state")
        except Exception as e:
            print(f"📊 Status error: {e}")

    def _on_gpio_button_press(self, channel):
        """GPIO callback for hardware button press"""
        print(f"🔘 InputHandler: GPIO button pressed (pin {channel})")
        self._handle_button_press()

    def cleanup(self):
        """Clean up resources"""
        if self.gpio_manager and hasattr(self.gpio_manager, "cleanup"):
            self.gpio_manager.cleanup()
        print("🔧 InputHandler: Cleanup complete")
