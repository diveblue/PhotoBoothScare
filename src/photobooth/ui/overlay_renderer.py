"""
OverlayRenderer - UI Overlay Management and Text Rendering

RESPONSIBILITIES:
- Renders all text overlays on camera frames based on session state
- Manages countdown numbers, gotcha text, idle instructions, and QR code display
- Handles font rendering with both PIL (custom fonts) and OpenCV (fallback) support
- Provides visual feedback for all photobooth session phases

KEY METHODS:
- draw_overlay(): Main rendering method that draws appropriate overlays based on state
- draw_countdown(): Large countdown numbers with pulsing animation
- draw_gotcha_text(): Scare text with dramatic visual effects
- draw_idle_text(): Instructions when system is waiting for user
- draw_qr_overlay(): QR code display with "Scan for Photos" caption

RENDERING FEATURES:
- Creepster font support via PIL for Halloween theming
- OpenCV fallback for systems without PIL/custom fonts
- Responsive text sizing based on frame dimensions
- Visual effects including shadows, outlines, and animations

ARCHITECTURE:
- Pure rendering class following Single Responsibility principle
- Stateless design - all state passed in via state parameter
- UI separation from business logic and session management
- Cross-platform font handling with graceful degradation
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
    """
    Handles all visual overlay rendering for photobooth display.

    Renders text, countdown, and visual effects on camera frames
    based on current session state with cross-platform font support.
    """

    def __init__(self, config):
        self.font_path = config["FONT_PATH"]
        self.font_size = config["FONT_SIZE"]
        self.gotcha_text = config["OVERLAY_GOTCHA_TEXT"]
        self.idle_text = config["OVERLAY_IDLE_TEXT"]
        self.pil_font = None
        if ImageFont is not None and os.path.exists(self.font_path):
            try:
                self.pil_font = ImageFont.truetype(self.font_path, self.font_size)
            except Exception:
                self.pil_font = None

    def draw_overlay(self, frame, state):
        # Debug: Show what state we're receiving (limit to avoid spam)
        if (
            not hasattr(self, "_last_state_debug")
            or time.time() - self._last_state_debug > 2.0
        ):
            phase = getattr(state, "phase", "unknown")
            countdown_number = getattr(state, "countdown_number", None)
            # gotcha_active removed
            print(
                f"🎨 OverlayRenderer: phase={phase}, countdown_number={countdown_number}"
            )
            print(
                f"OverlayRenderer: input frame shape={getattr(frame, 'shape', None)} state={state}"
            )
            self._last_state_debug = time.time()

        result = self._draw_overlay_impl(frame, state)
        print(
            f"[DEBUG] _draw_overlay_impl: returned {type(result)}, shape={getattr(result, 'shape', None)}"
        )
        if result is None:
            print(
                "[DEBUG] OverlayRenderer: _draw_overlay_impl returned None, falling back to original frame"
            )
            return frame
        return result

    def _draw_overlay_impl(self, frame, state):
        print(
            f"[DEBUG] _draw_overlay_impl: called with frame shape={getattr(frame, 'shape', None)} state={state}"
        )
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 6
        use_pil = (
            self.pil_font is not None and ImageDraw is not None and Image is not None
        )

        # Smile overlay: show whenever phase == 'smile'
        if getattr(state, "phase", None) == "smile":
            smile_text = "SMILE!"
            if use_pil:
                try:
                    if (
                        self.pil_font is not None
                        and ImageDraw is not None
                        and Image is not None
                    ):
                        img_pil = Image.fromarray(frame)
                        draw = ImageDraw.Draw(img_pil)
                        bbox = self.pil_font.getbbox(smile_text)
                        tw = bbox[2] - bbox[0]
                        th = bbox[3] - bbox[1]
                        x = (w - tw) // 2
                        y = (h - th) // 2
                        draw.text(
                            (x + 4, y + 4),
                            smile_text,
                            font=self.pil_font,
                            fill=(0, 0, 0, 255),
                        )
                        draw.text(
                            (x, y),
                            smile_text,
                            font=self.pil_font,
                            fill=(255, 0, 0, 255),
                        )
                        return np.array(img_pil)
                except Exception:
                    pass
            # OpenCV fallback
            scale = 3.0
            (tw, th), _ = cv2.getTextSize(smile_text, font, scale, thickness)
            x = (w - tw) // 2
            y = (h + th) // 2
            cv2.putText(
                frame,
                smile_text,
                (x + 6, y + 6),
                font,
                scale,
                (0, 0, 0),
                thickness + 4,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                smile_text,
                (x, y),
                font,
                scale,
                (0, 0, 255),
                thickness,
                cv2.LINE_AA,
            )
            return frame
        # Gotcha overlay with integrated QR code: show when phase == 'gotcha'
        if getattr(state, "phase", None) == "gotcha":
            lines = self.gotcha_text.split("\n")
            pil_success = False
            if use_pil:
                try:
                    if (
                        self.pil_font is not None
                        and ImageDraw is not None
                        and Image is not None
                    ):
                        img_pil = Image.fromarray(frame)
                        draw = ImageDraw.Draw(img_pil)
                        line_heights = [
                            self.pil_font.getbbox(line)[3]
                            - self.pil_font.getbbox(line)[1]
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
                                (x + 4, y + 4),
                                line,
                                font=self.pil_font,
                                fill=(0, 0, 0, 255),
                            )
                            draw.text(
                                (x, y),
                                line,
                                font=self.pil_font,
                                fill=(0, 0, 255, 255),
                            )
                            y += th
                        frame = np.array(img_pil)
                        pil_success = True
                except Exception:
                    pil_success = False
            if not pil_success:
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
            if getattr(state, "qr_url", None):
                frame = self._draw_qr_overlay(frame, getattr(state, "qr_url", None))
            return frame

        # Idle overlay
        if getattr(state, "phase", None) != "countdown":
            print("[DEBUG] _draw_overlay_impl: idle overlay path")
            blink_period = 4.0
            blink_on = 3.0
            t = time.time() % blink_period
            if t < blink_on:
                text = self.idle_text
                scale = 2.0
                pil_success = False
                if use_pil:
                    try:
                        if (
                            self.pil_font is not None
                            and ImageDraw is not None
                            and Image is not None
                        ):
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
                                self.pil_font.getbbox(line)[3]
                                - self.pil_font.getbbox(line)[1]
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
                                    (x, y),
                                    line,
                                    font=self.pil_font,
                                    fill=(0, 0, 255, 255),
                                )
                                y += th
                            print(
                                "[DEBUG] _draw_overlay_impl: idle overlay PIL path returning image"
                            )
                            return np.array(img_pil)
                            pil_success = True
                    except Exception:
                        pil_success = False
                if not pil_success:
                    # OpenCV fallback
                    max_width = int(w * 0.95)
                    words = text.split()
                    lines = []
                    current = words[0]
                    for word in words[1:]:
                        test_line = current + " " + word
                        (tw, th), _ = cv2.getTextSize(test_line, font, 1.0, thickness)
                        if tw > max_width:
                            lines.append(current)
                            current = word
                        else:
                            current = test_line
                    lines.append(current)
                    scale = 1.5
                    line_sizes = [
                        cv2.getTextSize(line, font, scale, thickness)[0]
                        for line in lines
                    ]
                    total_height = sum([size[1] for size in line_sizes])
                    y = (h - total_height) // 2
                    for line in lines:
                        (tw, th), _ = cv2.getTextSize(line, font, scale, thickness)
                        x = (w - tw) // 2
                        cv2.putText(
                            frame,
                            line,
                            (x + 3, y + th + 3),
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
                    # Debug print removed for normal operation
                    return frame
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
                    # Debug print removed for normal operation
                    return frame
            # Debug print removed for normal operation
            return frame

        # Countdown overlay (phase == 'countdown')
        seconds_left = getattr(state, "countdown_number", None)
        pil_success = False
        if use_pil:
            try:
                if (
                    self.pil_font is not None
                    and ImageDraw is not None
                    and Image is not None
                ):
                    img_pil = Image.fromarray(frame)
                    draw = ImageDraw.Draw(img_pil)
                    if seconds_left is not None and seconds_left > 0:
                        text = str(seconds_left)
                        font_size = self.pil_font.size * 2
                        color = (0, 0, 255, 255)
                    else:
                        text = "SMILE!"
                        font_size = self.pil_font.size * 3
                        color = (0, 0, 255, 255)
                    try:
                        font_for_count = self.pil_font.font_variant(size=font_size)
                    except Exception:
                        font_for_count = self.pil_font
                    bbox = font_for_count.getbbox(text)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    x = (w - tw) // 2
                    y = (h - th) // 2
                    draw.text(
                        (x + 4, y + 4),
                        text,
                        font=font_for_count,
                        fill=(0, 0, 0, 255),
                    )
                    draw.text((x, y), text, font=font_for_count, fill=color)
                    pil_success = True
                    return np.array(img_pil)
            except Exception:
                pil_success = False
        if not pil_success:
            # OpenCV fallback
            if seconds_left is not None and seconds_left > 0:
                text = str(seconds_left)
                scale = 4.0
                color = (0, 0, 255)
            else:
                text = "SMILE!"
                scale = 5.0
                color = (0, 0, 255)
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
                thickness + 4,
                cv2.LINE_AA,
            )
            cv2.putText(frame, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
            return frame
        else:
            if seconds_left is None or seconds_left <= 0:
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
        return frame

    def draw_rtsp_status(self, frame, status_text, status_color):
        """
        Draws a small overlay in the lower right corner with RTSP status.
        status_text: 'RTSP Connecting', 'ONLINE', 'OFFLINE', etc.
        status_color: (0,255,0) for green, (0,0,255) for red, etc.
        """
        import cv2

        h, w = frame.shape[:2]
        pad = 16
        font = cv2.FONT_HERSHEY_SIMPLEX
        # Reduce font size to about half for a compact indicator
        font_scale = 0.4
        thickness = 1
        text = status_text
        (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
        y = h - pad
        # Layout: compute total box width including dot + spacing + text + inner padding
        dot_radius = 6
        spacing = 8
        inner_pad = 10
        total_box_width = (dot_radius * 2) + spacing + tw + (inner_pad * 2)
        box_right = w - 10
        box_left = box_right - total_box_width
        # Draw background rectangle
        cv2.rectangle(
            frame,
            (int(box_left), int(y - th - inner_pad)),
            (int(box_right), int(y + inner_pad)),
            (30, 30, 30),
            -1,
        )
        # Dot position (left inside box)
        dot_x = int(box_left + inner_pad + dot_radius)
        dot_y = int(y - th // 2)
        cv2.circle(frame, (dot_x, dot_y), dot_radius, status_color, -1)
        # Text position (to the right of the dot)
        text_x = int(box_left + inner_pad + (dot_radius * 2) + spacing)
        cv2.putText(
            frame,
            text,
            (text_x, y),
            font,
            font_scale,
            status_color,
            thickness,
            cv2.LINE_AA,
        )
        return frame

    def _draw_qr_overlay(self, frame, qr_url):
        """Draw QR code in upper right corner with 'Scan for Photos' caption."""
        try:
            from photobooth.utils.qr_generator import generate_qr
            import tempfile
            import os

            h, w = frame.shape[:2]

            # Generate QR code to temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                qr_path = tmp.name

            generate_qr(qr_url, qr_path, size=6)  # Smaller size for corner display
            qr_img = cv2.imread(qr_path)

            if qr_img is not None:
                qr_h, qr_w = qr_img.shape[:2]

                # Position in upper right with padding
                margin = 20
                qr_x = w - qr_w - margin
                qr_y = margin

                # Ensure QR code fits on screen
                if qr_x > 0 and qr_y + qr_h < h:
                    # Overlay QR code
                    frame[qr_y : qr_y + qr_h, qr_x : qr_x + qr_w] = qr_img

                    # Add caption below QR code
                    caption = "Scan for Photos"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    thickness = 2
                    (tw, th), _ = cv2.getTextSize(caption, font, font_scale, thickness)

                    # Center caption under QR code
                    caption_x = qr_x + (qr_w - tw) // 2
                    caption_y = qr_y + qr_h + th + 10

                    if caption_y < h - 10:  # Ensure caption fits
                        # Caption background
                        cv2.rectangle(
                            frame,
                            (caption_x - 5, caption_y - th - 5),
                            (caption_x + tw + 5, caption_y + 5),
                            (0, 0, 0),
                            -1,
                        )
                        # Caption text
                        cv2.putText(
                            frame,
                            caption,
                            (caption_x, caption_y),
                            font,
                            font_scale,
                            (255, 255, 255),
                            thickness,
                            cv2.LINE_AA,
                        )

            # Clean up temp file
            try:
                os.unlink(qr_path)
            except Exception:
                pass
        except Exception:
            # Silently fail if QR generation doesn't work
            pass
        return frame
