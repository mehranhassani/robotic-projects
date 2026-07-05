"""Simulated hardware for development off the Pi."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from fnk0043.config import HardwareConfig


@dataclass
class MockState:
    motor_duties: dict[int, int] = field(default_factory=dict)
    servo_pulses: dict[int, float] = field(default_factory=dict)
    adc_voltages: list[float] = field(default_factory=lambda: [2.5, 2.5, 4.2])
    line_pins: dict[int, bool] = field(default_factory=lambda: {14: False, 15: True, 23: False})
    buzzer_on: bool = False
    distance_cm: float = 45.0


class MockPCA9685:
    def __init__(self, state: MockState):
        self._state = state

    def set_pwm_freq(self, freq: float) -> None:
        pass

    def set_motor_pwm(self, channel: int, duty: int) -> None:
        self._state.motor_duties[channel] = duty

    def set_servo_pulse(self, channel: int, pulse_us: float) -> None:
        self._state.servo_pulses[channel] = pulse_us

    def close(self) -> None:
        pass


class MockADC:
    def __init__(self, config: HardwareConfig, state: MockState):
        self.pcb_version = config.pcb_version
        self._state = state

    def read_voltage(self, channel: int) -> float:
        base = self._state.adc_voltages[channel]
        return round(base + random.uniform(-0.05, 0.05), 2)

    def close(self) -> None:
        pass


class MockGPIO:
    def __init__(self, state: MockState):
        self._state = state

    def read_line_sensor(self, pin: int) -> bool:
        return self._state.line_pins.get(pin, False)

    def set_output(self, pin: int, state: bool) -> None:
        if pin == 17:
            self._state.buzzer_on = state

    def read_distance_cm(self, trigger: int, echo: int, max_m: float) -> float:
        drift = random.uniform(-2, 2)
        self._state.distance_cm = max(5.0, min(max_m * 100, self._state.distance_cm + drift))
        return round(self._state.distance_cm, 1)

    def close(self) -> None:
        pass


class HALBundle:
    def __init__(self, config: HardwareConfig):
        self.state = MockState()
        self.pca9685 = MockPCA9685(self.state)
        self.adc = MockADC(config, self.state)
        self.gpio = MockGPIO(self.state)
        self.mock = True

    def close(self) -> None:
        pass
