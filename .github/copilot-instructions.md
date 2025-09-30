<!-- Copilot instructions for PhotoBoothScare -->
# Copilot quick instructions — PhotoBoothScare

Be concise. Prioritize actionable edits, tests, and runnable commands. When in doubt, produce the smallest change that satisfies the request and include a one-line test command. Give only essential steps/commands; no extra explanation unless asked.

Key concepts (read these files first)
- `main.py` — session orchestration and entrypoint (uses `gpio_manager`, `overlay_renderer`, `audio_manager`).
- `camera_manager.py` — camera abstraction: prefers Picamera2 on Pi, falls back to OpenCV (`cv2.VideoCapture`). Handles reopen logic; use `test_video_path` to override device.
- `gpio_manager.py`, `fake_gpio.py` — GPIO abstraction. `fake_gpio.py` is used for local development. On Pi replace with `RPi.GPIO`.
- `overlay_renderer.py` — draws countdown and labels onto frames for preview/save.
- `audio_manager.py` — loads `assets/{beep.wav,shutter.wav}` and plays during countdown.
- `config.json` — runtime pins, RTSP_URL and defaults. Use it to discover the RTSP stream or GPIO pins.
- `camera_test.py` / `camera_local_test.py` — quick test utilities (pygame and non-GUI) to validate capture sources.

Project-specific patterns
- Prefer non-invasive small edits. Many developers run locally in VS Code with a `.venv`; avoid requiring global system changes unless asked.
- Use `fake_gpio.py` for local development. When adding hardware code, add a clear guard or configuration entry so tests still run on desktop.
- Camera code must tolerate transient failures: reopen on `cap.read()` failure and return `None` for missing frames.
- UI preview uses `pygame` when OpenCV highgui is unavailable. If adding GUI features, update both `camera_test.py` and `main.py` preview paths.

Developer workflows (commands you can run or suggest)
- Setup (Windows/macOS/Linux developer):
  - python -m venv .venv; activate and pip install -r requirements.txt
  - python main.py
- On Raspberry Pi (hardware):
  - sudo apt update && sudo apt install -y python3-opencv python3-pygame v4l-utils
  - pip install RPi.GPIO (or use system package if needed)


Where to change behavior
- To swap from fake to real GPIO toggle the import in `main.py` to `RPi.GPIO` and set pins in `config.json`.
- To change preview backend: examine `main.py` preview code path and `camera_manager.py` init (Picamera2 vs OpenCV).

Testing & linting
- This repo doesn't include a test framework; prefer adding small scripts in `tests/` that assert core behaviors (camera open, config parsing). Use `camera_local_test.py` as an executable smoke test.

Common fix patterns
- If camera unexpectedly returns None frames: ensure reopen logic in `camera_manager.get_frame()` attempts release() then re-create `cv2.VideoCapture(test_video_path)`.
- If GUI fails in venv: either use system `python3-opencv` or use `pygame` preview. Add a small try/except around `cv2.namedWindow` and fall back to pygame.

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
