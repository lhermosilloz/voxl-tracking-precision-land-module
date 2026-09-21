#!/usr/bin/env python3
"""
tag_mount_check.py -- bench validator for the VOXL precision-landing mount transform.

Runs the SAME arithmetic as Nexus VoxlTagDetectorSource::handleBatch, against live
tag_detections packets, so the mount constants can be confirmed on a bench instead of
in the air.

It validates the BODY-RELATIVE half of the chain -- which is the whole platform-specific
part. The remaining "+ vehicle yaw" term just rotates body into NED and is identical on
every platform, so if the body-relative numbers are right, the NED ones are too.

  ./tag_mount_check.py --selftest              # no pipe needed; checks the algebra
  ./tag_mount_check.py                         # live, Starling defaults (yaw 180)
  ./tag_mount_check.py --cam-yaw 135 --off 0.15 -0.15 0.05
"""
import argparse, ctypes as ct, math, os, select, struct, sys

TAG_FMT = "<Iifq64si3f9f3f9f64si"
TAG_SIZE = struct.calcsize(TAG_FMT)          # 252
MAGIC = 0x564F584C
I_T, I_R, I_CAM = 6, 9, 30                   # field indices in the unpacked tuple


# ---------------------------------------------------------------- the math under test
def spin_deg(R, sign=-1.0):
    """Marker in-plane rotation, degrees. Mirrors atan2(R_tag_to_cam[3], [0]).

    sign=-1 (default, and what Nexus now does on VOXL): apriltag_pose.c left-multiplies the
    published pose by diag(1,-1,-1), which negates row 1 and hence this angle. Without the
    flip the heading runs backwards -- turn the pad left, the reading goes right.
    sign=+1 reproduces the OpenCV solvePnP convention used by the SITL ArUco source.
    """
    return sign * math.degrees(math.atan2(R[3], R[0]))


def optical_to_body(t_cam, cam_yaw_deg, offset):
    """Mirrors the tb[] block. cam_yaw 180 == legacy [-tx,-ty,tz]; 90 == SITL [-ty,tx,tz]."""
    c = math.cos(math.radians(cam_yaw_deg))
    s = math.sin(math.radians(cam_yaw_deg))
    tx, ty, tz = t_cam
    return (offset[0] + (c * tx - s * ty),
            offset[1] + (s * tx + c * ty),
            offset[2] + tz)


def heading_wrt_nose(R, cam_yaw_deg, front_off_deg, sign=-1.0):
    """Pad heading relative to the airframe nose. Adding vehicle yaw gives world NED."""
    return wrap180(spin_deg(R, sign) + cam_yaw_deg + front_off_deg)


def wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------- self test
def selftest():
    ok = True
    tx, ty, tz = 0.3, 0.7, 2.0
    z = (0.0, 0.0, 0.0)

    def check(name, got, want, tol=1e-9):
        nonlocal ok
        good = all(abs(a - b) < tol for a, b in zip(got, want))
        ok &= good
        print("  %-52s %s" % (name, "PASS" if good else "FAIL  got=%s want=%s" % (got, want)))

    print("Rz(cam_yaw) must reproduce the hardcoded permutations it replaced:")
    check("cam_yaw=180  ==  Starling  [-tx, -ty, tz]",
          optical_to_body((tx, ty, tz), 180.0, z), (-tx, -ty, tz))
    check("cam_yaw=90   ==  SITL      [-ty,  tx, tz]",
          optical_to_body((tx, ty, tz), 90.0, z), (-ty, tx, tz))
    check("cam_yaw=0    ==  identity",
          optical_to_body((tx, ty, tz), 0.0, z), (tx, ty, tz))

    print("\nLever arm adds in body frame, never rotates the measurement:")
    check("offset applied after rotation",
          optical_to_body((tx, ty, tz), 180.0, (0.15, -0.15, 0.05)),
          (0.15 - tx, -0.15 - ty, 0.05 + tz))

    print("\nMarker spin, OpenCV/ArUco convention (sign=+1):")
    for deg in (0.0, 30.0, 90.0, -45.0, 179.0):
        th = math.radians(deg)
        R = [math.cos(th), -math.sin(th), 0.0,
             math.sin(th), math.cos(th), 0.0,
             0.0, 0.0, 1.0]
        check("marker rotated %+7.1f deg" % deg, (spin_deg(R, 1.0),), (deg,), 1e-6)

    print("\nAprilTag's diag(1,-1,-1) pose fix negates that angle (sign=-1 undoes it):")
    th = math.radians(30.0)
    R_cv = [math.cos(th), -math.sin(th), 0.0, math.sin(th), math.cos(th), 0.0, 0.0, 0.0, 1.0]
    R_at = [R_cv[0], R_cv[1], R_cv[2], -R_cv[3], -R_cv[4], -R_cv[5], -R_cv[6], -R_cv[7], -R_cv[8]]
    check("apriltag-framed 30 deg, sign=-1 recovers +30", (spin_deg(R_at, -1.0),), (30.0,), 1e-6)

    print("\nStruct ABI:")
    good = TAG_SIZE == 252
    ok &= good
    print("  %-52s %s" % ("sizeof(tag_detection_t) == 252", "PASS" if good else "FAIL"))

    print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
    return 0 if ok else 1


