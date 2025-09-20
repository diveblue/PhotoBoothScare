import time
import threading
import cv2
import pygame
import os

try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except Exception:
    Picamera2 = None
    PICAMERA2_AVAILABLE = False

# Use real GPIO on Raspberry Pi, fallback to fake_gpio elsewhere
try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:
    import fake_gpio as GPIO

# ---- Config ----
BUTTON_PIN = 17
RELAY_PIN = 23
COUNTDOWN_SECONDS = 3
WINDOW_NAME = "Haunt Photo-Booth Preview"

# Camera source selection
# If Picamera2 is available (Raspberry Pi), we'll use it automatically.
# Otherwise, we'll fall back to OpenCV with the default webcam (device 0) or a file path/RTSP URL if you set one.
USE_WEBCAM = (
    True  # True = use default webcam (device 0) when Picamera2 is not available
)
# Optional: set to a file path or RTSP URL if you want to use a different source on non-Pi systems
# NOTE: Do not store real credentials in source control.
TEST_VIDEO_PATH = 0  # e.g., 0 for default cam, or "rtsp://username:password@ip:554/cam/realmonitor?channel=1&subtype=0"

# Display selection
# In terminal-only (no desktop), prefer pygame KMSDRM fullscreen for kiosk display.
# Can be disabled with env USE_PYGAME_DISPLAY=0
USE_PYGAME_DISPLAY = os.environ.get("USE_PYGAME_DISPLAY", "1") != "0"
os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
# ---- Audio setup (pygame) ----
class _Null:
    def play(self):
        pass

beep = _Null()
shutter = _Null()
try:
    pygame.mixer.init()
    try:
        beep = pygame.mixer.Sound("assets/beep.wav")
        shutter = pygame.mixer.Sound("assets/shutter.wav")
    except Exception as e:
        print(
            "[WARN] Audio files not found or could not be loaded, continuing sans sound:",
            e,
        )
except Exception as e:
    print("[WARN] Audio mixer init failed; continuing without sounds:", e)

# ---- GPIO mock setup ----
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# ---- State ----
state = {
    "countdown_active": False,
    "count_end_time": 0.0,
}


def play_beep():
    beep.play()


def play_shutter():
    shutter.play()


def trigger_scare():
    # Relay HIGH briefly, then LOW
    GPIO.output(RELAY_PIN, 1)
    time.sleep(0.3)
    GPIO.output(RELAY_PIN, 0)


def start_countdown():
    if state["countdown_active"]:
        return
    # Generate session timestamp and unique session ID
    import random
    from datetime import datetime

    session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_id = f"S{random.randint(100, 999)}"
    state["session_time"] = session_time
    state["session_id"] = session_id
    state["countdown_active"] = True
    state["gotcha_active"] = False
    state["count_end_time"] = time.time() + COUNTDOWN_SECONDS

    def sequence():
        # Trigger prop BEFORE countdown
        trigger_scare()
        # Synchronized countdown and beep
        for i in range(COUNTDOWN_SECONDS, 0, -1):
            state["countdown_number"] = i
            play_beep()
            time.sleep(1.0)
        state.pop("countdown_number", None)
        # Final moment: shutter
        play_shutter()
        # Pause for 5 seconds after shutter
        time.sleep(5.0)
        # Show 'Gotcha! Happy Halloween!' overlay for 10 seconds
        state["gotcha_active"] = True
        state["countdown_active"] = False
        state["gotcha_end_time"] = time.time() + 10.0
        time.sleep(10.0)
        state["gotcha_active"] = False

    threading.Thread(target=sequence, daemon=True).start()


def button_callback(_pin):
    # Falling edge detected (simulated)
    start_countdown()


# Register the mock callback
GPIO.add_event_detect(
    BUTTON_PIN, GPIO.FALLING, callback=button_callback, bouncetime=200
)


