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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _robot, _autonomy_task
    _robot = FNK0043()
    _autonomy_task = asyncio.create_task(_autonomy_loop())
    yield
    if _autonomy_task:
        _autonomy_task.cancel()
        try:
            await _autonomy_task
        except asyncio.CancelledError:
            pass
    if _robot:
        _robot.close()


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
            _robot.update()
        await asyncio.sleep(0.05)


def _require_robot() -> FNK0043:
    if _robot is None:
        raise RuntimeError("Robot not initialized")
    return _robot


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


@app.get("/api/status")
async def status():
    return _require_robot().status()


@app.get("/api/sensors")
async def sensors():
    snap = _require_robot().sensors()
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
    robot = _require_robot()
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
    return {"ok": True}


@app.post("/api/stop")
async def stop():
    robot = _require_robot()
    robot.set_drive_mode(DriveMode.MANUAL)
    robot.drive.stop()
    return {"ok": True}


@app.post("/api/mode")
async def set_mode(cmd: ModeCommand):
    robot = _require_robot()
    robot.set_drive_mode(DriveMode(cmd.mode))
    return {"ok": True, "mode": cmd.mode}


@app.post("/api/servo")
async def set_servo(cmd: ServoCommand):
    robot = _require_robot()
    robot.set_drive_mode(DriveMode.MANUAL)
    if cmd.channel == "0":
        robot.pan_servo.set_angle(cmd.angle)
    else:
        robot.servos.set_angle(cmd.channel, cmd.angle)
    return {"ok": True, "angle": cmd.angle}


@app.post("/api/buzzer")
async def buzzer(cmd: BuzzerCommand):
    b = _require_robot().buzzer
    b.on() if cmd.on else b.off()
    return {"ok": True}


@app.get("/stream")
async def video_stream():
    robot = _require_robot()
    robot.camera.start()

    async def generate():
        while True:
            frame = robot.camera.get_frame(timeout=1.0)
            if frame:
                yield (
                    b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
            await asyncio.sleep(0.03)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/ws")
async def websocket_control(websocket: WebSocket):
    await websocket.accept()
    robot = _require_robot()
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            if action == "drive":
                robot.set_drive_mode(DriveMode.MANUAL)
                if "raw" in msg:
                    duties = msg["raw"]
                    robot.drive.drive_raw(*duties)
                elif "direction" in msg:
                    robot.drive.move(
                        Direction(msg["direction"]),
                        msg.get("speed", 0.6),
                    )
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
                else:
                    robot.servos.set_angle(channel, angle)

            elif action == "buzzer":
                robot.buzzer.on() if msg.get("on") else robot.buzzer.off()

            elif action == "status":
                await websocket.send_json(robot.status())
                continue

            await websocket.send_json({"ok": True, **robot.status()})

    except WebSocketDisconnect:
        robot.drive.stop()


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
