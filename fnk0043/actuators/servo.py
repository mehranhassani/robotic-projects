"""PCA9685 servo control for camera pan and extras."""

from __future__ import annotations

from fnk0043.config import HardwareConfig


class ServoBank:
    CHANNEL_MAP = {
        "0": 8,
        "1": 9,
        "2": 10,
        "3": 11,
        "4": 12,
        "5": 13,
        "6": 14,
        "7": 15,
    }

    def __init__(self, pca9685, config: HardwareConfig):
        self._pwm = pca9685
        self._pwm.set_pwm_freq(50)
        for channel in self.CHANNEL_MAP.values():
            self._pwm.set_servo_pulse(channel, 1500)

    def set_angle(self, logical_channel: str, angle: int, error: int = 10) -> None:
        if logical_channel not in self.CHANNEL_MAP:
            raise ValueError(f"Invalid channel {logical_channel}")
        angle = int(angle)
        if logical_channel == "0":
            pulse = 2500 - int((angle + error) / 0.09)
        else:
            pulse = 500 + int((angle + error) / 0.09)
        self._pwm.set_servo_pulse(self.CHANNEL_MAP[logical_channel], pulse)

    def close(self) -> None:
        pass


class TiltServo:
    """Camera tilt servo (channel 1)."""

    MIN_ANGLE = 30
    CENTER_ANGLE = 90
    MAX_ANGLE = 150

    def __init__(self, servos: ServoBank):
        self._servos = servos
        self._angle = self.CENTER_ANGLE
        self.center()

    @property
    def angle(self) -> int:
        return self._angle

    def set_angle(self, angle: int) -> None:
        self._angle = max(self.MIN_ANGLE, min(self.MAX_ANGLE, angle))
        self._servos.set_angle("1", self._angle)

    def center(self) -> None:
        self.set_angle(self.CENTER_ANGLE)


class PanServo:
    """Ultrasonic scanner pan servo (channel 0)."""

    MIN_ANGLE = 30
    CENTER_ANGLE = 90
    MAX_ANGLE = 150

    def __init__(self, servos: ServoBank):
        self._servos = servos
        self._angle = self.CENTER_ANGLE
        self.center()

    @property
    def angle(self) -> int:
        return self._angle

    def set_angle(self, angle: int) -> None:
        self._angle = max(self.MIN_ANGLE, min(self.MAX_ANGLE, angle))
        self._servos.set_angle("0", self._angle)

    def center(self) -> None:
        self.set_angle(self.CENTER_ANGLE)

    def sweep_left_center_right(self) -> tuple[float, float, float]:
        """Return (left, center, right) ultrasonic scan positions."""
        readings: list[float] = []
        for angle in (self.MIN_ANGLE, self.CENTER_ANGLE, self.MAX_ANGLE):
            self.set_angle(angle)
            readings.append(angle)
        return tuple(readings)  # type: ignore[return-value]
