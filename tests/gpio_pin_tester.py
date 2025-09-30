#!/usr/bin/env python3
"""
Cycle through all GPIO pins and let you test which pin is connected to your button or relay/LED.
- For input: Press your button and see which pin reports a change.
- For output: The script will blink each pin in turn; watch your relay/LED to see which one lights up.
"""

import time

try:
    import RPi.GPIO as GPIO
except Exception as e:
    print("[ERROR] RPi.GPIO not available. Run this on a real Raspberry Pi.")
    exit(1)

GPIO.setmode(GPIO.BCM)
ALL_PINS = [
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
]

print("\n--- GPIO Pin Tester ---")
print(
    "This will cycle through all GPIO pins as output (relay/LED test), then as input (button test).\n"
)

# Output test: blink each pin
print("[OUTPUT TEST] Watching for relay/LED. Each pin will blink for 1 second.")
for pin in ALL_PINS:
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 1)
        print(f"[INFO] Pin {pin} ON (should see relay/LED if connected)")
        time.sleep(1)
        GPIO.output(pin, 0)
        GPIO.setup(pin, GPIO.IN)
    except Exception as e:
        print(f"[WARN] Pin {pin} could not be tested as output: {e}")

# Input test: detect button press
print("\n[INPUT TEST] Press your button now. Waiting 10 seconds...")
pressed = False
for pin in ALL_PINS:
    try:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    except Exception as e:
        print(f"[WARN] Pin {pin} could not be set as input: {e}")

start = time.time()
while time.time() - start < 10:
    for pin in ALL_PINS:
        try:
            if GPIO.input(pin) == 0:
                print(f"[INFO] Button press detected on pin {pin} (BCM numbering)")
                pressed = True
        except Exception:
            pass
    time.sleep(0.05)
if not pressed:
    print("[INFO] No button press detected on any tested pin.")

GPIO.cleanup()
print("[DONE] Pin test complete.")
