# Streaming

The tracking camera is streamed over RTSP by `voxl-streamer`, reading the
`tracking_leg_misp_encoded` pipe.

## Test it first

Before installing anything, confirm the pipeline works in the foreground:

```bash
./scripts/test-stream.sh
```

which runs:

```bash
voxl-streamer --standalone --port 8901 -i tracking_leg_misp_encoded
```

Pass a different port or pipe as arguments: `./scripts/test-stream.sh 8902 some_pipe`.

Open `rtsp://<voxl-ip>:8901/live` in VLC (or `ffplay`) to check the image.
Ctrl-C to stop.

## Install as a service

Once the stream works, install it so it comes up on boot:

```bash
sudo ./scripts/install-service.sh
```

This installs [`systemd/voxl-streamer-tracking.service`](../systemd/voxl-streamer-tracking.service)
to `/etc/systemd/system/`, reloads systemd, enables the unit and starts it,
then prints the status. An existing unit file is backed up before being
replaced.

The unit is ordered `After=voxl-camera-server.service` and restarts on failure
every 2 seconds, so it recovers if it starts before the camera server is ready.

## Managing it

```bash
systemctl status voxl-streamer-tracking
systemctl restart voxl-streamer-tracking
journalctl -u voxl-streamer-tracking -f
```

To change the port or pipe, edit `systemd/voxl-streamer-tracking.service` and
re-run `sudo ./scripts/install-service.sh`.

To remove it entirely:

```bash
sudo ./scripts/uninstall-service.sh
```
