"""
overhang_report.py — how much of each printed section hangs in the air, as it is laid.

WHY. Every section is laid on its flattest face and that is the whole of the orientation decision.
docs/13 Q32 asks the shop for its overhang limit and Q33 who removes supports; neither is answered,
and until they are the pipeline cannot CHOOSE an orientation. What it can do now is MEASURE what the
current one costs at any limit the shop might name, so the answer to Q32 changes a number here
instead of starting an investigation.

WHAT IT MEASURES, per file, in the file's own frame (Z up on the plate):
  - the area of faces whose normal points down, binned by how far past horizontal they lean;
  - the worst overhang angle on the part;
  - the same figures with the part turned over, because lay_flat chose "smallest dimension
    vertical" and never asked which side up -- and for a shell, which side is up decides whether
    the class-A face sits on supports.

An overhang angle here is measured from VERTICAL: 0 is a wall, 90 is a ceiling. A face at 45
prints unsupported on most FDM machines; a face past 60 usually does not. Those two are the bins
reported, and neither is a rule until the shop says so.

WHAT IT CANNOT DO. It sees geometry, not the printer: no bridging, no cooling, no material. It
does not know which face is class-A -- panel_production knows the outer surface and could pass it
down, but does not yet -- so "turned over is better" here means less air, not necessarily the
right face up.

    python3 01_CAD/scripts/overhang_report.py
"""

import csv
import glob
import math
import os
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRS = [("ready to bond", os.path.join(REPO, "03_PRINT", "production")),
        ("shape only", os.path.join(REPO, "03_PRINT", "shape_only"))]
OUT = os.path.join(REPO, "04_ENGINEERING", "reports", "overhang.csv")
BINS = (45.0, 60.0)
BED_MM = 0.5     # a face this close to the plate is resting on it


def tris(path):
    with open(path, "rb") as f:
        head = f.read(84)
        n = int.from_bytes(head[80:84], "little")
        body = f.read()
    return [struct.unpack("<9f", body[i * 50 + 12:i * 50 + 48]) for i in range(n)]


def measure(path):
    """Area fractions past each bin and the worst angle, as laid and turned over.

    TWO BUGS IN THE FIRST VERSION, both caught by the numbers it printed. It reported 393 m2 of
    supported surface on a car with 12.9 m2 of skin -- cm2 divided by 100 instead of 10,000. And it
    reported 49% of nearly every file at 90 degrees: that was the BOTTOM face lying on the plate,
    which is the base, not an overhang. A face is an overhang only if there is air under it, so
    faces sitting on the bed are excluded -- and for the turned-over case the part is first dropped
    onto the bed again, because turning a curved shell over changes what touches the plate."""
    T = tris(path)
    if not T:
        return None

    def run(flip):
        # EAGER, on purpose. The first version built each triangle as a generator expression
        # inside the list comprehension and materialised it on the next line -- by which time the
        # comprehension's `t` had moved on to the LAST triangle, so every entry in pts was that one
        # triangle. The report then printed 100% overhang at "worst 62.66 degrees" for P08_s05,
        # which is the angle of that single face, on a part whose true figures are 41% / 9% / 75.
        # A generator closes over the variable, not its value.
        pts = [tuple((t[i * 3], t[i * 3 + 1], (-t[i * 3 + 2] if flip else t[i * 3 + 2]))
                     for i in range(3)) for t in T]
        zmin = min(v[2] for p in pts for v in p)
        tot, worst = 0.0, 0.0
        over = {b: 0.0 for b in BINS}
        # Support VOLUME, not just angle. A curved shell laid flat has its whole underside as a
        # near-ceiling -- 90 degrees from vertical -- and the angle bins then say "49% overhang"
        # of almost every file, which is true and useless: an underside one millimetre above the
        # plate costs nothing, one a hundred millimetres up is a block of support. What a farm
        # charges for is area times the gap to whatever is below, and for a shell's underside
        # that gap is the height above the bed. Summed over the faces past 60 degrees.
        sup_mm3, gap_max = 0.0, 0.0
        for p in pts:
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = p
            ax, ay, az = x1 - x0, y1 - y0, z1 - z0
            bx, by, bz = x2 - x0, y2 - y0, z2 - z0
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            L = math.sqrt(nx * nx + ny * ny + nz * nz)
            if L < 1e-9:
                continue
            area = L / 2.0
            tot += area
            if nz >= 0:
                continue                                   # faces up: never an overhang
            if max(z0, z1, z2) - zmin < BED_MM:
                continue                                   # on the plate: the base, not air
            ang = math.degrees(math.asin(min(1.0, -nz / L)))
            worst = max(worst, ang)
            for b in BINS:
                if ang > b:
                    over[b] += area
            if ang > 60.0:
                gap = (z0 + z1 + z2) / 3.0 - zmin
                sup_mm3 += area * gap
                gap_max = max(gap_max, gap)
        return tot, over, worst, sup_mm3, gap_max

    tot, dn, wd, sv, gm = run(False)
    _, up, wu, fsv, fgm = run(True)
    if tot <= 0:
        return None
    return {"area_cm2": tot / 100.0,
            "over45": dn[45.0] / tot, "over60": dn[60.0] / tot, "worst": wd,
            "support_cm3": sv / 1000.0, "gap_max_mm": gm,
            "flip_over45": up[45.0] / tot, "flip_over60": up[60.0] / tot, "flip_worst": wu,
            "flip_support_cm3": fsv / 1000.0, "flip_gap_max_mm": fgm}


