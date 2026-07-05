"""Photoresistor light sensors via ADS7830 ADC."""

from __future__ import annotations

from dataclasses import dataclass

from fnk0043.config import HardwareConfig


@dataclass
class LightReading:
    left_v: float
    right_v: float

    @property
    def brighter_side(self) -> str | None:
        if abs(self.left_v - self.right_v) < 0.15:
            return None
        return "left" if self.left_v > self.right_v else "right"


class LightSensor:
    LEFT_CHANNEL = 0
    RIGHT_CHANNEL = 1

    def __init__(self, adc, config: HardwareConfig):
        self._adc = adc
        self._config = config

    def read(self) -> LightReading:
        return LightReading(
            self._adc.read_voltage(self.LEFT_CHANNEL),
            self._adc.read_voltage(self.RIGHT_CHANNEL),
        )

    def close(self) -> None:
        pass