# ---------------------------------------------------------------- display
def topdown(bx, by, rng, w=41, h=17):
    """Top-down body frame, nose up, right right. Answers 'is cam_yaw right?' visually."""
    grid = [[" "] * w for _ in range(h)]
    cx, cy = w // 2, h // 2
    for r in range(h):
        grid[r][cx] = "|"
    for c in range(w):
        grid[cy][c] = "-"
    grid[cy][cx] = "+"
    col = cx + int(round((by / rng) * cx))
    row = cy - int(round((bx / rng) * cy))
    tag_visible = 0 <= col < w and 0 <= row < h
    if tag_visible:
        grid[row][col] = "#"
    out = ["    nose/+X".ljust(w)]
    out += ["".join(r) for r in grid]
    out.append(("  %+.2f m full scale, right = +Y" % rng).ljust(w))
    if not tag_visible:
        out.append("  (tag off scale -- raise --range)")
    return out


def dial(d, w=41):
    half = w // 2
    pos = max(0, min(w - 1, int(round(half + (d / 180.0) * half))))
    cells = ["."] * w
    cells[half] = "|"
    cells[pos] = "#"
    return "".join(cells)


# ---------------------------------------------------------------- live
def run(args):
    mpa = ct.CDLL("libmodal_pipe.so")
    mpa.pipe_client_get_next_available_channel.argtypes = []
    mpa.pipe_client_get_next_available_channel.restype = ct.c_int
    mpa.pipe_client_open.argtypes = [ct.c_int, ct.c_char_p, ct.c_char_p, ct.c_int, ct.c_int]
    mpa.pipe_client_open.restype = ct.c_int
    mpa.pipe_client_get_fd.argtypes = [ct.c_int]
    mpa.pipe_client_get_fd.restype = ct.c_int

    ch = mpa.pipe_client_get_next_available_channel()
    ret = mpa.pipe_client_open(ch, b"tag_detections", b"mount_check", 0, TAG_SIZE * 16)
    if ret != 0:
        sys.exit("pipe_client_open failed: %d (is voxl-tag-detector running?)" % ret)
    fd = mpa.pipe_client_get_fd(ch)

    off = tuple(args.off)
    buf = b""
    while True:
        r, _, _ = select.select([fd], [], [], 1.0)
        if not r:
            continue
        data = os.read(fd, TAG_SIZE * 16)
        if not data:
            continue
        buf += data
        while len(buf) >= TAG_SIZE:
            f = struct.unpack_from(TAG_FMT, buf)
            buf = buf[TAG_SIZE:]
            if f[0] != MAGIC:
                continue
            if args.id >= 0 and f[1] != args.id:
                continue

            t_cam = (f[I_T], f[I_T + 1], f[I_T + 2])
            R = list(f[I_R:I_R + 9])
            if not all(math.isfinite(v) for v in t_cam + tuple(R[:4])):
                print("NaN pose -- is tag id %d listed in /etc/modalai/tag_locations.conf?" % f[1])
                continue

            b = optical_to_body(t_cam, args.cam_yaw, off)
            hd = heading_wrt_nose(R, args.cam_yaw, args.front_off, args.spin_sign)
            cam = f[I_CAM].decode("ascii", "ignore").split("\x00")[0]

            lines = []
            lines.append("\033[H\033[J" if not args.no_clear else "")
            lines.append("id=%d  cam=%s  cam_yaw=%.1f  front_off=%.1f  spin_sign=%+g  "
                         "offset=(%.2f,%.2f,%.2f)"
                         % (f[1], cam, args.cam_yaw, args.front_off, args.spin_sign,
                            off[0], off[1], off[2]))
            lines.append("")
            lines.append("optical  t_cam = (%+.2f, %+.2f, %+.2f)  range=%.2f m"
                         % (t_cam[0], t_cam[1], t_cam[2], t_cam[2]))
            lines.append("body     t_body= (%+.2f, %+.2f, %+.2f)   <- +X nose, +Y right, +Z down"
                         % b)
            lines.append("")
            lines += topdown(b[0], b[1], args.range)
            lines.append("")
            lines.append("marker spin in image : %+7.1f deg  (sign %+g applied)"
                         % (spin_deg(R, args.spin_sign), args.spin_sign))
            lines.append("pad heading wrt nose : %+7.1f deg   (0 = pad front faces the nose)"
                         % hd)
            lines.append(dial(hd))
            lines.append("")
            lines.append("NED heading = this + vehicle yaw. Nexus adds that term itself.")
            print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="check the algebra, no pipe needed")
    ap.add_argument("--cam-yaw", type=float, default=180.0, dest="cam_yaw",
                    help="cam_yaw_deg (Starling 180, SITL 90, leg drone 135 or 225)")
    ap.add_argument("--front-off", type=float, default=0.0, dest="front_off",
                    help="marker_front_offset_deg")
    ap.add_argument("--off", type=float, nargs=3, default=[0.0, 0.0, 0.05],
                    help="cam_offset_body, metres")
    ap.add_argument("--id", type=int, default=-1, help="only this tag id (default: all)")
    ap.add_argument("--range", type=float, default=2.0, help="plot half-scale, metres")
    ap.add_argument("--spin-sign", type=float, default=-1.0, choices=[-1.0, 1.0],
                    dest="spin_sign",
                    help="-1 (default) = AprilTag/VOXL convention; +1 = OpenCV/ArUco/SITL")
    ap.add_argument("--no-clear", action="store_true", help="scroll instead of redrawing")
    args = ap.parse_args()
    return selftest() if args.selftest else run(args)


if __name__ == "__main__":
    sys.exit(main())
