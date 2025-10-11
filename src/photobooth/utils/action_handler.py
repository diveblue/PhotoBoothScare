# DEPRECATED: This module is obsolete under the new PhotoBooth architecture (2025-10-08).
# All actions and state must be managed by SessionManager and PhotoBoothState.
#
# Attempting to import this module will raise an ImportError.
raise ImportError("action_handler.py is deprecated. Use SessionManager/PhotoBoothState only.")
"""
PhotoBoothScare Action Handler - Command Pattern Execution Layer

RESPONSIBILITIES:
- Executes actions returned by SessionManager following Command pattern
- Handles display rendering, user input processing, and hardware coordination
- Maintains clean separation between business logic (SessionManager) and execution
- Manages main event loop and frame processing

ARCHITECTURE OVERVIEW:
- SessionManager: Central orchestrator for all session state transitions
- ActionHandler: Pure execution layer that calls SessionManager.update() and executes returned actions
- Managers: Specialized classes handling camera, video, audio, GPIO, and photo capture
- UI Layer: Overlay rendering and display management separate from business logic

ACTION HANDLING FLOW:
1. Get camera frame and user input
2. Call SessionManager.update() with current state
3. Execute all actions returned in SessionAction object
4. Update display state for overlay rendering
5. Render frame with overlays and display to user

KEY ARCHITECTURAL PRINCIPLES:
- Single Responsibility: ActionHandler executes commands, doesn't make decisions
- Command Pattern: SessionManager returns actions, ActionHandler executes them
- Dependency Inversion: Hardware abstraction through manager interfaces
- Clean Separation: Business logic in SessionManager, execution logic here
"""

import os
import stat
import platform
import sys
import argparse
import time
import cv2
import pygame
import json

from photobooth.managers.camera_manager import CameraManager
from photobooth.hardware.gpio_manager import GPIOManager
from photobooth.managers.audio_manager import AudioManager
from photobooth.ui.overlay_renderer import OverlayRenderer

from photobooth.managers.rtsp_camera_manager import (
    RTSPCameraManager,
    get_rtsp_url_onvif,
)

from photobooth.managers.video_manager import VideoManager
from photobooth.managers.photo_capture_manager import PhotoCaptureManager

from photobooth.managers.countdown_manager import CountdownManager
from photobooth.managers.keyboard_input_manager import KeyboardInputManager
from photobooth.managers.session_manager import SessionManager

# ---- Parse Command Line Arguments ----
parser = argparse.ArgumentParser(description="PhotoBooth Scare Application")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
parser.add_argument(
    "--windowed",
    "-w",
    action="store_true",
    help="Run in windowed mode (not fullscreen)",
)
args = parser.parse_args(sys.argv[1:] if __name__ == "__main__" else sys.argv[1:])

# ---- Load Config ----
with open("config.json", "r") as f:
    CONFIG = json.load(f)

BUTTON_PIN = CONFIG["BUTTON_PIN"]
RELAY_PIN = CONFIG["RELAY_PIN"]
COUNTDOWN_SECONDS = CONFIG["COUNTDOWN_SECONDS"]
WINDOW_NAME = CONFIG["WINDOW_NAME"]
USE_WEBCAM = CONFIG["USE_WEBCAM"]
TEST_VIDEO_PATH = CONFIG["TEST_VIDEO_PATH"]
PHOTO_DIR = CONFIG["PHOTO_DIR"]
VIDEO_DIR = CONFIG["VIDEO_DIR"]
FONT_PATH = CONFIG["FONT_PATH"]
FONT_SIZE = CONFIG["FONT_SIZE"]
OVERLAY_GOTCHA_TEXT = CONFIG["OVERLAY_GOTCHA_TEXT"]
OVERLAY_IDLE_TEXT = CONFIG["OVERLAY_IDLE_TEXT"]
RTSP_URL = CONFIG["RTSP_URL"]
RTSP_VIDEO_FPS = CONFIG["RTSP_VIDEO_FPS"]
PYGAME_DRIVERS = CONFIG["PYGAME_DRIVERS"]
CAM_RESOLUTION_LOW = tuple(CONFIG["CAM_RESOLUTION_LOW"])
CAM_RESOLUTION_HIGH = tuple(CONFIG["CAM_RESOLUTION_HIGH"])
QR_DISPLAY_SECONDS = CONFIG.get("QR_DISPLAY_SECONDS", 5.0)

