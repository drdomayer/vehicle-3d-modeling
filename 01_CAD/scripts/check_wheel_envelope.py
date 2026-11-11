"""
check_wheel_envelope.py — does any part stand in the tyre's way when the wheel steers and rises?

    Blender:  import bpy; exec(open(".../check_wheel_envelope.py").read())

WHY (2026-11-12). The cage carries the STATIC tyre and a +-35 deg STEER_SWEEP box marked
do_not_trust; nothing ever measured a part against the tyre in motion. Since v078 the fender vent
sits right over the front tyre and its louvres hang into the arch, 65 mm above the static tread.

THE ENVELOPE, per wheel, in the wheel's own frame:
    tyre      a cylinder, radius OD/2, width W -- the 19" sizes from the skeleton (published sizes)
    steer     +-STEER deg about a VERTICAL axis through the wheel centre. The real steering axis is
              raked and sits near the tyre's centre plane at the ground (small scrub radius), so a
              vertical axis through the centre over-states the reach a little: conservative.
              35 deg: the 986's published turning circle 10.9 m on 2415 / 1465 gives ~26 deg outer,
              ~35 deg inner (Ackermann), workshop manual Group 0a.
    bump      the centre raised by 0..BUMP mm. NOT PUBLISHED in the manuals we have: 80 front /
              90 rear are ASSUMPTIONS for a MacPherson car of this class. docs/20 A8 / B5 measure
              the real free space (tread to wheelhouse at ride height); until then a clearance that
              depends on BUMP is a finding to measure, not a fact.
A part vertex (or face centre) closer to that swept solid than CLEAR mm is reported. Negative is
inside the tyre's path.
"""
import json
import math
import os
import time

import bpy

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
_sk = {"__file__": os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), "__name__": "_sk"}
with open(_sk["__file__"], encoding="utf-8") as _f:
    exec(_f.read().split("\ndef build(")[0], _sk)
WM = _sk["WHEEL_MOTION"]         # the ONE place the motion is written; stage03 trims to it too
CLEAR = WM["clear"]              # hard constraint 3: 15-20 mm to anything that moves or is OEM
WHEELS = {   # name: (spec X centre, |Y| centre, radius, width, bump mm, steer deg)
    "front": (0.0, 732.5, 647.1 / 2.0, 235.0, WM["bump_front"], WM["steer"]),
    "rear":  (2415.0, 764.0, 675.1 / 2.0, 275.0, WM["bump_rear"], 0.0),
}
STEER_STEP, BUMP_STEP = 2.5, 10.0


def tyre_distance(dx, dy, dz, r, w, bump, steer):
    """Least distance (mm) from a point (relative to the static wheel centre, dy positive outboard)
    to the tyre over every steer angle and bump height; negative = inside the tyre."""
    best = 1e9
    na = int(round(steer / STEER_STEP)) if steer > 0 else 0
    angles = [math.radians(STEER_STEP * k) for k in range(-na, na + 1)]
    nb = int(round(bump / BUMP_STEP))
    for b in [BUMP_STEP * k for k in range(nb + 1)]:
        dzb = dz - b
        for th in angles:
            c, s = math.cos(th), math.sin(th)
            u = dx * c + dy * s          # along the wheel plane
            v = -dx * s + dy * c         # along the axle
            rad = math.hypot(u, dzb) - r
            ax = abs(v) - w / 2.0
            if rad <= 0 and ax <= 0:
                d = max(rad, ax)
            else:
                d = math.hypot(max(rad, 0.0), max(ax, 0.0))
            if d < best:
                best = d
    return best


def main():
    coll = bpy.data.collections.get("STATEV_PANELS")
    if coll is None:
        print("no STATEV_PANELS -- run panel_extract.py first")
        return
    import builtins
    lines = []

    def print(*a, **k):                      # the report is also written to a file
        txt = " ".join(str(x) for x in a)
        lines.append(txt)
        builtins.print(txt, **k)
    print("=" * 96)
    print("WHEEL ENVELOPE — every part against the tyre steered and in bump")
    print("=" * 96)
    for k, (wx, wy, r, w, bump, steer) in WHEELS.items():
        print(f"  {k:<6} centre specX {wx:.0f} |Y| {wy:.1f}, r {r:.1f}, width {w:.0f}, "
              f"bump 0..{bump:.0f} (ASSUMED), steer +-{steer:.0f}")
    rows = []
    for ob in sorted(coll.objects, key=lambda o: o.get("panel_id", "")):
        pid = ob.get("panel_id")
        if not pid or ob.type != "MESH":
            continue
        M = ob.matrix_world
        pts = [M @ v.co for v in ob.data.vertices] + [M @ p.center for p in ob.data.polygons]
        for k, (wx, wy, r, w, bump, steer) in WHEELS.items():
            reach = math.hypot(r, w / 2.0) + bump + CLEAR + 60.0
            worst = None
            for p in pts:
                sx, y, z = -p.x * 1000.0, p.y * 1000.0, p.z * 1000.0
                dx, dy, dz = sx - wx, abs(y) - wy, z - r
                if abs(dx) > reach or abs(dy) > reach or dz > reach:
                    continue
                d = tyre_distance(dx, dy, dz, r, w, bump, steer)
                if worst is None or d < worst[0]:
                    worst = (d, sx, y, z)
            if worst is not None and worst[0] < CLEAR + 25.0:
                # the same point WITHOUT bump, to say what the assumption is carrying
                d0 = tyre_distance(worst[1] - wx, abs(worst[2]) - wy, worst[3] - r, r, w, 0.0, steer)
                rows.append((pid, ob.name, k, worst[0], d0, worst[1], worst[2], worst[3]))
    print(f"\n  {'part':<6}{'object':<26}{'wheel':<7}{'min mm':>8}{'no bump':>9}   at specX, Y, Z   verdict")
    bad = 0
    for pid, nm, k, d, d0, sx, y, z in sorted(rows, key=lambda t: t[3]):
        verdict = "ok" if d >= CLEAR else ("INSIDE" if d < 0 else "TIGHT")
        if d < CLEAR:
            bad += 1
            if d0 >= CLEAR:
                verdict += " (only with the assumed bump)"
        print(f"  {pid:<6}{nm[:25]:<26}{k:<7}{d:>8.1f}{d0:>9.1f}   {sx:6.0f},{y:6.0f},{z:5.0f}   {verdict}")
    print(f"\n  {bad} part(s) closer than {CLEAR:.0f} mm to the moving tyre. Parts more than "
          f"{CLEAR + 25:.0f} mm away are not listed.")
    print("  The steer axis is vertical through the wheel centre (conservative); the bump travel is an")
    print("  ASSUMPTION until docs/20 A8 / B5 are measured.")
    with open(os.path.join(REPO, "04_ENGINEERING", "reports", "wheel_envelope.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(REPO, "01_CAD", "scripts", "data", "last_wheel.json"), "w", encoding="utf-8") as f:
        json.dump({"wheel_tight": bad,
                   "wheel_tight_static": sum(1 for r_ in rows if r_[4] < CLEAR),
                   "when": time.time(),
                   "rows": [dict(part=a, wheel=c, min_mm=round(d, 1), no_bump_mm=round(e, 1))
                            for a, _b, c, d, e, *_r in rows]}, f, indent=2)
    return rows


main()
