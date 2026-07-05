"""Hold pan/tilt servos at center for hardware horn installation."""

from __future__ import annotations

import signal
import sys
import time


def main() -> None:
    print("FNK0043 - hardware servo recenter")
    print("=" * 40)
    print()
    print("Stop the web server first (otherwise I2C may be busy):")
    print("  systemctl --user stop fnk0043")
    print()

    from fnk0043 import FNK0043

    robot = FNK0043()
    if robot.mock:
        print("error: running in mock mode - run this on the Raspberry Pi, not your Mac.")
        robot.close()
        sys.exit(1)

    def cleanup(*_args) -> None:
        print("\nDone. Servos at center. You can restart the server:")
        print("  systemctl --user start fnk0043")
        robot.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    robot.pan_servo.center()
    robot.tilt_servo.center()

    print(
        """
Servo0 = PAN (left/right)  -  camera/ultrasonic bracket
Servo1 = TILT (up/down)    -  camera tilt

Hardware steps (Freenove Pan-Tilt, Ch. 2):
  1. Keep this program running - both servos stay at 90 deg
  2. If horns are already on, remove them carefully
  3. Mount horns/brackets so the camera points level and straight ahead
  4. Do NOT swap Servo0 and Servo1 on the expansion board
  5. Tighten the M2 horn screw on each servo (snug, don't strip)
  6. Tighten pan bracket: M2x10 screw + M2 nut on Servo0
  7. Press Ctrl+C when finished

Holding center position...
"""
    )

    try:
        while True:
            robot.pan_servo.center()
            robot.tilt_servo.center()
            time.sleep(0.5)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
