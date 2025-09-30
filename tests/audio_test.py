#!/usr/bin/env python3
"""
Test audio system
"""

import pygame
import time
import os

print("Audio Test")
print("=" * 20)

# Check if audio files exist
audio_files = ["assets/beep.wav", "assets/shutter.wav"]
for file in audio_files:
    if os.path.exists(file):
        print(f"✅ {file} exists")
    else:
        print(f"❌ {file} missing")

# Test pygame mixer
try:
    print("\nInitializing pygame mixer...")
    pygame.mixer.init()
    print("✅ Pygame mixer initialized")

    # Test loading sounds
    try:
        beep = pygame.mixer.Sound("assets/beep.wav")
        print("✅ Beep sound loaded")

        shutter = pygame.mixer.Sound("assets/shutter.wav")
        print("✅ Shutter sound loaded")

        # Test playing sounds
        print("\nTesting beep sound...")
        beep.play()
        time.sleep(1)

        print("Testing shutter sound...")
        shutter.play()
        time.sleep(2)

        print("✅ Audio test completed")

    except Exception as e:
        print(f"❌ Sound loading failed: {e}")

except Exception as e:
    print(f"❌ Pygame mixer init failed: {e}")

print("\nDone!")
