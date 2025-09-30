"""
file_manager.py
Handles file cleanup and management operations
"""

import os
import glob
import time
from pathlib import Path


class FileManager:
    def __init__(self, config, debug_log_func):
        self.config = config
        self.debug_log = debug_log_func

    def cleanup_old_files(self):
        """Clean up old files that might have accumulated."""
        try:
            self.debug_log("session", "🧹 CLEANING UP old files")

            # Clean up old photo files
            photo_files = glob.glob("*_photo_*.jpg")
            for photo_file in photo_files:
                try:
                    # Check if file is older than 1 hour
                    file_age = time.time() - os.path.getmtime(photo_file)
                    if file_age > 3600:  # 1 hour
                        os.remove(photo_file)
                        self.debug_log("session", f"🗑️ REMOVED old photo: {photo_file}")
                except Exception as e:
                    self.debug_log(
                        "session", f"❌ Failed to remove photo {photo_file}: {e}"
                    )

            # Clean up old video files
            video_files = glob.glob("*.mp4")
            for video_file in video_files:
                try:
                    # Check if file is older than 1 hour
                    file_age = time.time() - os.path.getmtime(video_file)
                    if file_age > 3600:  # 1 hour
                        os.remove(video_file)
                        self.debug_log("session", f"🗑️ REMOVED old video: {video_file}")
                except Exception as e:
                    self.debug_log(
                        "session", f"❌ Failed to remove video {video_file}: {e}"
                    )

            # Clean up temporary files
            temp_files = glob.glob("temp_*")
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    self.debug_log("session", f"🗑️ REMOVED temp file: {temp_file}")
                except Exception as e:
                    self.debug_log(
                        "session", f"❌ Failed to remove temp file {temp_file}: {e}"
                    )

            self.debug_log("session", "✅ CLEANUP completed")
            return True

        except Exception as e:
            self.debug_log("session", f"❌ CLEANUP failed: {e}")
            return False

    def ensure_directories(self):
        """Ensure required directories exist."""
        try:
            # Create photo directory if it doesn't exist
            photo_dir = Path(self.config["PHOTO_DIR"])
            photo_dir.mkdir(parents=True, exist_ok=True)

            # Create video directory if it doesn't exist
            video_dir = Path(self.config["VIDEO_DIR"])
            video_dir.mkdir(parents=True, exist_ok=True)

            self.debug_log("session", "📁 DIRECTORIES verified/created")
            return True

        except Exception as e:
            self.debug_log("session", f"❌ DIRECTORY creation failed: {e}")
            return False

    def get_file_info(self, filepath):
        """Get information about a file."""
        try:
            stat = os.stat(filepath)
            return {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
            }
        except Exception as e:
            self.debug_log("session", f"❌ Failed to get file info for {filepath}: {e}")
            return None

    def move_session_files_to_network(
        self,
        session_time_str,
        session_id_str,
        local_photo_dir,
        local_video_dir,
        network_photo_dir,
        network_video_dir,
    ):
        """
        Move files for this session from local dirs to network dirs.
        Only moves files that begin with the session prefix.

        Returns:
            int: Number of files successfully moved

        Raises:
            Exception: If file operations fail
        """
        import shutil

        prefix = f"{session_time_str}_{session_id_str}_"
        moved_files = []
        failed_files = []

        # Check if destination directories exist and are writable
        for desc, dest_dir in [
            ("photo", network_photo_dir),
            ("video", network_video_dir),
        ]:
            if not os.path.exists(dest_dir):
                self.debug_log(
                    "migrate",
                    f"❌ {desc} destination directory does not exist: {dest_dir}",
                )
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                    self.debug_log(
                        "migrate", f"✅ Created {desc} directory: {dest_dir}"
                    )
                except Exception as e:
                    self.debug_log(
                        "migrate",
                        f"❌ Failed to create {desc} directory {dest_dir}: {e}",
                    )
                    raise

            # Test write permissions
            test_file = os.path.join(dest_dir, ".test_write_permissions")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                self.debug_log("migrate", f"✅ {desc} directory writable: {dest_dir}")
            except Exception as e:
                self.debug_log(
                    "migrate", f"❌ {desc} directory not writable: {dest_dir} - {e}"
                )
                raise PermissionError(
                    f"Cannot write to {desc} directory {dest_dir}: {e}"
                )

        # Photos
        photo_files = glob.glob(os.path.join(local_photo_dir, prefix + "*"))
        self.debug_log("migrate", f"📸 Found {len(photo_files)} photos to move")
        for src in photo_files:
            dest = os.path.join(network_photo_dir, os.path.basename(src))
            try:
                # Check source file exists and is readable
                if not os.path.exists(src):
                    self.debug_log("migrate", f"❌ Source photo missing: {src}")
                    continue

                # Try direct move first
                shutil.move(src, dest)
                self.debug_log(
                    "migrate", f"✅ MOVED photo {os.path.basename(src)} -> {dest}"
                )
                moved_files.append(src)
            except Exception as move_error:
                # fallback to copy then remove
                try:
                    shutil.copy2(src, dest)
                    os.remove(src)
                    self.debug_log(
                        "migrate",
                        f"✅ COPIED photo {os.path.basename(src)} -> {dest} (removed local)",
                    )
                    moved_files.append(src)
                except Exception as copy_error:
                    self.debug_log("migrate", f"❌ FAILED moving photo {src} -> {dest}")
                    self.debug_log("migrate", f"   Move error: {move_error}")
                    self.debug_log("migrate", f"   Copy error: {copy_error}")
                    failed_files.append(src)

        # Videos
        video_files = glob.glob(os.path.join(local_video_dir, prefix + "*"))
        self.debug_log("migrate", f"🎥 Found {len(video_files)} videos to move")
        for src in video_files:
            dest = os.path.join(network_video_dir, os.path.basename(src))
            try:
                # Check source file exists and is readable
                if not os.path.exists(src):
                    self.debug_log("migrate", f"❌ Source video missing: {src}")
                    continue

                # Try direct move first
                shutil.move(src, dest)
                self.debug_log(
                    "migrate", f"✅ MOVED video {os.path.basename(src)} -> {dest}"
                )
                moved_files.append(src)
            except Exception as move_error:
                try:
                    shutil.copy2(src, dest)
                    os.remove(src)
                    self.debug_log(
                        "migrate",
                        f"✅ COPIED video {os.path.basename(src)} -> {dest} (removed local)",
                    )
                    moved_files.append(src)
                except Exception as copy_error:
                    self.debug_log("migrate", f"❌ FAILED moving video {src} -> {dest}")
                    self.debug_log("migrate", f"   Move error: {move_error}")
                    self.debug_log("migrate", f"   Copy error: {copy_error}")
                    failed_files.append(src)

        # Summary
        self.debug_log(
            "migrate",
            f"📁 Migration complete: {len(moved_files)} moved, {len(failed_files)} failed",
        )
        if failed_files:
            self.debug_log(
                "migrate",
                f"❌ Failed files: {[os.path.basename(f) for f in failed_files]}",
            )
            raise Exception(
                f"Failed to move {len(failed_files)} files to network storage"
            )

        return len(moved_files)

    def cleanup_old_local_sessions(
        self,
        local_photo_dir,
        local_video_dir,
        network_photo_dir,
        network_video_dir,
        exclude_current_session=None,
    ):
        """
        Move any old session files that are still in local directories to network storage.
        This handles cases where previous sessions didn't complete the file movement.

        Args:
            local_photo_dir: Local photo directory to scan
            local_video_dir: Local video directory to scan
            network_photo_dir: Destination for photos
            network_video_dir: Destination for videos
            exclude_current_session: Session prefix to exclude from cleanup (e.g., current session)

        Returns:
            int: Total number of old files moved
        """
        import shutil
        import glob

        total_moved = 0

        # Find all session files (pattern: YYYY-MM-DD_HH-MM-SS_SXXX_*)
        for desc, local_dir, network_dir in [
            ("photos", local_photo_dir, network_photo_dir),
            ("videos", local_video_dir, network_video_dir),
        ]:
            if not os.path.exists(local_dir):
                continue

            # Find all files that look like session files
            pattern = os.path.join(local_dir, "????-??-??_??-??-??_S???_*")
            old_files = glob.glob(pattern)

            # Filter out current session if specified
            if exclude_current_session:
                old_files = [
                    f
                    for f in old_files
                    if not os.path.basename(f).startswith(exclude_current_session)
                ]

            if not old_files:
                continue

            self.debug_log(
                "migrate", f"🧹 Found {len(old_files)} old {desc} files to cleanup"
            )

            for src in old_files:
                dest = os.path.join(network_dir, os.path.basename(src))
                try:
                    # Skip if destination already exists (avoid conflicts)
                    if os.path.exists(dest):
                        self.debug_log(
                            "migrate",
                            f"⚠️ Destination exists, removing local: {os.path.basename(src)}",
                        )
                        os.remove(src)
                        total_moved += 1
                        continue

                    # Try to move the file
                    shutil.move(src, dest)
                    self.debug_log(
                        "migrate",
                        f"✅ MOVED old {desc[:-1]} {os.path.basename(src)} -> {dest}",
                    )
                    total_moved += 1
                except Exception as e:
                    # If move fails, try copy+delete
                    try:
                        shutil.copy2(src, dest)
                        os.remove(src)
                        self.debug_log(
                            "migrate",
                            f"✅ COPIED old {desc[:-1]} {os.path.basename(src)} -> {dest} (removed local)",
                        )
                        total_moved += 1
                    except Exception as copy_error:
                        self.debug_log(
                            "migrate",
                            f"❌ Failed to cleanup old {desc[:-1]} {src}: move={e}, copy={copy_error}",
                        )

        if total_moved > 0:
            self.debug_log(
                "migrate",
                f"🧹 Cleanup complete: {total_moved} old files moved to network",
            )

        return total_moved
