"""
audio_manager.py
Handles sound effects using pygame.mixer.
"""

import pygame


class _Null:
    def play(self):
        pass


class AudioManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.beep = _Null()
        self.shutter = _Null()
        try:
            # Initialize with specific settings to reduce static
            # 44100 Hz, 16-bit, stereo, 1024 buffer
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()

            if self.debug:
                print(f"[AUDIO] Mixer initialized: {pygame.mixer.get_init()}")

            try:
                self.beep = pygame.mixer.Sound("assets/beep.wav")
                self.shutter = pygame.mixer.Sound("assets/shutter.wav")

                if self.debug:
                    print(f"[AUDIO] Beep loaded: {self.beep.get_length():.2f}s")
                    print(f"[AUDIO] Shutter loaded: {self.shutter.get_length():.2f}s")

            except Exception as e:
                print(
                    "[WARN] Audio files not found or could not be loaded, continuing sans sound:",
                    e,
                )
        except Exception as e:
            print("[WARN] Audio mixer init failed; continuing without sounds:", e)

    def play_beep(self):
        self.beep.play()

    def play_shutter(self):
        self.shutter.play()
