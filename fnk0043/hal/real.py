"""Real Raspberry Pi hardware via smbus and gpiozero."""

from __future__ import annotations

import math
import time

from fnk0043.config import HardwareConfig


def _open_smbus(bus_id: int = 1):
    """Prefer smbus2 (pip); fall back to system smbus."""
    try:
        import smbus2 as smbus
    except ImportError:
        import smbus  # type: ignore
    return smbus.SMBus(bus_id)


class RealPCA9685:
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06

    def __init__(self, config: HardwareConfig):
        self._bus = _open_smbus(1)
        self._address = config.pca9685_address
        self._bus.write_byte_data(self._address, self.__MODE1, 0x00)

    def write(self, reg: int, value: int) -> None:
        self._bus.write_byte_data(self._address, reg, value)

    def read(self, reg: int) -> int:
        return self._bus.read_byte_data(self._address, reg)

    def set_pwm_freq(self, freq: float) -> None:
        prescaleval = 25000000.0 / 4096.0 / float(freq) - 1.0
        prescale = math.floor(prescaleval + 0.5)
        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        self.write(self.__MODE1, newmode)
        self.write(self.__PRESCALE, int(math.floor(prescale)))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def set_pwm(self, channel: int, on: int, off: int) -> None:
        self.write(self.__LED0_ON_L + 4 * channel, on & 0xFF)
        self.write(self.__LED0_ON_L + 4 * channel + 1, on >> 8)
        self.write(self.__LED0_ON_L + 4 * channel + 2, off & 0xFF)
        self.write(self.__LED0_ON_L + 4 * channel + 3, off >> 8)

    def set_motor_pwm(self, channel: int, duty: int) -> None:
        self.set_pwm(channel, 0, duty)

    def set_servo_pulse(self, channel: int, pulse_us: float) -> None:
        pulse = pulse_us * 4096 / 20000
        self.set_pwm(channel, 0, int(pulse))

    def close(self) -> None:
        self._bus.close()


class RealADC:
    __COMMAND = 0x84

    def __init__(self, config: HardwareConfig):
        self.pcb_version = config.pcb_version
        self._scale = config.adc_voltage_scale
        self._bus = _open_smbus(1)
        self._address = config.adc_address

    def _read_stable_byte(self) -> int:
        while True:
            v1 = self._bus.read_byte(self._address)
            v2 = self._bus.read_byte(self._address)
            if v1 == v2:
                return v1

    def read_voltage(self, channel: int) -> float:
        command = self.__COMMAND | ((((channel << 2) | (channel >> 1)) & 0x07) << 4)
        self._bus.write_byte(self._address, command)
        value = self._read_stable_byte()
        return round(value / 255.0 * self._scale, 2)

    def close(self) -> None:
        self._bus.close()


class RealGPIO:
    def __init__(self, config: HardwareConfig):
        from gpiozero import DistanceSensor, LineSensor, OutputDevice

        self._config = config
        self._outputs: dict[int, OutputDevice] = {}
        self._line_sensors: dict[int, LineSensor] = {}
        self._distance: DistanceSensor | None = None

    def _output(self, pin: int) -> "OutputDevice":
        from gpiozero import OutputDevice

        if pin not in self._outputs:
            self._outputs[pin] = OutputDevice(pin)
        return self._outputs[pin]

    def read_line_sensor(self, pin: int) -> bool:
        from gpiozero import LineSensor

        if pin not in self._line_sensors:
            self._line_sensors[pin] = LineSensor(pin)
        return bool(self._line_sensors[pin].value)

    def set_output(self, pin: int, state: bool) -> None:
        device = self._output(pin)
        device.on() if state else device.off()

    def read_distance_cm(self, trigger: int, echo: int, max_m: float) -> float:
        from gpiozero import DistanceSensor

        if self._distance is None:
            self._distance = DistanceSensor(echo=echo, trigger=trigger, max_distance=max_m)
        return round(float(self._distance.distance * 100), 1)

    def close(self) -> None:
        if self._distance is not None:
            self._distance.close()
        for sensor in self._line_sensors.values():
            sensor.close()
        for output in self._outputs.values():
            output.close()


class HALBundle:
    def __init__(self, config: HardwareConfig):
        self.pca9685 = RealPCA9685(config)
        self.adc = RealADC(config)
        self.gpio = RealGPIO(config)
        self.mock = False

    def close(self) -> None:
        self.pca9685.close()
        self.adc.close()
        self.gpio.close()
