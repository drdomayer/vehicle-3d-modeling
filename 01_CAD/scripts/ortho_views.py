"""
ortho_views.py — the two orthographic silhouettes the goal check measures, rasterised not rendered.

WHY IT EXISTS AS A FILE. Until 2026-09-18 these two PNGs were produced by ad-hoc code typed into
Blender in whichever session needed them. check_goal.py reads them and compares against a recorded
baseline, so a STALE PNG does not fail: it reports the old geometry as agreeing with the reference
and prints "nothing regressed". Same shape of fault as shipping v024-v026 without measuring — the
check ran and the answer meant nothing. So it is a script, with a name, and check_goal refuses a
file older than the build scripts.

WHY IT DOES NOT RENDER. The first version of this file did render, with an auto-framed camera, and
silhouette_overlay came back with 441 mm mean against 15. Nothing was wrong with the geometry:
model_side.png has a HARD CONTRACT that is hard-coded at the top of silhouette_overlay.py — exactly
1680x560 px, 2.8753 mm/px, front-axle centre on the ground at pixel (417.4, 521.7) — and an
auto-framed render satisfies none of it. Worse, a render puts the engine, the materials, the lights,
the world colour, the film setting and colour management between the mesh and the measurement, and
every one of them can move the mask silently. The mask is a MEASUREMENT, so it is computed from the
vertices: each triangle of the body is projected orthographically and filled. Nothing else is in the
path, and the contract is asserted rather than hoped for.

THE MIRROR IS STILL THE TRAP. Getting the camera backwards cost a whole table of withdrawn numbers
on 2026-09-16: our nose was compared against the reference's tail. Here image +x is spec X rearward
by construction (spec X = -repo X), and the script asserts that the nose lands left of the tail and
that the front axle lands on 417.4 before writing anything.

    import bpy; exec(open(".../ortho_views.py").read())
"""

import os

import bpy
import numpy as np

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
SIDE = os.path.join(REPO, "04_ENGINEERING/statev_v01/overlay/model_side.png")
TOP = os.path.join(REPO, "04_ENGINEERING/statev_v01/plan/model_plan.png")
# FRONT and REAR, added 2026-09-26. Until then the goal check saw the car from the side and from
# above and never from ahead -- and ahead is the view in which the model looked nothing like the
# reference while every metric passed. Rendered as a silhouette of the whole car looking along
# the axis, so the outline is the widest extent at each height, which is what a front view shows.
FRONT = os.path.join(REPO, "04_ENGINEERING/statev_v01/front/model_front.png")
REAR = os.path.join(REPO, "04_ENGINEERING/statev_v01/front/model_rear.png")
END_W, END_H = 1000, 560          # plan-style contract: compared normalised, framing is free
BODY = ["STATEV_FRONT_VOLUME", "STATEV_SIDE_VOLUME", "STATEV_REAR_VOLUME"]

# The contract, copied from the top of silhouette_overlay.py. If that changes, this changes with it.
MMPX = 2.8753
SIDE_W, SIDE_H = 1680, 560
SIDE_OX, SIDE_OY = 417.4, 521.7        # front axle centre, on the ground
# The plan is compared NORMALISED, so its framing is free; it is kept on the same scale anyway so
# the two images can be read against each other by eye.
TOP_W, TOP_H = 1680, 720


def tris():
    """Every triangle of the body, in millimetres, as (spec_x, y, z)."""
    out = []
    for n in BODY:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        me = o.to_mesh()
        try:
            mw = o.matrix_world
            vs = [mw @ v.co for v in me.vertices]
            for p in me.polygons:
                idx = list(p.vertices)
                for k in range(1, len(idx) - 1):
                    t = []
                    for i in (idx[0], idx[k], idx[k + 1]):
                        w = vs[i]
                        t.append((-w.x * 1000.0, w.y * 1000.0, w.z * 1000.0))
                    out.append(t)
        finally:
            o.to_mesh_clear()
    if not out:
        raise RuntimeError("no STATEV_*_VOLUME in the scene — run statev_master_volumes.py first")
    return out


