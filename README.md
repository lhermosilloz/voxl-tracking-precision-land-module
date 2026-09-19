# voxl-tracking-precision-land-module

Bring-up notes, camera configuration and service files for running an **AR0144
tracking camera** on a VOXL-based platform and exposing it as an RTSP stream.

The camera is mounted on the landing leg (`tracking_leg`) and streams a
downward view over RTSP, which the precision-landing stack consumes as its
video source.

## Hardware

The sensor is an **AR0144**, connected with the **D0014-M0173** flex cable to
the VOXL camera port used for `camera_id: 1`.

<img src="docs/images/ar0144-image-sensor.png" alt="AR0144 image sensor" width="216">

*AR0144 image sensor*

<img src="docs/images/d0014-m0173-wiring.jpg" alt="D0014-M0173 wiring" width="640">

*Plug the camera in as shown - D0014-M0173*

Wire it up before doing anything else - see [docs/hardware.md](docs/hardware.md)
for cable orientation and how to verify the board sees the camera.

## What's here

| Path | Purpose |
| --- | --- |
| [config/cameras/](config/cameras/) | Camera definitions to merge into `voxl-camera-server.conf` |
| [systemd/](systemd/) | `voxl-streamer-tracking.service` unit file |
| [scripts/](scripts/) | Apply the config, test the stream, install the service |
| [docs/](docs/) | Step-by-step guides |

## Quick start

Run these **on the VOXL**, from a clone of this repo.

```bash
# 1. Wire the camera up first - see docs/hardware.md

# 2. Merge the camera definitions into /etc/modalai/voxl-camera-server.conf
sudo ./scripts/apply-camera-config.py --dry-run   # preview
sudo ./scripts/apply-camera-config.py
sudo systemctl restart voxl-camera-server

# 3. Verify the stream works before making it permanent (Ctrl-C to stop)
./scripts/test-stream.sh

# 4. Install it as a service that starts on boot
sudo ./scripts/install-service.sh
```

The stream is then available at `rtsp://<voxl-ip>:8901/live`.

## Guides

- [Hardware setup](docs/hardware.md) - which sensor, how it connects
- [Camera configuration](docs/camera-configuration.md) - what the config
  entries do and how to apply them
- [Streaming](docs/streaming.md) - testing the stream and installing the service
- [Troubleshooting](docs/troubleshooting.md) - common failures

## Requirements

- A VOXL / VOXL 2 board running `voxl-camera-server` and `voxl-streamer`
- An AR0144 sensor module (D0014-M0173 flex cable)
- Python 3 on the VOXL (for `scripts/apply-camera-config.py`)
- Root access on the board
