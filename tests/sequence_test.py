#!/usr/bin/env python3
"""
Test the countdown sequence and audio
Expected sequence: Button -> 3,2,1 (with beeps) -> SMILE (with shutter) -> Photos -> Gotcha
"""

import time


def test_countdown_sequence():
    """Test the expected countdown timing"""
    print("PhotoBooth Sequence Test")
    print("=" * 30)

    COUNTDOWN_SECONDS = 3

    print("Button pressed! Starting countdown...")
    countdown_start_time = time.time()
    last_countdown_number = None

    # Simulate the countdown loop
    for i in range(50):  # 5 seconds worth of checks at 10Hz
        now = time.time()
        elapsed = now - countdown_start_time

        if elapsed < COUNTDOWN_SECONDS:
            # During countdown
            seconds_left = int(math.ceil(COUNTDOWN_SECONDS - elapsed))

            if seconds_left > 0 and last_countdown_number != seconds_left:
                print(f"⏰ COUNTDOWN: {seconds_left} (BEEP!)")
                last_countdown_number = seconds_left

        elif elapsed >= COUNTDOWN_SECONDS and elapsed < COUNTDOWN_SECONDS + 0.1:
            # Right after countdown ends
            print("📸 SMILE! (SHUTTER SOUND!)")

        elif elapsed >= COUNTDOWN_SECONDS + 3:
            # After smile period
            print("👻 GOTCHA! (SCARE!)")
            break

        time.sleep(0.1)  # 10Hz like main loop

    print(f"Total sequence time: {time.time() - countdown_start_time:.1f}s")


if __name__ == "__main__":
    import math

    test_countdown_sequence()
