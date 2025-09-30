#!/usr/bin/env python3
"""
Quick pygame test for Wayland on Pi 4
"""

import os
import pygame
import numpy as np
import cv2
import time

print("Testing pygame on Wayland...")

# Set SDL video driver for Wayland
os.environ["SDL_VIDEODRIVER"] = "wayland"

try:
    pygame.init()
    pygame.display.init()

    info = pygame.display.Info()
    screen_size = (info.current_w, info.current_h)
    print(f"Display info: {screen_size}")

    # Try windowed mode first
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PhotoBooth Preview Test")

    print("✅ Pygame window created successfully!")
    print("Showing test pattern for 5 seconds...")

    # Create test image with OpenCV
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:] = (50, 100, 50)  # Dark green background

    # Add some text
    cv2.putText(
        test_frame,
        "PhotoBooth Preview",
        (50, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (255, 255, 255),
        3,
    )
    cv2.putText(
        test_frame,
        "Pygame + Wayland",
        (50, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2,
    )
    cv2.putText(
        test_frame,
        "Press any key to continue",
        (50, 350),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2,
    )

    # Convert BGR to RGB for pygame
    rgb_frame = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)

    # Scale to screen
    surf = pygame.image.frombuffer(rgb_frame.tobytes(), (640, 480), "RGB")
    surf = pygame.transform.scale(surf, (800, 600))

    start_time = time.time()
    running = True

    while running and (time.time() - start_time) < 10:  # 10 second timeout
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                print(f"Key pressed: {event.key}")
                running = False

        screen.fill((0, 0, 0))
        screen.blit(surf, (0, 0))
        pygame.display.flip()

        time.sleep(0.1)

    pygame.quit()
    print("✅ Pygame test completed successfully!")

except Exception as e:
    print(f"❌ Pygame test failed: {e}")

# Also test X11 as fallback
print("\nTesting pygame with X11...")
try:
    os.environ["SDL_VIDEODRIVER"] = "x11"

    pygame.init()
    pygame.display.init()

    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("X11 Test")

    print("✅ X11 pygame works too!")
    pygame.quit()

except Exception as e:
    print(f"❌ X11 pygame failed: {e}")

print("\nDone!")
