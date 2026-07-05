# Web API

The control server runs on port **8080** by default.

## REST endpoints

### `GET /api/status`

Robot state snapshot.

```json
{
  "mock": false,
  "chassis": "standard",
  "drive_mode": "manual",
  "battery_v": 7.8,
  "distance_cm": 42.5,
  "light": { "left": 2.1, "right": 2.3 },
  "line": { "left": 0, "center": 1, "right": 0 }
}
```

### `GET /api/sensors`

Raw sensor readings (same fields, flat structure).

### `POST /api/drive`

Manual drive command. Stops autonomous mode.

```json
{ "direction": "forward", "speed": 0.6 }
```

```json
{ "raw": [600, 600, 600, 600] }
```

```json
{ "joystick": { "angle": 0, "magnitude": 0.8 } }
```

Directions: `forward`, `backward`, `left`, `right`, `stop`.

### `POST /api/stop`

Stop all motors.

### `POST /api/mode`

Set autonomous mode: `manual`, `light_follow`, `line_follow`, `obstacle_avoid`.

### `POST /api/servo`

```json
{ "channel": "0", "angle": 90 }
```

### `POST /api/buzzer`

```json
{ "on": true }
```

### `GET /stream`

MJPEG camera stream (`multipart/x-mixed-replace`).

## WebSocket `/ws`

Send JSON messages; server replies with `{ "ok": true, ...status }`.

| action | fields |
|--------|--------|
| `drive` | `direction` + `speed`, or `raw` [fl,bl,fr,br], or `joystick` |
| `stop` | — |
| `mode` | `mode` |
| `servo` | `channel`, `angle` |
| `buzzer` | `on` |
| `status` | request update only |

Example:

```javascript
ws.send(JSON.stringify({ action: "drive", direction: "forward", speed: 0.5 }));
ws.send(JSON.stringify({ action: "mode", mode: "line_follow" }));
```

## Python package API

See `fnk0043.robot.FNK0043` — the web server is a thin layer over the same class.

```python
robot.drive.move(Direction.FORWARD, 0.6)
robot.set_drive_mode(DriveMode.OBSTACLE_AVOID)
robot.update()  # call in loop for autonomous modes
robot.sensors() # SensorSnapshot dataclass
```
