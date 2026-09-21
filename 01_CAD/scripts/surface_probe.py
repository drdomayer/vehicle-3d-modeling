"""
surface_probe.py — the surface as a FUNCTION, on a fixed grid, where the vertices cannot lie.

WHY IT EXISTS. On 2026-09-21 a change to how rings are smoothed along X moved the principal-
curvature ratio from 0.279 to 0.242, the first time this project's own criterion read PASS, and it
was committed as the largest single gain so far. It was not a gain at all. The estimator in
highlight_test.py reads a vertex's one-ring, and the change aligned one-rings with the flow of the
surface; the shape did not move. Measured as a function -- the half-width y(x, z) on a fixed grid,
where sliding samples along the same curve changes nothing -- the two versions are the same car to
within a percent.

That is the fourth time a number produced by the DISCRETISATION has been reported as a fact about
the SURFACE, and the earlier three are written up in this repo: isophote elongation of 34,211:1,
the boundary-travel figures of 28.0/42.5/60.1 mm, and a rocker read 0.888 m2 wide because the
measurement took a mirrored pair for one part. The pattern is always the same and always invisible
from inside the metric that produced it. The cure is not more care; it is a second measurement that
the same trick cannot move.

WHAT IT MEASURES. y(x, z) on a 25 mm grid, and the mean absolute second difference of it along each
axis. Sliding vertices along a curve, changing how many there are, or re-tessellating leaves this
untouched; bending the surface changes it.

WHAT IT CANNOT DO. It says how smooth the surface is, not whether it is the RIGHT shape -- the
silhouette, the plan and the edge test answer that -- and a perfectly smooth car scores best of all,
so a falling number is not on its own an improvement. It is a control, to be read beside the others.

AND IT IS NOT INVARIANT TO EVERYTHING, which its first real use made clear. Sliding samples along a
straight run does not move it; ADDING a sample at a corner does, because the ring is a polyline and
a corner that was being cut across is now being followed. On 2026-09-21 anchoring the front fender
crest pushed |d2y/dx2| from 17.37 to 19.15 while the volume and the design angle did not move at
all. That is the crease appearing in the surface, not the surface getting worse -- the same
direction the docstring above warns about, read the other way round. A rise wants a reason written
beside it exactly as a fall does.

    import bpy; exec(open(".../surface_probe.py").read())
"""

import json
import os
import time

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
SRC = os.path.join(REPO, "01_CAD/scripts/statev_master_volumes.py")
STEP = 25          # mm of the sampling grid, in both axes
Z_LO, Z_HI = 250, 880


def load():
    src = open(SRC).read().split("\ndef build():")[0]
    M = {"__name__": "mv"}
    exec(compile(src, SRC, "exec"), M)
    return M


def y_at(ring_pts, z):
    """Half-width of the +Y side at this height: the surface as a function of (station, height)."""
    h = sorted([(zz, yy) for yy, zz in ring_pts if yy >= 0])
    for i in range(len(h) - 1):
        (z0, y0), (z1, y1) = h[i], h[i + 1]
        if z0 <= z <= z1 and z1 != z0:
            return y0 + (z - z0) / (z1 - z0) * (y1 - y0)
    return None


def main():
    M = load()
    order = sorted(v[0] for v in M["SECTIONS"].values())
    st = []
    for i in range(len(order) - 1):
        st += [order[i] + (order[i + 1] - order[i]) * k / M["SUBDIV"] for k in range(M["SUBDIV"])]
    st.append(order[-1])
    raw = [M["ring"](x) for x in st]

    # the same smoothing build() applies, so this describes the car that gets built
    npts = len(raw[0])
    rings = []
    for i in range(len(raw)):
        row = []
        for k in range(npts):
            ay = az = w = 0.0
            for d, g in ((-2, 1), (-1, 4), (0, 6), (1, 4), (2, 1)):
                j = min(len(raw) - 1, max(0, i + d))
                ay += raw[j][k][0] * g
                az += raw[j][k][1] * g
                w += g
            row.append((ay / w, az / w))
        rings.append(row)

    G = {}
    for i, r in enumerate(rings):
        for z in range(Z_LO, Z_HI + 1, STEP):
            v = y_at(r, z)
            if v is not None:
                G[(i, z)] = v
    tx = cx = tz = cz = 0.0
    worst = (0.0, None)
    for (i, z), v in G.items():
        a, b = G.get((i - 1, z)), G.get((i + 1, z))
        if a is not None and b is not None:
            d = abs(a - 2 * v + b)
            tx += d
            cx += 1
            if d > worst[0]:
                worst = (d, (st[i], z))
        c, e = G.get((i, z - STEP)), G.get((i, z + STEP))
        if c is not None and e is not None:
            tz += abs(c - 2 * v + e)
            cz += 1
    mx, mz = tx / cx, tz / cz

    print("=" * 92)
    print("SURFACE PROBE — y(x, z) on a fixed grid, which the vertex arrangement cannot change")
    print("=" * 92)
    print(f"\n  grid {STEP} mm, {len(G)} samples over {len(st)} stations, Z {Z_LO}..{Z_HI}")
    print(f"  mean |d2y/dx2|  {mx:7.3f} mm      worst {worst[0]:7.2f} mm at "
          f"spec X {worst[1][0]:.0f}, Z {worst[1][1]}")
    print(f"  mean |d2y/dz2|  {mz:7.3f} mm")
    print("\n  Sliding samples along the same curve, changing how many there are, or")
    print("  re-tessellating leaves these untouched. Bending the surface changes them.")
    print("  A falling number is not by itself an improvement: a featureless car scores best.")
    print("  Read it beside the silhouette, the plan and the edge test, never instead of them.")
    p = os.path.join(REPO, "01_CAD/scripts/data/last_surface.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"surf_x_mm": round(mx, 3), "surf_z_mm": round(mz, 3),
                   "when": time.time()}, f, indent=2)
    print(f"\n  wrote {p}")


main()
