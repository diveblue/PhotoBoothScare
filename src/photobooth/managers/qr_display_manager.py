"""
qr_display_manager.py
Handles QR code generation, display timing, and file movement coordination
"""

import os
import time
import qrcode
import cv2


class QRDisplayManager:
    def __init__(self, config, debug_log_func):
        self.config = config
        self.debug_log = debug_log_func

        # QR display state
        self.display_start_time = None
        self.qr_generated = False
        self.last_log_time = 0  # Throttle debug output

        # Configuration
        self.display_duration = config.get("QR_DISPLAY_SECONDS", 5.0)
        self.base_website_url = "https://diveblue.synology.me/index.php"
        self.qr_path = "qr_code.png"

        # QR code configuration
        self.qr_config = {
            "version": 1,
            "error_correction": qrcode.constants.ERROR_CORRECT_M,
            "box_size": 6,
            "border": 2,
        }

    def start_display(self, session_id):
        """
        Start QR code display phase.
        Generates QR code and begins display timer.

        Args:
            session_id: Session ID for the QR URL

        Returns:
            dict: QR display info with image dimensions and path
        """
        if self.display_start_time is not None:
            return None  # Already displaying

        self.display_start_time = time.time()
        self.qr_generated = False
        self.last_log_time = 0

        try:
            # Generate session URL
            session_url = f"{self.base_website_url}?key={session_id}"

            # Create QR code
            qr = qrcode.QRCode(
                version=self.qr_config["version"],
                error_correction=self.qr_config["error_correction"],
                box_size=self.qr_config["box_size"],
                border=self.qr_config["border"],
            )
            qr.add_data(session_url)
            qr.make(fit=True)

            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(self.qr_path)

            # Load with OpenCV to get dimensions
            qr_img = cv2.imread(self.qr_path)
            qr_dimensions = None
            if qr_img is not None:
                qr_h, qr_w = qr_img.shape[:2]
                qr_dimensions = (qr_w, qr_h)

            self.qr_generated = True
            self.debug_log("timing", f"📱 QR CODE GENERATED: {session_url}")

            return {
                "success": True,
                "url": session_url,
                "qr_path": self.qr_path,
                "dimensions": qr_dimensions,
                "display_duration": self.display_duration,
            }

        except Exception as e:
            self.debug_log("timing", f"❌ QR CODE GENERATION failed: {e}")
            return {"success": False, "error": str(e)}

    def get_display_status(self, now):
        """
        Get current QR display status and timing information.

        Args:
            now: Current time in seconds

        Returns:
            dict: Display status information
        """
        if self.display_start_time is None:
            return {"active": False, "elapsed": 0, "remaining": 0, "progress": 0}

        elapsed = now - self.display_start_time
        remaining = max(0, self.display_duration - elapsed)
        progress = min(100, (elapsed / self.display_duration) * 100)

        return {
            "active": True,
            "elapsed": elapsed,
            "remaining": remaining,
            "progress": progress,
            "duration": self.display_duration,
        }

    def update(self, now):
        """
        Update QR display state and check for completion.

        Args:
            now: Current time in seconds

        Returns:
            dict: Update result with completion status
        """
        if self.display_start_time is None:
            return {"active": False}

        status = self.get_display_status(now)

        # Log progress periodically (throttled to once per second)
        if status["active"] and (now - self.last_log_time) >= 1.0:
            self.debug_log(
                "timing",
                f"🔄 QR display active for {status['elapsed']:.1f}s / {self.display_duration:.1f}s",
            )
            self.last_log_time = now

        # Check for completion
        if status["elapsed"] >= self.display_duration:
            self.debug_log("timing", "🏁 QR DISPLAY COMPLETE")
            return {"active": True, "completed": True}

        return {"active": True, "completed": False}

    def is_active(self):
        """Check if QR display is currently active."""
        return self.display_start_time is not None

    def is_complete(self, now):
        """Check if QR display duration has elapsed."""
        if self.display_start_time is None:
            return False
        return (now - self.display_start_time) >= self.display_duration

    def reset(self):
        """Reset QR display state for a new session."""
        self.display_start_time = None
        self.qr_generated = False
        self.last_log_time = 0
        self.debug_log("timing", "📱 QR display manager reset")

    def cleanup(self):
        """Cleanup QR display resources."""
        try:
            if os.path.exists(self.qr_path):
                os.remove(self.qr_path)
        except Exception as e:
            self.debug_log("timing", f"❌ QR cleanup failed: {e}")

        self.reset()
