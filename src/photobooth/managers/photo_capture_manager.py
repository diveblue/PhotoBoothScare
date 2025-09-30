"""
photo_capture_manager.py
Handles photo capture logic during the SMILE phase
"""

import os
import cv2


class PhotoCaptureManager:
    def __init__(self, config, debug_log_func):
        self.config = config
        self.debug_log = debug_log_func

        # Photo capture state
        self.photos_taken = 0
        self.last_photo_time = 0
        self.max_photos = 5
        self.photo_interval = 0.7  # seconds between photos
        self.smile_phase_started = False

        # Configuration
        self.photo_dir = config["PHOTO_DIR"]

        # Ensure photo directory exists
        os.makedirs(self.photo_dir, exist_ok=True)

    def start_smile_phase(self, audio_manager):
        """
        Start the SMILE photo capture phase.
        Plays shutter sound and resets photo capture state.
        """
        if not self.smile_phase_started:
            self.debug_log("timing", "📸 SMILE phase started")
            self.debug_log("audio", "🔊 Playing shutter sound")
            audio_manager.play_shutter()
            self.smile_phase_started = True
            self.photos_taken = 0
            self.last_photo_time = 0

    def should_take_photo(self, now):
        """
        Check if it's time to take another photo.

        Args:
            now: Current time in seconds

        Returns:
            bool: True if a photo should be taken
        """
        if self.photos_taken >= self.max_photos:
            return False

        # Take first photo immediately, then wait for interval
        if self.photos_taken == 0:
            return True

        return (now - self.last_photo_time) >= self.photo_interval

    def capture_photo(self, frame, session_time, session_id, now):
        """
        Capture a photo and save it to disk.

        Args:
            frame: The camera frame to save
            session_time: Session time string for filename
            session_id: Session ID string for filename
            now: Current time in seconds

        Returns:
            dict: Photo capture result with success status and filename
        """
        if self.photos_taken >= self.max_photos:
            return {"success": False, "reason": "max_photos_reached"}

        try:
            # Generate filename with zero-padded photo number
            photo_filename = (
                f"{session_time}_{session_id}_photo_{self.photos_taken + 1:02d}.jpg"
            )
            photo_path = os.path.join(self.photo_dir, photo_filename)

            # Save the photo
            success = cv2.imwrite(photo_path, frame)

            if success:
                self.photos_taken += 1
                self.last_photo_time = now

                self.debug_log(
                    "timing",
                    f"📷 PHOTO {self.photos_taken}/{self.max_photos} SAVED: {photo_filename}",
                )

                return {
                    "success": True,
                    "filename": photo_filename,
                    "path": photo_path,
                    "photo_number": self.photos_taken,
                    "total_photos": self.max_photos,
                }
            else:
                self.debug_log("timing", f"❌ Failed to save photo: {photo_path}")
                return {"success": False, "reason": "cv2_write_failed"}

        except Exception as e:
            self.debug_log("timing", f"❌ Photo capture error: {e}")
            return {"success": False, "reason": str(e)}

    def is_complete(self):
        """Check if all photos have been taken."""
        return self.photos_taken >= self.max_photos

    def get_progress(self):
        """Get current photo capture progress."""
        return {
            "photos_taken": self.photos_taken,
            "max_photos": self.max_photos,
            "percentage": (self.photos_taken / self.max_photos) * 100,
            "is_complete": self.is_complete(),
        }

    def reset(self):
        """Reset photo capture state for a new session."""
        self.photos_taken = 0
        self.last_photo_time = 0
        self.smile_phase_started = False
        self.debug_log("timing", "📸 Photo capture manager reset")

    def cleanup(self):
        """Cleanup photo capture resources."""
        # No resources to cleanup for now, but available for future use
        pass
