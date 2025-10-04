# Archive - Old Entry Point Files

This folder contains obsolete entry point files that were replaced during the transition to the proper `photobooth.py` entry point structure.

## Archived Files:

### `main_direct.py` (archived 2025-10-03)
- **Purpose**: Temporary entry point that bypassed import issues
- **Function**: Called `setup_and_run()` from action_handler directly
- **Reason for archival**: Replaced by proper `photobooth.py` → `src/photobooth/main.py` chain

### `debug_direct.py` (archived 2025-10-03)  
- **Purpose**: Debugging entry point with direct ActionHandler initialization
- **Function**: Created to bypass setup_and_run() complexity during debugging
- **Reason for archival**: Debugging should use proper `photobooth.py` entry point

### `main_old.py` (archived 2025-10-03)
- **Purpose**: Previous main.py implementation before ActionHandler architecture
- **Function**: Contained old main loop logic
- **Reason for archival**: Replaced by ActionHandler-based architecture

### `main_redirect.py` (archived 2025-10-03)
- **Purpose**: Root main.py redirect wrapper
- **Function**: Used subprocess to call photobooth.py
- **Reason for archival**: Redundant wrapper - photobooth.py is the proper entry point

## Current Entry Point Structure:
- `photobooth.py` - Main entry point (sets up Python path)
- `src/photobooth/main.py` - Thin wrapper calling setup_and_run()
- `src/photobooth/action_handler.py` - Contains ActionHandler class and setup_and_run()

## Recovery Notes:
If any of these files need to be restored for reference:
1. Copy from archive back to project root (for main_direct.py, debug_direct.py)
2. Copy to src/photobooth/ (for main_old.py)
3. Ensure no import conflicts with current structure