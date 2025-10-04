#!/usr/bin/env python3
"""
Main entry point - redirects to photobooth.py for proper path setup
"""

import subprocess
import sys
import os

# Run photobooth.py which handles the proper Python path setup
photobooth_path = os.path.join(os.path.dirname(__file__), "photobooth.py")
subprocess.run([sys.executable, photobooth_path])
