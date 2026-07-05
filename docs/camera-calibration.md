# Camera pan/tilt — hardware recenter

Use this when the camera head is loose, horns were removed, or Center/Level in the web UI never look straight.

Based on [Freenove Chapter 2 — Pan Tilt](https://docs.freenove.com/projects/fnk0043/en/latest/fnk0043/codes/tutorial/2_Assemble_Smart_Car.html).

## Before you start

- Car powered (battery + Pi on)
- **Stop the web server** so it does not fight for the motor driver:
  ```bash
  systemctl --user stop fnk0043
  ```
- Know which servo is which:
  - **Servo0** — pan (left/right)
  - **Servo1** — tilt (up/down)

## Run the centering program

On the Pi:

```bash
cd ~/robotic-projects
source .venv/bin/activate
fnk0043-center-servos
```

Both servos move to **90°** and stay there until you press **Ctrl+C**.

## Physical steps (while program is running)

1. **Remove old horns** if they are misaligned (note which arm type you used).
2. **Pan (Servo0):** mount the horn/bracket so the ultrasonic/camera assembly points **straight forward**.
3. **Tilt (Servo1):** mount so the camera is **level** (not pointing up or down).
4. **Tighten** the small **M2 horn screw** on each servo spline.
5. **Tighten** the pan servo to the bracket: **M2×10 screw + M2 nut** (hold nut with screwdriver from below).
6. Check nothing binds when you gently move the head by hand (power off first if you need to test freely).
7. Press **Ctrl+C** in the terminal to exit the program.

## After recenter

```bash
systemctl --user start fnk0043
```

Open the web UI → **Camera** → **Center** and **Level**. Use the fine sliders if it is still slightly off (mechanical center is not always exactly 90° in software).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Servos don't move | Battery on? `i2cdetect -y 1` shows `0x40`? Server stopped? |
| Wrong axis moves | Servo0/Servo1 plugs swapped on board — fix wiring |
| Still crooked after recenter | Note slider values that look correct; ask to add `Pan_Center` / `Tilt_Center` to `params.json` |
| Horn slips on spline | Tighten M2 screw; horn fully pressed onto splines before tightening |

## Freenove original command (alternative)

If you still have their repo:

```bash
cd ~/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server
sudo python3 servo.py
```

Same idea — keeps servos at 90° while you install the hardware.
