"""
audio_manager.py
Handles sound effects using pygame.mixer.
"""

import pygame


class _Null:
    def play(self):
        pass


class AudioManager:
    def __init__(self):
        self.beep = _Null()
        self.shutter = _Null()
        try:
            pygame.mixer.init()
            try:
                self.beep = pygame.mixer.Sound("assets/beep.wav")
                self.shutter = pygame.mixer.Sound("assets/shutter.wav")
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
