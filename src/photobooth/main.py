"""""""""

PhotoBooth Main - Application startup and dependency injection

PhotoBooth Main - Application startup and dependency injectionPhotoBooth Main - Application startup and dependency injection

This is the main entry point that creates all managers and shared objects.

Goal: Replace ActionHandler's setup_and_run() and move toward clean separation.

"""

This is the main entry point that creates all managers and shared objects.This is the main entry point that creates all managers and shared objects.

import os

import statGoal: Replace ActionHandler's setup_and_run() and move toward clean separation.Goal: Replace ActionHandler's setup_and_run() and move toward clean separation.

import json

import argparse""""""

import sys

import platform



from photobooth.utils.thread_safe_display_state import ThreadSafeDisplayStateimport osim    except KeyboardInterrupt:

from photobooth.managers.session_manager import SessionManager

from photobooth.managers.camera_manager import CameraManagerimport stat        print("🛑 Interrupted by user")

from photobooth.hardware.gpio_manager import GPIOManager

from photobooth.managers.audio_manager import AudioManagerimport json    finally:

from photobooth.ui.overlay_renderer import OverlayRenderer

from photobooth.managers.video_manager import VideoManagerimport argparse        print("🔧 Shutting down...")

from photobooth.managers.photo_capture_manager import PhotoCaptureManager

from photobooth.ui.video_renderer import VideoRendererimport sys        shutdown_event.set()

from photobooth.ui.camera_controls import CameraControls

from photobooth.ui.settings_overlay import SettingsOverlayimport platform        video_renderer.cleanup()



import time        print("🔧 Cleanup complete")stat

def debug_log(category, message):

    """Simple debug logging function"""import json

    print(f"[{category.upper()}] {message}")

from photobooth.utils.thread_safe_display_state import ThreadSafeDisplayStateimport argparse



def check_user_and_permissions():from photobooth.managers.session_manager import SessionManagerimport sys

    """Check if we're running as expected user and have necessary permissions."""

from photobooth.managers.camera_manager import CameraManagerimport platform

    if platform.system() == "Linux":

        import pwdfrom photobooth.hardware.gpio_manager import GPIOManagerimport time



        # Get current user infofrom photobooth.managers.audio_manager import AudioManager

        current_user = pwd.getpwuid(os.getuid()).pw_name

from photobooth.ui.overlay_renderer import OverlayRendererfrom photobooth.utils.thread_safe_display_state import ThreadSafeDisplayState

        # Only enforce user check on Raspberry Pi (has /boot/config.txt)

        if os.path.exists("/boot/config.txt"):from photobooth.managers.video_manager import VideoManagerfrom photobooth.managers.session_manager import SessionManager

            expected_users = ["pi", "scott"]

            if current_user not in expected_users:from photobooth.managers.photo_capture_manager import PhotoCaptureManagerfrom photobooth.managers.camera_manager import CameraManager

                print(

                    f"⚠️ Running as '{current_user}'. Expected: {expected_users}. May encounter permission issues."from photobooth.ui.video_renderer import VideoRendererfrom photobooth.hardware.gpio_manager import GPIOManager

                )

