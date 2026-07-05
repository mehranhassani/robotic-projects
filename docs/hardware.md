# Hardware reference

Pin map and I2C devices for the FNK0043 standard 4WD kit (fnk0043A).

## I2C devices

| Address | Chip | Function |
|---------|------|----------|
| `0x40` | PCA9685 | 16-channel PWM — motors + servos |
| `0x48` | ADS7830 | 8-bit ADC — photoresistors + battery |

Scan bus: `i2cdetect -y 1`

## GPIO (BCM numbering)

| Pin | Module |
|-----|--------|
| 27 | Ultrasonic trigger |
| 22 | Ultrasonic echo |
| 17 | Buzzer |
| 14 | IR line sensor 1 (left) |
| 15 | IR line sensor 2 (center) |
| 23 | IR line sensor 3 (right) |

## PCA9685 motor channels

| Motor | Forward | Reverse |
|-------|---------|---------|
| Front-left | 0 | 1 |
| Rear-left | 3 | 2 |
| Front-right | 6 | 7 |
| Rear-right | 4 | 5 |

PWM duty range: **−4095 to 4095** (Freenove convention).

## Servo channels (logical → PCA9685)

| Logical | Channel | Default use |
|---------|---------|-------------|
| `0` | 8 | Ultrasonic pan |
| `1`–`7` | 9–15 | Spare |

Pan range: 30° (left) – 150° (right), center 90°.

## ADC channels

| Channel | Sensor |
|---------|--------|
| 0 | Left photoresistor |
| 1 | Right photoresistor |
| 2 | Battery voltage divider |

Battery voltage = `ADC reading × multiplier` where multiplier is **3×** (PCB v1) or **2×** (PCB v2).

## params.json

Created during Freenove setup; this project reads the same file:

```json
{
    "Connect_Version": 2,
    "Pcb_Version": 1,
    "Pi_Version": 1
}
```

| Field | Values | Meaning |
|-------|--------|---------|
| Connect_Version | 1, 2 | Expansion board revision |
| Pcb_Version | 1, 2 | Motor driver PCB |
| Pi_Version | 1, 2 | Pi &lt; 5 vs Pi 5 |
| Invert_Drive | true/false | Flip all motor directions if forward/back are swapped |

## Chassis variants

Set `FNK0043_CHASSIS=mecanum` for the fnk0043B Mecanum kit. Default is `standard` (ordinary 4WD).

## Modules included in kit

- 4× gear motors + encoder-capable driver board
- HC-SR04 ultrasonic + pan servo
- 3× IR line tracking sensors
- 2× photoresistors (light tracking)
- Active buzzer
- 8× WS2812 RGB LEDs
- Raspberry Pi camera (ov5647 or imx219)

Official wiring diagrams: [Freenove docs](https://docs.freenove.com/projects/fnk0043/en/latest/).
