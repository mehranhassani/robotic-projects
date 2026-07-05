"""Semantic 4WD motor control built on PCA9685."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from fnk0043.config import ChassisType, HardwareConfig


class Direction(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    STOP = "stop"


@dataclass
class WheelDuties:
    front_left: int
    rear_left: int
    front_right: int
    rear_right: int

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.front_left, self.rear_left, self.front_right, self.rear_right


class DriveSystem:
    """High-level drive API with normalized speed (0.0–1.0)."""

    def __init__(self, pca9685, config: HardwareConfig):
        self._pwm = pca9685
        self._config = config
        self._pwm.set_pwm_freq(config.motor_pwm_freq)
        self._speed_scale = 0.8  # matches Freenove client scaling

    def _to_duty(self, speed: float) -> int:
        speed = max(-1.0, min(1.0, speed))
        return int(round(speed * self._config.max_duty * self._speed_scale))

    def _clamp_duty(self, *duties: int) -> tuple[int, ...]:
        limit = self._config.max_duty
        return tuple(max(-limit, min(limit, d)) for d in duties)

    def _set_wheel(self, channel_fwd: int, channel_rev: int, duty: int) -> None:
        if duty > 0:
            self._pwm.set_motor_pwm(channel_fwd, 0)
            self._pwm.set_motor_pwm(channel_rev, duty)
        elif duty < 0:
            self._pwm.set_motor_pwm(channel_rev, 0)
            self._pwm.set_motor_pwm(channel_fwd, abs(duty))
        else:
            self._pwm.set_motor_pwm(channel_fwd, 4095)
            self._pwm.set_motor_pwm(channel_rev, 4095)

    def set_wheels(self, duties: WheelDuties) -> None:
        fl, bl, fr, br = self._clamp_duty(*duties.as_tuple())
        if self._config.invert_drive:
            fl, bl, fr, br = -fl, -bl, -fr, -br
        self._set_wheel(0, 1, fl)
        self._set_wheel(3, 2, bl)
        self._set_wheel(6, 7, fr)
        self._set_wheel(4, 5, br)

    def stop(self) -> None:
        self.set_wheels(WheelDuties(0, 0, 0, 0))

    def move(self, direction: Direction, speed: float = 0.6) -> None:
        duty = self._to_duty(speed)
        mapping = {
            Direction.FORWARD: WheelDuties(duty, duty, duty, duty),
            Direction.BACKWARD: WheelDuties(-duty, -duty, -duty, -duty),
            Direction.LEFT: WheelDuties(-duty, -duty, duty, duty),
            Direction.RIGHT: WheelDuties(duty, duty, -duty, -duty),
            Direction.STOP: WheelDuties(0, 0, 0, 0),
        }
        self.set_wheels(mapping[direction])

    def drive_raw(self, fl: int, bl: int, fr: int, br: int) -> None:
        """Set per-wheel PWM duty (-4095..4095), matching Freenove CMD_MOTOR."""
        self.set_wheels(WheelDuties(fl, bl, fr, br))

    def drive_joystick(self, angle_deg: float, magnitude: float) -> None:
        """Single-stick drive: angle 0° = forward, 90° = right."""
        rad = math.radians(angle_deg)
        lx = -int(magnitude * self._config.max_duty * math.sin(rad))
        ly = int(magnitude * self._config.max_duty * math.cos(rad))
        self.drive_mecanum(lx, ly, 0, 0)

    def drive_mecanum(
        self,
        left_angle: float,
        left_mag: float,
        right_angle: float,
        right_mag: float,
    ) -> None:
        """Dual-stick / mecanum mixing (CMD_M_MOTOR compatible)."""
        if self._config.chassis == ChassisType.STANDARD:
            lx = -int(left_mag * self._config.max_duty * math.sin(math.radians(left_angle)))
            ly = int(left_mag * self._config.max_duty * math.cos(math.radians(left_angle)))
            rx = int(right_mag * self._config.max_duty * math.sin(math.radians(right_angle)))
            ry = int(right_mag * self._config.max_duty * math.cos(math.radians(right_angle)))
        else:
            lx = -int(left_mag * math.sin(math.radians(left_angle)))
            ly = int(left_mag * math.cos(math.radians(left_angle)))
            rx = int(right_mag * math.sin(math.radians(right_angle)))
            ry = int(right_mag * math.cos(math.radians(right_angle)))

        fr = ly - lx + rx
        fl = ly + lx - rx
        bl = ly - lx - rx
        br = ly + lx + rx
        self.drive_raw(fl, bl, fr, br)

    def close(self) -> None:
        self.stop()