from photobooth.ui.camera_controls import CameraControlsfrom photobooth.managers.audio_manager import AudioManager

        # Check XDG_RUNTIME_DIR for audio/video access

        uid = os.getuid()from photobooth.ui.settings_overlay import SettingsOverlayfrom photobooth.ui.overlay_renderer import OverlayRenderer

        default_runtime = f"/run/user/{uid}"

        xr = os.environ.get("XDG_RUNTIME_DIR", default_runtime)from photobooth.managers.video_manager import VideoManager



        if not os.path.exists(xr):from photobooth.managers.photo_capture_manager import PhotoCaptureManager

            print(f"⚠️ {xr} doesn't exist. Creating it...")

            try:def debug_log(category, message):from photobooth.ui.video_renderer import VideoRenderer

                os.makedirs(xr, mode=0o700)

                os.chown(xr, uid, -1)    """Simple debug logging function"""from photobooth.ui.camera_controls import CameraControls

                os.environ["XDG_RUNTIME_DIR"] = xr

                print(f"✅ Created {xr}")    print(f"[{category.upper()}] {message}")from photobooth.ui.settings_overlay import SettingsOverlay

            except Exception as e:

                print(f"❌ Failed to create {xr}: {e}")

        else:

            # Ensure correct permissions

            try:

                current_stat = os.stat(xr)def check_user_and_permissions():def debug_log(category, message):

                expected_mode = stat.S_IMODE(current_stat.st_mode)

                if expected_mode != 0o700:    """Check if we're running as expected user and have necessary permissions."""    """Simple debug logging function"""

                    os.chmod(xr, 0o700)

                    os.chown(xr, uid, -1)    print(f"[{category.upper()}] {message}")

                    print(f"🔧 Fixed permissions on {xr}")

            except Exception as e:    if platform.system() == "Linux":

                print(f"⚠️ Permission check failed for {xr}: {e}")

        import pwd



