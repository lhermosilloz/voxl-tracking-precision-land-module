# Troubleshooting

## The `tracking_down_misp_encoded` pipe doesn't exist

```bash
voxl-list-pipes
```

If `tracking_down_misp_encoded` is missing:

- Is the camera server running? `systemctl status voxl-camera-server`
- Is the entry applied and enabled? Check that `tracking_down` appears in
  `/etc/modalai/voxl-camera-server.conf` with `"enabled": true`.
- Is `misp_venc_enable` still `true`? Without it the MISP path produces frames
  but no encoded pipe.
- Check the camera server's own log: `journalctl -u voxl-camera-server -n 100`.

## The camera server fails to start after applying the config

Most likely a bad merge or a `camera_id` collision. Roll back to the backup the
script wrote:

```bash
ls /etc/modalai/voxl-camera-server.conf.bak.*
sudo cp /etc/modalai/voxl-camera-server.conf.bak.<timestamp> /etc/modalai/voxl-camera-server.conf
sudo systemctl restart voxl-camera-server
```

Then re-run with `--dry-run` to inspect what the merge would produce.

## `apply-camera-config.py` refuses to run

- *"is not valid JSON"* - the existing config has a syntax error (or comments,
  which aren't valid JSON). Fix or restore it first.
- *"has no `cameras` array"* - you're pointing at the wrong file. The default is
  `/etc/modalai/voxl-camera-server.conf`; override with `--conf PATH`.
- *"is not writable"* - run it with `sudo`.

## The service starts but no video

- Test in the foreground first (`./scripts/test-stream.sh`) - the error is
  usually visible there and swallowed by the service otherwise.
- Check that nothing else is already bound to port 8901.
- `journalctl -u voxl-streamer-tracking -f` while reconnecting the client.

## The service restarts in a loop

Usually the streamer starting before the camera pipe exists. The unit is
configured to retry every 2 seconds, so it should settle once
`voxl-camera-server` is up. If it never settles, the pipe name is wrong - verify
it against `voxl-list-pipes`.

## Image is dark, noisy or blurry

See the auto-exposure notes in
[camera-configuration.md](camera-configuration.md#what-matters-in-the-tracking-camera-entry).
Briefly: raise `ae_desired_msv` for a brighter image, lower `exposure_max_us` to
cut motion blur (at the cost of more gain/noise), and raise `misp_venc_mbps` if
the image is blocky rather than noisy.
