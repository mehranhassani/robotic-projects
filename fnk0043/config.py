"""Hardware configuration and runtime settings."""

from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ChassisType(str, Enum):
    STANDARD = "standard"  # fnk0043A — ordinary 4WD
    MECANUM = "mecanum"  # fnk0043B — omni wheels


@dataclass
class PinConfig:
    ultrasonic_trigger: int = 27
    ultrasonic_echo: int = 22
    buzzer: int = 17
    ir_sensors: dict[int, int] = field(
        default_factory=lambda: {1: 14, 2: 15, 3: 23}
    )


@dataclass
class HardwareConfig:
    """Board-specific settings from Freenove params.json."""

    connect_version: int = 2
    pcb_version: int = 1
    pi_version: int = 1
    chassis: ChassisType = ChassisType.STANDARD
    pins: PinConfig = field(default_factory=PinConfig)
    pca9685_address: int = 0x40
    adc_address: int = 0x48
    motor_pwm_freq: int = 50
    max_duty: int = 4095
    default_speed: float = 0.6
    invert_drive: bool = False
    swap_forward_back: bool = True
    swap_left_right: bool = True

    @property
    def adc_voltage_scale(self) -> float:
        return 3.3 if self.pcb_version == 1 else 5.2

    @property
    def battery_multiplier(self) -> float:
        return 3.0 if self.pcb_version == 1 else 2.0


def is_raspberry_pi() -> bool:
    if os.environ.get("FNK0043_MOCK", "").lower() in ("1", "true", "yes"):
        return False
    try:
        with open("/proc/device-tree/model") as f:
            return "Raspberry Pi" in f.read()
    except OSError:
        return platform.system() == "Linux" and Path("/sys/firmware/devicetree/base/model").exists()


def use_mock_hardware() -> bool:
    return os.environ.get("FNK0043_MOCK", "").lower() in ("1", "true", "yes") or not is_raspberry_pi()


def default_params_path() -> Path:
    env_path = os.environ.get("FNK0043_PARAMS")
    if env_path:
        return Path(env_path)
    return Path.cwd() / "params.json"


def load_params(path: Path | str | None = None) -> dict[str, Any]:
    path = Path(path) if path else default_params_path()
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _param_bool(params: dict[str, Any], key: str, default: bool) -> bool:
    if key not in params:
        return default
    return bool(params[key])


def hardware_from_params(
    params_path: Path | str | None = None,
    chassis: ChassisType | None = None,
) -> HardwareConfig:
    params = load_params(params_path)
    invert_env = os.environ.get("FNK0043_INVERT_DRIVE", "").lower()
    invert_drive = params.get("Invert_Drive")
    if invert_drive is None:
        invert_drive = invert_env in ("1", "true", "yes")
    else:
        invert_drive = bool(invert_drive)
    swap_forward_back = _param_bool(params, "Swap_Forward_Back", True)
    swap_left_right = _param_bool(params, "Swap_Left_Right", True)
    return HardwareConfig(
        connect_version=params.get("Connect_Version", 2),
        pcb_version=params.get("Pcb_Version", 1),
        pi_version=params.get("Pi_Version", 1),
        chassis=chassis or ChassisType(os.environ.get("FNK0043_CHASSIS", "standard")),
        invert_drive=invert_drive,
        swap_forward_back=swap_forward_back,
        swap_left_right=swap_left_right,
    )
