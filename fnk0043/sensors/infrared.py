"""Three-channel infrared line tracker."""

from __future__ import annotations

from dataclasses import dataclass

from fnk0043.config import HardwareConfig


@dataclass
class LineReading:
    left: int
    center: int
    right: int

    @property
    def bitmask(self) -> int:
        return (self.left << 2) | (self.center << 1) | self.right

    def on_line(self) -> bool:
        return self.bitmask != 0


class LineTracker:
    CHANNELS = (1, 2, 3)

    def __init__(self, gpio, config: HardwareConfig):
        self._gpio = gpio
        self._pins = config.pins.ir_sensors

    def read(self) -> LineReading:
        values = {
            ch: 1 if self._gpio.read_line_sensor(self._pins[ch]) else 0
            for ch in self.CHANNELS
        }
        return LineReading(values[1], values[2], values[3])

    def close(self) -> None:
        pass
