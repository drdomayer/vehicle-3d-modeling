"""
print_qc.py — are the exported files actually printable? Nobody had asked.

WHAT WAS MISSING. The pipeline checks that a section fits the plate and that a file holds one
connected piece. Neither is the question a slicer asks. A slicer needs a CLOSED, MANIFOLD solid
with consistent winding and a positive volume; given anything else it either guesses, or prints a
shell with holes in it, or silently drops geometry. 417 files have been produced across this
project and not one of them had been opened and checked.

WHAT IT CHECKS, per file:
  watertight   every edge shared by exactly two triangles. An edge with one is a hole; an edge
               with three or more is a non-manifold junction that no slicer handles predictably.
  winding      the two triangles on each edge traverse it in opposite directions. Consistent
               winding is what tells the slicer which side is inside.
  volume       the signed volume is positive. Negative means the solid is inside out, and a
               slicer will happily print its complement.
  degenerate   triangles with no area, which come from cuts that landed on an existing vertex.

It runs OUTSIDE Blender on purpose: it reads the files that will be sent, not the objects they
came from, so nothing about the build can hide a problem in the file.

WHAT IT CANNOT DO. It says the file is a well-formed solid, not that the solid is the right shape
-- assembly_check.py answers that -- and it says nothing about printability in the other sense:
overhangs, thin walls and supports depend on the shop's answers in docs/13 Q30 and Q32.

    python3 01_CAD/scripts/print_qc.py
"""

import glob
import os
import struct
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRS = [("ready to bond", os.path.join(REPO, "03_PRINT", "production")),
        ("shape only", os.path.join(REPO, "03_PRINT", "shape_only"))]
# MILLIMETRES, and the number matters. The first version used 1e-4 "metres" on files that are in
# millimetres, so the tolerance was 0.0001 mm -- and a float32 at 900 mm has a step of about
# 1.07e-4 mm, so the threshold sat BELOW the noise of the format. Vertices that are the same point
# landed in different buckets, and the checker reported 349 of 417 files as broken. A micron is
# four orders below any printing tolerance and two above the float32 step at this size.
Q = 1e-3          # mm of quantisation when matching vertices


def read_tris(path):
    with open(path, "rb") as f:
        head = f.read(84)
        if len(head) < 84:
            return None
        n = int.from_bytes(head[80:84], "little")
        body = f.read()
    if len(body) < n * 50:
        return None
    return [struct.unpack("<9f", body[i * 50 + 12:i * 50 + 48]) for i in range(n)]


def check(path):
    tris = read_tris(path)
    if tris is None:
        return {"unreadable": True}
    if not tris:
        return {"empty": True}
    edges = defaultdict(int)
    directed = defaultdict(int)
    vol = 0.0
    degen = 0
    for t in tris:
        p = [(round(t[i * 3] / Q), round(t[i * 3 + 1] / Q), round(t[i * 3 + 2] / Q))
             for i in range(3)]
        a, b, c = (t[0:3], t[3:6], t[6:9])
        # signed volume of the tetrahedron to the origin; summed over a closed surface it is 6V
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0]))
        if p[0] == p[1] or p[1] == p[2] or p[0] == p[2]:
            degen += 1
            continue
        for i in range(3):
            u, v = p[i], p[(i + 1) % 3]
            edges[tuple(sorted((u, v)))] += 1
            directed[(u, v)] += 1
    holes = sum(1 for k, n in edges.items() if n == 1)
    nonmanifold = sum(1 for k, n in edges.items() if n > 2)
    # winding: for a consistently wound closed mesh every directed edge appears exactly once
    bad_wind = sum(1 for k, n in directed.items() if n > 1)
    return {"tris": len(tris), "holes": holes, "nonmanifold": nonmanifold,
            "winding": bad_wind, "volume_cm3": vol / 6.0 / 1000.0, "degenerate": degen}


def main():
    total, bad = 0, []
    print("=" * 96)
    print("PRINT QC — the exported files, read as a slicer would read them")
    print("=" * 96)
    for label, d in DIRS:
        files = sorted(glob.glob(os.path.join(d, "*.stl")))
        if not files:
            continue
        issues = 0
        for p in files:
            total += 1
            r = check(p)
            why = []
            if r.get("unreadable"):
                why.append("unreadable")
            elif r.get("empty"):
                why.append("no triangles")
            else:
                if r["holes"]:
                    why.append(f"{r['holes']} open edge(s)")
                if r["nonmanifold"]:
                    why.append(f"{r['nonmanifold']} non-manifold edge(s)")
                # Winding is only reported where it is an INDEPENDENT defect. An edge shared by
                # three or more faces necessarily has two of them traversing it the same way, so
                # on a file that already has non-manifold edges the winding count is the same
                # fault counted again -- the first version printed both and made one problem look
                # like two.
                if r["winding"] and not r["nonmanifold"]:
                    why.append(f"{r['winding']} inconsistent winding")
                if r["volume_cm3"] <= 0:
                    why.append(f"volume {r['volume_cm3']:.1f} cm3")
                if r["degenerate"]:
                    why.append(f"{r['degenerate']} degenerate")
            if why:
                issues += 1
                bad.append((os.path.relpath(p, REPO), "; ".join(why)))
        print(f"\n  {label:15s} {len(files):4d} files, {len(files)-issues:4d} clean, "
              f"{issues:4d} with something to say")
    if bad:
        print(f"\n  {len(bad)} of {total} files are not a well-formed solid:")
        for p, why in bad[:25]:
            print(f"    {os.path.basename(p):42s} {why}")
        if len(bad) > 25:
            print(f"    ... and {len(bad)-25} more")
    else:
        print(f"\n  all {total} files are closed, manifold, consistently wound and positive")
    print("\n  This says the file is a well-formed SOLID, not that it is the right SHAPE —")
    print("  assembly_check.py answers that. It says nothing about overhangs, thin walls or")
    print("  supports, which wait on docs/13 Q30 and Q32.")
    return 1 if bad else 0


sys.exit(main())
