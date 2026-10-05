"""
waviness_check.py — how wavy is the car that gets PRINTED, in millimetres, and where.

Why it exists (2026-10-05). The glossy renders of the assembled files show lumps along the doors,
the haunches and the tail, and the measurements this repo keeps could not say how big they are:
the silhouette and the plan compare outlines, the curvature test reads the master mesh's vertex
rings, surface_probe reads second differences of the master. None of them looks at the PRINT FILES,
which are what the laminate follows and what the paint will show.

The measure. Profiles are cast across the assembled files -- rays from the side at five heights,
rays from above along four lines -- every 10 mm. Each profile is split wherever it jumps (an
opening, a seam step, a lamp slot), and on every run longer than the window a QUADRATIC is fitted
over a 300 mm window centred on each sample (Savitzky-Golay): the residual is what is left once the
car's own curvature is taken out. A curved panel scores zero; a 1 mm ripple scores 1 mm. A moving
average would not do -- on a 2 m radius it reads ~2 mm of "waviness" that is only curvature.

What it does NOT say: whether a wave is in the design (the loft) or added by the pipeline. Run with
WAVY_SOURCE = "master" to read the master body the same way; the difference is the pipeline's.

    import bpy; exec(open(".../waviness_check.py").read())
"""

import json
import os

import bpy
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "reports", "waviness.txt")
STEP = 10.0         # mm between samples along a profile
WINDOW = float(globals().get("WAVY_WINDOW", 300.0))   # mm, the quadratic's span: waves shorter than this are measured
JUMP = 15.0         # mm; a step bigger than this between neighbours breaks the profile
SIDE_Z = (350.0, 450.0, 550.0, 650.0, 750.0)
TOP_Y = (0.0, 250.0, 500.0, 700.0)
X0, X1 = -900.0, 3350.0

_ac = {"__file__": os.path.join(REPO, "01_CAD/scripts/assembly_check.py"), "__name__": "_ac"}
with open(_ac["__file__"], encoding="utf-8") as _f:
    exec(_f.read().split("\ndef main(")[0], _ac)


def files_tree():
    placement = {}
    for d in (_ac["PROD"], _ac["SHAPE"]):
        p = os.path.join(d, "placement.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for k, v in json.load(f)["parts"].items():
                    placement[os.path.join(d, k)] = v
    bm, used, _missing = _ac["assembled_tree"](placement)
    return BVHTree.FromBMesh(bm), used


def master_tree():
    bm = _ac["master_bm"]()
    return BVHTree.FromBMesh(bm), 1


def profile(tree, origin_fn, direction, coord):
    """[(spec_x, value)] along spec X; value is the hit's coordinate `coord` in mm."""
    out = []
    x = X0
    while x <= X1:
        o = origin_fn(x)
        hit = tree.ray_cast(o, direction)
        if hit[0] is not None:
            out.append((x, hit[0][coord] * 1000.0))
        else:
            out.append((x, None))
        x += STEP
    return out


def runs(prof):
    cur, all_ = [], []
    for x, v in prof:
        if v is None or (cur and abs(v - cur[-1][1]) > JUMP):
            if len(cur) * STEP > WINDOW:
                all_.append(cur)
            cur = [] if v is None else [(x, v)]
            continue
        cur.append((x, v))
    if len(cur) * STEP > WINDOW:
        all_.append(cur)
    return all_


def residuals(run):
    xs = np.array([p[0] for p in run])
    vs = np.array([p[1] for p in run])
    h = int(WINDOW / STEP / 2)
    res = []
    for i in range(h, len(run) - h):
        sx, sv = xs[i - h:i + h + 1], vs[i - h:i + h + 1]
        c = np.polyfit(sx - xs[i], sv, 2)
        res.append((xs[i], vs[i] - c[2]))
    return res


def main():
    source = globals().get("WAVY_SOURCE", "files")
    tree, used = files_tree() if source == "files" else master_tree()
    lines = []
    for z in SIDE_Z:
        prof = profile(tree, lambda x, z=z: mathutils.Vector((-x / 1000.0, 2.0, z / 1000.0)),
                       mathutils.Vector((0.0, -1.0, 0.0)), 1)
        lines.append((f"side  Z {z:.0f}", prof))
    for y in TOP_Y:
        prof = profile(tree, lambda x, y=y: mathutils.Vector((-x / 1000.0, y / 1000.0, 3.0)),
                       mathutils.Vector((0.0, 0.0, -1.0)), 2)
        lines.append((f"top   Y {y:.0f}", prof))
    rows, allr = [], []
    for name, prof in lines:
        rr = [r for run in runs(prof) for r in residuals(run)]
        if not rr:
            rows.append((name, 0, None, None, None))
            continue
        a = np.array([abs(r[1]) for r in rr])
        k = int(np.argmax(a))
        rows.append((name, len(rr), float(np.sqrt(np.mean(a ** 2))), float(a.max()), rr[k][0]))
        allr += list(a)
    txt = ["=" * 92,
           f"WAVINESS — the {'PRINT FILES (assembled)' if source == 'files' else 'MASTER body'}, "
           f"residual from a local quadratic over {WINDOW:.0f} mm",
           "=" * 92, "",
           f"  {'profile':<14}{'samples':>8}{'RMS mm':>9}{'max mm':>9}   at spec X"]
    for name, n, rms, mx, at in rows:
        txt.append(f"  {name:<14}{n:>8}" + (f"{rms:>9.2f}{mx:>9.2f}   {at:.0f}" if rms is not None
                                           else "        -        -"))
    if allr:
        a = np.array(allr)
        txt += ["", f"  ALL: RMS {np.sqrt(np.mean(a ** 2)):.2f} mm   90th {np.percentile(a, 90):.2f}   "
                    f"99th {np.percentile(a, 99):.2f}   max {a.max():.2f}   ({len(a)} samples)"]
    txt += ["", "  A ripple shorter than the window reads at its own height; the car's curvature does",
            "  not. Seams, lamp slots and openings break a profile rather than counting as waves.",
            "  Source: " + source + (f", {used} files" if source == "files" else "")]
    print("\n".join(txt))
    if source == "files":
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("\n".join(txt) + "\n")
        print(f"\n  wrote {OUT}")


main()
