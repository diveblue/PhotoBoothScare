"""
settings_overlay.py
Handles visual overlay display for camera settings adjustments
"""

import time
import cv2


class SettingsOverlay:
    def __init__(self, duration=3.0):
        self.duration = duration
        self.timer = 0
        self.last_change = ""
        self.current_settings = {}

    def show_setting_change(self, setting_name, display_value):
        """Trigger overlay display for a setting change."""
        self.last_change = f"🎛️ {setting_name}: {display_value}"
        self.timer = time.time()

    def update_current_settings(
        self,
        wb_mode,
        wb_modes,
        brightness,
        contrast,
        saturation,
        exposure,
        gain,
        noise_reduction,
    ):
        """Update the current settings display."""
        self.current_settings = {
            "wb_mode": wb_mode,
            "wb_modes": wb_modes,
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "exposure": exposure,
            "gain": gain,
            "noise_reduction": noise_reduction,
        }

    def is_visible(self):
        """Check if overlay should be visible."""
        return self.timer > 0 and time.time() - self.timer < self.duration

    def draw_overlay(self, frame):
        """Draw settings overlay on frame if visible."""
        if not self.is_visible():
            return frame

        # Semi-transparent overlay background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (650, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

        # Current settings text
        settings = self.current_settings
        if settings:
            wb_name = (
                settings["wb_modes"][settings["wb_mode"]]
                if settings["wb_modes"]
                else "Unknown"
            )
            settings_text = [
                f"WB: {wb_name}  Bright: {settings['brightness']:.2f}  Contrast: {settings['contrast']:.1f}",
                f"Sat: {settings['saturation']:.1f}  Exp: {settings['exposure']}µs  Gain: {settings['gain']:.1f}",
                self.last_change,
            ]
        else:
            settings_text = ["Camera Settings", "", self.last_change]

        y_offset = 25
        for i, text in enumerate(settings_text):
            color = (
                (0, 255, 255) if i == 2 else (255, 255, 255)
            )  # Highlight last change
            cv2.putText(
                frame,
                text,
                (15, y_offset + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        return frame
