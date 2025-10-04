"""
SessionAction - Command Pattern for Session Operations

RESPONSIBILITIES:
- Encapsulates all possible actions that SessionManager can request from main.py
- Maintains SOLID separation: SessionManager decides what to do, main.py executes it
- Provides structured communication between session orchestration and execution layers
- Acts as contract defining all possible photobooth operations

ACTION CATEGORIES:
- Video: start_video, stop_video with dimensions and session metadata
- Audio: play_beep (countdown), play_shutter (photo capture)
- GPIO: trigger_scare (relay activation for props)
- Display: show_countdown, show_smile, show_gotcha, show_qr with parameters
- Photo: capture_photo with session timing information
- File: move_files, cleanup_session for resource management
- Session: session_complete flag for state transitions

ARCHITECTURE:
- Command Pattern implementation for loose coupling
- Immutable data structure passed from SessionManager to main.py
- Clear separation of concerns: decision-making vs execution
- Enables testing of SessionManager logic without hardware dependencies
"""


class SessionAction:
    """
    Command object that encapsulates actions for main.py to execute.

    Maintains SOLID principle separation where SessionManager makes decisions
    and returns this action object telling main.py exactly what to do.
    """

    def __init__(self):
        # Video actions
        self.start_video = False
        self.stop_video = False
        self.video_dimensions = None

        # Coordinated actions (better than individual flags)
        self.countdown_update = (
            None  # {'number': 3, 'play_beep': True, 'show_display': True}
        )
        self.smile_action = (
            None  # {'show_display': True, 'play_shutter': True, 'capture_photo': True}
        )
        self.gotcha_action = None  # {'show_display': True, 'duration': 10.0}

        # Legacy individual actions (for backward compatibility)
        self.play_beep = False
        self.play_shutter = False
        self.trigger_scare = False
        self.show_countdown = False
        self.countdown_number = None
        self.show_smile = False
        self.show_gotcha = False
        self.show_qr = False
        self.qr_url = None

        # Photo actions
        self.capture_photo = False

        # File management
        self.move_files = False
        self.cleanup_session = False

        # Session control
        self.session_complete = False
        self.session_id = None
        self.session_time = None

    def __repr__(self):
        active_actions = []
        for attr, value in self.__dict__.items():
            if value and not attr.startswith("_"):
                active_actions.append(f"{attr}={value}")
        return f"SessionAction({', '.join(active_actions)})"
