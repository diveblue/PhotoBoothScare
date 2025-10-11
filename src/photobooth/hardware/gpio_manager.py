"""
GPIOManager - Hardware Abstraction for GPIO Operations

RESPONSIBILITIES:
- Abstracts GPIO access for both Raspberry Pi hardware and development environments
- Manages button input detection with debouncing and callback registration
- Controls relay/prop trigger output for scare effects
- Provides unified interface regardless of underlying GPIO implementation

KEY METHODS:
- add_event_detect(): Register callback for button press events with debouncing
- trigger_scare(): Activate relay/prop for scare effect (active-low, 0.3s duration)
- cleanup(): Clean shutdown of GPIO resources

HARDWARE ABSTRACTION:
- Real Hardware: Uses RPi.GPIO for actual Raspberry Pi deployment
- Development: Uses fake_gpio module for testing without hardware
- Automatic fallback ensures code works in both environments

GPIO CONFIGURATION:
- Button: Input with pull-up resistor, falling edge detection
- Relay: Output for controlling external scare props (active-low)
- BCM pin numbering mode for consistency

ARCHITECTURE:
- Hardware abstraction following Dependency Inversion principle
- Encapsulates GPIO complexity from higher-level managers
- Clean separation between hardware interface and business logic
"""

import logging

try:
    import RPi.GPIO as GPIO
except Exception:
    from . import fake_gpio as GPIO


class GPIOManager:
    """
    Hardware abstraction layer for GPIO operations.

    Provides unified GPIO interface for button input and relay control,
    with automatic fallback between real hardware and development mock.
    """

    def __init__(self, config):
        self.button_pin = config["BUTTON_PIN"]
        self.relay_pin = config["RELAY_PIN"]
        self.logger = logging.getLogger(__name__)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        # Ensure relay/LED is OFF at startup - HIGH for active-low relay
        GPIO.output(self.relay_pin, 1)

        self.logger.debug(
            f"🔌 GPIO INITIALIZED: Button={self.button_pin}, Relay={self.relay_pin}"
        )

    def add_event_detect(self, callback):
        GPIO.add_event_detect(
            self.button_pin, GPIO.FALLING, callback=callback, bouncetime=200
        )

    def trigger_scare(self):
        self.logger.debug(
            f"🔌 PROP TRIGGER: Pin {self.relay_pin} -> LOW for 0.3s (active-low)"
        )
        GPIO.output(self.relay_pin, 0)  # LOW to trigger
        import time

        time.sleep(0.3)
        GPIO.output(self.relay_pin, 1)  # HIGH to turn off
        self.logger.debug(f"🔌 PROP TRIGGER: Pin {self.relay_pin} -> HIGH (off)")

    def cleanup(self):
        GPIO.cleanup()
