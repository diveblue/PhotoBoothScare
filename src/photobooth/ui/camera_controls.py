"""
camera_controls.py
Handles live camera adjustment controls during preview
"""

import cv2


class CameraControls:
    def __init__(self, camera, lighting_config, settings_overlay=None):
        self.camera = camera
        self.lighting_config = lighting_config
        self.settings_overlay = settings_overlay

        # Initialize current settings from config
        self.current_wb_mode = lighting_config.get("AwbMode", 0)
        self.current_brightness = lighting_config.get("Brightness", 0.0)
        self.current_contrast = lighting_config.get("Contrast", 1.0)
        self.current_saturation = lighting_config.get("Saturation", 1.0)
        self.current_exposure = lighting_config.get("ExposureTime", 16666)
        self.current_gain = lighting_config.get("AnalogueGain", 1.0)
        self.current_noise_reduction = lighting_config.get("NoiseReductionMode", 0)

        self.wb_modes = [
            "Auto",
            "Incandescent",
            "Tungsten",
            "Fluorescent",
            "Indoor",
            "Daylight",
            "Cloudy",
        ]

    def handle_key(self, key):
        """Handle camera control key presses. Returns True if key was handled."""
        # Check if we have Picamera2 (real camera controls) or OpenCV (limited/simulated)
        has_picam2 = hasattr(self.camera, "picam2") and self.camera.picam2
        has_opencv = hasattr(self.camera, "cap") and self.camera.cap
        
        if not (has_picam2 or has_opencv):
            print("❌ No camera backend available for controls")
            return False
            
        if not has_picam2:
            print("⚠️ Using OpenCV camera - controls will be simulated/limited")

        handled = True

        if key == ord("w"):  # White balance mode
            self._cycle_white_balance()
        elif key == ord("b"):  # Brightness up
            self._adjust_brightness(0.1)
        elif key == ord("B"):  # Brightness down (Shift+B)
            self._adjust_brightness(-0.1)
        elif key == ord("c"):  # Contrast up
            self._adjust_contrast(0.1)
        elif key == ord("C"):  # Contrast down (Shift+C)
            self._adjust_contrast(-0.1)
        elif key == ord("s"):  # Saturation up
            self._adjust_saturation(0.1)
        elif key == ord("S"):  # Saturation down (Shift+S)
            self._adjust_saturation(-0.1)
        elif key == ord("e"):  # Exposure up
            self._adjust_exposure(5000)
        elif key == ord("E"):  # Exposure down (Shift+E)
            self._adjust_exposure(-5000)
        elif key == ord("g"):  # Gain up
            self._adjust_gain(0.5)
        elif key == ord("G"):  # Gain down (Shift+G)
            self._adjust_gain(-0.5)
        elif key == ord("n"):  # Toggle noise reduction
            self._toggle_noise_reduction()
        elif key == ord("r"):  # Reset to config defaults
            self._reset_to_defaults()
        elif key == ord("h"):  # Show help
            self._show_help()
        else:
            handled = False

        return handled

    def _cycle_white_balance(self):
        """Cycle through white balance modes."""
        self.current_wb_mode = (self.current_wb_mode + 1) % len(self.wb_modes)
        
        # Apply to Picamera2 if available
        if hasattr(self.camera, "picam2") and self.camera.picam2:
            self.camera.picam2.set_controls({"AwbMode": self.current_wb_mode})
        
        message = f"🎨 White Balance: {self.wb_modes[self.current_wb_mode]} (Mode {self.current_wb_mode})"
        print(message)
        if self.settings_overlay:
            self.settings_overlay.show_setting_change(
                "White Balance",
                f"{self.wb_modes[self.current_wb_mode]} (Mode {self.current_wb_mode})",
            )
            self._update_overlay_settings()

    def _adjust_brightness(self, delta):
        """Adjust brightness by delta."""
        self.current_brightness = max(-1.0, min(1.0, self.current_brightness + delta))
        
        # Apply to Picamera2 if available
        if hasattr(self.camera, "picam2") and self.camera.picam2:
            self.camera.picam2.set_controls({"Brightness": self.current_brightness})
        elif hasattr(self.camera, "cap") and self.camera.cap:
            # OpenCV brightness is 0-255, convert from -1.0 to 1.0 range
            opencv_brightness = int((self.current_brightness + 1.0) * 127.5)
            self.camera.cap.set(cv2.CAP_PROP_BRIGHTNESS, opencv_brightness)
        
        message = f"💡 Brightness: {self.current_brightness:.1f}"
        print(message)
        if self.settings_overlay:
            self.settings_overlay.show_setting_change(
                "Brightness", f"{self.current_brightness:.2f}"
            )
            self._update_overlay_settings()

    def _adjust_contrast(self, delta):
        """Adjust contrast by delta."""
        self.current_contrast = max(0.0, min(2.0, self.current_contrast + delta))
        
        # Apply to Picamera2 if available
        if hasattr(self.camera, "picam2") and self.camera.picam2:
            self.camera.picam2.set_controls({"Contrast": self.current_contrast})
        elif hasattr(self.camera, "cap") and self.camera.cap:
            # OpenCV contrast is 0-255, convert from 0.0 to 2.0 range
            opencv_contrast = int(self.current_contrast * 127.5)
            self.camera.cap.set(cv2.CAP_PROP_CONTRAST, opencv_contrast)
            
        print(f"🔳 Contrast: {self.current_contrast:.1f}")
        if self.settings_overlay:
            self.settings_overlay.show_setting_change(
                "Contrast", f"{self.current_contrast:.2f}"
            )
            self._update_overlay_settings()

    def _adjust_saturation(self, delta):
        """Adjust saturation by delta."""
        self.current_saturation = max(0.0, min(2.0, self.current_saturation + delta))
        
        # Apply to Picamera2 if available
        if hasattr(self.camera, "picam2") and self.camera.picam2:
            self.camera.picam2.set_controls({"Saturation": self.current_saturation})
        elif hasattr(self.camera, "cap") and self.camera.cap:
            # OpenCV saturation is 0-255, convert from 0.0 to 2.0 range
            opencv_saturation = int(self.current_saturation * 127.5)
            self.camera.cap.set(cv2.CAP_PROP_SATURATION, opencv_saturation)
            
        print(f"🌈 Saturation: {self.current_saturation:.1f}")
        if self.settings_overlay:
            self.settings_overlay.show_setting_change(
                "Saturation", f"{self.current_saturation:.2f}"
            )
            self._update_overlay_settings()

    def _adjust_exposure(self, delta):
        """Adjust exposure by delta microseconds."""
        self.current_exposure = max(1000, min(100000, self.current_exposure + delta))
        self.camera.picam2.set_controls({"ExposureTime": self.current_exposure})
        print(
            f"⏱️  Exposure: {self.current_exposure}μs ({self.current_exposure / 1000:.1f}ms)"
        )

    def _adjust_gain(self, delta):
        """Adjust gain by delta."""
        self.current_gain = max(1.0, min(8.0, self.current_gain + delta))
        self.camera.picam2.set_controls({"AnalogueGain": self.current_gain})
        print(f"📈 Gain: {self.current_gain:.1f}x")

    def _toggle_noise_reduction(self):
        """Toggle noise reduction on/off."""
        self.current_noise_reduction = 1 - self.current_noise_reduction
        self.camera.picam2.set_controls(
            {"NoiseReductionMode": self.current_noise_reduction}
        )
        print(f"🔇 Noise Reduction: {'ON' if self.current_noise_reduction else 'OFF'}")

    def _reset_to_defaults(self):
        """Reset all settings to config defaults."""
        self.current_wb_mode = self.lighting_config.get("AwbMode", 0)
        self.current_brightness = self.lighting_config.get("Brightness", 0.0)
        self.current_contrast = self.lighting_config.get("Contrast", 1.0)
        self.current_saturation = self.lighting_config.get("Saturation", 1.0)
        self.current_exposure = self.lighting_config.get("ExposureTime", 16666)
        self.current_gain = self.lighting_config.get("AnalogueGain", 1.0)
        self.current_noise_reduction = self.lighting_config.get("NoiseReductionMode", 0)

        reset_controls = {
            "AwbMode": self.current_wb_mode,
            "Brightness": self.current_brightness,
            "Contrast": self.current_contrast,
            "Saturation": self.current_saturation,
            "ExposureTime": self.current_exposure,
            "AnalogueGain": self.current_gain,
            "NoiseReductionMode": self.current_noise_reduction,
        }
        self.camera.picam2.set_controls(reset_controls)
        lighting_mode = self.lighting_config.get("_mode", "unknown")
        print(f"🔄 Reset to {lighting_mode} defaults")

    def _show_help(self):
        """Display help for camera controls."""
        print("\n=== Camera Controls ===")
        print("  W = cycle white balance modes")
        print("  B/Shift+B = brightness up/down")
        print("  C/Shift+C = contrast up/down")
        print("  S/Shift+S = saturation up/down")
        print("  E/Shift+E = exposure up/down")
        print("  G/Shift+G = gain up/down")
        print("  N = toggle noise reduction")
        print("  R = reset to defaults")
        print("  H = show this help")
        print("========================")

    @staticmethod
    def print_controls_help():
        """Print initial controls help."""
        print("Controls:")
        print("  SPACE = simulate button press, Q/ESC/F11 = quit")
        print(
            "  Camera Settings: W(WB mode), B(brightness ±), C(contrast ±), S(saturation ±)"
        )
        print("  E(exposure ±), G(gain ±), N(noise reduction), R(reset to defaults)")
        print("  H = show this help again")

    def _update_overlay_settings(self):
        """Update the settings overlay with current values."""
        if self.settings_overlay:
            self.settings_overlay.update_current_settings(
                self.current_wb_mode,
                self.wb_modes,
                self.current_brightness,
                self.current_contrast,
                self.current_saturation,
                self.current_exposure,
                self.current_gain,
                self.current_noise_reduction,
            )
