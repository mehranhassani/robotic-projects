# FNK0043 Robotic Projects

A clean Python foundation and web control panel for the [Freenove FNK0043 4WD Smart Car Kit](https://docs.freenove.com/projects/fnk0043/en/latest/) (Raspberry Pi).

This repo replaces Freenove’s scattered tutorial scripts with typed wrappers, a unified `FNK0043` robot class, in-repo documentation, and a browser-based controller you can open from any device on your network.

## Features

- **Semantic motor API** — `forward()`, `stop()`, joystick drive, and raw PWM when you need it
- **Sensor wrappers** — ultrasonic, line IR, photoresistors, battery
- **Autonomous modes** — light follow, line follow, ultrasonic avoidance (from official tutorials)
- **Mock hardware** — develop on your Mac/PC without a Pi (`FNK0043_MOCK=1`)
- **Web control** — FastAPI + WebSocket UI with live camera stream and sensor readouts

## Quick start

### On your dev machine (mock mode)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

export FNK0043_MOCK=1
fnk0043-server
```

Open [http://localhost:8080](http://localhost:8080).

### On the Raspberry Pi

1. Flash Raspberry Pi OS and enable I2C, SPI, and camera (see [docs/setup.md](docs/setup.md)).
2. Install hardware libs from apt, then this package into a venv:

```bash
sudo apt install -y python3-gpiozero python3-smbus python3-picamera2 python3-numpy
python3 -m venv --copies --system-site-packages .venv
source .venv/bin/activate
pip install -e .
cp params.json.example params.json
fnk0043-server
```

Browse to `http://<pi-ip>:8080` from your phone or laptop.

## Project layout

```
fnk0043/           Python package — wrappers, HAL, web server
  hal/             Real Pi hardware + mock backend
  motors/          4WD drive system
  sensors/         Ultrasonic, IR line, light, battery
  actuators/       Servo, buzzer, LED strip
  behaviors/       Autonomous driving modes
  web/             FastAPI server + static UI
docs/              Setup guides, hardware reference, API docs
```

## Python API

```python
from fnk0043 import FNK0043, DriveMode
from fnk0043.motors.drive import Direction

with FNK0043() as robot:
    robot.drive.move(Direction.FORWARD, speed=0.5)
    print(robot.sensors())
    robot.set_drive_mode(DriveMode.LINE_FOLLOW)
    while True:
        robot.update()
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/setup.md](docs/setup.md) | Pi OS prep, wiring, first boot |
| [docs/hardware.md](docs/hardware.md) | Pins, I2C addresses, modules |
| [docs/api.md](docs/api.md) | REST/WebSocket API for the webapp |
| [docs/freenove.md](docs/freenove.md) | Links to official Freenove tutorials |

## Official resources

- [FNK0043 documentation](https://docs.freenove.com/projects/fnk0043/en/latest/)
- [Freenove GitHub (reference code)](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi)
- [Amazon product listing](https://www.amazon.ca/Freenove-Raspberry-Tracking-Avoidance-Ultrasonic/dp/B07YD2LT9D)

## License

MIT — Freenove hardware docs and reference code remain © Freenove.
