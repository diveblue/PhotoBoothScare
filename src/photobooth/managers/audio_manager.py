"""
AudioManager - Sound Effects and Audio Playback

RESPONSIBILITIES:
- Manages audio initialization using pygame.mixer for cross-platform compatibility
- Loads and plays sound effects (beep.wav for countdown, shutter.wav for photos)
- Provides graceful fallback when audio hardware/files are unavailable
- Handles audio system configuration for optimal playback quality

KEY METHODS:
- play_beep(): Play countdown beep sound effect
- play_shutter(): Play camera shutter sound effect
- cleanup(): Clean shutdown of audio resources

AUDIO CONFIGURATION:
- 44100 Hz frequency for high quality playback
- 16-bit stereo audio with 1024 sample buffer
- Loads from assets/ directory with error handling

ARCHITECTURE:
- Self-contained audio management following Single Responsibility
- Null object pattern for graceful degradation when audio unavailable
- Cross-platform compatibility through pygame.mixer abstraction
- Designed for Raspberry Pi audio output and desktop development
"""

import pygame


class _Null:
    """Null object pattern for graceful audio fallback when sounds unavailable."""

    def play(self):
        pass


class AudioManager:
    """
    Manages audio playback for photobooth sound effects.

    Provides countdown beeps and shutter sounds with graceful fallback
    when audio hardware or sound files are not available.
    """

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
