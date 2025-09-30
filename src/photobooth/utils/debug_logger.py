"""
debug_logger.py
Centralized debug logging system with categories
"""

import time
from datetime import datetime


class DebugLogger:
    def __init__(self, debug_mode=False, categories=None):
        self.debug_mode = debug_mode
        self.enabled_categories = categories or ["all"]
        self.start_time = time.time()

    def log(self, category, message):
        """Log a debug message if the category is enabled."""
        if not self.debug_mode:
            return

        if (
            "all" not in self.enabled_categories
            and category not in self.enabled_categories
        ):
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = time.time() - self.start_time

        print(f"[{timestamp}] [{elapsed:8.3f}s] [{category.upper():8}] {message}")

    def enable_category(self, category):
        """Enable a debug category."""
        if category not in self.enabled_categories:
            self.enabled_categories.append(category)

    def disable_category(self, category):
        """Disable a debug category."""
        if category in self.enabled_categories:
            self.enabled_categories.remove(category)

    def set_categories(self, categories):
        """Set the enabled debug categories."""
        self.enabled_categories = categories

    def get_categories(self):
        """Get the current enabled debug categories."""
        return self.enabled_categories.copy()

    def set_debug_mode(self, enabled):
        """Enable or disable debug mode."""
        self.debug_mode = enabled

    def is_debug_enabled(self):
        """Check if debug mode is enabled."""
        return self.debug_mode

    def reset_timer(self):
        """Reset the elapsed time timer."""
        self.start_time = time.time()
