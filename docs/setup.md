# Raspberry Pi setup

Guide for preparing a Raspberry Pi to run this project with the Freenove FNK0043 kit.

## Requirements

- Raspberry Pi 3B+ or newer (Pi 5 supported)
- Raspberry Pi OS (Bookworm recommended)
- Freenove 4WD Smart Car assembled per [Chapter 2](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/2_Assemble_Smart_Car.html)

## OS configuration

Run `sudo raspi-config` and enable:

| Interface | Why |
|-----------|-----|
| I2C | PCA9685 motor driver, ADS7830 ADC |
| SPI | WS2812 LED strip (Connect v2 boards) |
| Camera | Pi Camera module |

For Pi 5, configure the camera overlay in `/boot/firmware/config.txt`:

```
dtparam=spi=on
camera_auto_detect=0
dtoverlay=imx219,cam0
```

Replace `imx219` with your module (`ov5647` or `imx219`) and `cam0`/`cam1` with the port you use.

## Software install

Install Pi hardware libraries from apt (avoids pip build failures like `python-prctl` / `picamera2`):

```bash
sudo apt update
sudo apt install -y \
  python3-venv python3-full \
  python3-gpiozero python3-smbus python3-picamera2 python3-numpy \
  i2c-tools
```

Then create a venv that can see those system packages:

```bash
cd ~/robotic-projects
rm -rf .venv
python3 -m venv --copies --system-site-packages .venv
source .venv/bin/activate
pip install -e .
```

Do **not** use `pip install -e ".[pi]"` unless apt packages are unavailable — that path often fails compiling native deps.

Copy and edit hardware params (from Freenove Chapter 1):

```bash
cp params.json.example params.json
# Connect_Version: 1 or 2 (check expansion board silkscreen)
# Pcb_Version: 1 or 2
```

Reboot after first-time camera/SPI changes.

## Run the web controller

```bash
fnk0043-server
# or: python -m fnk0043.web.server
```

Default port: **8080**. The server binds to `0.0.0.0` so any device on your LAN can connect.

## Start on boot (systemd)

After the venv is set up and `fnk0043-server` works manually:

```bash
cd ~/robotic-projects
git pull
chmod +x scripts/install-service.sh scripts/uninstall-service.sh
./scripts/install-service.sh
```

This installs a **user** systemd service that:
- Starts `fnk0043-server` when the Pi boots
- Restarts on failure
- Runs as your login user (needed for GPIO/camera access)

Useful commands:

```bash
systemctl --user status fnk0043          # is it running?
journalctl --user -u fnk0043 -f          # live logs
systemctl --user restart fnk0043         # restart after git pull
./scripts/uninstall-service.sh           # remove autostart
```

If the service does not start at boot, enable linger (one-time):

```bash
sudo loginctl enable-linger $USER
```

### Manual systemd install (alternative)

If you prefer a system-wide service, edit paths and user in `deploy/fnk0043.service`, then:

```bash
sudo cp deploy/fnk0043.service /etc/systemd/system/fnk0043.service
# edit User=, WorkingDirectory=, ExecStart= paths for your account
sudo systemctl daemon-reload
sudo systemctl enable --now fnk0043
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No module named smbus` | `pip install smbus2` or `sudo apt install python3-smbus` |
| Motors don’t move | Check PCA9685 power jumper; verify I2C `0x40` with `i2cdetect -y 1` |
| Camera blank | Confirm overlay in config.txt; reboot |
| Permission errors on GPIO | Add user to `gpio` group or run with appropriate udev rules |

See also [hardware.md](hardware.md) and the [official module tests](https://docs.freenove.com/projects/fnk0043/en/fnk0043/codes/tutorial/3_Module_test.html).
