"""Active buzzer on GPIO 17."""

from __future__ import annotations

from fnk0043.config import HardwareConfig


class Buzzer:
    def __init__(self, gpio, config: HardwareConfig):
        self._gpio = gpio
        self._pin = config.pins.buzzer

    def on(self) -> None:
        self._gpio.set_output(self._pin, True)

    def off(self) -> None:
        self._gpio.set_output(self._pin, False)

    def beep(self, times: int = 1, duration_s: float = 0.1) -> None:
        import time

        for _ in range(times):
            self.on()
            time.sleep(duration_s)
            self.off()
            time.sleep(duration_s)

    def close(self) -> None:
        self.off()
