"""
InputHandler - Simple input event handling

This class handles:
- Keyboard input detection
- GPIO button input (future)
- Notifying SessionManager of events

Clean separation: InputHandler detects events, SessionManager handles business logic.
"""


class InputHandler:
    """
    Simple input handler that detects events and notifies SessionManager.

    No business logic - just converts input events to SessionManager calls.
    """

    def __init__(self, session_manager):
        self.session_manager = session_manager

    def handle_key_input(self, key_pressed):
        """
        Handle keyboard input and notify SessionManager.

        Args:
            key_pressed: String like 'button', 'quit', 'status', etc.

        Returns:
            bool: True if quit requested, False otherwise
        """
        if key_pressed == "quit":
            print("🛑 InputHandler: Quit requested")
            return True
        elif key_pressed == "button":
            print("🔘 InputHandler: Button press detected - notifying SessionManager")
            self.session_manager.start_countdown()
        elif key_pressed == "status":
            print("📊 InputHandler: Status requested")
            # Could add session_manager.get_status() method later

        return False

    def handle_gpio_button(self):
        """
        Handle GPIO button press (future implementation).
        """
        print("🔘 InputHandler: GPIO button press - notifying SessionManager")
        self.session_manager.start_countdown()
