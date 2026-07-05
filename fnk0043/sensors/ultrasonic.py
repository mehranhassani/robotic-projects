"""HC-SR04 ultrasonic distance sensor."""

from __future__ import annotations

from fnk0043.config import HardwareConfig


class UltrasonicSensor:
    def __init__(self, gpio, config: HardwareConfig, max_distance_m: float = 3.0):
        self._gpio = gpio
        self._trigger = config.pins.ultrasonic_trigger
        self._echo = config.pins.ultrasonic_echo
        self._max_m = max_distance_m

    def distance_cm(self) -> float | None:
        try:
            return self._gpio.read_distance_cm(self._trigger, self._echo, self._max_m)
        except RuntimeError:
            return None

    def close(self) -> None:
        pass
