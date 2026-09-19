# Running DepthAnythingV2 on VOXL

The steps taken to run [DepthAnythingV2](https://github.com/DepthAnything/Depth-Anything-V2)
on this platform, via `voxl-tflite-server`.

The model runs alongside the existing TFLite server config rather than
replacing it: the depth model gets its own config file, so the stock one is
left intact.

## 1. Check the existing config

Start from what's already there:

```bash
cat /etc/modalai/voxl-tflite-server.conf
```

## 2. Set up a Python environment

```bash
python3 -m venv ~/depthanything_env
source ~/depthanything_env/bin/activate

pip install qai-hub-models-cli
```

## 3. Fetch the model

Inspect what's available for the model first:

```bash
qai-hub-models info Depth-Anything-V2
```

Then fetch the TFLite float build:

```bash
qai-hub-models fetch Depth-Anything-V2 \
    --runtime tflite \
    --precision float
```

## 4. Install the model on the board

Models live in `/usr/bin/dnn/`. Copy the fetched `.tflite` there under the name
the config expects:

```bash
sudo cp <fetched-model>.tflite /usr/bin/dnn/depth_anything_v2.tflite
```

Verify it landed:

```bash
ls /usr/bin/dnn/
```

## 5. Create a depth-specific config

Copy the stock config rather than editing it:

```bash
cp /etc/modalai/voxl-tflite-server.conf \
   /etc/modalai/voxl-tflite-server-depth.conf
```

Populate it with:

```json
{
    "skip_n_frames": 4,
    "model": "/usr/bin/dnn/depth_anything_v2.tflite",
    "input_pipe": "/run/mpa/hires_small_color/",
    "delegate": "gpu",
    "model_architecture": "FAST_DEPTH",
    "norm_type": "HARD_DIVISION",
    "score_threshold": 0.25,
    "confidence_threshold": 0.25,
    "nms_threshold": 0.45,
    "requires_labels": false,
    "labels": "",
    "allow_multiple": true,
    "output_pipe_prefix": "depth"
}
```

Notes on the settings that matter here:

- **`model`** must match the filename used in step 4.
- **`input_pipe`** is the hires camera's small colour stream, so the hires
  camera has to be enabled in `voxl-camera-server.conf` - see
  [docs/camera-configuration.md](docs/camera-configuration.md).
- **`delegate: "gpu"`** runs inference on the GPU.
- **`skip_n_frames: 4`** processes every 5th frame; raise it if inference can't
  keep up with the camera.
- **`output_pipe_prefix: "depth"`** determines the output pipe names, visible
  in `voxl-list-pipes`.

## 6. Run it

```bash
voxl-tflite-server -d -t -p /etc/modalai/voxl-tflite-server-depth.conf
```
