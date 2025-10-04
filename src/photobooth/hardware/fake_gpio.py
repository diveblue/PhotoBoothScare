# Minimal RPi.GPIO emulator for local testing
BCM = "BCM"
IN = "IN"
OUT = "OUT"
PUD_UP = "PUD_UP"
FALLING = "FALLING"

_callbacks = {}
_pin_states = {}


def setmode(mode):
    pass


def setup(pin, direction, pull_up_down=None):
    _pin_states[pin] = 1 if direction == IN else 0


def input(pin):
    return _pin_states.get(pin, 1)


def output(pin, value):
    _pin_states[pin] = value
    state = "HIGH" if value else "LOW"
    trigger_msg = " (TRIGGER!)" if value == 0 else " (off)"
    print(f"[FAKE RELAY] Pin {pin} -> {state}{trigger_msg}")


def add_event_detect(pin, edge, callback=None, bouncetime=200):
    if callback:
        _callbacks[pin] = callback


def trigger(pin):
    # Manually trigger a falling edge
    if pin in _callbacks:
        _callbacks[pin](pin)


def cleanup():
    pass
