"""
gpio_manager.py
Abstracts GPIO access for both real Raspberry Pi and fake/mock GPIO for development.
"""

try:
    import RPi.GPIO as GPIO
except Exception:
    import fake_gpio as GPIO


class GPIOManager:
    def __init__(self, button_pin, relay_pin):
        self.button_pin = button_pin
        self.relay_pin = relay_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.relay_pin, GPIO.OUT)

    def add_event_detect(self, callback):
        GPIO.add_event_detect(
            self.button_pin, GPIO.FALLING, callback=callback, bouncetime=200
        )

    def trigger_scare(self):
        GPIO.output(self.relay_pin, 1)
        import time

        time.sleep(0.3)
        GPIO.output(self.relay_pin, 0)

    def cleanup(self):
        GPIO.cleanup()
