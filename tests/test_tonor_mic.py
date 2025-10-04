#!/usr/bin/env python3
"""
Simple test for TONOR microphone with pyaudio
"""

import pyaudio
import wave


def test_microphone():
    print("=== TONOR Microphone PyAudio Test ===")

    p = pyaudio.PyAudio()

    print("\nAvailable input devices:")
    tonor_device = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"  Device {i}: {info['name']} ({info['maxInputChannels']} channels)")
            if "TONOR" in info["name"] or "Mic" in info["name"]:
                tonor_device = i
                print(f"    ^ FOUND TONOR DEVICE: {i}")

    if tonor_device is None:
        print("❌ No TONOR device found, using default")
        tonor_device = None

    print(f"\nTesting recording with device {tonor_device}...")

    try:
        # Configure for mono recording
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=tonor_device,
            frames_per_buffer=1024,
        )

        print("Recording 2 seconds... speak now!")
        frames = []
        for _ in range(int(44100 / 1024 * 2)):  # 2 seconds
            data = stream.read(1024)
            frames.append(data)

        stream.close()

        # Save audio
        wf = wave.open("tonor_pyaudio_test.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b"".join(frames))
        wf.close()

        print("✅ Recording successful: tonor_pyaudio_test.wav")

        # Play back
        import subprocess

        print("Playing back recording...")
        subprocess.run(["aplay", "tonor_pyaudio_test.wav"])

        return True

    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return False
    finally:
        p.terminate()


if __name__ == "__main__":
    success = test_microphone()
    if success:
        print("\n🎤 TONOR microphone is ready for PhotoBooth!")
        print('Add to config.json: "ENABLE_AUDIO": true')
    else:
        print("\n❌ Microphone test failed")
