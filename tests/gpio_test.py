#!/usr/bin/env python3
"""
Test GPIO functionality on Pi
"""

print("GPIO Test")
print("=" * 20)

# Test what GPIO module we're using
try:
    import RPi.GPIO as GPIO

    print("✅ Using REAL RPi.GPIO")
    gpio_type = "REAL"
except ImportError:
    import fake_gpio as GPIO

    print("⚠️  Using FAKE GPIO (development mode)")
    gpio_type = "FAKE"

# Test GPIO setup
try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.OUT)  # Relay pin from config
    print(f"✅ GPIO pin 27 setup as OUTPUT")

    # Test the trigger sequence
    print("Testing relay trigger sequence...")
    print("Pin 27 -> HIGH")
    GPIO.output(27, 1)

    import time

    time.sleep(1)  # Longer for testing

    print("Pin 27 -> LOW")
    GPIO.output(27, 0)

    print("✅ GPIO test completed")

    GPIO.cleanup()

except Exception as e:
    print(f"❌ GPIO test failed: {e}")

print(f"\nGPIO module in use: {gpio_type}")
if gpio_type == "FAKE":
    print("💡 To use real GPIO on Pi, make sure RPi.GPIO is installed:")
    print("   sudo apt install python3-rpi.gpio")
    print("   or: pip install RPi.GPIO")