def main():def load_config():

    # Parse command-line arguments

    parser = argparse.ArgumentParser(description="PhotoBooth Application")        # Get current user info    """Load configuration from config.json"""

    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")

    parser.add_argument(        current_user = pwd.getpwuid(os.getuid()).pw_name    with open("config.json", "r") as f:

        "--windowed", "-w", action="store_true", help="Run in windowed mode"

    )        return json.load(f)

    args = parser.parse_args()

        # Only enforce user check on Raspberry Pi (has /boot/config.txt)

    # Check system permissions

    check_user_and_permissions()        if os.path.exists("/boot/config.txt"):



    print("🚀 PhotoBooth starting up...")            expected_users = ["pi", "scott"]def setup_linux_runtime():



    # Load configuration            if current_user not in expected_users:    """Fix XDG runtime dir permissions on Linux"""

    try:

        with open("config.json", "r") as f:                print(    if platform.system() != "Linux":

            config = json.load(f)

        print("✅ Configuration loaded")                    f"⚠️ Running as '{current_user}'. Expected: {expected_users}. May encounter permission issues."        return

    except FileNotFoundError:

        print("❌ config.json not found")                )

        sys.exit(1)

    except json.JSONDecodeError as e:    try:

        print(f"❌ Invalid JSON in config.json: {e}")

        sys.exit(1)        # Check XDG_RUNTIME_DIR for audio/video access        uid = os.getuid()



    # Create shared objects        uid = os.getuid()        default_runtime = f"/run/user/{uid}"

    print("🔧 Creating shared objects...")

    try:        default_runtime = f"/run/user/{uid}"        xr = os.environ.get("XDG_RUNTIME_DIR", default_runtime)

        display_state = ThreadSafeDisplayState()

        print("✅ ThreadSafeDisplayState created")        xr = os.environ.get("XDG_RUNTIME_DIR", default_runtime)



        session_manager = SessionManager(        # Ensure dir exists

            config, debug_log, display_state=display_state

        )        if not os.path.exists(xr):        if not os.path.isdir(xr):

        print("✅ SessionManager created with shared state")

    except Exception as e:            print(f"⚠️ {xr} doesn't exist. Creating it...")            try:

        print(f"❌ Shared object creation failed: {e}")

        raise            try:                os.makedirs(xr, exist_ok=True)



    # Initialize all managers                os.makedirs(xr, mode=0o700)            except Exception:

    print("🔧 Initializing managers...")

    try:                os.chown(xr, uid, -1)                xr = f"/tmp/runtime-{uid}"

        lighting_config = config.get("LIGHTING_CONFIG", {})

        camera = CameraManager(                os.environ["XDG_RUNTIME_DIR"] = xr                os.makedirs(xr, exist_ok=True)

            config["CAM_RESOLUTION"],

            config.get("TEST_VIDEO_PATH", 0),                print(f"✅ Created {xr}")                os.environ["XDG_RUNTIME_DIR"] = xr

            config.get("USE_WEBCAM", True),

            lighting_config,            except Exception as e:

        )

        print("✅ Camera manager initialized")                print(f"❌ Failed to create {xr}: {e}")        # Ensure 0700 perms



        gpio = GPIOManager(config["BUTTON_PIN"], config["RELAY_PIN"], debug_log)        else:        st = os.stat(xr)

        print("✅ GPIO manager initialized")

            # Ensure correct permissions        mode = stat.S_IMODE(st.st_mode)

        audio = AudioManager(debug=args.debug or config.get("DEBUG_AUDIO", False))

        print("✅ Audio manager initialized")            try:        if mode != 0o700:



        overlay = OverlayRenderer(                current_stat = os.stat(xr)            try:

            config["FONT_PATH"],

            config["FONT_SIZE"],                expected_mode = stat.S_IMODE(current_stat.st_mode)                os.chmod(xr, 0o700)

            config["OVERLAY_GOTCHA_TEXT"],

            config["OVERLAY_IDLE_TEXT"],                if expected_mode != 0o700:            except Exception:

        )

        print("✅ Overlay renderer initialized")                    os.chmod(xr, 0o700)                pass



        video_manager = VideoManager(config, debug_log)                    os.chown(xr, uid, -1)

        print("✅ Video manager initialized")

                    print(f"🔧 Fixed permissions on {xr}")        # Ensure ownership

        photo_manager = PhotoCaptureManager(config, debug_log)

        print("✅ Photo manager initialized")            except Exception as e:        try:



        # Camera control components                print(f"⚠️ Permission check failed for {xr}: {e}")            if st.st_uid != uid:

        settings_overlay = SettingsOverlay()

        camera_controls = CameraControls(camera, lighting_config, settings_overlay)                os.chown(xr, uid, -1)

        print("✅ Camera controls initialized")

        except Exception:

    except Exception as e:

        print(f"❌ Manager initialization failed: {e}")def main():            pass

        raise

    # Parse command-line arguments    except Exception:

    # Create VideoRenderer with shared state

    print("🔧 Creating VideoRenderer...")    parser = argparse.ArgumentParser(description="PhotoBooth Application")        pass

    try:

        video_renderer = VideoRenderer(    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")

            display_state=display_state,

            camera_manager=camera,    parser.add_argument(

            overlay_renderer=overlay,

            config=config,        "--windowed", "-w", action="store_true", help="Run in windowed mode"def main():

            camera_controls=camera_controls,

            settings_overlay=settings_overlay,    )    """Main application entry point - creates all objects and starts the application"""

        )

        print("✅ VideoRenderer created")    args = parser.parse_args()    print("🚀 PhotoBooth starting up...")

    except Exception as e:

        print(f"❌ VideoRenderer creation failed: {e}")

        raise

    # Check system permissions    # Parse arguments

    print("🎮 Starting application with threaded VideoRenderer...")

    check_user_and_permissions()    parser = argparse.ArgumentParser(description="PhotoBooth Scare Application")

    # Start VideoRenderer in its own thread

    import threading    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")



    try:    print("🚀 PhotoBooth starting up...")    parser.add_argument(

        # Start video rendering thread

        print("🎬 Starting video rendering thread...")        "--windowed", "-w", action="store_true", help="Run in windowed mode"

        video_thread = threading.Thread(

            target=video_renderer.run_continuous_loop, name="VideoRenderer"    # Load configuration    )

        )

        video_thread.daemon = True  # Thread will exit when main program exits    try:    args = parser.parse_args()

        video_thread.start()

        print("✅ Video thread started")        with open("config.json", "r") as f:



        # Main thread just waits (for now - will handle countdown logic later)            config = json.load(f)    # Load configuration

        print("⏳ Main thread waiting... Press Ctrl+C to quit")

        while True:        print("✅ Configuration loaded")    config = load_config()

            import time

            time.sleep(1)  # Sleep 1 second between checks    except FileNotFoundError:



    except KeyboardInterrupt:        print("❌ config.json not found")    # Setup Linux runtime

        print("🛑 Interrupted by user")

    finally:        sys.exit(1)    setup_linux_runtime()

        print("🔧 Shutting down...")

        video_renderer.cleanup()    except json.JSONDecodeError as e:

        print("🔧 Cleanup complete")

        print(f"❌ Invalid JSON in config.json: {e}")    # Extract config values



if __name__ == "__main__":        sys.exit(1)    cam_resolution = tuple(config["CAM_RESOLUTION_HIGH"])

    main()
    lighting_mode = config.get("LIGHTING_MODE", "TESTING")

    # Create shared objects    camera_settings = config.get("CAMERA_SETTINGS", {})

    print("🔧 Creating shared objects...")    lighting_config = camera_settings.get(lighting_mode, {})

    try:    lighting_config["_mode"] = lighting_mode

        display_state = ThreadSafeDisplayState()

        print("✅ ThreadSafeDisplayState created")    print("🔧 Creating shared objects...")



        session_manager = SessionManager(    # Create thread-safe shared state (STEP 1 of our refactoring)

            config, debug_log, display_state=display_state    display_state = ThreadSafeDisplayState()

        )    print("✅ ThreadSafeDisplayState created")

        print("✅ SessionManager created with shared state")

    except Exception as e:    # Create session manager with shared state (STEP 2 of our refactoring)

        print(f"❌ Shared object creation failed: {e}")    session_manager = SessionManager(config, debug_log, display_state)

        raise    print("✅ SessionManager created with shared state")



    # Initialize all managers    print("🔧 Initializing managers...")

    print("🔧 Initializing managers...")

    try:    # Create all managers

        lighting_config = config.get("LIGHTING_CONFIG", {})    try:

        camera = CameraManager(        camera = CameraManager(

            config["CAM_RESOLUTION"],            cam_resolution,

            config.get("TEST_VIDEO_PATH", 0),            config["TEST_VIDEO_PATH"],

            config.get("USE_WEBCAM", True),            config["USE_WEBCAM"],

            lighting_config,            lighting_config,

        )        )

        print("✅ Camera manager initialized")        print("✅ Camera manager initialized")



        gpio = GPIOManager(config["BUTTON_PIN"], config["RELAY_PIN"], debug_log)        gpio = GPIOManager(config["BUTTON_PIN"], config["RELAY_PIN"], debug_log)

        print("✅ GPIO manager initialized")        print("✅ GPIO manager initialized")



        audio = AudioManager(debug=args.debug or config.get("DEBUG_AUDIO", False))        audio = AudioManager(debug=args.debug or config.get("DEBUG_AUDIO", False))

        print("✅ Audio manager initialized")        print("✅ Audio manager initialized")



        overlay = OverlayRenderer(        overlay = OverlayRenderer(

            config["FONT_PATH"],            config["FONT_PATH"],

            config["FONT_SIZE"],            config["FONT_SIZE"],

            config["OVERLAY_GOTCHA_TEXT"],            config["OVERLAY_GOTCHA_TEXT"],

            config["OVERLAY_IDLE_TEXT"],            config["OVERLAY_IDLE_TEXT"],

        )        )

        print("✅ Overlay renderer initialized")        print("✅ Overlay renderer initialized")



        video_manager = VideoManager(config, debug_log)        video_manager = VideoManager(config, debug_log)

        print("✅ Video manager initialized")        print("✅ Video manager initialized")



        photo_manager = PhotoCaptureManager(config, debug_log)        photo_manager = PhotoCaptureManager(config, debug_log)

        print("✅ Photo manager initialized")        print("✅ Photo manager initialized")



        # Camera control components        # Camera control components

        settings_overlay = SettingsOverlay()        settings_overlay = SettingsOverlay()

        camera_controls = CameraControls(camera, lighting_config, settings_overlay)        camera_controls = CameraControls(camera, lighting_config, settings_overlay)

        print("✅ Camera controls initialized")        print("✅ Camera controls initialized")

        

    except Exception as e:        # Show camera controls help

        print(f"❌ Manager initialization failed: {e}")        print("\n🎛️ Camera Controls Available:")

        raise        camera_controls.print_controls_help()



    # Create VideoRenderer with shared state    except Exception as e:

    print("🔧 Creating VideoRenderer...")        print(f"❌ Manager initialization failed: {e}")

    try:        raise

        video_renderer = VideoRenderer(

            display_state=display_state,    # Create VideoRenderer with shared state

            camera_manager=camera,    print("🔧 Creating VideoRenderer...")

            overlay_renderer=overlay,    try:

            config=config,        video_renderer = VideoRenderer(

            camera_controls=camera_controls,            display_state=display_state,

            settings_overlay=settings_overlay,            camera_manager=camera,

        )            overlay_renderer=overlay,

        print("✅ VideoRenderer created")            config=config,

    except Exception as e:            camera_controls=camera_controls,

        print(f"❌ VideoRenderer creation failed: {e}")            settings_overlay=settings_overlay,

        raise        )

        print("✅ VideoRenderer created")

    print("🎮 Starting application with threaded VideoRenderer...")    except Exception as e:

        print(f"❌ VideoRenderer creation failed: {e}")

    # Start VideoRenderer in its own thread        raise

    import threading

    print("🎮 Starting application with threaded VideoRenderer...")

    # Create a flag to coordinate shutdown

    shutdown_event = threading.Event()    # Start VideoRenderer in its own thread

    import threading

    try:

        # Start video rendering thread    # Create a flag to coordinate shutdown

        print("🎬 Starting video rendering thread...")    shutdown_event = threading.Event()

        video_thread = threading.Thread(

            target=video_renderer.run_continuous_loop, name="VideoRenderer"    try:

        )        # Start video rendering thread

        video_thread.daemon = True  # Thread will exit when main program exits        print("🎬 Starting video rendering thread...")

        video_thread.start()        video_thread = threading.Thread(

        print("✅ Video thread started")            target=video_renderer.run_continuous_loop, name="VideoRenderer"

        )

        # Main thread just waits (for now - will handle countdown logic later)        video_thread.daemon = True  # Thread will exit when main program exits

        print("⏳ Main thread waiting... Press Ctrl+C to quit")        video_thread.start()

        while not shutdown_event.is_set():        print("✅ Video thread started")

            threading.Event().wait(1)  # Sleep 1 second between checks

        # Main thread handles session timing and user input

    except KeyboardInterrupt:        print("⏳ Main thread handling session logic... Press Ctrl+C to quit")

        print("🛑 Interrupted by user")        last_update = time.time()

    finally:        

        print("🔧 Shutting down...")        while not shutdown_event.is_set():

        shutdown_event.set()            try:

        video_renderer.cleanup()                now = time.time()

        print("🔧 Cleanup complete")                

                # Update session manager (handles countdown timing and state transitions)

                height, width = 720, 1280  # Default dimensions

if __name__ == "__main__":                action = session_manager.update(

    main()                    now=now,
                    frame_dimensions=(width, height),
                    video_recording=False,  # TODO: Connect video manager
                    video_finalized=False,
                )
                
                # Handle countdown updates (beeps and timing)
                if session_manager.state.countdown_active:
                    countdown_result = session_manager.update_countdown(now, audio, gpio)
                    if countdown_result == "gotcha":
                        print("🎭 Starting gotcha phase...")
                        session_manager.trigger_gotcha(now)
                    elif isinstance(countdown_result, int):
                        # Update display with countdown number
                        display_state.update_countdown(countdown_result)
                        print(f"⏰ Countdown: {countdown_result}")
                
                # Check for quit request from video renderer
                # Note: VideoRenderer runs in its own thread, but we can't easily get
                # key presses from it to main thread without additional complexity.
                # For now, we'll add button handling in next iteration.
                
                time.sleep(0.1)  # 10 FPS update rate for session logic
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                break

    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    finally:
        print("🔧 Shutting down...")
        shutdown_event.set()
        video_renderer.cleanup()
        print("🔧 Cleanup complete")

    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
    finally:
        print("� Shutting down...")
        shutdown_event.set()
        video_renderer.cleanup()
        print("🔧 Cleanup complete")


if __name__ == "__main__":
    main()
