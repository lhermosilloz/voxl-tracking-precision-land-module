#!/bin/bash
# Stop, disable and remove the voxl-streamer-tracking systemd service.
#
# Usage: sudo ./scripts/uninstall-service.sh

set -euo pipefail

UNIT="voxl-streamer-tracking.service"
DEST="/etc/systemd/system/$UNIT"

if [ "$(id -u)" -ne 0 ]; then
    echo "error: must be run as root (try: sudo $0)" >&2
    exit 1
fi

systemctl stop "$UNIT" 2>/dev/null || true
systemctl disable "$UNIT" 2>/dev/null || true
rm -f "$DEST"
systemctl daemon-reload

echo "removed $UNIT"