# Lighting configuration
LIGHTING_MODE = CONFIG.get("LIGHTING_MODE", "TESTING")
CAMERA_SETTINGS = CONFIG.get("CAMERA_SETTINGS", {})
LIGHTING_CONFIG = CAMERA_SETTINGS.get(LIGHTING_MODE, {})
LIGHTING_CONFIG["_mode"] = LIGHTING_MODE  # Add mode indicator for logging

# Debug configuration - command line overrides config
DEBUG_ENABLED = args.debug or CONFIG.get("DEBUG_ENABLED", False)
DEBUG_TIMING = DEBUG_ENABLED or CONFIG.get("DEBUG_TIMING", False)
DEBUG_AUDIO = DEBUG_ENABLED or CONFIG.get("DEBUG_AUDIO", False)
DEBUG_GPIO = DEBUG_ENABLED or CONFIG.get("DEBUG_GPIO", False)
DEBUG_CAMERA = DEBUG_ENABLED or CONFIG.get("DEBUG_CAMERA", False)

IS_LINUX = platform.system() == "Linux"
HAS_DISPLAY_SERVER = bool(
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
)

    # Check specific debug categories
    if category == "timing" and not DEBUG_TIMING:
        return
    elif category == "audio" and not DEBUG_AUDIO:
        return
    elif category == "gpio" and not DEBUG_GPIO:
        return
    elif category == "camera" and not DEBUG_CAMERA:
        return

    timestamp = time.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
    print(f"[{timestamp}] [{category.upper()}] {message}")


SSH_SESSION = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))
ON_CONSOLE_VT = (
    IS_LINUX and not HAS_DISPLAY_SERVER and not SSH_SESSION and sys.stdout.isatty()
)
USE_PYGAME_DISPLAY = (
    os.environ.get("USE_PYGAME_DISPLAY")
    or ("1" if (ON_CONSOLE_VT or IS_LINUX) else "0")
) != "0"
if IS_LINUX:
    os.environ.setdefault("SDL_AUDIODRIVER", "alsa")

# Always use low resolution for performance on Pi
CAM_RESOLUTION = CAM_RESOLUTION_LOW

print(
    f"[ENV] IS_LINUX={IS_LINUX} HAS_DISPLAY_SERVER={HAS_DISPLAY_SERVER} SSH_SESSION={SSH_SESSION} ON_CONSOLE_VT={ON_CONSOLE_VT} USE_PYGAME_DISPLAY={USE_PYGAME_DISPLAY}"
)


