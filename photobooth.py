#!/usr/bin/env python3
"""
PhotoBooth Scare - Halloween photobooth application entry point.

This script serves as the main entry point for the PhotoBooth Scare application.
It adds the src directory to the Python path and launches the main application.
"""

import sys
import os

# Add src directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

# Import and run the main application
if __name__ == "__main__":
    from photobooth.main import main

    main()
