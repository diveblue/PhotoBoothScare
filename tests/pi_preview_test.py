#!/usr/bin/env python3
"""
Test the photobooth preview with overlays on Pi 4
This tests the exact same code path as main.py
"""

import os
import sys
import time
import cv2
import pygame
import json

# Import your existing modules
from camera_manager import CameraManager
from overlay_renderer import OverlayRenderer

# Load config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Force OpenCV to use /dev/video0 for this test
TEST_VIDEO_PATH = 0  # This maps to /dev/video0
CAM_RESOLUTION_LOW = tuple(CONFIG["CAM_RESOLUTION_LOW"])
WINDOW_NAME = "PhotoBooth Preview Test"

# Environment detection (same as main.py)
IS_LINUX = os.name == "posix"
HAS_DISPLAY_SERVER = bool(
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
)
SSH_SESSION = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))
ON_CONSOLE_VT = (
    IS_LINUX and not HAS_DISPLAY_SERVER and not SSH_SESSION and sys.stdout.isatty()
)
USE_PYGAME_DISPLAY = os.environ.get("USE_PYGAME_DISPLAY") or (
    "1" if ON_CONSOLE_VT else "0"
)
USE_PYGAME_DISPLAY = USE_PYGAME_DISPLAY == "1"

print(
    f"Environment: Linux={IS_LINUX}, Display={HAS_DISPLAY_SERVER}, SSH={SSH_SESSION}, Console={ON_CONSOLE_VT}"
)
print(f"Using pygame display: {USE_PYGAME_DISPLAY}")


def test_preview():
    """Test the preview with overlays"""
    global USE_PYGAME_DISPLAY

    # Initialize camera
    print(
        f"Initializing camera at {TEST_VIDEO_PATH} with resolution {CAM_RESOLUTION_LOW}"
    )
    camera = CameraManager(
        CAM_RESOLUTION_LOW, test_video_path=TEST_VIDEO_PATH, use_webcam=True
    )

    # Initialize overlay renderer
    overlay = OverlayRenderer(
        font_path=CONFIG["FONT_PATH"], font_size=CONFIG["FONT_SIZE"]
    )

    # Setup display
    screen = None
    screen_size = None

    if USE_PYGAME_DISPLAY:
        print("Setting up pygame display...")
        # Try framebuffer drivers for Pi console
        drivers_to_try = ["kmsdrm", "fbcon", "directfb", "svgalib"]

        if HAS_DISPLAY_SERVER:
            drivers_to_try = ["x11"] + drivers_to_try

        for drv in drivers_to_try:
            try:
                print(f"Trying SDL driver: {drv}")
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

                print(f"✅ Pygame fullscreen with driver '{drv}' -> {screen_size}")
                break

            except Exception as e:
                print(f"❌ Driver '{drv}' failed: {e}")
                screen = None

        if screen is None:
            print("❌ All pygame drivers failed, falling back to OpenCV")
            USE_PYGAME_DISPLAY = False

    if not USE_PYGAME_DISPLAY:
        print("Setting up OpenCV display...")
        try:
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(
                WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )
            print("✅ OpenCV window created")
        except Exception as e:
            print(f"❌ OpenCV window failed: {e}")
            return False

    print("\nStarting preview loop (press 'q' to quit, SPACE for countdown test)...")
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            # Get frame from camera
            frame = camera.get_frame()
            if frame is None:
                print("⚠️  No frame from camera")
                time.sleep(0.1)
                continue

            # Flip frame (like main.py does)
            frame = cv2.flip(frame, 1)

            # Add test overlay
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0

            # Test countdown overlay (cycles 3,2,1)
            countdown_num = (frame_count // 30) % 4  # Change every ~1 second
            if countdown_num > 0:
                frame = overlay.add_countdown_overlay(frame, countdown_num)
            else:
                frame = overlay.add_text_overlay(
                    frame, "Press SPACE for countdown test"
                )

            # Add FPS info
            cv2.putText(
                frame,
                f"FPS: {fps:.1f} Frame: {frame_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Display frame
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

                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return True
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_q, pygame.K_ESCAPE):
                            return True
                        elif event.key == pygame.K_SPACE:
                            print("Countdown test triggered!")
            else:
                # OpenCV display
                try:
                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        return True
                    elif key == ord(" "):
                        print("Countdown test triggered!")
                except Exception as e:
                    print(f"OpenCV display error: {e}")
                    return False

            # Print status every 60 frames
            if frame_count % 60 == 0:
                print(f"Preview running: {frame_count} frames, {fps:.1f} FPS")

    except KeyboardInterrupt:
        print("\nQuitting...")
        return True

    finally:
        camera.release()
        if screen is not None:
            pygame.quit()
        else:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    print("PhotoBooth Preview Test for Pi 4")
    print("=================================")

    success = test_preview()
    if success:
        print("✅ Preview test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Preview test failed")
        sys.exit(1)
