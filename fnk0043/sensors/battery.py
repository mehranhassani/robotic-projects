"""Battery voltage monitor."""

from __future__ import annotations

from fnk0043.config import HardwareConfig


class BatteryMonitor:
    POWER_CHANNEL = 2

    def __init__(self, adc, config: HardwareConfig):
        self._adc = adc
        self._multiplier = config.battery_multiplier

    @property
    def voltage(self) -> float:
        return round(self._adc.read_voltage(self.POWER_CHANNEL) * self._multiplier, 2)

    def close(self) -> None:
        pass
