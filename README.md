
# PhotoBooth Scare 🎃

A **Halloween photo booth** system with **scare prop integration**. Originally designed for Raspberry Pi, but runs locally for development in VS Code. Features live camera preview with **countdown overlay**, **audio cues**, **relay triggers** for scare props, **video recording**, **QR codes** for easy photo sharing, and **configurable lighting modes** for different environments.

## ✨ Features

- 🎥 **Live Camera Preview** - Real-time feed with overlay graphics
- ⏰ **Countdown Sequence** - Customizable countdown with audio cues  
- 📸 **Photo Capture** - High-quality photos saved with unique session IDs
- 🎬 **Video Recording** - Full session recording with RTSP streaming
- 📱 **QR Code Generation** - Instant sharing links for captured photos
- 🎵 **Audio Management** - Countdown beeps and shutter sounds
- ⚡ **GPIO Relay Control** - Trigger scare props via hardware relay
- 🌙 **Lighting Modes** - Optimized settings for different environments
- 🎮 **Live Camera Controls** - Real-time adjustment of camera settings
- 🐛 **Debug System** - Comprehensive logging with multiple categories

---

## 🚀 Quick Start

### Local Development (Windows/macOS/Linux)
```bash
python -m venv .venv --system-site-packages
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py --debug --windowed
```

### Command Line Options
- `--debug` or `-d` - Enable debug output with timing information
- `--windowed` or `-w` - Run in windowed mode (not fullscreen)

### Controls
- **Space** or **Hardware Button** - Start photo session
- **Live Camera Controls** (during idle):
  - `W` - Cycle white balance modes
  - `B/Shift+B` - Adjust brightness (±0.05)
  - `C/Shift+C` - Adjust contrast (±0.1) 
  - `S/Shift+S` - Adjust saturation (±0.1)
  - `E/Shift+E` - Adjust exposure time
  - `G/Shift+G` - Adjust gain (±0.2)
  - `R` - Reset to defaults
  - `H` - Show help
- **Esc** or **Q** - Quit application

---

## 🏗️ Architecture

The application follows **SOLID principles** with a clean, modular architecture:

### Core Manager Classes
- **`config_manager.py`** - Configuration loading and environment management
- **`debug_logger.py`** - Centralized logging system with categories
- **`camera_manager.py`** - Camera abstraction (Picamera2/OpenCV) with live controls
- **`display_manager.py`** - Display system (pygame/OpenCV) with environment detection
- **`session_manager.py`** - Photo booth session state management and transitions
- **`video_manager.py`** - Video recording and RTSP streaming
- **`audio_manager.py`** - Sound playback for countdown and shutter
- **`gpio_manager.py`** - Hardware abstraction for buttons and relays
- **`overlay_renderer.py`** - Graphics rendering for countdown and UI elements
- **`camera_controls.py`** - Live camera adjustment via keyboard shortcuts
- **`qr_manager.py`** - QR code generation and file management
- **`file_manager.py`** - File cleanup and directory management

### Session Flow
1. **Idle State** - Live preview with "Press Button" overlay
2. **Countdown** - 3-2-1 countdown with audio beeps
3. **Gotcha** - Relay triggers scare prop, photo captured
4. **QR Display** - Shows QR code for 5 seconds, files moved to network storage
5. **Return to Idle** - Ready for next session

---

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "LIGHTING_MODE": "TESTING",          // or "HALLOWEEN_NIGHT" 
  "COUNTDOWN_SECONDS": 3,              // Countdown duration
  "QR_DISPLAY_SECONDS": 5.0,          // QR code display time
  "BUTTON_PIN": 17,                    // GPIO pin for button
  "RELAY_PIN": 27,                     // GPIO pin for relay
  "PHOTO_DIR": "path/to/photos",       // Network photo storage
  "VIDEO_DIR": "path/to/videos",       // Network video storage
  "RTSP_URL": "rtsp://camera.ip/",     // Secondary recording stream
  "CAMERA_SETTINGS": {
    "TESTING": { /* bright indoor settings */ },
    "HALLOWEEN_NIGHT": { /* dimly lit porch settings */ }
  }
}
```

### Lighting Modes
- **TESTING** - Optimized for bright indoor development conditions
- **HALLOWEEN_NIGHT** - Optimized for dimly lit porch/outdoor Halloween setup

---

## 🔧 Hardware Setup (Raspberry Pi)

### Wiring Diagram
```
    [Big Arcade Button] ──┐
                          ├─── GPIO17 (Button Input)
    [Scare Prop Relay] ───┼─── GPIO27 (Relay Output)  
                          │
    [Pi Camera] ──────────┼─── CSI Port
                          │
    [HDMI Display] ───────┼─── HDMI Port
                          │
    [USB Audio/BT] ───────┘
