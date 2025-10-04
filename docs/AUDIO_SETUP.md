# Audio Setup Instructions for Pi 4

## Prerequisites
Your Pi 4 (2GB+) can handle real-time audio recording with video. Here's how to set it up:

## System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install audio system dependencies
sudo apt install -y \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    pulseaudio

# Optional: Install system-wide OpenCV to save memory
sudo apt install -y python3-opencv
```

## Python Dependencies
```bash
# In your virtual environment
pip install pyaudio
# or if system installation fails:
sudo apt install python3-pyaudio
```

## Audio Device Setup

### Test Audio Input
```bash
# List audio devices
arecord -l

# Test recording (Ctrl+C to stop)
arecord -D hw:1,0 -f cd test.wav
aplay test.wav
```

### Configure Audio Device
Add to your `config.json`:
```json
{
  "ENABLE_AUDIO": true,
  "AUDIO_DEVICE_INDEX": null,  // null = default device, or specify index
  "AUDIO_CHANNELS": 1,         // 1 = mono, 2 = stereo
  "AUDIO_SAMPLE_RATE": 44100   // CD quality
}
```

## Usage

### Option 1: Replace Current Video Manager
Replace `video_manager.py` with `video_manager_with_audio.py` in your imports:

```python
# In main.py, change:
from photobooth.managers.video_manager import VideoManager
# To:
from photobooth.managers.video_manager_with_audio import VideoManagerWithAudio as VideoManager
```

### Option 2: Gradual Integration
Keep current video manager and test audio separately first:

```bash
# Test audio recording
python -c "
import pyaudio
import wave

# Record 5 seconds of audio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
frames = [stream.read(1024) for _ in range(220)]  # ~5 seconds
stream.close()
p.terminate()

# Save audio
wf = wave.open('test_audio.wav', 'wb')
wf.setnchannels(1)
wf.setsampwidth(2)
wf.setframerate(44100)
wf.writeframes(b''.join(frames))
wf.close()
print('Audio saved to test_audio.wav')
"
```

## Performance Considerations

### Pi 4 Memory Usage
- **2GB Pi 4**: Mono audio (1 channel) recommended
- **4GB+ Pi 4**: Stereo audio (2 channels) supported
- **Video + Audio**: Uses ~200MB additional RAM during recording

### Quality Settings
```json
{
  "AUDIO_SAMPLE_RATE": 22050,  // Lower for smaller files
  "AUDIO_CHANNELS": 1,         // Mono saves 50% space
  "VIDEO_FPS": 15             // Lower FPS if performance issues
}
```

## Troubleshooting

### "No audio input device found"
```bash
# Check ALSA devices
cat /proc/asound/cards

# Enable USB audio if using USB microphone
sudo modprobe snd-usb-audio
```

### "Permission denied" for audio device
```bash
# Add user to audio group
sudo usermod -a -G audio scott
# Reboot required
```

### ffmpeg not found
```bash
# Install ffmpeg
sudo apt install -y ffmpeg

# Test ffmpeg
ffmpeg -version
```

## File Output
With audio enabled, your video files will be:
- `session_video.mp4` - Video + Audio combined
- Original size increase: ~10-20% for mono audio
- Compatible with VLC, web browsers, mobile devices