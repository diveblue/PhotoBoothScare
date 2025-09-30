#!/usr/bin/env python3
"""
camera_test.py

Quick test utility to open two camera sources and display them side-by-side using
pygame for rendering and OpenCV for capture. Usage:

  python3 camera_test.py [source1] [source2]

source may be an integer index (0), a /dev/video path (/dev/video0) or an RTSP URL.
Defaults: 0 1
"""

import sys
import time
import argparse
import cv2
import pygame


def parse_source(s):
    # integer -> numeric device index
    if s is None:
        return 0
    try:
        return int(s)
    except Exception:
        return s


def open_cap(src):
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[WARN] Could not open source {src}")
        return None
    return cap


def frame_to_surface(frame, size=None):
    # frame is BGR from OpenCV; convert to RGB then to pygame surface
    try:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    except Exception:
        return None
    if size is not None:
        rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_LINEAR)
    surf = pygame.image.frombuffer(rgb.tobytes(), rgb.shape[1::-1], "RGB")
    return surf


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src1", nargs="?", default="0", help="first camera source")
    p.add_argument("src2", nargs="?", default="1", help="second camera source")
    args = p.parse_args()

    srcs = [parse_source(args.src1), parse_source(args.src2)]

    print(f"[INFO] Sources: {srcs}")

    caps = [open_cap(s) for s in srcs]

    pygame.init()
    # prefer a reasonable preview size
    W, H = 1280, 480
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Camera Test")
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 24)

    running = True
    last_reopen = 0
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        now = time.time()
        # try read frames
        frames = []
        for i, cap in enumerate(caps):
            if cap is None or not cap.isOpened():
                frames.append(None)
                continue
            try:
                ok, frame = cap.read()
            except Exception as e:
                print(f"[WARN] read() raised for src {srcs[i]}: {e}")
                ok = False
                frame = None

            if not ok or frame is None:
                frames.append(None)
            else:
                frames.append(frame)

        # if both None, attempt a reopen occasionally
        if (now - last_reopen) > 2.0:
            for i, f in enumerate(frames):
                if f is None:
                    if caps[i] is not None:
                        try:
                            caps[i].release()
                        except Exception:
                            pass
                    caps[i] = open_cap(srcs[i])
            last_reopen = now

        screen.fill((0, 0, 0))

        # render each feed side-by-side
        half_w = W // 2
        for i, frame in enumerate(frames):
            x = i * half_w
            if frame is not None:
                surf = frame_to_surface(frame, size=(half_w, H))
                if surf:
                    screen.blit(surf, (x, 0))
            else:
                # draw placeholder
                pygame.draw.rect(screen, (32, 32, 32), (x, 0, half_w, H))
                txt = font.render(f"No feed: {srcs[i]}", True, (200, 200, 200))
                screen.blit(txt, (x + 10, 10))

        # overlay simple labels and fps
        fps = int(clock.get_fps())
        screen.blit(font.render(f"FPS: {fps}", True, (255, 255, 0)), (10, H - 30))
        for i, s in enumerate(srcs):
            label = font.render(str(s), True, (255, 255, 255))
            screen.blit(label, (i * half_w + 10, 10))

        pygame.display.flip()
        clock.tick(30)

    # cleanup
    for c in caps:
        try:
            if c is not None:
                c.release()
        except Exception:
            pass
    pygame.quit()


if __name__ == "__main__":
    main()
