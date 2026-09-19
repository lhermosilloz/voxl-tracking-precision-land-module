#!/usr/bin/env python3
"""Merge the camera definitions in config/cameras/ into voxl-camera-server.conf.

Entries are matched on "name": a camera already present under that name is
replaced in place, a new name is appended. The target file is backed up first.

Usage: sudo ./scripts/apply-camera-config.py [--conf PATH] [--dry-run]
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMERA_DIR = os.path.join(REPO_DIR, "config", "cameras")
DEFAULT_CONF = "/etc/modalai/voxl-camera-server.conf"


def die(msg):
    print("error: %s" % msg, file=sys.stderr)
    sys.exit(1)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except ValueError as e:
        die("%s is not valid JSON (%s)" % (path, e))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conf", default=DEFAULT_CONF, help="target config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the merged result instead of writing it")
    args = parser.parse_args()

    if not os.path.isfile(args.conf):
        die("%s not found" % args.conf)
    if not args.dry_run and not os.access(args.conf, os.W_OK):
        die("%s is not writable (try: sudo %s)" % (args.conf, sys.argv[0]))

    conf = load_json(args.conf)
    if not isinstance(conf.get("cameras"), list):
        die('%s has no "cameras" array; refusing to modify it' % args.conf)

    entries = sorted(f for f in os.listdir(CAMERA_DIR) if f.endswith(".json"))
    if not entries:
        die("no camera definitions found in %s" % CAMERA_DIR)

    for filename in entries:
        camera = load_json(os.path.join(CAMERA_DIR, filename))
        name = camera.get("name")
        if not name:
            die("%s has no \"name\" field" % filename)

        for i, existing in enumerate(conf["cameras"]):
            if existing.get("name") == name:
                conf["cameras"][i] = camera
                print('replaced camera "%s" (from %s)' % (name, filename))
                break
        else:
            conf["cameras"].append(camera)
            print('added camera "%s" (from %s)' % (name, filename))

    text = json.dumps(conf, indent=4) + "\n"

    if args.dry_run:
        print()
        print(text, end="")
        return

    backup = "%s.bak.%s" % (args.conf, datetime.now().strftime("%Y%m%d-%H%M%S"))
    suffix = 0
    while os.path.exists(backup):
        suffix += 1
        backup = "%s.bak.%s-%d" % (
            args.conf, datetime.now().strftime("%Y%m%d-%H%M%S"), suffix)
    shutil.copy2(args.conf, backup)
    print("backed up %s -> %s" % (args.conf, backup))

    with open(args.conf, "w") as f:
        f.write(text)

    print("\ncameras now configured:")
    for camera in conf["cameras"]:
        print("  %-14s %-8s enabled=%s"
              % (camera.get("name"), camera.get("type"),
                 json.dumps(camera.get("enabled"))))
    print("\nRestart the camera server to pick up the changes:")
    print("  systemctl restart voxl-camera-server")


if __name__ == "__main__":
    main()
