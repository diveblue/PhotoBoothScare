#!/usr/bin/env python3
"""
Quick test to see if we're using real or fake GPIO and test the LED trigger.
"""

try:
    import RPi.GPIO as GPIO

    print("[INFO] Using real RPi.GPIO")
    is_real_gpio = True
except Exception as e:
    import fake_gpio as GPIO

    print(f"[INFO] Using fake_gpio (RPi.GPIO import failed: {e})")
    is_real_gpio = False


import json

with open("config.json", "r") as f:
    CONFIG = json.load(f)
RELAY_PIN = CONFIG["RELAY_PIN"]
import time

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.OUT)

    print(f"[INFO] Testing relay on pin {RELAY_PIN}")
    print("[INFO] Triggering relay (LED should flash)...")

    for i in range(3):
        print(f"[INFO] Flash {i + 1}/3")
        GPIO.output(RELAY_PIN, 1)
        time.sleep(0.5)
        GPIO.output(RELAY_PIN, 0)
        time.sleep(0.5)

    print("[INFO] Test complete")

except Exception as e:
    print(f"[ERROR] GPIO test failed: {e}")
finally:
    try:
        GPIO.cleanup()
    except:
        pass
