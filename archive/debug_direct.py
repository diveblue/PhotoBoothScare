#!/usr/bin/env python3
"""
Debug entry point - goes directly to ActionHandler setup
"""

import sys
import os
import json

# Add src directory to Python path for imports  
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    # Import all the pieces we need
    from photobooth.action_handler import ActionHandler, debug_log
    from photobooth.managers.session_manager import SessionManager
    from photobooth.ui.overlay_renderer import OverlayRenderer
    from photobooth.managers.camera_manager import CameraManager
    from photobooth.managers.video_manager import VideoManager
    from photobooth.managers.audio_manager import AudioManager
    from photobooth.hardware.gpio_manager import GPIOManager
    from photobooth.managers.photo_capture_manager import PhotoCaptureManager

    # Load config
    with open("config.json", "r") as f:
        CONFIG = json.load(f)

    print("🔧 DEBUG: Starting direct initialization...")

    # Initialize core components with minimal setup
    try:
        # These are the critical ones - initialize with simple defaults
        camera = CameraManager(
            CONFIG.get("CAM_RESOLUTION_HIGH", [1280, 720]), 
            CONFIG.get("TEST_VIDEO_PATH", "assets/test_video.mp4"),
            CONFIG.get("USE_WEBCAM", True), 
            {}  # lighting config
        )
        print("✅ Camera manager initialized")

        gpio = GPIOManager(
            CONFIG.get("BUTTON_PIN", 18), 
            CONFIG.get("RELAY_PIN", 27), 
            debug_log
        )
        print("✅ GPIO manager initialized")

        audio = AudioManager(debug=False)
        print("✅ Audio manager initialized")

        overlay = OverlayRenderer(
            CONFIG.get("FONT_PATH", "assets/Creepster-Regular.ttf"),
            CONFIG.get("FONT_SIZE", 72),
            CONFIG.get("OVERLAY_GOTCHA_TEXT", "GOTCHA!"),
            CONFIG.get("OVERLAY_IDLE_TEXT", "Press button to take photos")
        )
        print("✅ Overlay renderer initialized")

        video_manager = VideoManager(CONFIG, debug_log)
        print("✅ Video manager initialized")

        photo_manager = PhotoCaptureManager(CONFIG, debug_log)
        print("✅ Photo manager initialized")

        session_manager = SessionManager(CONFIG, debug_log)
        print("✅ Session manager initialized")

        # Create action handler - THIS IS WHERE YOU WANT TO DEBUG
        action_handler = ActionHandler(
            session_manager=session_manager,
            overlay_renderer=overlay,
            camera_manager=camera,
            video_manager=video_manager,
            audio_manager=audio,
            gpio_manager=gpio,
            photo_manager=photo_manager,
        )
        print("✅ ActionHandler created - STARTING MAIN LOOP")

        # SET YOUR BREAKPOINT HERE OR IN ActionHandler.run_main_loop()
        action_handler.run_main_loop()

    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        raise