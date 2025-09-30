"""
config_manager.py
Configuration loading and management
"""

import json


class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
            print(f"✅ Configuration loaded from {self.config_file}")
        except FileNotFoundError:
            print(f"❌ Configuration file {self.config_file} not found, using defaults")
            self.config = self.get_default_config()
            self.save_config()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {self.config_file}: {e}")
            print("Using default configuration")
            self.config = self.get_default_config()

    def get_default_config(self):
        """Return default configuration."""
        return {
            "BUTTON_PIN": 17,
            "RELAY_PIN": 27,
            "COUNTDOWN_DURATION": 10,
            "GOTCHA_DURATION": 10,
            "QR_DURATION": 5,
            "PHOTO_DIR": "Z:/PhotoBooth/photos",
            "VIDEO_DIR": "Z:/PhotoBooth/videos",
            "RTSP_URL": "rtsp://192.168.86.18:8080/h264_pcm.sdp",
            "LIGHTING_MODE": "TESTING",
            "CAMERA_SETTINGS": {
                "TESTING": {
                    "brightness": 0.1,
                    "contrast": 1.2,
                    "saturation": 1.0,
                    "auto_white_balance": True,
                    "awb_mode": "auto",
                    "exposure_mode": "auto",
                },
                "HALLOWEEN_NIGHT": {
                    "brightness": 0.3,
                    "contrast": 1.5,
                    "saturation": 1.2,
                    "auto_white_balance": False,
                    "awb_mode": "tungsten",
                    "exposure_mode": "night",
                },
            },
        }

    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value

    def get_camera_settings(self):
        """Get camera settings for current lighting mode."""
        lighting_mode = self.get("LIGHTING_MODE", "TESTING")
        camera_settings = self.get("CAMERA_SETTINGS", {})
        return camera_settings.get(lighting_mode, camera_settings.get("TESTING", {}))

    def set_lighting_mode(self, mode):
        """Set the lighting mode."""
        if mode in ["TESTING", "HALLOWEEN_NIGHT"]:
            self.set("LIGHTING_MODE", mode)
            print(f"✅ Lighting mode set to: {mode}")
        else:
            print(f"❌ Invalid lighting mode: {mode}")

    def get_all(self):
        """Get the entire configuration dictionary."""
        return self.config.copy()

    def update(self, updates):
        """Update multiple configuration values."""
        self.config.update(updates)

    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.get_default_config()
        self.save_config()
        print("✅ Configuration reset to defaults")
