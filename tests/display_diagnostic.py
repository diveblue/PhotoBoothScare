#!/usr/bin/env python3
"""
Display diagnostic for PhotoBooth - check why preview isn't showing
"""

import os
import sys
import platform
import cv2
import pygame

print("PhotoBooth Display Diagnostic")
print("=" * 40)

# Environment detection (exactly like main.py)
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
) == "1"

print(f"Platform: {platform.system()}")
print(f"IS_LINUX: {IS_LINUX}")
print(f"HAS_DISPLAY_SERVER: {HAS_DISPLAY_SERVER}")
print(f"SSH_SESSION: {SSH_SESSION}")
print(f"ON_CONSOLE_VT: {ON_CONSOLE_VT}")
print(f"USE_PYGAME_DISPLAY: {USE_PYGAME_DISPLAY}")

# Check environment variables
print("\nEnvironment variables:")
print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
print(f"WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'Not set')}")
print(f"SSH_CONNECTION: {os.environ.get('SSH_CONNECTION', 'Not set')}")
print(f"SSH_TTY: {os.environ.get('SSH_TTY', 'Not set')}")
print(f"XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'Not set')}")

# Test pygame display
print("\n" + "=" * 40)
print("Testing Pygame Display")
print("=" * 40)

if USE_PYGAME_DISPLAY:
    # Try drivers like main.py does
    if IS_LINUX and HAS_DISPLAY_SERVER:
        drivers_to_try = ["x11", "kmsdrm", "fbcon", "directfb"]
    else:
        drivers_to_try = ["kmsdrm", "fbcon", "directfb", "svgalib"]

    print(f"Will try drivers: {drivers_to_try}")

    screen = None
    working_driver = None

    for drv in drivers_to_try:
        print(f"\nTrying SDL driver: {drv}")
        try:
            os.environ["SDL_VIDEODRIVER"] = drv

            if not pygame.get_init():
                pygame.init()
            else:
                pygame.display.quit()

            pygame.display.init()
            info = pygame.display.Info()
            screen_size = (info.current_w, info.current_h)
            screen = pygame.display.set_mode((640, 480), 0)  # Small window first

            print(f"✅ Driver '{drv}' SUCCESS -> screen size: {screen_size}")
            print(f"   Display surface: {screen.get_size()}")
            working_driver = drv

            # Try fullscreen
            try:
                screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
                print(f"✅ Fullscreen mode works: {screen_size}")
            except Exception as e:
                print(f"⚠️  Fullscreen failed: {e}")

            pygame.display.quit()
            break

        except Exception as e:
            print(f"❌ Driver '{drv}' FAILED: {e}")
            screen = None

    if working_driver:
        print(f"\n✅ Best pygame driver: {working_driver}")
    else:
        print("\n❌ No pygame drivers worked!")

else:
    print("Pygame display disabled by environment detection")

# Test OpenCV display
print("\n" + "=" * 40)
print("Testing OpenCV Display")
print("=" * 40)

try:
    print("Testing cv2.namedWindow()...")
    cv2.namedWindow("test_window", cv2.WINDOW_NORMAL)
    print("✅ OpenCV window created successfully")

    # Test if we can show something
    import numpy as np

    test_img = np.zeros((240, 320, 3), dtype=np.uint8)
    test_img[:] = (0, 100, 0)  # Dark green

    cv2.putText(
        test_img,
        "OpenCV Test",
        (50, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    print("Showing test image for 3 seconds...")
    cv2.imshow("test_window", test_img)

    # Wait and check for display
    key = cv2.waitKey(3000)  # 3 seconds
    print(f"✅ OpenCV display test completed (key pressed: {key})")

    cv2.destroyAllWindows()

except Exception as e:
    print(f"❌ OpenCV display failed: {e}")

# Check if we're in a virtual terminal
print("\n" + "=" * 40)
print("Terminal/Console Information")
print("=" * 40)

print(f"sys.stdout.isatty(): {sys.stdout.isatty()}")
print(f"TERM: {os.environ.get('TERM', 'Not set')}")
print(f"TTY: {os.environ.get('TTY', 'Not set')}")

if IS_LINUX:
    try:
        with open("/proc/version", "r") as f:
            print(f"Kernel: {f.read().strip()}")
    except Exception:
        pass

    # Check if we can access framebuffer
    fb_devices = [f for f in os.listdir("/dev") if f.startswith("fb")]
    print(f"Framebuffer devices: {fb_devices}")

    if fb_devices:
        fb0_path = "/dev/fb0"
        if os.path.exists(fb0_path):
            try:
                stat = os.stat(fb0_path)
                print(f"✅ {fb0_path} exists and accessible")
            except Exception as e:
                print(f"❌ {fb0_path} not accessible: {e}")

print("\n" + "=" * 40)
print("Recommendations")
print("=" * 40)

if USE_PYGAME_DISPLAY and not working_driver:
    print("❌ PROBLEM: Pygame display enabled but no drivers work")
    print("   Solutions:")
    print("   1. Run from desktop environment (not SSH)")
    print("   2. Check user permissions for framebuffer access")
    print("   3. Try: export USE_PYGAME_DISPLAY=0")

elif not USE_PYGAME_DISPLAY:
    print("ℹ️  OpenCV display mode active")
    print("   - Requires X11/Wayland display server")
    print("   - Won't work on console without X forwarding")

if HAS_DISPLAY_SERVER:
    print("✅ Display server detected - OpenCV should work")
else:
    print("⚠️  No display server - need pygame framebuffer mode")

print("\n" + "=" * 40)
