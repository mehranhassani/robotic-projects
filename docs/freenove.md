# Freenove official documentation

This repo is built for the **FNK0043** kit. The guides below are the manufacturer tutorials — we keep copies of setup-critical info in [setup.md](setup.md) and [hardware.md](hardware.md), but the full walkthrough with photos lives on Freenove’s site.

## Product

- **Model:** FNK0043 — Freenove 4WD Smart Car Kit for Raspberry Pi
- **Docs home:** [docs.freenove.com/projects/fnk0043](https://docs.freenove.com/projects/fnk0043/en/latest/)
- **Code download:** [GitHub ZIP](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/archive/refs/heads/master.zip)
- **Support:** support@freenove.com

## Tutorial chapters (standard 4WD — fnk0043A)

| Chapter | Topic | Link |
|---------|-------|------|
| 0 | Raspberry Pi preparation | [Preparation](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/Preparation.html) |
| 1 | Software installation | [Software](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/1_Software_installation.html) |
| 2 | Assembly | [Assemble](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/2_Assemble_Smart_Car.html) |
| 3 | Module test | [Module test](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/3_Module_test.html) |
| 4 | Light tracing | [Light car](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/4_Light_tracing_Car.html) |
| 5 | Ultrasonic avoidance | [Ultrasonic](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/5_Ultrasonic_Car.html) |
| 6 | Line tracking | [Infrared](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/6_Infrared_Car.html) |
| 7 | Smart video car | [Video car](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/7_Smart_video_car.html) |

## Mecanum variant (fnk0043B)

Same chapters under the [Mecanum section](https://docs.freenove.com/projects/fnk0043/en/latest/) — set `FNK0043_CHASSIS=mecanum` in this project.

## How this repo relates to Freenove code

| Freenove original | This repo |
|-------------------|-----------|
| `Code/Server/*.py` flat modules | `fnk0043/` package with HAL + typed API |
| PyQt5 desktop server + TCP client | FastAPI web UI + WebSocket |
| String commands (`CMD_MOTOR#…`) | JSON REST/WS + Python methods |
| `params.json` interactive setup | Same file format, documented in [hardware.md](hardware.md) |

Autonomous logic in `fnk0043/behaviors/` is ported from Freenove’s `car.py` tutorial modes.

## Reference repository

Upstream sample code (not vendored — install separately if needed for LED drivers):

https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi

For SPI LED support on Connect v2 boards, copy `spi_ledpixel.py` from that repo into `fnk0043/vendor/` on the Pi.
