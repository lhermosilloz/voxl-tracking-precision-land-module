# Camera definitions

Each file here is one entry from the `cameras` array in
`/etc/modalai/voxl-camera-server.conf`, kept separately so it can be diffed and
version-controlled.

Apply them with:

```bash
sudo ../../scripts/apply-camera-config.py
```

Entries are matched on the `name` field. See
[docs/camera-configuration.md](../../docs/camera-configuration.md) for details.
