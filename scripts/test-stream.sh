#!/bin/bash
# Run voxl-streamer in the foreground to verify the tracking pipeline before
# installing it as a service. Ctrl-C to stop.
#
# Usage: ./scripts/test-stream.sh [port] [pipeline]

set -euo pipefail

PORT="${1:-8901}"
PIPELINE="${2:-tracking_down_misp_encoded}"

if [ ! -e "/run/mpa/$PIPELINE" ]; then
    echo "warning: pipe /run/mpa/$PIPELINE does not exist yet." >&2
    echo "         Check 'voxl-list-pipes' and that voxl-camera-server is running." >&2
fi

echo "streaming $PIPELINE on rtsp://<voxl-ip>:$PORT/live"
exec voxl-streamer --standalone --port "$PORT" -i "$PIPELINE"
