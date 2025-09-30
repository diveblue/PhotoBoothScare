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
from photobooth.utils.photobooth_state import PhotoBoothState
from photobooth.managers.rtsp_camera_manager import (
    RTSPCameraManager,
    get_rtsp_url_onvif,
)
from photobooth.managers.file_manager import FileManager
from photobooth.managers.video_manager import VideoManager
from photobooth.managers.photo_capture_manager import PhotoCaptureManager
from photobooth.managers.qr_display_manager import QRDisplayManager
from photobooth.managers.countdown_manager import CountdownManager
from photobooth.managers.gotcha_manager import GotchaManager
from photobooth.managers.keyboard_input_manager import KeyboardInputManager

# ---- Parse Command Line Arguments ----
parser = argparse.ArgumentParser(description="PhotoBooth Scare Application")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
parser.add_argument(
    "--windowed",
    "-w",
    action="store_true",
    help="Run in windowed mode (not fullscreen)",
)
args = parser.parse_args()

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


# Debug helper function
def debug_log(category, message):
    """Log debug messages with timestamp if debugging is enabled"""
    if not DEBUG_ENABLED:
        return

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


def main():
    # Session state variables
    files_moved_to_network = False
    qr_img = None
    qr_h, qr_w = 0, 0
    """
    Main orchestration function for the PhotoBoothScare application.
    Initializes all managers and runs the main event loop.
    """

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
    gpio = GPIOManager(BUTTON_PIN, RELAY_PIN)
    audio = AudioManager(debug=DEBUG_AUDIO)
    overlay = OverlayRenderer(
        FONT_PATH, FONT_SIZE, OVERLAY_GOTCHA_TEXT, OVERLAY_IDLE_TEXT
    )

    # Initialize file manager
    file_manager = FileManager(CONFIG, debug_log)

    # Initialize video manager
    video_manager = VideoManager(CONFIG, debug_log)

    # Initialize photo capture manager
    photo_manager = PhotoCaptureManager(CONFIG, debug_log)

    # Initialize QR display manager
    qr_manager = QRDisplayManager(CONFIG, debug_log)

    # Initialize countdown manager
    countdown_manager = CountdownManager(CONFIG, debug_log)

    # Initialize gotcha manager
    gotcha_manager = GotchaManager(CONFIG, debug_log)

    # Initialize state (can be replaced by session_manager.state in future)
    state = PhotoBoothState()

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
    keyboard_input = KeyboardInputManager(camera_controls, debug_log)

    # Removed duplicate camera control functions - using CameraControls class instead

    # Camera controls now handled by CameraControls class

    # Settings overlay now handled by SettingsOverlay class

    # Non-blocking state machine
    # Countdown now handled by CountdownManager
    # Gotcha now handled by GotchaManager
    # Photo capture now handled by PhotoCaptureManager

    def start_countdown():
        nonlocal files_moved_to_network
        if countdown_manager.start_countdown(audio, gpio):
            state.start_countdown(COUNTDOWN_SECONDS)
            files_moved_to_network = False
            photo_manager.reset()  # Reset photo capture state
            gotcha_manager.reset()  # Reset gotcha state

    def button_callback(_pin):
        debug_log("gpio", f"Hardware button callback triggered (pin {_pin})")
        start_countdown()

    gpio.add_event_detect(button_callback)
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
            frame = cv2.flip(frame, 1)

            now = time.time()
            # Handle countdown state machine
            if state.countdown_active:
                # Start video recording if not already
                if not video_manager.recording:
                    height, width = frame.shape[:2]
                    # Use actual frame dimensions for video
                    video_size = (width, height)
                    video_manager.start_recording(
                        state.session_id, state.session_time, video_size
                    )
                # Update countdown and handle beeps
                countdown_info = countdown_manager.update(audio)
                if countdown_info:
                    state.countdown_number = countdown_info["countdown_number"]
                    elapsed = countdown_info["elapsed"]
                    # After countdown, show SMILE!
                    if countdown_info["countdown_finished"]:
                        state.countdown_number = None
                        # Start SMILE phase and play shutter sound once
                        photo_manager.start_smile_phase(audio)

                        # Take multiple SMILE photos using photo manager
                        if (
                            not photo_manager.is_complete()
                            and photo_manager.should_take_photo(now)
                        ):
                            photo_manager.capture_photo(
                                frame, state.session_time, state.session_id, now
                            )

                        # Check if ready for gotcha phase (all photos taken + pause)
                        if gotcha_manager.should_trigger_gotcha(
                            photo_manager, elapsed, COUNTDOWN_SECONDS
                        ):
                            gotcha_manager.trigger_gotcha(state, 10)
                # Update gotcha and check for completion
                gotcha_info = gotcha_manager.update(state)
                if gotcha_info and gotcha_info["completed"]:
                    # Stop video recording NOW - before file movement during QR display
                    if video_manager.recording:
                        video_manager.stop_recording()

                    # Start QR display phase
                    if not qr_manager.is_active():
                        qr_result = qr_manager.start_display(state.session_id)
                        if qr_result and qr_result["success"]:
                            if qr_result["dimensions"]:
                                qr_w, qr_h = qr_result["dimensions"]
                                qr_img = cv2.imread(qr_result["qr_path"])

                    # Handle file movement during QR display (responsibility of file manager)
                    if not files_moved_to_network and IS_LINUX:
                        try:
                            debug_log(
                                "timing",
                                "📁 MOVING FILES to web server during QR display",
                            )

                            # First, cleanup any old sessions that might still be in local directories
                            current_session_prefix = (
                                f"{state.session_time}_{state.session_id}_"
                            )
                            old_files_moved = file_manager.cleanup_old_local_sessions(
                                local_photo_dir,
                                local_video_dir,
                                network_photo_dir,
                                network_video_dir,
                                exclude_current_session=current_session_prefix,
                            )

                            # Then move current session files
                            files_moved = file_manager.move_session_files_to_network(
                                state.session_time,
                                state.session_id,
                                local_photo_dir,
                                local_video_dir,
                                network_photo_dir,
                                network_video_dir,
                            )
                            if files_moved >= 0:  # Success (even if 0 files)
                                files_moved_to_network = True
                                total_moved = files_moved + old_files_moved
                                debug_log(
                                    "timing",
                                    f"✅ Moved {files_moved} current + {old_files_moved} old = {total_moved} total files to web server",
                                )
                        except Exception as e:
                            debug_log(
                                "timing", f"❌ FILE MOVE failed during QR display: {e}"
                            )
                # End QR display after configured time
                # Update QR code display timing
                qr_manager.update(now)
                status = qr_manager.get_display_status(now)
                if status and status["active"]:
                    debug_log(
                        "timing",
                        f"🔄 QR display active for {status['elapsed']:.1f}s / {status['duration']:.1f}s",
                    )

                if qr_manager.is_complete(now):
                    debug_log("timing", "🏁 SESSION COMPLETE - Returning to IDLE state")
                    state.countdown_active = False
                    state.gotcha_active = False  # <- FIX: Also reset gotcha state
                    files_moved_to_network = False
                    countdown_manager.reset()  # Reset countdown state
                    gotcha_manager.reset()  # Reset gotcha state
                    photo_manager.reset()  # Reset photo capture state
                    qr_manager.reset()  # Reset QR display state

            # Write frame to video if recording (should stop before QR display)
            if video_manager.recording:
                video_manager.write_frame(frame)

                # Video recording is now stopped earlier when gotcha completes
                # This ensures files can be moved during QR display without corruption

                # Draw overlay
                # Periodic RTSP health check and reconnect
                try:
                    if now - rtsp_last_check >= rtsp_check_interval:
                        rtsp_last_check = now
                        alive = False
                        if rtsp_manager is not None:
                            try:
                                cap = getattr(rtsp_manager, "cap", None)
                                if (
                                    cap is not None
                                    and hasattr(cap, "isOpened")
                                    and cap.isOpened()
                                ):
                                    alive = True
                                elif (
                                    hasattr(rtsp_manager, "is_recording")
                                    and rtsp_manager.is_recording()
                                ):
                                    alive = True
                            except Exception:
                                alive = False
                        if not alive:
                            rtsp_retries += 1
                            print(
                                f"[RTSP] Stream not healthy, attempt {rtsp_retries}/{rtsp_max_retries}"
                            )
                            # Stop existing manager if present
                            try:
                                if rtsp_manager is not None:
                                    rtsp_manager.stop()
                            except Exception:
                                pass
                            rtsp_manager = None
                            # Try to obtain a usable RTSP URL
                            rtsp_candidate = None
                            try:
                                if RTSP_URL.startswith("onvif://"):
                                    # parse host/creds
                                    from urllib.parse import urlparse

                                    p = urlparse(RTSP_URL)
                                    net = p.netloc
                                    if "@" in net:
                                        creds, host = net.split("@", 1)
                                        if ":" in creds:
                                            user, pwd = creds.split(":", 1)
                                        else:
                                            user, pwd = creds, ""
                                    else:
                                        host = net
                                        user, pwd = (
                                            CONFIG.get("RTSP_USER", ""),
                                            CONFIG.get("RTSP_PASS", ""),
                                        )
                                    fetched = get_rtsp_url_onvif(host, user, pwd)
                                    if fetched:
                                        rtsp_candidate = fetched
                                else:
                                    # inject credentials if missing
                                    try:
                                        from urllib.parse import urlparse, urlunparse

                                        p = urlparse(RTSP_URL)
                                        rtsp_candidate = RTSP_URL
                                        if p.username is None and CONFIG.get(
                                            "RTSP_USER"
                                        ):
                                            netloc = f"{CONFIG.get('RTSP_USER')}:{CONFIG.get('RTSP_PASS', '')}@{p.hostname}"
                                            if p.port:
                                                netloc += f":{p.port}"
                                            rtsp_candidate = urlunparse(
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
                                        rtsp_candidate = RTSP_URL
                                # If no candidate yet, try ONVIF using configured creds and host from RTSP_URL
                                if not rtsp_candidate:
                                    try:
                                        from urllib.parse import urlparse

                                        p = urlparse(RTSP_URL)
                                        host = p.hostname or p.netloc
                                        user = CONFIG.get("RTSP_USER", "")
                                        pwd = CONFIG.get("RTSP_PASS", "")
                                        if host and (user or pwd):
                                            print(
                                                f"[RTSP] Attempting ONVIF fetch on {host} during reconnect..."
                                            )
                                            fetched_fallback = get_rtsp_url_onvif(
                                                host, user, pwd
                                            )
                                            if fetched_fallback:
                                                rtsp_candidate = fetched_fallback
                                    except Exception:
                                        pass
                            except Exception as e:
                                print(f"[RTSP] Error preparing candidate URL: {e}")
                                rtsp_candidate = None

                            # Attempt to start manager if we have a candidate URL
                            if rtsp_candidate:
                                # Mark as connecting so overlay shows activity
                                rtsp_status = "CONNECTING"
                                # Lightweight probe: try to open a short cv2 cap and read a frame or two
                                probe_ok = False
                                try:
                                    if cv2 is not None:
                                        probe_cap = cv2.VideoCapture(rtsp_candidate)
                                        t0 = time.time()
                                        while time.time() - t0 < 2.0:
                                            ret, _f = probe_cap.read()
                                            if ret:
                                                probe_ok = True
                                                break
                                            time.sleep(0.15)
                                        try:
                                            probe_cap.release()
                                        except Exception:
                                            pass
                                    else:
                                        # If no cv2 available, optimistically try to start manager
                                        probe_ok = True
                                except Exception:
                                    probe_ok = False

                                if not probe_ok:
                                    print(
                                        "[RTSP] Probe failed; skipping manager start for now."
                                    )
                                    rtsp_manager = None
                                    rtsp_status = "OFFLINE"
                                else:
                                    try:
                                        rtsp_manager = RTSPCameraManager(
                                            rtsp_candidate,
                                            os.path.join(
                                                video_dir,
                                                f"rtsp_secondary_{int(time.time())}.mp4",
                                            ),
                                            RTSP_VIDEO_FPS,
                                        )
                                        rtsp_manager.start()
                                        rtsp_status = "ONLINE"
                                        rtsp_retries = 0
                                        print(
                                            "[RTSP] Reconnected secondary RTSP stream."
                                        )
                                    except Exception as e:
                                        print(f"[RTSP] Reconnect failed: {e}")
                                        rtsp_manager = None
                                        rtsp_status = "OFFLINE"
                            else:
                                rtsp_status = "OFFLINE"
                            # If exceeded max retries, reset counter and wait longer
                            if rtsp_retries >= rtsp_max_retries:
                                rtsp_retries = 0
                                rtsp_last_check = now + rtsp_check_interval * 4
                except Exception:
                    pass
            frame = overlay.draw_overlay(frame, vars(state))
            # Render RTSP status indicator in lower-right
            try:
                # Compute compact status text and color
                # rtsp_status may be "ONLINE", "OFFLINE", "CONNECTING" or None
                st = rtsp_status if isinstance(rtsp_status, str) else None
                if st is None:
                    # derive from manager health
                    if (
                        rtsp_manager
                        and getattr(rtsp_manager, "is_recording", lambda: False)()
                    ):
                        st = "ONLINE"
                    else:
                        st = "OFFLINE"

                if st == "ONLINE":
                    # try to detect backend method (ffmpeg vs cv2)
                    method = "ffmpeg" if getattr(rtsp_manager, "proc", None) else "cv2"
                    status_text_compact = f"cam 2 connected: {method}"
                    status_color = (0, 200, 0)
                elif st == "CONNECTING":
                    status_text_compact = "cam 2 connecting"
                    status_color = (0, 200, 200)  # yellow-ish (cyan-ish on BGR)
                else:
                    status_text_compact = "cam 2 offline"
                    status_color = (0, 0, 200)

                frame = overlay.draw_rtsp_status(
                    frame, status_text_compact, status_color
                )
            except Exception:
                pass
            # If QR display is active, show QR code centered with caption
            if qr_manager.is_active() and qr_img is not None:
                # Resize QR code to 1/3 of frame height
                scale = frame.shape[0] // 3 / qr_h
                qr_resized = cv2.resize(
                    qr_img,
                    (int(qr_w * scale), int(qr_h * scale)),
                    interpolation=cv2.INTER_AREA,
                )
                h, w = qr_resized.shape[:2]
                # Center QR code
                y1 = (frame.shape[0] - h) // 2
                x1 = (frame.shape[1] - w) // 2
                y2 = y1 + h
                x2 = x1 + w
                frame[y1:y2, x1:x2] = qr_resized
                # Add caption below QR code
                caption = "Scan for Your Photos"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.2
                thickness = 3
                (tw, th), _ = cv2.getTextSize(caption, font, font_scale, thickness)
                cx = (frame.shape[1] - tw) // 2
                cy = y2 + th + 10
                if cy + th < frame.shape[0]:
                    cv2.putText(
                        frame,
                        caption,
                        (cx, cy),
                        font,
                        font_scale,
                        (0, 0, 0),
                        thickness + 2,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        frame,
                        caption,
                        (cx, cy),
                        font,
                        font_scale,
                        (0, 255, 0),
                        thickness,
                        cv2.LINE_AA,
                    )

            # Add camera settings overlay if visible
            frame = settings_overlay.draw_overlay(frame)

            # Display
            if screen is not None:
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
                # Handle pygame events
                if keyboard_input.handle_pygame_events(
                    state, qr_manager, start_countdown
                ):
                    raise KeyboardInterrupt()
            else:
                try:
                    # Add camera settings overlay if visible
                    frame = settings_overlay.draw_overlay(frame)
                    cv2.imshow(WINDOW_NAME, frame)
                    # Non-blocking waitKey to keep display responsive
                    key = cv2.waitKey(1) & 0xFF
                    if keyboard_input.handle_opencv_key(
                        key, state, qr_manager, start_countdown
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
        gotcha_manager.cleanup()
        qr_manager.cleanup()
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
    main()
