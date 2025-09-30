"""
qr_manager.py
Handles QR code generation and file management
"""

import qrcode
import cv2
import numpy as np
import os
import shutil
import glob


class QRManager:
    def __init__(self, config, debug_log_func):
        self.config = config
        self.debug_log = debug_log_func

        # Configuration
        self.photo_dir = config["PHOTO_DIR"]
        self.video_dir = config["VIDEO_DIR"]
        self.base_website_url = "http://192.168.86.35/session.php"

        # Current QR data
        self.qr_img = None
        self.session_url = None

    def generate_qr_code(self, session_id):
        """Generate QR code for the session."""
        try:
            self.session_url = f"{self.base_website_url}?key={session_id}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=6,
                border=2,
            )
            qr.add_data(self.session_url)
            qr.make(fit=True)

            # Create QR code image
            qr_pil = qr.make_image(fill_color="black", back_color="white")
            qr_array = np.array(qr_pil.convert("RGB"))
            self.qr_img = cv2.cvtColor(qr_array, cv2.COLOR_RGB2BGR)

            self.debug_log("timing", f"📱 QR CODE GENERATED: {self.session_url}")
            return True

        except Exception as e:
            print(f"[ERROR] QR code generation failed: {e}")
            self.qr_img = None
            return False

    def get_qr_image(self):
        """Get the current QR code image."""
        return self.qr_img

    def get_session_url(self):
        """Get the current session URL."""
        return self.session_url

    def move_files_to_network(self, session_id):
        """Move session files to network storage."""
        try:
            self.debug_log("timing", "📁 MOVING FILES to web server")

            # Move photos
            photo_pattern = f"*_{session_id}_photo_*.jpg"
            photo_files = glob.glob(os.path.join(".", photo_pattern))

            for photo_file in photo_files:
                try:
                    dest_path = os.path.join(
                        self.photo_dir, os.path.basename(photo_file)
                    )
                    shutil.move(photo_file, dest_path)
                    self.debug_log(
                        "timing", f"📁 MOVED PHOTO: {os.path.basename(photo_file)}"
                    )
                except Exception as e:
                    self.debug_log(
                        "timing",
                        f"❌ PHOTO MOVE failed: {os.path.basename(photo_file)} - {e}",
                    )

            # Move videos
            video_pattern = f"*_{session_id}_*.mp4"
            video_files = glob.glob(os.path.join(".", video_pattern))

            for video_file in video_files:
                try:
                    dest_path = os.path.join(
                        self.video_dir, os.path.basename(video_file)
                    )
                    shutil.move(video_file, dest_path)
                    self.debug_log(
                        "timing", f"📁 MOVED VIDEO: {os.path.basename(video_file)}"
                    )
                except Exception as e:
                    self.debug_log(
                        "timing",
                        f"❌ VIDEO MOVE failed: {os.path.basename(video_file)} - {e}",
                    )

            self.debug_log("timing", "✅ FILES MOVED to web server successfully")
            return True

        except Exception as e:
            self.debug_log("timing", f"❌ FILE MOVE failed: {e}")
            return False
