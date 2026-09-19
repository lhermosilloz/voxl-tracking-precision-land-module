# Camera configuration

Both cameras are defined in `/etc/modalai/voxl-camera-server.conf`, inside its
`cameras` array. This repo keeps each definition as its own file under
[`config/cameras/`](../config/cameras/):

| File | `name` | `camera_id` | Notes |
| --- | --- | --- | --- |
| `hires-imx412.json` | `hires` | 0 | Existing hires camera, H.264 small + large video |
| `tracking_leg-ar0144.json` | `tracking_leg` | 1 | The AR0144 tracking camera |

## Applying them

`scripts/apply-camera-config.py` merges both files into the config, matching on
`name`: an entry already present under that name is replaced, a new name is
appended. Everything else in the file is left alone, and the original is backed
up to `voxl-camera-server.conf.bak.<timestamp>` first.

```bash
sudo ./scripts/apply-camera-config.py --dry-run   # print the result, change nothing
sudo ./scripts/apply-camera-config.py             # write it
sudo systemctl restart voxl-camera-server
```

Point it at a different file with `--conf PATH`.

To apply the entries by hand instead, paste the contents of each file into the
`cameras` array of `/etc/modalai/voxl-camera-server.conf`.

## What matters in the tracking camera entry

The `tracking_leg` entry is what produces the stream the precision-landing
stack consumes:

- **`en_misp` / `misp_*`** - the MISP path produces the encoded output at
  1280x800. `misp_venc_enable: true` is what creates the
  `tracking_leg_misp_encoded` pipe used for streaming.
- **`misp_venc_mode: "h265"`** with `cbr` rate control at `1.2` Mbps - keeps the
  stream light enough to share the link with the hires camera.
- **`en_rotate: true`** - the camera is mounted rotated on the leg.
- **`ae_mode: "lme_msv"`** with `ae_desired_msv: 60` - auto-exposure targeting a
  mean sample value, rather than the ISP's own AE.
- **`exposure_max_us: 12000`** - caps exposure to limit motion blur while
  tracking; `exposure_soft_min_us: 5000` keeps it from bottoming out and
  raising gain unnecessarily in normal light.

Raising `misp_venc_mbps` improves image quality at the cost of link bandwidth.
Lowering `exposure_max_us` reduces motion blur but forces higher gain (noisier
image) in low light.

After any change: `sudo systemctl restart voxl-camera-server`.