class ActionHandler:
    """Executes actions returned by SessionManager following Command pattern"""

    def __init__(
        self,
        session_manager,
        overlay_renderer,
        camera_manager,
        video_manager,
        audio_manager,
        gpio_manager,
        photo_manager,
    ):
        self.session_manager = session_manager
        self.overlay_renderer = overlay_renderer
        self.camera_manager = camera_manager
        self.video_manager = video_manager
        self.audio_manager = audio_manager
        self.gpio_manager = gpio_manager
        self.photo_manager = photo_manager

        # UI state variables (not session state - that's handled by SessionManager)
        self.qr_img = None
        self.qr_h = 0
        self.qr_w = 0

        # Set up GPIO button callback
        self.gpio_manager.add_event_detect(self._on_button_press)

    def _on_button_press(self, channel):
        """GPIO callback for button press events"""
        print("🔘 Button pressed - starting countdown!")
        self.session_manager.start_countdown()

    def run_main_loop(self):
        """DEPRECATED: Main event loop - being replaced by VideoRenderer + InputHandler"""
        print(
            "⚠️  ActionHandler.run_main_loop() is deprecated - use VideoRenderer + InputHandler instead"
        )
        raise NotImplementedError(
            "This method has been replaced by VideoRenderer and InputHandler classes"
        )

    def _execute_action(self, action, frame, width, height, now):
        """Execute all actions returned by SessionManager"""
        if action is None:
            # No action means idle state - create idle state dict for overlay renderer
            idle_state = {
                "phase": "idle",
                "countdown_active": False,
                # gotcha_active removed
            }
            print(f"🔧 Creating idle state: {idle_state}")
            return self.overlay_renderer.draw_overlay(frame, idle_state)

        # Only execute when there are actual actions to perform
        action_count = sum(
            1
            for attr in dir(action)
            if not attr.startswith("_")
            and getattr(action, attr) is not None
            and getattr(action, attr) is not False
        )

        if action_count == 0:
            # No actions means idle state - create complete state dict for overlay renderer
            idle_state = {
                "phase": "idle",
                "countdown_active": False,
                # gotcha_active removed
            }
            print(f"🔧 Creating idle state (no actions): {idle_state}")
            return self.overlay_renderer.draw_overlay(frame, idle_state)

        print(
            f"🎬 Executing {action_count} actions (phase: {getattr(action, 'current_phase', 'unknown')})"
        )

        # Handle beep sound
        if hasattr(action, "play_beep") and action.play_beep:
            print("🔊 Playing beep")
            self.audio_manager.play_beep()

        # Handle shutter sound
        if hasattr(action, "play_shutter") and action.play_shutter:
            print("📸 Playing shutter")
            self.audio_manager.play_shutter()

        # Handle photo capture
        if hasattr(action, "capture_photo") and action.capture_photo:
            print("📷 Capturing photo")
            self.photo_manager.capture_photo(frame)

        # Create state dict for overlay renderer based on current actions
        countdown_active = hasattr(action, "show_countdown") and action.show_countdown
    # gotcha_active removed

        # Determine phase from action state
        phase = "active"  # default
        if hasattr(action, "show_smile") and action.show_smile:
            phase = "smile"
        elif hasattr(action, "show_qr") and action.show_qr:
            phase = "qr"
    # gotcha_active removed
            phase = "gotcha"
        elif countdown_active:
            phase = "countdown"

        render_state = {
            "phase": phase,
            "countdown_number": getattr(action, "countdown_number", 0)
            if countdown_active
            else 0,
            "countdown_active": countdown_active,
            # gotcha_active removed
            "qr_url": getattr(action, "qr_url", None)
            if hasattr(action, "show_qr") and action.show_qr
            else None,
            "count_end_time": getattr(action, "count_end_time", 0),
        }

        # Apply overlays - always call draw_overlay for consistent state handling
        if render_state["countdown_active"]:
            print(f"⏰ Showing countdown: {render_state['countdown_number']}")
    # gotcha_active removed
            print("👻 Showing gotcha overlay")
        if render_state["qr_url"]:
            print("🔗 Showing QR overlay")

        print(
            f"🎨 Calling overlay with phase={render_state['phase']}, countdown={render_state['countdown_active']}"
        )
        frame = self.overlay_renderer.draw_overlay(frame, render_state)

        # Handle video recording
        if hasattr(action, "start_video") and action.start_video:
            print("🎥 Starting video recording")
            session_id = getattr(action, "session_id", "unknown")
            self.video_manager.start_recording(session_id, now, (width, height))

        if hasattr(action, "stop_video") and action.stop_video:
            print("🛑 Stopping video recording")
            self.video_manager.stop_recording()

        # Handle scare trigger
        if hasattr(action, "trigger_scare") and action.trigger_scare:
            print("💀 Triggering scare!")
            self.gpio_manager.trigger_scare()

        # Always return the (potentially modified) frame
        return frame

    def _cleanup(self):
        """Clean up resources"""
        if hasattr(self.camera_manager, "cleanup"):
            self.camera_manager.cleanup()
        if hasattr(self.video_manager, "cleanup"):
            self.video_manager.cleanup()
        if hasattr(self.audio_manager, "cleanup"):
            self.audio_manager.cleanup()
        if hasattr(self.gpio_manager, "cleanup"):
            self.gpio_manager.cleanup()
        cv2.destroyAllWindows()

    def _report_state(self):
        """Report current state for debugging"""
        debug_log("state", f"Session state: {self.session_manager.current_phase}")
        debug_log("state", f"Video recording: {self.video_manager.recording}")
        debug_log("state", f"GPIO button: {self.gpio_manager.is_button_pressed()}")


