#!/usr/bin/env python3
"""
Test script to verify the new directory structure and imports work correctly.
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)


def test_imports():
    """Test that all imports work correctly."""
    try:
        print("Testing imports...")

        # Test manager imports
        from photobooth.managers.camera_manager import CameraManager
        from photobooth.managers.audio_manager import AudioManager
        from photobooth.managers.countdown_manager import CountdownManager
        from photobooth.managers.gotcha_manager import GotchaManager
        from photobooth.managers.keyboard_input_manager import KeyboardInputManager

        print("✅ Manager imports successful")

        # Test hardware imports
        from photobooth.hardware.gpio_manager import GPIOManager

        print("✅ Hardware imports successful")

        # Test UI imports
        from photobooth.ui.overlay_renderer import OverlayRenderer

        print("✅ UI imports successful")

        # Test utils imports
        from photobooth.utils.photobooth_state import PhotoBoothState

        print("✅ Utils imports successful")

        print("🎉 All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
