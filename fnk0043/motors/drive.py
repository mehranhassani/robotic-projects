"""Semantic 4WD motor control built on PCA9685."""

from __future__ import annotations

import math
import threading
import time
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
    """High-level drive API with normalized speed (0.0–1.0) and PWM ramping."""

    SMOOTH_INTERVAL_S = 0.02  # 50 Hz
    RAMP_STEP = 280  # duty units per tick (~0.35 s to full speed)

    def __init__(self, pca9685, config: HardwareConfig):
        self._pwm = pca9685
        self._config = config
        self._pwm.set_pwm_freq(config.motor_pwm_freq)
        self._speed_scale = 0.8  # matches Freenove client scaling
        self._target = [0, 0, 0, 0]
        self._current = [0, 0, 0, 0]
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._smooth_thread = threading.Thread(
            target=self._smooth_loop, name="motor-smooth", daemon=True
        )
        self._smooth_thread.start()

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

    def _apply_pwm(self, duties: tuple[int, int, int, int]) -> None:
        fl, bl, fr, br = self._clamp_duty(*duties)
        if self._config.invert_drive:
            fl, bl, fr, br = -fl, -bl, -fr, -br
        self._set_wheel(0, 1, fl)
        self._set_wheel(3, 2, bl)
        self._set_wheel(6, 7, fr)
        self._set_wheel(4, 5, br)

    def _smooth_loop(self) -> None:
        while not self._stop_event.is_set():
            changed = False
            with self._lock:
                for i in range(4):
                    diff = self._target[i] - self._current[i]
                    if diff == 0:
                        continue
                    step = min(abs(diff), self.RAMP_STEP)
                    self._current[i] += step if diff > 0 else -step
                    changed = True
                if changed:
                    self._apply_pwm(tuple(self._current))
            time.sleep(self.SMOOTH_INTERVAL_S)

    def set_wheels(self, duties: WheelDuties, *, immediate: bool = False) -> None:
        with self._lock:
            self._target = list(self._clamp_duty(*duties.as_tuple()))
            if immediate:
                self._current = self._target.copy()
                self._apply_pwm(tuple(self._current))

    def stop(self) -> None:
        self.set_wheels(WheelDuties(0, 0, 0, 0))

    def move(self, direction: Direction, speed: float = 0.6) -> None:
        duty = self._to_duty(speed)
        forward = -duty if self._config.swap_forward_back else duty
        backward = duty if self._config.swap_forward_back else -duty
        mapping = {
            Direction.FORWARD: WheelDuties(forward, forward, forward, forward),
            Direction.BACKWARD: WheelDuties(backward, backward, backward, backward),
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
        self._stop_event.set()
        self._smooth_thread.join(timeout=1.0)
        with self._lock:
            self._target = [0, 0, 0, 0]
            self._current = [0, 0, 0, 0]
            self._apply_pwm((0, 0, 0, 0))