def setup_and_run():
    """Setup function that initializes managers and runs the ActionHandler"""
    print("🚀 setup_and_run called!")
    global session_manager, overlay_renderer

    # Fix XDG runtime dir permissions on Linux to avoid Qt/libcamera warnings and preview instability
    if IS_LINUX:
        try:
            uid = os.getuid()
            default_runtime = f"/run/user/{uid}"
            xr = os.environ.get("XDG_RUNTIME_DIR", default_runtime)
            # Ensure dir exists
            if not os.path.isdir(xr):
                try:
                    os.makedirs(xr, exist_ok=True)
                except Exception:
                    # fallback to /tmp if /run is managed by systemd
                    xr = f"/tmp/runtime-{uid}"
                    os.makedirs(xr, exist_ok=True)
                    os.environ["XDG_RUNTIME_DIR"] = xr
            # Ensure 0700 perms
            st = os.stat(xr)
            mode = stat.S_IMODE(st.st_mode)
            if mode != 0o700:
                try:
                    os.chmod(xr, 0o700)
                except Exception:
                    pass
            # Ensure ownership
            try:
                if st.st_uid != uid:
                    os.chown(xr, uid, -1)
            except Exception:
                # chown may not be permitted; best effort only
                pass
        except Exception:
            pass

    # Initialize managers
    print("🔧 Initializing managers...")
    try:
        camera = CameraManager(
            CAM_RESOLUTION, TEST_VIDEO_PATH, USE_WEBCAM, LIGHTING_CONFIG
        )
        print("✅ Camera manager initialized")
        gpio = GPIOManager(BUTTON_PIN, RELAY_PIN, debug_log)
        print("✅ GPIO manager initialized")
        audio = AudioManager(debug=DEBUG_AUDIO)
        print("✅ Audio manager initialized")
        overlay = OverlayRenderer(
            FONT_PATH, FONT_SIZE, OVERLAY_GOTCHA_TEXT, OVERLAY_IDLE_TEXT
        )
        print("✅ Overlay renderer initialized")
    except Exception as e:
        print(f"❌ Manager initialization failed: {e}")
        raise

    # Initialize remaining managers
    print("🔧 Initializing video manager...")
    try:
        video_manager = VideoManager(CONFIG, debug_log)
        print("✅ Video manager initialized")
    except Exception as e:
        print(f"❌ Video manager failed: {e}")
        raise

    print("🔧 Initializing photo manager...")
    try:
        photo_manager = PhotoCaptureManager(CONFIG, debug_log)
        print("✅ Photo manager initialized")
    except Exception as e:
        print(f"❌ Photo manager failed: {e}")
        raise

    # Initialize session manager
    print("🔧 Initializing session manager...")
    try:
        session_manager = SessionManager(CONFIG, debug_log)
        print("✅ Session manager initialized")
        overlay_renderer = overlay
        print("✅ Overlay renderer assigned")
    except Exception as e:
        print(f"❌ Session manager failed: {e}")
        raise  # Create action handler with all managers
    print("🔧 Creating ActionHandler...")
    try:
        action_handler = ActionHandler(
            session_manager=session_manager,
            overlay_renderer=overlay_renderer,
            camera_manager=camera,
            video_manager=video_manager,
            audio_manager=audio,
            gpio_manager=gpio,
            photo_manager=photo_manager,
        )
        print("✅ ActionHandler created")
    except Exception as e:
        print(f"❌ ActionHandler creation failed: {e}")
        raise

    print("🎮 Starting main loop...")
    action_handler.run_main_loop()

    # Fix XDG runtime dir permissions on Linux to avoid Qt/libcamera warnings and preview instability
    if IS_LINUX:
        try:
            uid = os.getuid()
            default_runtime = f"/run/user/{uid}"
            xr = os.environ.get("XDG_RUNTIME_DIR", default_runtime)
            # Ensure dir exists
            if not os.path.isdir(xr):
                try:
                    os.makedirs(xr, exist_ok=True)
                except Exception:
                    # fallback to /tmp if /run is managed by systemd
                    xr = f"/tmp/runtime-{uid}"
                    os.makedirs(xr, exist_ok=True)
                    os.environ["XDG_RUNTIME_DIR"] = xr
            # Ensure 0700 perms
            st = os.stat(xr)
            mode = stat.S_IMODE(st.st_mode)
            if mode != 0o700:
                try:
                    os.chmod(xr, 0o700)
                except Exception:
                    pass
            # Ensure ownership
            try:
                if st.st_uid != uid:
                    os.chown(xr, uid, -1)
            except Exception:
                # chown may not be permitted; best effort only
                pass
        except Exception:
            pass

    # Initialize managers
    camera = CameraManager(CAM_RESOLUTION, TEST_VIDEO_PATH, USE_WEBCAM, LIGHTING_CONFIG)
    gpio = GPIOManager(BUTTON_PIN, RELAY_PIN, debug_log)
    audio = AudioManager(debug=DEBUG_AUDIO)
    overlay = OverlayRenderer(
        FONT_PATH, FONT_SIZE, OVERLAY_GOTCHA_TEXT, OVERLAY_IDLE_TEXT
    )

    # Initialize file manager

    # Initialize video manager
    video_manager = VideoManager(CONFIG, debug_log)

    # Initialize photo capture manager
    photo_manager = PhotoCaptureManager(CONFIG, debug_log)

    # Initialize QR display manager
    # QR code variables
    qr_img = None
    qr_w, qr_h = 0, 0

    # Initialize countdown manager
    countdown_manager = CountdownManager(CONFIG, debug_log)

    # Initialize session manager (follows SOLID design principles)
    # SessionManager handles all session timing including gotcha display transitions
    session_manager = SessionManager(CONFIG, debug_log)
    state = session_manager.state  # Backward compatibility for overlay code

    # Output directories
    # Network (NAS) paths -- where files will finally live (from config, adapted per platform)
    network_photo_dir = CONFIG.get(
        "NETWORK_PHOTO_DIR", "\\\\SKYNAS\\web\\Halloween2025\\media\\photos"
    )
    network_video_dir = CONFIG.get(
        "NETWORK_VIDEO_DIR", "\\\\SKYNAS\\web\\Halloween2025\\media\\videos"
    )

    # Adapt network paths for Linux (convert UNC to mount points)
    if IS_LINUX:
        if network_photo_dir.startswith("\\\\"):
            network_photo_dir = network_photo_dir.replace(
                "\\\\SKYNAS", "/mnt/skynas"
            ).replace("\\", "/")
        if network_video_dir.startswith("\\\\"):
            network_video_dir = network_video_dir.replace(
                "\\\\SKYNAS", "/mnt/skynas"
            ).replace("\\", "/")

    # Local paths from config (these are the working directories during capture)
    local_photo_dir = CONFIG.get("PHOTO_DIR", "./local_photos")
    local_video_dir = CONFIG.get("VIDEO_DIR", "./local_videos")

    # On Linux, use local paths for capture, then copy to network during QR display
    if IS_LINUX:
        photo_dir = local_photo_dir
        video_dir = local_video_dir
    else:
        # Non-Linux (development host) write directly to network paths
        photo_dir = network_photo_dir
        video_dir = network_video_dir

    # Log directory configuration for debugging
    debug_log("migrate", "📁 Directory configuration:")
    debug_log("migrate", f"   Local photos:  {local_photo_dir}")
    debug_log("migrate", f"   Local videos:  {local_video_dir}")
    debug_log("migrate", f"   Network photos: {network_photo_dir}")
    debug_log("migrate", f"   Network videos: {network_video_dir}")
    debug_log(
        "migrate",
        f"   Active photos:  {photo_dir} ({'local' if photo_dir == local_photo_dir else 'network'})",
    )
    debug_log(
        "migrate",
        f"   Active videos:  {video_dir} ({'local' if video_dir == local_video_dir else 'network'})",
    )

    # Ensure local and network directories exist where feasible
    for d in (local_photo_dir, local_video_dir, network_photo_dir, network_video_dir):
        try:
            os.makedirs(d, exist_ok=True)
            debug_log("migrate", f"✅ Directory ready: {d}")
        except Exception as e:
            # best-effort only; failures for network dirs are acceptable at startup
            debug_log("migrate", f"❌ Directory failed: {d} - {e}")
            pass

    # Try to initialize RTSP secondary camera manager if RTSP_URL present
    if RTSP_URL:
        try:
            # Health-check / reconnection settings
            rtsp_check_interval = float(CONFIG.get("RTSP_CHECK_INTERVAL", 5.0))
            rtsp_last_check = 0.0
            rtsp_retries = 0
            rtsp_max_retries = int(CONFIG.get("RTSP_MAX_RETRIES", 6))
            if RTSP_URL.startswith("onvif://"):
                # onvif://username:password@ip
                from urllib.parse import urlparse

                p = urlparse(RTSP_URL)
                net = p.netloc  # may contain user:pass@host
                if "@" in net:
                    creds, host = net.split("@", 1)
                    if ":" in creds:
                        user, pwd = creds.split(":", 1)
                    else:
                        user, pwd = creds, ""
                else:
                    host = net
                    user, pwd = "", ""
                print(f"[RTSP] Fetching RTSP URL from ONVIF on {host}...")
                fetched = get_rtsp_url_onvif(host, user, pwd)
                if fetched:
                    try:
                        rtsp_manager = RTSPCameraManager(
                            fetched,
                            os.path.join(
                                video_dir, f"rtsp_secondary_{int(time.time())}.mp4"
                            ),
                            RTSP_VIDEO_FPS,
                        )
                        rtsp_manager.start()
                        rtsp_status = "ONLINE"
                        print("[RTSP] Secondary RTSP stream started via ONVIF.")
                    except Exception as e:
                        print(
                            f"[RTSP] Failed to start RTSP manager with fetched URL: {e}"
                        )
                        rtsp_manager = None
                        rtsp_status = "OFFLINE"
                else:
                    print("[RTSP] Could not fetch RTSP URL via ONVIF; leaving offline.")
                    rtsp_status = "OFFLINE"
            else:
                # Try to use RTSP_URL directly (inject credentials if present in config)
                try:
                    rtsp_to_use = RTSP_URL
                    try:
                        # If URL lacks credentials, and config provides them, inject
                        from urllib.parse import urlparse, urlunparse

                        p = urlparse(RTSP_URL)
                        if p.username is None and CONFIG.get("RTSP_USER"):
                            netloc = f"{CONFIG.get('RTSP_USER')}:{CONFIG.get('RTSP_PASS', '')}@{p.hostname}"
                            if p.port:
                                netloc += f":{p.port}"
                            rtsp_to_use = urlunparse(
                                (
                                    p.scheme,
                                    netloc,
                                    p.path or "",
                                    p.params or "",
                                    p.query or "",
                                    p.fragment or "",
                                )
                            )
                    except Exception:
                        pass

                    rtsp_manager = RTSPCameraManager(
                        rtsp_to_use,
                        os.path.join(
                            video_dir, f"rtsp_secondary_{int(time.time())}.mp4"
                        ),
                        RTSP_VIDEO_FPS,
                    )
                    rtsp_manager.start()
                    rtsp_status = "ONLINE"
                    print("[RTSP] Secondary RTSP stream started.")
                except Exception as e:
                    print(f"[RTSP] Failed to start RTSP manager: {e}")
                    rtsp_manager = None
                    rtsp_status = "OFFLINE"
        except Exception as e:
            print(f"[RTSP] Initialization error: {e}")
            rtsp_manager = None
            rtsp_status = "OFFLINE"

    # Display setup
    screen = None
    screen_size = None
    if USE_PYGAME_DISPLAY:
        # Try X11 first on Linux with display server, then framebuffer drivers
        if IS_LINUX and HAS_DISPLAY_SERVER:
            drivers_to_try = ["x11", "kmsdrm", "fbcon", "directfb"]
        else:
            drivers_to_try = ["kmsdrm", "fbcon", "directfb", "svgalib"]
        for drv in drivers_to_try:
            try:
                os.environ["SDL_VIDEODRIVER"] = drv
                if not pygame.get_init():
                    pygame.init()
                else:
                    pygame.display.quit()
                pygame.display.init()
                info = pygame.display.Info()

                if args.windowed:
                    # Windowed mode for development
                    screen_size = (1024, 768)
                    screen = pygame.display.set_mode(screen_size, 0)
                    pygame.mouse.set_visible(True)
                    pygame.display.set_caption("PhotoBooth Scare - Development Mode")
                    print(
                        f"[INFO] Pygame windowed mode with driver '{drv}' -> {screen_size}"
                    )
                else:
                    # Fullscreen mode for production
                    screen_size = (info.current_w, info.current_h)
                    screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
                    pygame.mouse.set_visible(False)
                    print(
                        f"[INFO] Pygame fullscreen with driver '{drv}' -> {screen_size}"
                    )
                break
            except Exception as e:
                print(f"[WARN] Driver '{drv}' failed: {e}")
                screen = None
        if screen is None:
            print(
                "[ERROR] No suitable SDL framebuffer driver worked; no live preview will show."
            )
            try:
                cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
                if not args.windowed:
                    # Try to make OpenCV window fullscreen
                    try:
                        cv2.setWindowProperty(
                            WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                        )
                        cv2.moveWindow(WINDOW_NAME, 0, 0)
                    except Exception:
                        pass
                else:
                    # Windowed mode - resize to development size
                    try:
                        cv2.resizeWindow(WINDOW_NAME, 1024, 768)
                    except Exception:
                        pass
            except Exception:
                pass
    else:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        if not args.windowed:
            # Try to make OpenCV window fullscreen
            try:
                cv2.setWindowProperty(
                    WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                )
                cv2.moveWindow(WINDOW_NAME, 0, 0)
            except Exception:
                pass
        else:
            # Windowed mode - resize to development size
            try:
                cv2.resizeWindow(WINDOW_NAME, 1024, 768)
            except Exception:
                pass

    print("Controls:")
    print("  SPACE = simulate button press, Q/ESC/F11 = quit")
    print(
        "  Camera Settings: W(WB mode), B(brightness ±), C(contrast ±), S(saturation ±)"
    )
    print("  E(exposure ±), G(gain ±), N(noise reduction), R(reset to defaults)")
    print("  H = show this help again")

    # Camera settings now handled by CameraControls class

    # wb_modes now handled by CameraControls class

    # Initialize camera controls and settings overlay
    from photobooth.ui.camera_controls import CameraControls
    from photobooth.ui.settings_overlay import SettingsOverlay

    settings_overlay = SettingsOverlay()
    camera_controls = CameraControls(camera, LIGHTING_CONFIG, settings_overlay)

    # Initialize keyboard input manager
    keyboard_input = KeyboardInputManager(camera_controls, debug_log, session_manager)

    # Helper functions for clean SOLID main loop
    def _display_frame(frame):
        """Display frame using pygame or OpenCV."""
        if screen is not None:
            # Pygame display
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fh, fw = rgb.shape[:2]
            sw, sh = screen_size
            scale = min(sw / fw, sh / fh)
            new_size = (int(fw * scale), int(fh * scale))
            surf_img = cv2.resize(rgb, new_size, interpolation=cv2.INTER_LINEAR)
            surf = pygame.image.frombuffer(surf_img.tobytes(), new_size, "RGB")
            screen.fill((0, 0, 0))
            x = (sw - new_size[0]) // 2
            y = (sh - new_size[1]) // 2
            screen.blit(surf, (x, y))
            pygame.display.flip()
        else:
            # OpenCV display
            try:
                cv2.imshow(WINDOW_NAME, frame)
            except Exception:
                pass

    # Removed duplicate camera control functions - using CameraControls class instead

    # Camera controls now handled by CameraControls class

    # Settings overlay now handled by SettingsOverlay class

    # Non-blocking state machine
    # Countdown now handled by CountdownManager
    # Gotcha display handled by SessionManager and OverlayRenderer
    # Photo capture now handled by PhotoCaptureManager

    def start_countdown():
        # Use SessionManager to check and coordinate session state
        if not session_manager.is_idle():
            debug_log("timing", "⚠️ Session already active - ignoring countdown start")
            return False

        # CRITICAL: Stop any existing video recording first
        if video_manager.recording:
            debug_log(
                "timing", "⚠️ Force stopping previous video recording before new session"
            )
            video_manager.stop_recording()

        # Reset all managers before starting new session
        photo_manager.reset()
        # Reset QR display (now handled by SessionManager)
        qr_img = None
        qr_w, qr_h = 0, 0
        video_manager.cleanup()

        # Let SessionManager handle session state coordination
        session_manager.start_countdown()

        # Trigger hardware effects
        countdown_manager.start_countdown(audio, gpio)
        return True

    last_button_time = 0

    def button_callback(_pin):
        nonlocal last_button_time
        current_time = time.time()

        # Debounce: ignore button presses within 2 seconds of last press
        if current_time - last_button_time < 2.0:
            debug_log(
                "gpio",
                f"Hardware button debounced (too soon: {current_time - last_button_time:.1f}s)",
            )
            return

        # Use SessionManager to check if idle (SOLID principle)
        if not session_manager.is_idle() or video_manager.recording:
            debug_log(
                "gpio", "Hardware button ignored (session active or video recording)"
            )
            return

        last_button_time = current_time
        debug_log("gpio", f"Hardware button callback triggered (pin {_pin})")
        start_countdown()

    # Create action handler with all managers
    print("🔧 Creating ActionHandler...")
    try:
        action_handler = ActionHandler(
            session_manager=session_manager,
            overlay_renderer=overlay_renderer,
            camera_manager=camera,
            video_manager=video_manager,
            audio_manager=audio,
            gpio_manager=gpio,
            photo_manager=photo_manager,
        )
        print("✅ ActionHandler created")
    except Exception as e:
        print(f"❌ ActionHandler creation failed: {e}")
        raise

    print("🎮 Starting main loop...")
    action_handler.run_main_loop()
    return  # Exit function, don't run old code

    gpio.add_event_detect(button_callback)
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
            frame = cv2.flip(frame, 1)

            now = time.time()
            height, width = frame.shape[:2]

            # SOLID ARCHITECTURE: Single call to SessionManager orchestrates everything
            action = session_manager.update(
                now=now,
                frame_dimensions=(width, height),
                video_recording=video_manager.recording,
                video_finalized=video_manager.is_finalized()
                if hasattr(video_manager, "is_finalized")
                else False,
            )

            # EXECUTE ACTIONS returned by SessionManager
            if action.start_video:
                debug_log(
                    "timing",
                    f"🎥 MAIN: Starting video recording {action.video_dimensions}",
                )
                video_manager.start_recording(
                    action.session_id, action.session_time, action.video_dimensions
                )

            if action.stop_video:
                debug_log("timing", "🎬 MAIN: Stopping video recording")
                video_manager.stop_recording()

            # Handle coordinated countdown action (beep + display + prop trigger together)
            if action.countdown_update:
                countdown_data = action.countdown_update
                if countdown_data.get("play_beep"):
                    audio.play_beep()
                if countdown_data.get("show_display"):
                    state.countdown_number = countdown_data.get("number")
                    state.countdown_active = True
                    # gotcha_active removed
                if countdown_data.get("trigger_prop"):
                    gpio.trigger_scare()
                    debug_log("timing", "👻 Prop triggered with countdown!")
                debug_log(
                    "timing",
                    f"⏰ Coordinated countdown: {countdown_data.get('number')}",
                )

            # Handle coordinated smile action (display + shutter + photo together)
            if action.smile_action:
                smile_data = action.smile_action
                if smile_data.get("show_display"):
                    state.countdown_number = None
                    state.countdown_active = False
                    # gotcha_active removed
                    state.phase = "smile"
                if smile_data.get("play_shutter"):
                    audio.play_shutter()
                if smile_data.get("capture_photo"):
                    photo_manager.capture_photo(
                        frame, action.session_time, action.session_id, now
                    )
                debug_log("timing", "📸 Coordinated smile action executed")

            # Handle coordinated gotcha action (display + QR integration)
            if action.gotcha_action:
                gotcha_data = action.gotcha_action
                if gotcha_data.get("show_display"):
                    state.countdown_number = None
                    state.countdown_active = False
                    # gotcha_active removed
                    state.phase = "gotcha"
                    state.qr_url = gotcha_data.get("qr_url")
                debug_log(
                    "timing",
                    f"👻 Coordinated gotcha action (duration: {gotcha_data.get('duration', 0):.1f}s)",
                )

            # Legacy individual actions (remove after coordinated actions are working)
            if action.play_beep:
                audio.play_beep()
            if action.play_shutter:
                audio.play_shutter()
            if action.trigger_scare:
                gpio.trigger_scare()
                debug_log("timing", "👻 Scare triggered!")
            if action.capture_photo:
                photo_manager.capture_photo(
                    frame, action.session_time, action.session_id, now
                )

            # Handle QR code generation and display
            if action.show_qr and action.qr_url:
                if qr_img is None:
                    from photobooth.utils.qr_generator import generate_qr

                    qr_path = f"qr_{action.session_id}.png"
                    generate_qr(action.qr_url, qr_path, size=8)
                    qr_img = cv2.imread(qr_path)
                    if qr_img is not None:
                        qr_h, qr_w = qr_img.shape[:2]
                        debug_log(
                            "timing", f"📱 QR code generated: {qr_path} ({qr_w}x{qr_h})"
                        )

            # Update state for overlay rendering
            if action.show_countdown and action.countdown_number:
                state.countdown_number = action.countdown_number
                state.countdown_active = True
                # gotcha_active removed
            elif action.show_smile or action.show_gotcha:
                state.countdown_number = None
                state.countdown_active = False
                # gotcha_active removed
            elif action.session_complete:
                state.countdown_number = None
                state.countdown_active = False
                # gotcha_active removed
                # Clean up session
                qr_img = None
                photo_manager.reset()
                video_manager.cleanup()

            # Write frame to video if recording (SessionManager controls timing)
            if video_manager.recording:
                video_manager.write_frame(frame)

            # Draw overlays (overlay renderer handles QR code display based on state)
            frame = overlay.draw_overlay(frame, vars(state))

            # Add camera settings overlay if visible
            frame = settings_overlay.draw_overlay(frame)

            # Display frame
            _display_frame(frame)

            # Handle user input (keyboard controls)
            if screen is not None:
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt()
                    elif event.type == pygame.KEYDOWN:
                        if keyboard_input.handle_pygame_key(
                            event.key, state, None, session_manager.start_countdown
                        ):
                            raise KeyboardInterrupt()
            else:
                try:
                    key = cv2.waitKey(1) & 0xFF
                    if keyboard_input.handle_opencv_key(
                        key, state, None, session_manager.start_countdown
                    ):
                        break
                except Exception:
                    pass

            # Minimal sleep to prevent excessive CPU usage
            time.sleep(0.005)
    finally:
        video_manager.cleanup()
        photo_manager.cleanup()
        countdown_manager.cleanup()
        # Gotcha cleanup now handled by SessionManager
        # QR cleanup handled by simple variables
        keyboard_input.cleanup()
        camera.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            if screen is not None:
                pygame.display.quit()
        except Exception:
            pass
        gpio.cleanup()


if __name__ == "__main__":
    setup_and_run()
