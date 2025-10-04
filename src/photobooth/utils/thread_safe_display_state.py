"""
ThreadSafeDisplayState - Thread-safe communication between Main and Video threads

This class provides thread-safe state sharing between:
- Main Thread: Updates display state based on session events
- Video Thread: Reads current state for overlay rendering

Similar to .NET's thread-safe properties with lock() statements.
"""

import threading
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class DisplayState:
    """Current display state data - what the video thread needs to render"""

    phase: str = "idle"  # "idle", "countdown", "smile", "gotcha", "qr"
    countdown_number: Optional[int] = None  # 3, 2, 1 for countdown display
    gotcha_active: bool = False
    qr_data: Optional[str] = None
    session_id: Optional[str] = None


class ThreadSafeDisplayState:
    """
    Thread-safe wrapper for display state communication.

    Main Thread calls update_* methods to set state.
    Video Thread calls get_* methods to read current state.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state = DisplayState()

    # ========== MAIN THREAD METHODS (Setters) ==========

    def update_phase(self, phase: str):
        """Update the current display phase"""
        with self._lock:
            self._state.phase = phase

    def update_countdown(self, number: Optional[int]):
        """Update countdown number (3, 2, 1, or None)"""
        with self._lock:
            self._state.countdown_number = number

    def update_gotcha(self, active: bool):
        """Update gotcha activation state"""
        with self._lock:
            self._state.gotcha_active = active

    def update_qr(self, qr_data: Optional[str]):
        """Update QR code data to display"""
        with self._lock:
            self._state.qr_data = qr_data

    def update_session(self, session_id: Optional[str]):
        """Update current session ID"""
        with self._lock:
            self._state.session_id = session_id

    def update_all(
        self,
        phase: str = None,
        countdown: int = None,
        gotcha: bool = None,
        qr_data: str = None,
        session_id: str = None,
    ):
        """Update multiple state values atomically"""
        with self._lock:
            if phase is not None:
                self._state.phase = phase
            if countdown is not None:
                self._state.countdown_number = countdown
            if gotcha is not None:
                self._state.gotcha_active = gotcha
            if qr_data is not None:
                self._state.qr_data = qr_data
            if session_id is not None:
                self._state.session_id = session_id

    # ========== VIDEO THREAD METHODS (Getters) ==========

    def get_current_state(self) -> DisplayState:
        """Get a snapshot of current display state (thread-safe copy)"""
        with self._lock:
            # Return a copy so video thread can use it without holding lock
            return DisplayState(
                phase=self._state.phase,
                countdown_number=self._state.countdown_number,
                gotcha_active=self._state.gotcha_active,
                qr_data=self._state.qr_data,
                session_id=self._state.session_id,
            )

    def get_phase(self) -> str:
        """Get current phase"""
        with self._lock:
            return self._state.phase

    def get_countdown(self) -> Optional[int]:
        """Get current countdown number"""
        with self._lock:
            return self._state.countdown_number

    # ========== UTILITY METHODS ==========

    def is_idle(self) -> bool:
        """Check if system is in idle state"""
        with self._lock:
            return self._state.phase == "idle"

    def debug_state(self) -> Dict[str, Any]:
        """Get current state for debugging (thread-safe)"""
        with self._lock:
            return {
                "phase": self._state.phase,
                "countdown_number": self._state.countdown_number,
                "gotcha_active": self._state.gotcha_active,
                "has_qr_data": self._state.qr_data is not None,
                "session_id": self._state.session_id,
            }
