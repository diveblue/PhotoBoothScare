"""
overlay_renderer.py
Handles all overlay drawing logic for the photo booth.
"""

import os
import cv2
import time
import numpy as np

try:
    from PIL import ImageFont, ImageDraw, Image
except ImportError:
    ImageFont = None
    ImageDraw = None
    Image = None


class OverlayRenderer:
    def __init__(self, font_path, font_size, gotcha_text, idle_text):
        self.font_path = font_path
        self.font_size = font_size
        self.gotcha_text = gotcha_text
        self.idle_text = idle_text
        self.pil_font = None
        if ImageFont is not None and os.path.exists(self.font_path):
            try:
                self.pil_font = ImageFont.truetype(self.font_path, self.font_size)
            except Exception:
                self.pil_font = None

    def draw_overlay(self, frame, state):
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 6
        use_pil = (
            self.pil_font is not None and ImageDraw is not None and Image is not None
        )
        # Gotcha overlay
        if state.get("gotcha_active", False):
            lines = self.gotcha_text.split("\n")
            if use_pil:
                img_pil = Image.fromarray(frame)
                draw = ImageDraw.Draw(img_pil)
                line_heights = [
                    self.pil_font.getbbox(line)[3] - self.pil_font.getbbox(line)[1]
                    for line in lines
                ]
                total_height = sum(line_heights)
                y = (h - total_height) // 2
                for line in lines:
                    bbox = self.pil_font.getbbox(line)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    x = (w - tw) // 2
                    draw.text(
                        (x + 4, y + 4), line, font=self.pil_font, fill=(0, 0, 0, 255)
                    )
                    draw.text((x, y), line, font=self.pil_font, fill=(0, 0, 255, 255))
                    y += th
                return np.array(img_pil)
            else:
                scale = 2.5
                line_sizes = [
                    cv2.getTextSize(line, font, scale, thickness)[0] for line in lines
                ]
                total_height = sum([size[1] for size in line_sizes])
                y = (h - total_height) // 2
                for line in lines:
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
        # Idle overlay
        if not state["countdown_active"]:
            blink_period = 4.0
            blink_on = 3.0
            t = time.time() % blink_period
            if t < blink_on:
                text = self.idle_text
                scale = 2.0
                if use_pil:
                    img_pil = Image.fromarray(frame)
                    draw = ImageDraw.Draw(img_pil)
                    max_width = int(w * 0.95)
                    words = text.split()
                    lines = []
                    current = words[0]
                    for word in words[1:]:
                        test_line = current + " " + word
                        bbox = self.pil_font.getbbox(test_line)
                        tw = bbox[2] - bbox[0]
                        if tw > max_width:
                            lines.append(current)
                            current = word
                        else:
                            current = test_line
                    lines.append(current)
                    total_height = sum(
                        self.pil_font.getbbox(line)[3] - self.pil_font.getbbox(line)[1]
                        for line in lines
                    )
                    y = (h - total_height) // 2
                    for line in lines:
                        bbox = self.pil_font.getbbox(line)
                        tw = bbox[2] - bbox[0]
                        th = bbox[3] - bbox[1]
                        x = (w - tw) // 2
                        draw.text(
                            (x + 3, y + 3),
                            line,
                            font=self.pil_font,
                            fill=(0, 0, 0, 255),
                        )
                        draw.text(
                            (x, y), line, font=self.pil_font, fill=(0, 0, 255, 255)
                        )
                        y += th
                    return np.array(img_pil)
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
        # Countdown overlay
        seconds_left = int(round(state["count_end_time"] - time.time()))
        if use_pil:
            img_pil = Image.fromarray(frame)
            draw = ImageDraw.Draw(img_pil)
            countdown_number = state.get("countdown_number")
            if countdown_number is not None:
                text = str(countdown_number)
                font_size = self.pil_font.size * 2
                color = (0, 0, 255, 255)
            elif state.get("countdown_active") and not state.get("countdown_number"):
                text = "SMILE!"
                font_size = self.pil_font.size * 3
                color = (0, 0, 255, 255)
            else:
                return frame
            try:
                font_for_count = self.pil_font.font_variant(size=font_size)
            except Exception:
                font_for_count = self.pil_font
            bbox = font_for_count.getbbox(text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (w - tw) // 2
            y = (h - th) // 2
            draw.text((x + 4, y + 4), text, font=font_for_count, fill=(0, 0, 0, 255))
            draw.text((x, y), text, font=font_for_count, fill=color)
            return np.array(img_pil)
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
                frame,
                text,
                (x, y),
                font,
                scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )
            return frame
