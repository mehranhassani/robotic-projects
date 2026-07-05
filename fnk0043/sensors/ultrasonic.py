"""HC-SR04 ultrasonic distance sensor."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from fnk0043.config import HardwareConfig

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ultrasonic")


class UltrasonicSensor:
    READ_TIMEOUT_S = 0.4

    def __init__(self, gpio, config: HardwareConfig, max_distance_m: float = 3.0):
        self._gpio = gpio
        self._trigger = config.pins.ultrasonic_trigger
        self._echo = config.pins.ultrasonic_echo
        self._max_m = max_distance_m
        self._last_reading: float | None = None

    def _read_blocking(self) -> float | None:
        try:
            return self._gpio.read_distance_cm(self._trigger, self._echo, self._max_m)
        except (RuntimeError, OSError):
            return None

    def distance_cm(self) -> float | None:
        future = _executor.submit(self._read_blocking)
        try:
            reading = future.result(timeout=self.READ_TIMEOUT_S)
        except FuturesTimeout:
            future.cancel()
            return self._last_reading
        self._last_reading = reading
        return reading

    def close(self) -> None:
        pass
