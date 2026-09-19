# voxl-tracking-precision-land-module

Targetting this camera for VOXL based platforms (Show ar0144_image_sensor.png)

Plug in the camera according to the image. (Show D0014-M0173.jpg)

Edit /etc/modalai/voxl-camera-server.conf:

{
                        "type": "imx412",
                        "name": "hires",
                        "enabled":      true,
                        "camera_id":    0,
                        "fps":  30,
                        "en_rotate":    false,
                        "en_preview":   false,
                        "preview_width":        640,
                        "preview_height":       480,
                        "en_raw_preview":       false,
                        "en_small_video":       true,
                        "small_video_width":    1280,
                        "small_video_height":   720,
                        "small_venc_mode":      "h264",
                        "small_venc_br_ctrl":   "cqp",
                        "small_venc_Qfixed":    30,
                        "small_venc_Qmin":      15,
                        "small_venc_Qmax":      40,
                        "small_venc_nPframes":  9,
                        "small_venc_mbps":      2,
                        "en_large_video":       true,
                        "large_video_width":    1920,
                        "large_video_height":   1080,
                        "large_venc_mode":      "h264",
                        "large_venc_br_ctrl":   "cqp",
                        "large_venc_Qfixed":    40,
                        "large_venc_Qmin":      15,
                        "large_venc_Qmax":      50,
                        "large_venc_nPframes":  29,
                        "large_venc_mbps":      40,
                        "en_snapshot":  true,
                        "en_snapshot_width":    1920,
                        "en_snapshot_height":   1080,
                        "exif_focal_length":    3.1,
                        "exif_focal_length_in_35mm_format":     17,
                        "exif_fnumber": 1.24,
                        "snapshot_jpeg_quality":        75,
                        "ae_mode":      "isp",
                        "gain_min":     54,
                        "gain_max":     8000
                }

{
                        "type": "ar0144",
                        "name": "tracking_leg",
                        "enabled":      true,
                        "camera_id":    1,
                        "fps":  30,
                        "en_rotate":    true,
                        "en_preview":   true,
                        "preview_width":        1280,
                        "preview_height":       800,
                        "en_raw_preview":       true,
                        "en_misp":      true,
                        "misp_width":   1280,
                        "misp_height":  800,
                        "misp_venc_enable":     true,
                        "misp_venc_mode":       "h265",
                        "misp_venc_br_ctrl":    "cbr",
                        "misp_venc_Qfixed":     38,
                        "misp_venc_Qmin":       15,
                        "misp_venc_Qmax":       50,
                        "misp_venc_nPframes":   9,
                        "misp_venc_mbps":       1.2,
                        "misp_awb":     "auto",
                        "misp_gamma":   1,
                        "misp_zoom":    1,
                        "ae_mode":      "lme_msv",
                        "gain_min":     54,
                        "gain_max":     8000,
                        "ae_desired_msv":       60,
                        "exposure_min_us":      20,
                        "exposure_max_us":      12000,
                        "exposure_soft_min_us": 5000,
                        "ae_filter_alpha":      0.6,
                        "ae_ignore_fraction":   0.2,
                        "ae_slope":     0.05,
                        "ae_exposure_period":   1,
                        "ae_gain_period":       1
                }

Test with:
voxl-streamer --standalone --port 8901 -i tracking_leg_misp_encoded

Once works:
sudo nano /etc/systemd/system/voxl-streamer-tracking.service

Content in service:
[Unit]
Description=VOXL Streamer - Tracking Camera
After=voxl-camera-server.service
Wants=voxl-camera-server.service

[Service]
Type=simple
ExecStart=/usr/bin/voxl-streamer --standalone --port 8901 -i tracking_leg_misp_encoded
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target

Then:
sudo systemctl daemon-reload
sudo systemctl enable voxl-streamer-tracking
sudo systemctl start voxl-streamer-tracking

systemctl status voxl-streamer-tracking