def main():
    rows = []
    for tier, d in DIRS:
        for p in sorted(glob.glob(os.path.join(d, "*.stl"))):
            m = measure(p)
            if m is None:
                continue
            m["tier"], m["file"] = tier, os.path.basename(p)
            m["better_flipped"] = "yes" if m["flip_support_cm3"] < m["support_cm3"] * 0.8 else ""
            rows.append(m)
    if not rows:
        print("  no files — run panel_production.py first")
        return 1
    print("=" * 92)
    print("OVERHANG — what the current orientation costs, at the limits a shop might name")
    print("=" * 92)
    print("\n  angle is from VERTICAL: 0 a wall, 90 a ceiling. Two bins, neither a rule until Q32.")
    for tier, _ in DIRS:
        r = [x for x in rows if x["tier"] == tier]
        if not r:
            continue
        n45 = sum(1 for x in r if x["over45"] > 0.10)
        n60 = sum(1 for x in r if x["over60"] > 0.10)
        a60 = sum(x["over60"] * x["area_cm2"] for x in r) / 10000.0     # cm2 -> m2
        flip = sum(1 for x in r if x["better_flipped"])
        hug = sum(1 for x in r if x["gap_max_mm"] < 5.0)
        tall = sum(1 for x in r if x["gap_max_mm"] > 30.0)
        sv = sum(x["support_cm3"] for x in r) / 1000.0
        print(f"\n  {tier:15s} {len(r):4d} files")
        print(f"     with more than 10% of their area past 45 deg: {n45:4d}")
        print(f"     with more than 10% of their area past 60 deg: {n60:4d}   "
              f"({a60:.2f} m2 of underside in the air)")
        print(f"     underside hugging the bed, under 5 mm of gap:  {hug:4d}   (angle says overhang, "
              f"cost says none)")
        print(f"     underside more than 30 mm off the bed:        {tall:4d}   (real support)")
        print(f"     support volume, all files, past 60 deg:      {sv:6.2f} L")
        print(f"     that would need LESS support turned over:      {flip:4d}")
    worst = sorted(rows, key=lambda x: -x["support_cm3"])[:8]
    print(f"\n  {'worst files by SUPPORT VOLUME':40s} {'>60':>5s} {'gap max':>8s} {'support':>9s}  turned over")
    for x in worst:
        print(f"  {x['file']:40s} {x['over60']*100:4.0f}% {x['gap_max_mm']:6.0f}mm "
              f"{x['support_cm3']:7.0f}cm3  {x['flip_support_cm3']:7.0f}cm3")
    print("\n  'turned over' is the same part upside down. Since 2026-09-26 production puts the")
    print("  CLASS-A face UP on every file (CLASS_A_UP in the schedule), so what 'turned over'")
    print("  would save in support it would pay for in scars on the face that gets laminated.")
    print("  That is a deliberate trade; the litres above are what it costs, for Q32 and Q33.")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tier", "file", "area_cm2", "over45", "over60", "worst",
                                          "support_cm3", "gap_max_mm",
                                          "flip_over45", "flip_over60", "flip_worst",
                                          "flip_support_cm3", "flip_gap_max_mm",
                                          "better_flipped"])
        w.writeheader()
        for x in rows:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in x.items()})
    print(f"\n  wrote {OUT}")
    return 0


sys.exit(main())