def draw_overlay(frame):
    """Draws the countdown overlay text on frame."""
    h, w = frame.shape[:2]
    # Try to use a Halloween font if available, else fallback
    try:
        import os
        import numpy as np
        from PIL import ImageFont, ImageDraw, Image

        font_path = os.path.join(
            "assets", "Creepster-Regular.ttf"
        )  # Place your Halloween font here
        pil_font = ImageFont.truetype(font_path, 64)
        use_pil = True
    except Exception:
        pil_font = None
        use_pil = False
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 6
    if state.get("gotcha_active", False):
        # Show Gotcha overlay (red, centered, multi-line)
        gotcha_text = "Gotcha!\nHappy Halloween!"
        lines = gotcha_text.split("\n")
        if use_pil and pil_font:
            img_pil = Image.fromarray(frame)
            draw = ImageDraw.Draw(img_pil)
            # Calculate total height
            line_heights = [
                pil_font.getbbox(line)[3] - pil_font.getbbox(line)[1] for line in lines
            ]
            total_height = sum(line_heights)
            y = (h - total_height) // 2
            for i, line in enumerate(lines):
                bbox = pil_font.getbbox(line)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                x = (w - tw) // 2
                # Shadow
                draw.text((x + 4, y + 4), line, font=pil_font, fill=(0, 0, 0, 255))
                # Red text
                draw.text((x, y), line, font=pil_font, fill=(0, 0, 255, 255))
                y += th
            frame = np.array(img_pil)
        else:
            scale = 2.5
            # Calculate total height for OpenCV
            line_sizes = [
                cv2.getTextSize(line, font, scale, thickness)[0] for line in lines
            ]
            total_height = sum([size[1] for size in line_sizes])
            y = (h - total_height) // 2
            for i, line in enumerate(lines):
                (tw, th), _ = cv2.getTextSize(line, font, scale, thickness)
                x = (w - tw) // 2
                cv2.putText(
                    frame,
                    line,
                    (x + 4, y + th + 4),
                    font,
                    scale,
                    (0, 0, 0),
                    thickness + 2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    line,
                    (x, y + th),
                    font,
                    scale,
                    (0, 0, 255),
                    thickness,
                    cv2.LINE_AA,
                )
                y += th
        return frame

    if not state["countdown_active"]:
        # Blinking idle overlay: on 3s, off 1s
        blink_period = 4.0
        blink_on = 3.0
        t = time.time() % blink_period
        if t < blink_on:
            text = "Press Button to Take Photo"
            scale = 2.0
            if use_pil and pil_font:
                # Draw with PIL for custom font and wrap text if needed
                img_pil = Image.fromarray(frame)
                draw = ImageDraw.Draw(img_pil)
                max_width = int(w * 0.95)
                words = text.split()
                lines = []
                current = words[0]
                for word in words[1:]:
                    test_line = current + " " + word
                    bbox = pil_font.getbbox(test_line)
                    tw = bbox[2] - bbox[0]
                    if tw > max_width:
                        lines.append(current)
                        current = word
                    else:
                        current = test_line
                lines.append(current)
                # Draw each line, centered vertically
                total_height = sum(
                    pil_font.getbbox(line)[3] - pil_font.getbbox(line)[1]
                    for line in lines
                )
                y = (h - total_height) // 2
                for line in lines:
                    bbox = pil_font.getbbox(line)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    x = (w - tw) // 2
                    # Shadow
                    draw.text((x + 3, y + 3), line, font=pil_font, fill=(0, 0, 0, 255))
                    # Red text
                    draw.text((x, y), line, font=pil_font, fill=(0, 0, 255, 255))
                    y += th
                frame = np.array(img_pil)
            else:
                (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
                x = (w - tw) // 2
                y = (h + th) // 2
                cv2.putText(
                    frame,
                    text,
                    (x + 3, y + 3),
                    font,
                    scale,
                    (0, 0, 0),
                    thickness + 2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    text,
                    (x, y),
                    font,
                    scale,
                    (0, 0, 255),
                    thickness,
                    cv2.LINE_AA,
                )
        return frame
    seconds_left = int(round(state["count_end_time"] - time.time()))
    if use_pil and pil_font:
        # Draw countdown or SMILE! with custom font
        img_pil = Image.fromarray(frame)
        draw = ImageDraw.Draw(img_pil)
        # Use explicit countdown_number if present
        countdown_number = state.get("countdown_number")
        if countdown_number is not None:
            text = str(countdown_number)
            font_size = pil_font.size * 2
            color = (0, 0, 255, 255)  # Red
        elif state.get("countdown_active") and not state.get("countdown_number"):
            # Only show SMILE! if countdown just finished (countdown_active True, but no countdown_number)
            text = "SMILE!"
            font_size = pil_font.size * 3
            color = (0, 0, 255, 255)  # Red
        else:
            # Not in countdown, show nothing (or could show idle overlay)
            return frame
        # Use a resized font for countdown
        try:
            font_for_count = pil_font.font_variant(size=font_size)
        except Exception:
            font_for_count = pil_font
        bbox = font_for_count.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (w - tw) // 2
        y = (h - th) // 2
        # Shadow
        draw.text((x + 4, y + 4), text, font=font_for_count, fill=(0, 0, 0, 255))
        # Main text
        draw.text((x, y), text, font=font_for_count, fill=color)
        frame = np.array(img_pil)
        return frame
    else:
        if seconds_left <= 0:
            text = "SMILE!"
            scale = 3.0
        else:
            text = str(seconds_left)
            scale = 5.0
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
        x = (w - tw) // 2
        y = (h + th) // 2
        cv2.putText(
            frame,
            text,
            (x + 4, y + 4),
            font,
            scale,
            (0, 0, 0),
            thickness + 2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA
        )
        return frame


def main():
    # Initialize camera
    cap = None
    picam2 = None
    if PICAMERA2_AVAILABLE:
        try:
            picam2 = Picamera2()
            cam_config = picam2.create_preview_configuration(main={"size": (1280, 720)})
            picam2.configure(cam_config)
            picam2.start()
            # Warm-up
            time.sleep(0.5)
            print("[INFO] Using PiCam via Picamera2")
        except Exception as e:
            print(f"[WARN] Picamera2 init failed: {e}; falling back to OpenCV capture")
            picam2 = None
    if picam2 is None:
        src = TEST_VIDEO_PATH if USE_WEBCAM else TEST_VIDEO_PATH
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(
                "Could not open camera/video. Check camera connection or TEST_VIDEO_PATH."
            )
            return

    # Init display (pygame fullscreen if requested, else OpenCV window)
    screen = None
    screen_size = None
    if USE_PYGAME_DISPLAY:
        try:
            # Use KMSDRM on console; if running under X/Wayland it will choose appropriate backend
            os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
            if not pygame.get_init():
                pygame.init()
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except Exception:
                    pass
            pygame.display.init()
            info = pygame.display.Info()
            screen_size = (info.current_w, info.current_h)
            screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
            print(f"[INFO] Pygame fullscreen display initialized (kmsdrm): {screen_size}")
        except Exception as e:
            print(f"[WARN] Pygame KMSDRM init failed: {e}; trying fbcon fallback")
            try:
                os.environ["SDL_VIDEODRIVER"] = "fbcon"
                if not pygame.get_init():
                    pygame.init()
                pygame.display.quit()
                pygame.display.init()
                info = pygame.display.Info()
                screen_size = (info.current_w, info.current_h)
                screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
                pygame.mouse.set_visible(False)
                print(f"[INFO] Pygame fullscreen display initialized (fbcon): {screen_size}")
            except Exception as e2:
                print(f"[WARN] Pygame fbcon init failed: {e2}; falling back to OpenCV window (may not work headless)")
                screen = None
                try:
                    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
                except Exception:
                    pass
    else:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        # cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Controls: SPACE = simulate button press, Q = quit")
    video_writer = None
    recording = False
    # Output directories (override via env on Pi, e.g., /mnt/halloween/photos)
    photo_dir = os.environ.get(
        "MEDIA_PHOTOS_DIR", r"\\SKYNAS\web\Halloween2025\media\photos"
    )
    video_dir = os.environ.get(
        "MEDIA_VIDEOS_DIR", r"\\SKYNAS\web\Halloween2025\media\videos"
    )
    # Ensure directories exist if local/mounted
    try:
        os.makedirs(photo_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)
    except Exception:
        # Likely UNC on non-Windows or missing mount; will attempt writes anyway
        pass
    last_countdown_number = None
    smile_captured = False
    try:
        while True:
            # Grab frame from appropriate source
            if picam2 is not None:
                frame = picam2.capture_array()
                ok = frame is not None
                if ok:
                    # Ensure BGR for OpenCV operations
                    try:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    except Exception:
                        pass
            else:
                ok, frame = cap.read()
                if not ok:
                    # For video files, loop
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

            frame = cv2.flip(frame, 1)  # mirror like a real booth

            # Start video recording if countdown just started
            if state.get("countdown_active") and not recording:
                # Prepare video writer
                session_time = state.get("session_time")
                session_id = state.get("session_id")
                video_filename = f"{session_time}_{session_id}_booth.mp4"
                video_path = os.path.join(video_dir, video_filename)
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                fps = 20.0
                height, width = frame.shape[:2]
                video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
                recording = True
                print(f"[INFO] Recording video to {video_path}")
                last_countdown_number = None
                smile_captured = False

            # Save snapshot for each countdown number (only once per number)
            countdown_number = state.get("countdown_number")
            session_time = state.get("session_time")
            session_id = state.get("session_id")
            if state.get("countdown_active") and countdown_number is not None:
                if countdown_number != last_countdown_number:
                    photo_filename = f"{session_time}_{session_id}_photo.jpg"
                    photo_path = os.path.join(photo_dir, photo_filename)
                    cv2.imwrite(photo_path, frame)
                    print(f"[INFO] Saved countdown photo: {photo_path}")
                    last_countdown_number = countdown_number

            # Save snapshot at SMILE! (after countdown, only once)
            if (
                state.get("countdown_active")
                and countdown_number is None
                and not smile_captured
            ):
                photo_filename = f"{session_time}_{session_id}_photo.jpg"
                photo_path = os.path.join(photo_dir, photo_filename)
                cv2.imwrite(photo_path, frame)
                print(f"[INFO] Saved SMILE photo: {photo_path}")
                smile_captured = True

            # Write frame if recording
            if recording and video_writer is not None:
                video_writer.write(frame)

            # Stop recording after gotcha overlay
            if (
                recording
                and not state.get("countdown_active")
                and not state.get("gotcha_active")
            ):
                video_writer.release()
                video_writer = None
                recording = False
                print("[INFO] Video recording stopped and saved.")

            frame = draw_overlay(frame)

            if screen is not None:
                # Convert BGR->RGB and scale to screen while preserving aspect ratio
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                fh, fw = rgb.shape[:2]
                sw, sh = screen_size
                scale = min(sw / fw, sh / fh)
                new_size = (int(fw * scale), int(fh * scale))
                surf_img = cv2.resize(rgb, new_size, interpolation=cv2.INTER_LINEAR)
                # Create surface and blit centered
                surf = pygame.image.frombuffer(surf_img.tobytes(), new_size, "RGB")
                screen.fill((0, 0, 0))
                x = (sw - new_size[0]) // 2
                y = (sh - new_size[1]) // 2
                screen.blit(surf, (x, y))
                pygame.display.flip()
                # Event handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt()
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_q, pygame.K_ESCAPE):
                            raise KeyboardInterrupt()
                        if event.key == pygame.K_SPACE:
                            GPIO.trigger(BUTTON_PIN)
            else:
                # Fallback to OpenCV window
                try:
                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    elif key == ord(" "):
                        GPIO.trigger(BUTTON_PIN)
                except Exception:
                    # Headless: nothing to display; still run
                    pass

    finally:
        if video_writer is not None:
            video_writer.release()
        if cap is not None:
            cap.release()
        if picam2 is not None:
            try:
                picam2.stop()
            except Exception:
                pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            if screen is not None:
                pygame.display.quit()
        except Exception:
            pass
        GPIO.cleanup()


if __name__ == "__main__":
    main()
