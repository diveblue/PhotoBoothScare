#!/usr/bin/env python3
"""
Enhanced PhotoBooth test with comprehensive file logging
"""

import os
import sys
import logging
from datetime import datetime


# Setup comprehensive logging
def setup_logging():
    """Setup logging to both file and console"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"photobooth_debug_{timestamp}.log"

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    log_filepath = os.path.join("logs", log_filename)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_filepath), logging.StreamHandler(sys.stdout)],
    )

    return log_filepath


# Redirect stderr to also go to our log
class TeeToLogger:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.original = sys.stderr

    def write(self, message):
        if message.strip():
            self.logger.log(self.level, message.strip())
        self.original.write(message)

    def flush(self):
        self.original.flush()


def run_photobooth_with_logging():
    """Run photobooth with comprehensive logging"""
    log_filepath = setup_logging()
    logger = logging.getLogger(__name__)

    # Redirect stderr to logger (for ALSA errors)
    sys.stderr = TeeToLogger(logger, logging.WARNING)

    logger.info("=== PhotoBooth Debug Session Started ===")
    logger.info(f"Log file: {log_filepath}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")

    try:
        # Add src to Python path
        src_path = os.path.join(os.getcwd(), "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            logger.info(f"Added to Python path: {src_path}")

        # Import and run main photobooth
        logger.info("Importing photobooth main module...")
        from photobooth.main import main

        logger.info("Starting photobooth main...")
        main()

    except KeyboardInterrupt:
        logger.info("PhotoBooth stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"PhotoBooth crashed: {e}", exc_info=True)
    finally:
        logger.info("=== PhotoBooth Debug Session Ended ===")
        print(f"\nDebug log saved to: {log_filepath}")


if __name__ == "__main__":
    run_photobooth_with_logging()
