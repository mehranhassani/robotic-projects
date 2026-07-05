"""Select real or mock hardware backend."""

from __future__ import annotations

from fnk0043.config import HardwareConfig, use_mock_hardware


def create_hal(config: HardwareConfig):
    if use_mock_hardware():
        from fnk0043.hal import mock as backend

        return backend.HALBundle(config)
    from fnk0043.hal import real as backend

    return backend.HALBundle(config)
