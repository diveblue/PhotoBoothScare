<!-- Copilot instructions for PhotoBoothScare -Developer workflows (commands you can run or suggest)
- Setup (Windows/macOS/Linux developer):
  - python -m venv .venv; activate and pip install -r requirements.txt
  - python photobooth.py (new entry point)
- On Raspberry Pi (hardware):
  - cd /home/scott/photobooth && .venv/bin/python photobooth.py
  - CIFS mount: //SKYNAS/web → /mnt/skynas/web (credentials: scott:dive2000)
  - Camera: Picamera2 with IMX708 sensor, libcamera backend
  - Audio: Uses pygame.mixer for beep.wav/shutter.wav playback
- Testing: Use tools/run_test_session.py for comprehensive session testing with logsilot quick instructions — PhotoBoothScare

Be concise. Prioritize actionable edits, tests, and runnable commands. When in doubt, produce the smallest change that satisfies the request and include a one-line test command. Give only essential steps/commands; no extra explanation unless asked.

**Communication Style:** Be analytical and critical. Avoid excessive agreement phrases like "You're absolutely right!" Focus on technical assessment, best practices, complexity analysis, and identifying potential issues. Constructive criticism and architectural concerns are expected and valued.

**File Organization Rules (MANDATORY):**
- **Test scripts:** ALL test files go in `tests/` directory (test_*.py, *_test.py)
- **Tools/utilities:** ALL utility scripts go in `tools/` directory (debug_*.py, run_*.py, helper scripts)
- **Documentation:** ALL .md files except README.md go in `docs/` directory
- **NEVER create files in project root** - always use appropriate subdirectory
- When creating test/utility files, place them in correct directory from the start

## Current Architecture (Updated 2025-10-01)
**CRITICAL RULE: ALWAYS USE SESSION MANAGER FOR SESSION STATE**
**Package Structure:** Reorganized to `src/photobooth/` with managers/, hardware/, ui/, utils/ subdirectories
**Entry Point:** `photobooth.py` (not main.py directly)
**Deployment:** Raspberry Pi 4 (2GB+) with Picamera2 (IMX708), 1280x720 video recording
**Network Storage:** CIFS mount //SKYNAS/web → /mnt/skynas/web with file sync during QR display

## ARCHITECTURAL REQUIREMENTS (MUST FOLLOW)
**Session Management:** ALWAYS use `SessionManager` class - NEVER scatter session state across multiple managers or main.py
**SOLID Principles:** Each manager has single responsibility. SessionManager coordinates all session state transitions.
**State Management:** Use `session_manager.is_idle()`, `session_manager.start_countdown()` - NOT manual state checks
**No Duplicate Sessions:** SessionManager prevents overlapping sessions automatically when used correctly

Key concepts (read these files first)
- `src/photobooth/managers/session_manager.py` — **MANDATORY:** Controls ALL session state, transitions, timing. Use this INSTEAD of scattered state management.
- `src/photobooth/main.py` — Thin orchestration layer, delegates to SessionManager for all session logic
- `src/photobooth/managers/camera_manager.py` — Picamera2 preferred (RGB888 format), OpenCV fallback. Pi 2W setup confirmed working.
- `src/photobooth/managers/video_manager.py` — Records 1280x720 mp4v codec, stops recording BEFORE file movement to prevent corruption
- `src/photobooth/managers/gpio_manager.py`, `fake_gpio.py` — GPIO abstraction via hardware/ directory
- `src/photobooth/ui/overlay_renderer.py` — draws countdown and labels onto frames
- `src/photobooth/managers/audio_manager.py` — loads `assets/{beep.wav,shutter.wav}` for countdown/shutter sounds
- `config.json` — Camera resolutions: HIGH[1280,720], LOW[960,540]. Network paths use UNC format for cross-platform compatibility
- `photobooth.py` — New entry point that handles Python path setup for reorganized structure

Project-specific patterns
- **Video Recording Timing:** CRITICAL - Video recording must stop when gotcha phase completes, BEFORE QR display and file movement. Moving files while recording causes "moov atom not found" corruption.
- **Camera Format:** Picamera2 provides RGB888 frames at 1280x720. No RGB/BGR conversion needed - write frames directly to cv2.VideoWriter with mp4v codec.
- **Hardware:** Pi 4 (2GB+) supports audio recording with sufficient processing power for real-time audio/video muxing.
- **File Management:** Files move from local_videos/ to /mnt/skynas/web/Halloween2025/media/videos/ during QR display phase. Ensure video is stopped and flushed first.
- **Package Imports:** Use reorganized structure: `from photobooth.managers.camera_manager import CameraManager`
- Use `fake_gpio.py` for local development. When adding hardware code, add a clear guard or configuration entry so tests still run on desktop.
- Camera code must tolerate transient failures: reopen failures handled in camera_manager.py with fallback logic.

Developer workflows (commands you can run or suggest)
- Setup (Windows/macOS/Linux developer):
  - python -m venv .venv; activate and pip install -r requirements.txt
  - python photobooth.py (new entry point)
- On Raspberry Pi (hardware):
  - cd /home/scott/photobooth && .venv/bin/python photobooth.py
  - CIFS mount: //SKYNAS/web → /mnt/skynas/web (credentials: scott:dive2000)
  - Camera: Picamera2 with IMX708 sensor, libcamera backend
  - Audio: Uses pygame.mixer for beep.wav/shutter.wav playback


Where to change behavior
- To swap from fake to real GPIO toggle the import in `main.py` to `RPi.GPIO` and set pins in `config.json`.
- To change preview backend: examine `main.py` preview code path and `camera_manager.py` init (Picamera2 vs OpenCV).
- Video codec/format: video_manager.py uses mp4v codec, no frame conversion (writes RGB888 directly).

Testing & linting
- This repo doesn't include a test framework; prefer adding small scripts in `tests/` that assert core behaviors (camera open, config parsing). Use `camera_local_test.py` as an executable smoke test.
- Test video recording: `test_photobooth_camera.py` creates working mp4 files using actual camera manager.

Common fix patterns
- If camera unexpectedly returns None frames: ensure reopen logic in `camera_manager.get_frame()` attempts release() then re-create `cv2.VideoCapture(test_video_path)`.
- If GUI fails in venv: either use system `python3-opencv` or use `pygame` preview. Add a small try/except around `cv2.namedWindow` and fall back to pygame.
- If videos are corrupted ("moov atom not found"): ensure video recording stops BEFORE file movement. Never move files while VideoWriter is still active.

Integration points & external dependencies
- Picamera2 (optional) — code checks `PICAMERA2_AVAILABLE` in `camera_manager.py`.
- OpenCV (`cv2`) — used for capture and image ops; may be installed via apt (recommended on Pi) or pip.
- ffmpeg/ffplay — used externally for stream validation and recording via `rtsp_camera_manager.py`.
- Web UI: `Website/` contains PHP pages used to display sessions. `sync_website_to_skynas.sh` and `sync_website_to_skynas.ps1` are deploy helpers.

When editing
- Keep changes minimal and runnable. After edits run: python -m py_compile <edited_file>. Example: python -m py_compile overlay_renderer.py
- If adding new dependencies, update `requirements.txt`.

Files to reference for examples
- `main.py` — orchestration example
- `camera_manager.py` — recovery and backend selection
- `gpio_manager.py` / `fake_gpio.py` — hardware abstraction
- `camera_test.py`, `camera_local_test.py` — test patterns
- `overlay_renderer.py` — drawing and timing of countdown

If anything in these instructions is unclear or missing, respond with the exact area (file name or workflow) to expand.
