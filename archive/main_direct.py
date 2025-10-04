#!/usr/bin/env python3
"""
PhotoBooth Scare - Direct entry point that bypasses import issues.
"""

import sys
import os

# Add src directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

# Direct import and run
if __name__ == "__main__":
    from photobooth.action_handler import setup_and_run

    setup_and_run()
