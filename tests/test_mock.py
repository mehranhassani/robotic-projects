"""Basic tests runnable without Raspberry Pi hardware."""

import os

os.environ["FNK0043_MOCK"] = "1"

from fnk0043 import FNK0043, DriveMode
from fnk0043.motors.drive import Direction


def test_robot_mock_sensors():
    with FNK0043() as robot:
        assert robot.mock is True
        snap = robot.sensors()
        assert snap.battery_v > 0


def test_drive_stop():
    with FNK0043() as robot:
        robot.drive.move(Direction.FORWARD, 0.5)
        robot.drive.stop()


def test_autonomous_mode_switch():
    with FNK0043() as robot:
        robot.set_drive_mode(DriveMode.LINE_FOLLOW)
        assert robot.autonomous.mode == DriveMode.LINE_FOLLOW
        robot.update()
        robot.set_drive_mode(DriveMode.MANUAL)
