"""Main robot facade combining all subsystems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fnk0043.actuators.buzzer import Buzzer
from fnk0043.actuators.leds import LedStrip
from fnk0043.actuators.servo import PanServo, ServoBank, TiltServo
from fnk0043.behaviors.autonomous import AutonomousController, DriveMode
from fnk0043.camera.stream import CameraStream
from fnk0043.config import HardwareConfig, hardware_from_params
from fnk0043.hal.factory import create_hal
from fnk0043.motors.drive import DriveSystem
from fnk0043.sensors.battery import BatteryMonitor
from fnk0043.sensors.infrared import LineTracker
from fnk0043.sensors.light import LightSensor
from fnk0043.sensors.ultrasonic import UltrasonicSensor


@dataclass
class SensorSnapshot:
    distance_cm: float | None
    light_left_v: float
    light_right_v: float
    line_left: int
    line_center: int
    line_right: int
    battery_v: float
    mock: bool


class FNK0043:
    """Unified interface to the Freenove FNK0043 smart car."""

    def __init__(self, config: HardwareConfig | None = None):
        self.config = config or hardware_from_params()
        self._hal = create_hal(self.config)
        self.drive = DriveSystem(self._hal.pca9685, self.config)
        self.ultrasonic = UltrasonicSensor(self._hal.gpio, self.config)
        self.line = LineTracker(self._hal.gpio, self.config)
        self.light = LightSensor(self._hal.adc, self.config)
        self.battery = BatteryMonitor(self._hal.adc, self.config)
        self.buzzer = Buzzer(self._hal.gpio, self.config)
        self.servos = ServoBank(self._hal.pca9685, self.config)
        self.pan_servo = PanServo(self.servos)
        self.tilt_servo = TiltServo(self.servos)
        self.leds = LedStrip(self.config)
        self.camera = CameraStream()
        self.autonomous = AutonomousController(self)
        self._closed = False
        self._sensor_cache: dict[str, object] = {}
        self._sensor_cache_at = 0.0

    def _sensor_cache_ttl(self) -> float:
        return 0.4

    def _read_sensors_cached(self) -> SensorSnapshot:
        import time

        now = time.time()
        if now - self._sensor_cache_at < self._sensor_cache_ttl():
            cached = self._sensor_cache.get("snap")
            if cached is not None:
                return cached  # type: ignore[return-value]

        light = self.light.read()
        line = self.line.read()
        snap = SensorSnapshot(
            distance_cm=self.ultrasonic.distance_cm(),
            light_left_v=light.left_v,
            light_right_v=light.right_v,
            line_left=line.left,
            line_center=line.center,
            line_right=line.right,
            battery_v=self.battery.voltage,
            mock=self.mock,
        )
        self._sensor_cache["snap"] = snap
        self._sensor_cache_at = now
        return snap

    @property
    def mock(self) -> bool:
        return self._hal.mock

    def sensors(self) -> SensorSnapshot:
        return self._read_sensors_cached()

    def set_drive_mode(self, mode: DriveMode) -> None:
        self.autonomous.set_mode(mode)

    def update(self) -> None:
        """Call periodically when an autonomous mode is active."""
        self.autonomous.tick()

    def status(self) -> dict[str, Any]:
        snap = self.sensors()
        return {
            "mock": snap.mock,
            "chassis": self.config.chassis.value,
            "drive_mode": self.autonomous.mode.value,
            "battery_v": snap.battery_v,
            "distance_cm": snap.distance_cm,
            "light": {"left": snap.light_left_v, "right": snap.light_right_v},
            "line": {"left": snap.line_left, "center": snap.line_center, "right": snap.line_right},
            "pan_angle": self.pan_servo.angle,
            "tilt_angle": self.tilt_servo.angle,
            "swap_forward_back": self.config.swap_forward_back,
            "swap_left_right": self.config.swap_left_right,
            "invert_drive": self.config.invert_drive,
        }

    def close(self) -> None:
        if self._closed:
            return
        self.autonomous.set_mode(DriveMode.MANUAL)
        self.camera.close()
        self.leds.close()
        self.drive.close()
        self.ultrasonic.close()
        self.line.close()
        self.light.close()
        self.battery.close()
        self.buzzer.close()
        self.servos.close()
        self._hal.close()
        self._closed = True

    def __enter__(self) -> "FNK0043":
        return self

    def __exit__(self, *args) -> None:
        self.close()
