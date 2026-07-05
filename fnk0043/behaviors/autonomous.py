"""Light follow, line follow, and ultrasonic obstacle avoidance."""

from __future__ import annotations

import time
from enum import Enum

from fnk0043.motors.drive import DriveSystem, WheelDuties


class DriveMode(str, Enum):
    MANUAL = "manual"
    LIGHT_FOLLOW = "light_follow"
    LINE_FOLLOW = "line_follow"
    OBSTACLE_AVOID = "obstacle_avoid"


class AutonomousController:
    def __init__(self, robot):
        self._robot = robot
        self.mode = DriveMode.MANUAL
        self._last_tick = 0.0
        self._scan_angle = 30
        self._scan_dir = 1
        self._scan_distances = [30.0, 30.0, 30.0]

    def set_mode(self, mode: DriveMode) -> None:
        if mode == DriveMode.MANUAL:
            self._robot.drive.stop()
        self.mode = mode

    def tick(self) -> None:
        if time.time() - self._last_tick < 0.2:
            return
        self._last_tick = time.time()

        if self.mode == DriveMode.LIGHT_FOLLOW:
            self._light_follow()
        elif self.mode == DriveMode.LINE_FOLLOW:
            self._line_follow()
        elif self.mode == DriveMode.OBSTACLE_AVOID:
            self._obstacle_avoid()

    def _light_follow(self) -> None:
        drive = self._robot.drive
        light = self._robot.light.read()
        drive.stop()
        if light.left_v < 2.99 and light.right_v < 2.99:
            drive.drive_raw(600, 600, 600, 600)
        elif light.brighter_side == "left":
            drive.drive_raw(-1200, -1200, 1400, 1400)
        elif light.brighter_side == "right":
            drive.drive_raw(1400, 1400, -1200, -1200)

    def _line_follow(self) -> None:
        drive = self._robot.drive
        line = self._robot.line.read()
        pattern = line.bitmask
        if pattern == 2:
            drive.drive_raw(800, 800, 800, 800)
        elif pattern == 4:
            drive.drive_raw(-1500, -1500, 2500, 2500)
        elif pattern == 6:
            drive.drive_raw(-2000, -2000, 4000, 4000)
        elif pattern == 1:
            drive.drive_raw(2500, 2500, -1500, -1500)
        elif pattern == 3:
            drive.drive_raw(4000, 4000, -2000, -2000)
        elif pattern == 7:
            drive.stop()

    def _obstacle_avoid(self) -> None:
        servo = self._robot.pan_servo
        sonic = self._robot.ultrasonic
        drive = self._robot.drive

        servo.set_angle(self._scan_angle)
        if self._scan_angle == 30:
            self._scan_distances[0] = sonic.distance_cm() or 30
        elif self._scan_angle == 90:
            self._scan_distances[1] = sonic.distance_cm() or 30
        elif self._scan_angle == 150:
            self._scan_distances[2] = sonic.distance_cm() or 30

        d = self._scan_distances
        if (d[0] < 30 and d[1] < 30 and d[2] < 30) or d[1] < 30:
            drive.drive_raw(-1450, -1450, -1450, -1450)
            time.sleep(0.1)
            if d[0] < d[2]:
                drive.drive_raw(1450, 1450, -1450, -1450)
            else:
                drive.drive_raw(-1450, -1450, 1450, 1450)
        elif d[0] < 30 and d[1] < 30:
            drive.drive_raw(1500, 1500, -1500, -1500)
        elif d[2] < 30 and d[1] < 30:
            drive.drive_raw(-1500, -1500, 1500, 1500)
        elif d[0] < 20:
            drive.drive_raw(2000, 2000, -500, -500)
            if d[0] < 10:
                drive.drive_raw(1500, 1500, -1000, -1000)
        elif d[2] < 20:
            drive.drive_raw(-500, -500, 2000, 2000)
            if d[2] < 10:
                drive.drive_raw(-1500, -1500, 1500, 1500)
        else:
            drive.drive_raw(600, 600, 600, 600)

        if self._scan_angle <= 30:
            self._scan_dir = 1
        elif self._scan_angle >= 150:
            self._scan_dir = 0
        self._scan_angle += 60 if self._scan_dir else -60