```

### Recommended Hardware
- **Raspberry Pi 4** (4GB+ recommended)
- **Pi Camera Module v2/v3** (better than USB webcam)
- **Large Arcade Button** (LED illuminated preferred)  
- **5V Relay Module** (for prop control)
- **HDMI Monitor/TV** (for guest display)
- **Bluetooth Speaker** (eliminates ground loop audio issues)
- **MicroSD Card** (32GB+ Class 10)

### Pi Installation Steps

1. **Flash Raspberry Pi OS** (Bookworm recommended)
2. **Install system dependencies:**
   ```bash
   sudo apt update && sudo apt install -y python3-opencv python3-pygame python3-pip
   sudo apt install -y v4l-utils ffmpeg pulseaudio-module-bluetooth
   ```

3. **Install Python packages:**
   ```bash
   python -m venv .venv --system-site-packages
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install RPi.GPIO  # Hardware GPIO support
   ```

4. **Enable camera and I2C:**
   ```bash
   sudo raspi-config
   # Interface Options → Camera → Enable
   # Interface Options → I2C → Enable  
   ```

5. **Configure for hardware:**
   - Update `gpio_manager.py` to import `RPi.GPIO` instead of `fake_gpio`
   - Set correct GPIO pins in `config.json`
   - Configure network paths for photo/video storage

---

## 🐛 Development & Debugging

### Debug Categories
Enable specific debug output with `--debug`:
- **session** - Session state transitions and lifecycle
- **timing** - Precise timing information for performance analysis  
- **camera** - Camera operations and settings changes
- **gpio** - Hardware button presses and relay triggers
- **audio** - Sound playback and audio device status
- **display** - Graphics rendering and display operations

### Test Utilities
- **`camera_test.py`** - Camera functionality with pygame preview
- **`camera_local_test.py`** - Non-GUI camera testing
- **`camera_color_test.py`** - Color balance and lighting optimization
- **`night_lighting_test.py`** - Halloween night condition testing
- **`gpio_pin_tester.py`** - Hardware GPIO validation
- **`audio_test.py`** - Audio device and playback testing

### Common Issues & Solutions

**Camera Issues:**
- On Pi: Prefer Picamera2 over OpenCV for better performance
- Color cast problems: Use `HALLOWEEN_NIGHT` lighting mode for outdoor conditions
- Frame drops: Check `/boot/config.txt` for `gpu_mem=128` or higher

**Audio Issues:**  
- Static/ground loops: Use Bluetooth audio instead of 3.5mm jack
- No audio device: Install `pulseaudio` and configure default sink

**Display Issues:**
- Wayland compatibility: Application automatically detects and adapts
- Performance: Use `--windowed` for development, fullscreen for production

---

## 🌐 Web Integration

The system includes a PHP web interface for photo viewing:

### Website Structure
- **`Website/`** - Main web interface
- **`Halloween2025Website/`** - Current year's themed interface
- **`sync_website_to_skynas.sh/.ps1`** - Deployment scripts

### QR Code Integration
- Each session generates a unique URL: `http://your-server/session.php?key=SESSION_ID`
- Photos and videos automatically moved to network storage
- Guests scan QR code to view/download their photos

---

## 🛠️ VS Code + Copilot Development

This project is optimized for **GitHub Copilot** assistance:

### Copilot-Friendly Features
- **`.github/copilot-instructions.md`** - Project context for Copilot
- **Modular architecture** - Easy for Copilot to understand and extend
- **Clear separation of concerns** - Each manager handles one responsibility
- **Comprehensive documentation** - Rich context for intelligent suggestions

### Effective Copilot Prompts
- *"Add a second relay output for a strobe light that triggers 2 seconds into countdown"*
- *"Implement face detection to auto-adjust camera settings"*  
- *"Add Instagram-style filters to photos before saving"*
- *"Create a web admin panel for changing settings remotely"*

### Development Workflow
1. Open project in **VS Code**
2. Ensure **GitHub Copilot** extension is enabled
3. Use `--debug --windowed` for development
4. Test individual components with included test utilities
5. Deploy to Pi for hardware integration testing

---

## 📂 Project Structure

```
PhotoBoothScare/
├── main.py                 # Main application entry point  
├── config.json             # Configuration settings
├── requirements.txt        # Python dependencies
│
├── Manager Classes/        # Core architecture
│   ├── config_manager.py   # Configuration management
│   ├── debug_logger.py     # Centralized logging
│   ├── camera_manager.py   # Camera abstraction
│   ├── display_manager.py  # Display system
│   ├── session_manager.py  # Session state management
│   ├── video_manager.py    # Video recording
│   ├── audio_manager.py    # Audio playback
│   ├── gpio_manager.py     # Hardware control
│   ├── overlay_renderer.py # Graphics rendering
│   ├── camera_controls.py  # Live camera adjustment
│   ├── qr_manager.py       # QR code generation
│   └── file_manager.py     # File operations
│
├── Test Utilities/         # Development tools
│   ├── camera_test.py      # Camera testing with GUI
│   ├── camera_local_test.py # Camera testing without GUI
│   ├── night_lighting_test.py # Halloween condition testing
│   └── gpio_pin_tester.py  # Hardware validation
│
├── Web Interface/          # Photo sharing
│   ├── Website/            # Main web interface
│   └── Halloween2025Website/ # Themed interface
│
└── assets/                 # Media files
    ├── beep.wav           # Countdown sound
    ├── shutter.wav        # Photo capture sound
    └── Creepster-Regular.ttf # Halloween font
```

---

## 🎃 Happy Halloween!

**Enjoy creating memorable (and scary) photo experiences!** 

For questions, issues, or feature requests, the modular architecture makes it easy to extend functionality. Each manager class handles a specific concern, so adding new features is straightforward.

*Built with ❤️ for makers, haunters, and Halloween enthusiasts!*
