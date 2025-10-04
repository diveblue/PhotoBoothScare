#!/bin/bash
# Test script for PhotoBooth microphone setup

echo "=== PhotoBooth Microphone Test ==="

echo "1. Checking audio devices..."
echo "Available recording devices:"
arecord -l

echo ""
echo "2. Testing microphone (5 second recording)..."
echo "Speak into your microphone for 5 seconds..."
arecord -D hw:1,0 -f cd -t wav -d 5 photobooth_mic_test.wav

echo ""
echo "3. Playing back recording..."
aplay photobooth_mic_test.wav

echo ""
echo "4. Checking audio file info..."
file photobooth_mic_test.wav
ls -lh photobooth_mic_test.wav

echo ""
echo "5. Testing with Python/pyaudio..."
python3 -c "
import pyaudio
import wave
import sys

print('Available audio devices:')
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'  Device {i}: {info[\"name\"]} ({info[\"maxInputChannels\"]} channels)')

# Test recording
print('\\nRecording 3 seconds with pyaudio...')
try:
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []
    for _ in range(int(44100 / 1024 * 3)):
        data = stream.read(1024)
        frames.append(data)
    stream.close()
    
    # Save test file
    wf = wave.open('pyaudio_test.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(44100)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print('✅ PyAudio recording successful: pyaudio_test.wav')
    
except Exception as e:
    print(f'❌ PyAudio recording failed: {e}')
finally:
    p.terminate()
"

echo ""
echo "6. If everything works, your microphone is ready for PhotoBooth!"
echo "   Add to config.json: \"ENABLE_AUDIO\": true"