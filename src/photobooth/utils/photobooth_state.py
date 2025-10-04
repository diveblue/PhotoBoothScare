"""
photobooth_state.py
Encapsulates all state for the photo booth session.
"""

import time


class PhotoBoothState:
    def __init__(self):
        self.countdown_active = False
        self.count_end_time = 0.0
        self.gotcha_active = False
        self.gotcha_end_time = 0.0
        self.session_time = None
        self.session_id = None
        self.countdown_number = None
        self.phase = None  # "smile", "gotcha", etc.
        self.qr_url = None  # QR URL for gotcha overlay integration

    def start_countdown(self, countdown_seconds):
        import random
        from datetime import datetime

        self.session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_id = f"S{random.randint(100, 999)}"
        self.countdown_active = True
        self.gotcha_active = False
        self.count_end_time = time.time() + countdown_seconds
        self.countdown_number = None

    def end_countdown(self):
        self.countdown_active = False
        self.countdown_number = None

    def trigger_gotcha(self, duration=10):
        self.gotcha_active = True
        self.gotcha_end_time = time.time() + duration

    def end_gotcha(self):
        self.gotcha_active = False
        self.gotcha_end_time = 0.0