def fill(tri_px, w, h):
    """Scanline fill of projected triangles into a boolean mask of (h, w)."""
    m = np.zeros((h, w), bool)
    for (ax, ay), (bx, by), (cx, cy) in tri_px:
        y0 = max(0, int(np.floor(min(ay, by, cy))))
        y1 = min(h - 1, int(np.ceil(max(ay, by, cy))))
        if y1 < y0:
            continue
        for y in range(y0, y1 + 1):
            yc = y + 0.5
            xs = []
            for (px, py), (qx, qy) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy)),
                                       ((cx, cy), (ax, ay))):
                if (py > yc) != (qy > yc):
                    xs.append(px + (yc - py) * (qx - px) / (qy - py))
            if len(xs) < 2:
                continue
            lo = max(0, int(np.floor(min(xs))))
            hi = min(w - 1, int(np.ceil(max(xs))))
            if hi >= lo:
                m[y, lo:hi + 1] = True
    return m


def save(mask, path):
    h, w = mask.shape
    px = np.zeros((h, w, 4), np.float32)
    px[..., 3] = 1.0
    px[mask, 0:3] = 1.0
    img = bpy.data.images.new(os.path.basename(path), width=w, height=h, alpha=True)
    # Blender image rows run bottom-up; the mask's row 0 is the TOP of the picture.
    img.pixels.foreach_set(px[::-1].ravel())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def main():
    T = tris()
    sx = [p[0] for t in T for p in t]

    side_px = [[(SIDE_OX + p[0] / MMPX, SIDE_OY - p[2] / MMPX) for p in t] for t in T]
    top_px = [[(SIDE_OX + p[0] / MMPX, TOP_H / 2.0 - p[1] / MMPX) for p in t] for t in T]

    # the mirror check, before anything is written
    nose_px = SIDE_OX + min(sx) / MMPX
    tail_px = SIDE_OX + max(sx) / MMPX
    assert nose_px < tail_px, "image +x is not spec X rearward — the view is mirrored"
    assert abs((SIDE_OX + 0.0 / MMPX) - SIDE_OX) < 1e-9

    ms = fill(side_px, SIDE_W, SIDE_H)
    mt = fill(top_px, TOP_W, TOP_H)
    save(ms, SIDE)
    save(mt, TOP)
    # front view: image x = car Y (left of the car on the right of the image, as a person standing
    # in front sees it), image y down = Z down; rear view is the mirror in x.
    zs = [p[2] for t in T for p in t]
    zc = (min(zs) + max(zs)) / 2.0
    # ZONE-FILTERED. The first version projected the whole car, and the audit on 2026-09-26 showed
    # that the front zone then owns NOTHING in the outline: from |Y| 350 to 775 the highest thing
    # is the rear buttress and haunch, from 800 to 875 the door tops. A front view of the whole
    # car measures the rear. The front mask is the front zone only (spec X < door_front), the rear
    # mask the rear zone only (spec X > hoop plane), so each measures the surfaces its name says.
    ft = [t for t in T if max(p[0] for p in t) < 440.0]
    rt = [t for t in T if min(p[0] for p in t) > 1760.0]
    front_px = [[(END_W / 2.0 - p[1] / MMPX, END_H / 2.0 - (p[2] - zc) / MMPX) for p in t] for t in ft]
    rear_px = [[(END_W / 2.0 + p[1] / MMPX, END_H / 2.0 - (p[2] - zc) / MMPX) for p in t] for t in rt]
    save(fill(front_px, END_W, END_H), FRONT)
    save(fill(rear_px, END_W, END_H), REAR)
    print(f"  front/rear: {END_W}x{END_H}, {MMPX} mm/px, Z centred; FRONT ZONE ONLY / REAR ZONE ONLY"
          f" ({len(ft)} / {len(rt)} triangles); compared normalised")

    cols = np.where(ms.any(axis=0))[0]
    rows = np.where(mt.any(axis=0))[0]
    print(f"  {len(T)} triangles")
    print(f"  side: {SIDE_W}x{SIDE_H}, front axle at px {SIDE_OX}, {MMPX} mm/px")
    print(f"        nose px {cols.min()} (spec X {(cols.min()-SIDE_OX)*MMPX:.0f}), "
          f"tail px {cols.max()} (spec X {(cols.max()-SIDE_OX)*MMPX:.0f})")
    top_rows = np.where(mt.any(axis=1))[0]
    print(f"  top : half-width {abs(top_rows.min()-TOP_H/2)*MMPX:.0f} / "
          f"{abs(top_rows.max()-TOP_H/2)*MMPX:.0f} mm about the centreline")
    print(f"  wrote {SIDE}")
    print(f"  wrote {TOP}")


main()
