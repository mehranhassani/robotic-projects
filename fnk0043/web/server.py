"""FastAPI web server for remote robot control."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from fnk0043.behaviors.autonomous import DriveMode
from fnk0043.motors.drive import Direction
from fnk0043.robot import FNK0043

STATIC_DIR = Path(__file__).parent / "static"
_robot: FNK0043 | None = None
_robot_lock = asyncio.Lock()
_autonomy_task: asyncio.Task | None = None


class DriveCommand(BaseModel):
    direction: str | None = None
    speed: float = Field(default=0.6, ge=0.0, le=1.0)
    raw: list[int] | None = None
    joystick: dict[str, float] | None = None


class ModeCommand(BaseModel):
    mode: str


class ServoCommand(BaseModel):
    channel: str = "0"
    angle: int = Field(ge=0, le=180)


class BuzzerCommand(BaseModel):
    on: bool


async def _get_robot() -> FNK0043:
    global _robot
    if _robot is not None:
        return _robot
    async with _robot_lock:
        if _robot is None:
            _robot = await asyncio.to_thread(FNK0043)
    return _robot


async def _run_robot(fn, *args, **kwargs):
    robot = await _get_robot()
    return await asyncio.to_thread(fn, robot, *args, **kwargs)


def _call(robot: FNK0043, method: str, *args, **kwargs):
    return getattr(robot, method)(*args, **kwargs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _autonomy_task
    _autonomy_task = asyncio.create_task(_autonomy_loop())
    yield
    if _autonomy_task:
        _autonomy_task.cancel()
        try:
            await _autonomy_task
        except asyncio.CancelledError:
            pass
    global _robot
    if _robot is not None:
        await asyncio.to_thread(_robot.close)
        _robot = None


app = FastAPI(
    title="FNK0043 Control",
    description="Web control for the Freenove 4WD Smart Car",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


async def _autonomy_loop() -> None:
    while True:
        if _robot and _robot.autonomous.mode != DriveMode.MANUAL:
            await asyncio.to_thread(_robot.update)
        await asyncio.sleep(0.05)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


@app.get("/api/status")
async def status():
    robot = await _get_robot()
    return await asyncio.to_thread(robot.status)


@app.get("/api/sensors")
async def sensors():
    robot = await _get_robot()
    snap = await asyncio.to_thread(robot.sensors)
    return {
        "distance_cm": snap.distance_cm,
        "light_left_v": snap.light_left_v,
        "light_right_v": snap.light_right_v,
        "line": [snap.line_left, snap.line_center, snap.line_right],
        "battery_v": snap.battery_v,
        "mock": snap.mock,
    }


@app.post("/api/drive")
async def drive(cmd: DriveCommand):
    def _drive(robot: FNK0043) -> None:
        robot.set_drive_mode(DriveMode.MANUAL)
        if cmd.raw and len(cmd.raw) == 4:
            robot.drive.drive_raw(*cmd.raw)
        elif cmd.joystick:
            robot.drive.drive_joystick(
                cmd.joystick.get("angle", 0),
                cmd.joystick.get("magnitude", 0),
            )
        elif cmd.direction:
            robot.drive.move(Direction(cmd.direction), cmd.speed)

    await _run_robot(_drive)
    return {"ok": True}


@app.post("/api/stop")
async def stop():
    def _stop(robot: FNK0043) -> None:
        robot.set_drive_mode(DriveMode.MANUAL)
        robot.drive.stop()

    await _run_robot(_stop)
    return {"ok": True}


@app.post("/api/mode")
async def set_mode(cmd: ModeCommand):
    await _run_robot(lambda r: r.set_drive_mode(DriveMode(cmd.mode)))
    return {"ok": True, "mode": cmd.mode}


@app.post("/api/servo")
async def set_servo(cmd: ServoCommand):
    def _servo(robot: FNK0043) -> None:
        robot.set_drive_mode(DriveMode.MANUAL)
        if cmd.channel == "0":
            robot.pan_servo.set_angle(cmd.angle)
        elif cmd.channel == "1":
            robot.tilt_servo.set_angle(cmd.angle)
        else:
            robot.servos.set_angle(cmd.channel, cmd.angle)

    await _run_robot(_servo)
    return {"ok": True, "angle": cmd.angle, "channel": cmd.channel}


@app.post("/api/buzzer")
async def buzzer(cmd: BuzzerCommand):
    def _buzzer(robot: FNK0043) -> None:
        robot.buzzer.on() if cmd.on else robot.buzzer.off()

    await _run_robot(_buzzer)
    return {"ok": True}


@app.get("/stream")
async def video_stream():
    robot = await _get_robot()
    await asyncio.to_thread(robot.camera.start)

    async def generate():
        while True:
            frame = await asyncio.to_thread(robot.camera.get_frame, 1.0)
            if frame:
                yield (
                    b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
            await asyncio.sleep(0.03)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


def _handle_ws_action(robot: FNK0043, msg: dict) -> None:
    action = msg.get("action")

    if action == "drive":
        robot.set_drive_mode(DriveMode.MANUAL)
        if "raw" in msg:
            duties = msg["raw"]
            robot.drive.drive_raw(*duties)
        elif "direction" in msg:
            robot.drive.move(Direction(msg["direction"]), msg.get("speed", 0.6))
        elif "joystick" in msg:
            j = msg["joystick"]
            robot.drive.drive_joystick(j.get("angle", 0), j.get("magnitude", 0))

    elif action == "stop":
        robot.set_drive_mode(DriveMode.MANUAL)
        robot.drive.stop()

    elif action == "mode":
        robot.set_drive_mode(DriveMode(msg["mode"]))

    elif action == "servo":
        robot.set_drive_mode(DriveMode.MANUAL)
        channel = msg.get("channel", "0")
        angle = int(msg.get("angle", 90))
        if channel == "0":
            robot.pan_servo.set_angle(angle)
        elif channel == "1":
            robot.tilt_servo.set_angle(angle)
        else:
            robot.servos.set_angle(channel, angle)

    elif action == "buzzer":
        robot.buzzer.on() if msg.get("on") else robot.buzzer.off()


@app.websocket("/ws")
async def websocket_control(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            if action == "status":
                robot = await _get_robot()
                await websocket.send_json(await asyncio.to_thread(robot.status))
                continue

            await _run_robot(_handle_ws_action, msg)
            robot = await _get_robot()
            await websocket.send_json({"ok": True, **await asyncio.to_thread(robot.status)})

    except WebSocketDisconnect:
        if _robot is not None:
            await asyncio.to_thread(_robot.drive.stop)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "fnk0043.web.server:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    main()
