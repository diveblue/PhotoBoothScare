
# Photo Booth Scare (VS Code + Copilot Ready)

A local simulator for your haunt **photo‑booth scare**. Run it in VS Code on your laptop (no Raspberry Pi required).
It shows a mirrored live preview (or test video), overlays a **3‑2‑1‑SMILE** countdown, plays beeps/shutter sounds, and toggles a **fake relay**.
Press **Space** to simulate the big arcade button; Copilot can then help you extend the features.

---

## Quickstart

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Controls: **Space** = trigger countdown, **Q** = quit.

> If you get an audio device warning, the app still runs; add WAVs in `assets/` or plug in a sound device.

---

## Wiring Concept (for when you move to hardware)

```
         [Big Arcade Button]
                |
         +------+------+
         |             |
   (1) GPIO to Pi   (2) Relay Trigger
      Input Pin          (Prop power / solenoid)
```

**Flow:** Button → Overlay/Audio → Relay → Scare prop → Reset to live feed

**Recommended parts:** Raspberry Pi, USB webcam, arcade button, 5V relay module, HDMI monitor, powered speaker.

---

## Using Copilot Effectively

- Open this folder in **VS Code**.
- Ensure you have **GitHub Copilot** (and Copilot Chat) enabled.
- Start a chat in the command palette: “*Add a second relay output for a strobe at t=2.5s*” or “*Capture a photo to disk at shutter moment*”.
- Copilot reads your workspace, so keep TODOs in code where you want help.

---

## Move to a Real Raspberry Pi

- Replace this line in `main.py`:

```py
import fake_gpio as GPIO
# with:
# import RPi.GPIO as GPIO
```

- Wire your button to `GPIO17`, relay to `GPIO23` (or change pins).
- Install dependencies on the Pi:
```bash
sudo apt update && sudo apt install -y python3-opencv python3-pygame
pip install RPi.GPIO
```

Optional: Swap OpenCV preview for OBS if you prefer drag‑and‑drop overlays.

---

## Notes

- Live preview uses your default webcam; change `TEST_VIDEO_PATH` if desired.
- Audio files live in `assets/` → add `beep.wav` and `shutter.wav` of your choice.
- Fullscreen is disabled by default for smoother behavior inside VS Code terminals; enable it in `main.py` if you want.

Enjoy the screams 👻
