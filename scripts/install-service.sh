#!/bin/bash
# Install and start the voxl-streamer-tracking systemd service.
#
# Usage: sudo ./scripts/install-service.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT="voxl-streamer-tracking.service"
SRC="$REPO_DIR/systemd/$UNIT"
DEST="/etc/systemd/system/$UNIT"

if [ "$(id -u)" -ne 0 ]; then
    echo "error: must be run as root (try: sudo $0)" >&2
    exit 1
fi

if [ ! -f "$SRC" ]; then
    echo "error: $SRC not found" >&2
    exit 1
fi

if [ -f "$DEST" ] && ! cmp -s "$SRC" "$DEST"; then
    cp -a "$DEST" "$DEST.bak.$(date +%Y%m%d-%H%M%S)"
    echo "backed up existing unit file"
fi

install -m 0644 "$SRC" "$DEST"
echo "installed $DEST"

systemctl daemon-reload
systemctl enable "$UNIT"
systemctl restart "$UNIT"

sleep 1
systemctl status "$UNIT" --no-pager
