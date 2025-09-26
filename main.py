import os
import platform
import sys
import threading
import time
import cv2
import pygame
import json

from camera_manager import CameraManager
from gpio_manager import GPIOManager
from audio_manager import AudioManager
from overlay_renderer import OverlayRenderer
from photobooth_state import PhotoBoothState

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

IS_LINUX = platform.system() == "Linux"
HAS_DISPLAY_SERVER = bool(
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
)
SSH_SESSION = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))
ON_CONSOLE_VT = (
    IS_LINUX and not HAS_DISPLAY_SERVER and not SSH_SESSION and sys.stdout.isatty()
)
USE_PYGAME_DISPLAY = (
    os.environ.get("USE_PYGAME_DISPLAY") or ("1" if ON_CONSOLE_VT else "0")
) != "0"
if IS_LINUX:
    os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
LOW_POWER = os.environ.get("LOW_POWER") == "1"
CAM_RESOLUTION = CAM_RESOLUTION_LOW if LOW_POWER else CAM_RESOLUTION_HIGH

print(
    f"[ENV] IS_LINUX={IS_LINUX} HAS_DISPLAY_SERVER={HAS_DISPLAY_SERVER} SSH_SESSION={SSH_SESSION} ON_CONSOLE_VT={ON_CONSOLE_VT} USE_PYGAME_DISPLAY={USE_PYGAME_DISPLAY} LOW_POWER={LOW_POWER}"
)


def main():
    """
    Main orchestration function for the PhotoBoothScare application.
    Initializes all managers and runs the main event loop.
    """
    # Initialize managers
    camera = CameraManager(CAM_RESOLUTION, TEST_VIDEO_PATH, USE_WEBCAM)
    gpio = GPIOManager(BUTTON_PIN, RELAY_PIN)
    audio = AudioManager()
    overlay = OverlayRenderer(
        FONT_PATH, FONT_SIZE, OVERLAY_GOTCHA_TEXT, OVERLAY_IDLE_TEXT
    )
    state = PhotoBoothState()

    # Output directories
    photo_dir = os.environ.get(
        "MEDIA_PHOTOS_DIR", r"\\SKYNAS\web\Halloween2025\media\photos"
    )
    video_dir = os.environ.get(
        "MEDIA_VIDEOS_DIR", r"\\SKYNAS\web\Halloween2025\media\videos"
    )
    try:
        os.makedirs(photo_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)
    except Exception:
        pass

    # Display setup
    screen = None
    screen_size = None
    if USE_PYGAME_DISPLAY:
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
                screen_size = (info.current_w, info.current_h)
                screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
                pygame.mouse.set_visible(False)
                print(f"[INFO] Pygame fullscreen with driver '{drv}' -> {screen_size}")
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
            except Exception:
                pass
    else:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    print("Controls: SPACE = simulate button press, Q = quit")

    # Countdown/trigger logic
    def start_countdown():
        if state.countdown_active:
            return
        state.start_countdown(COUNTDOWN_SECONDS)

        def sequence():
            gpio.trigger_scare()
            for i in range(COUNTDOWN_SECONDS, 0, -1):
                state.countdown_number = i
                audio.play_beep()
                time.sleep(1.0)
            state.countdown_number = None
            audio.play_shutter()
            time.sleep(5.0)
            state.trigger_gotcha(10)
            state.countdown_active = False
            time.sleep(10.0)
            state.end_gotcha()

        threading.Thread(target=sequence, daemon=True).start()

    def button_callback(_pin):
        start_countdown()

    gpio.add_event_detect(button_callback)

    video_writer = None
    recording = False
    last_countdown_number = None
    smile_captured = False
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
            frame = cv2.flip(frame, 1)

            # Start video recording if countdown just started
            if state.countdown_active and not recording:
                video_filename = f"{state.session_time}_{state.session_id}_booth.mp4"
                video_path = os.path.join(video_dir, video_filename)
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                fps = 15.0 if LOW_POWER else 20.0
                height, width = frame.shape[:2]
                video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
                recording = True
                print(f"[INFO] Recording video to {video_path}")
                last_countdown_number = None
                smile_captured = False

            # Save snapshot for each countdown number (only once per number)
            countdown_number = state.countdown_number
            if state.countdown_active and countdown_number is not None:
                if countdown_number != last_countdown_number:
                    photo_filename = (
                        f"{state.session_time}_{state.session_id}_photo.jpg"
                    )
                    photo_path = os.path.join(photo_dir, photo_filename)
                    cv2.imwrite(photo_path, frame)
                    print(f"[INFO] Saved countdown photo: {photo_path}")
                    last_countdown_number = countdown_number

            # Save snapshot at SMILE! (after countdown, only once)
            if (
                state.countdown_active
                and countdown_number is None
                and not smile_captured
            ):
                photo_filename = f"{state.session_time}_{state.session_id}_photo.jpg"
                photo_path = os.path.join(photo_dir, photo_filename)
                cv2.imwrite(photo_path, frame)
                print(f"[INFO] Saved SMILE photo: {photo_path}")
                smile_captured = True

            # Write frame if recording
            if recording and video_writer is not None:
                video_writer.write(frame)

            # Stop recording after gotcha overlay
            if recording and not state.countdown_active and not state.gotcha_active:
                video_writer.release()
                video_writer = None
                recording = False
                print("[INFO] Video recording stopped and saved.")

            # Draw overlay
            frame = overlay.draw_overlay(frame, vars(state))

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
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt()
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_q, pygame.K_ESCAPE):
                            raise KeyboardInterrupt()
                        if event.key == pygame.K_SPACE:
                            start_countdown()
            else:
                try:
                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    elif key == ord(" "):
                        start_countdown()
                except Exception:
                    pass
    finally:
        if video_writer is not None:
            video_writer.release()
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
