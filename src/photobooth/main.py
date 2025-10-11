import os
import sys
import argparse
import json
import logging
import threading
import time
import platform

from photobooth.managers.session_manager import SessionManager
from photobooth.managers.camera_manager import CameraManager
from photobooth.hardware.gpio_manager import GPIOManager
from photobooth.managers.audio_manager import AudioManager
from photobooth.ui.overlay_renderer import OverlayRenderer
from photobooth.ui.video_renderer import VideoRenderer
from photobooth.ui.camera_controls import CameraControls
from photobooth.ui.settings_overlay import SettingsOverlay
from photobooth.input.input_handler import InputHandler
from photobooth.managers.video_manager import VideoManager
from photobooth.managers.photo_capture_manager import PhotoCaptureManager
from photobooth.ui.display_manager import DisplayManager


def main():
    from photobooth.managers.keyboard_input_manager import KeyboardInputManager

    """Main PhotoBooth application entry point"""

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler("photobooth.log", mode="w"),
            logging.StreamHandler(),
        ],
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PhotoBooth Application")
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration JSON file",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug output"
    )
    parser.add_argument(
        "--windowed",
        "-w",
        action="store_true",
        help="Run in windowed mode (not fullscreen)",
    )
    args = parser.parse_args(sys.argv[1:] if __name__ == "__main__" else sys.argv[1:])

    # Load configuration
    from photobooth.managers.config_manager import ConfigManager

    config_manager = ConfigManager(args.config)
    config = config_manager.config

    gpio_manager = GPIOManager(config)

    # Initialize managers and UI components
    camera_manager = CameraManager(config)
    settings_overlay = SettingsOverlay(3.0)
    camera_controls = CameraControls(
        DisplayManager, config.get("LIGHTING_CONFIG", {}), settings_overlay
    )

    overlay_renderer = OverlayRenderer(config)

    session_manager = SessionManager(config)

    video_renderer = VideoRenderer(
        DisplayManager, camera_manager, overlay_renderer, config
    )
    audio_manager = AudioManager(config)

    input_handler = InputHandler(session_manager)
    video_manager = VideoManager(config)

    photo_capture_manager = PhotoCaptureManager(config)

    # Instantiate KeyboardInputManager
    keyboard_input_manager = KeyboardInputManager(
        camera_controls, print, session_manager
    )
    display_manager = DisplayManager(
        config,
        camera_manager,
        overlay_renderer,
        session_manager,
        keyboard_input_manager,
    )

    import traceback

    try:
        display_manager.run()
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")
        logging.info("PhotoBooth interrupted by user.")
    except Exception as e:
        print(f"[ERROR] Unhandled exception: {e}")
        logging.exception("Unhandled exception in PhotoBooth main loop:")
        traceback.print_exc()
    finally:
        try:
            display_manager.cleanup()
        except Exception as e:
            logging.warning(f"Error during display_manager cleanup: {e}")
        try:
            camera_manager.release()
        except Exception as e:
            logging.warning(f"Error during camera_manager cleanup: {e}")
        try:
            gpio_manager.cleanup()
        except Exception as e:
            logging.warning(f"Error during gpio_manager cleanup: {e}")
        # Add any other cleanup as needed
        print("PhotoBooth exited cleanly.")


def _main_loop():
    """try:
        print("Starting PhotoBooth...")
        while True:
            key = video_renderer.render_frame()
            if key == "q":
                print("Quitting PhotoBooth...")
                break
            elif key == " ":
                camera_controls.handle_button_press("capture")

            # Update settings overlay if active
            if display_state.get_current_state() == "settings":
                settings_overlay.render()

            time.sleep(0.01)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")

    finally:
        # Cleanup resources
        camera_manager.cleanup()
        gpio_manager.cleanup()
        cv2.destroyAllWindows()"""

    print("PhotoBooth exited cleanly.")


if __name__ == "__main__":
    main()
