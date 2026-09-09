"""
block_986.py — approximate 3D volume of the Porsche 986 donor for use as an underlay.

Inputs (all measured, none guessed):
  * side silhouette  — 04_ENGINEERING/reference/getoutlines_986_2003_ccby.gif, calibrated in cage_986.py
  * plan half-width  — data/986_plan_section.json  (from the 4-view blueprint, extract_blueprint_986.py)
  * cross-section    — same JSON: front/rear view silhouettes give half-width vs height
Wheel arches are cut with cylinders around the cage wheel centres.

Accuracy: side ±15 mm, plan/section ±30 mm (9 mm/px drawing). This is a VOLUME underlay for
design. It is NOT the donor's real surface — never use it for flanges, mounts or clearances.

Run after cage_986.py (reads DIMS/BLUEPRINT_SIDE from it). Re-running rebuilds UNDERLAY_986.
"""

import bpy
import json
import math
import os
import numpy as np

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.join(REPO, "01_CAD/scripts")
_ns = {}
with open(os.path.join(_here, "cage_986.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("# ---------------------------------------------------------------- helpers")[0], _ns)
DIMS, BLUEPRINT_SIDE = _ns["DIMS"], _ns["BLUEPRINT_SIDE"]
with open(os.path.join(_here, "data", "986_plan_section.json"), "r", encoding="utf-8") as f:
    PS = json.load(f)

COLL_NAME = "UNDERLAY_986"

# --- the few remaining assumptions (mm / px)
FLOOR_Z = 130            # flat underside of the body block
BELTLINE_ROW_CLAMP = 88  # side-blueprint pixel row: cabin cut — nothing above the beltline between hoops and cowl
ARCH_GAP = 45            # radial gap tyre → arch
ARCH_EXTRA_W = 120       # arch width beyond tyre width
STEP_PX = 4              # section spacing along x, in side-blueprint px (≈17 mm)
N_SIDE = 14              # points per side of a section (floor → top)
SECTION_Z_TOP_TAPER = 0.55  # half-width fraction at the very top edge of a section (crown rounding)


def mm(v):
    return v / 1000.0


def load_silhouette():
    path = os.path.join(REPO, BLUEPRINT_SIDE["path"])
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    dark = (px[..., :3].mean(axis=2) < 0.5)[::-1, :]   # image row order (top-down)
    top = np.full(w, -1)
    for c in range(w):
        rows = np.where(dark[:, c])[0]
        if rows.size:
            top[c] = rows.min()
    return w, h, top


def smooth(a, k=7):
    ker = np.ones(k) / k
    return np.convolve(np.pad(a, (k // 2, k // 2), mode="edge"), ker, mode="valid")


def interp_table(table, x):
    """table = [[key, value], ...] sorted by key descending or ascending; linear interpolation, clamped."""
    keys = np.array([t[0] for t in table]); vals = np.array([t[1] for t in table])
    if keys[0] > keys[-1]:
        keys, vals = keys[::-1], vals[::-1]
    return float(np.interp(x, keys, vals))


def section_fraction(z):
    """half-width fraction (0..1) at height z from the averaged front/rear silhouettes."""
    f = interp_table(PS["section_front"], z); r = interp_table(PS["section_rear"], z)
    hw = 0.5 * (f + r)
    hw_max = 0.5 * (max(v for _, v in PS["section_front"]) + max(v for _, v in PS["section_rear"]))
    return max(0.25, min(1.0, hw / hw_max))


def build():
    w_px, h_px, top = load_silhouette()
    fx, _ = BLUEPRINT_SIDE["px_front_wc"]; rx, _ = BLUEPRINT_SIDE["px_rear_wc"]
    gr = BLUEPRINT_SIDE["px_ground_row"]
    s_mm = DIMS["wheelbase"][0] / (fx - rx)

    valid = np.where(top >= 0)[0]
    c0, c1 = int(valid.min()), int(valid.max())
    cowl_c = fx + DIMS["cowl_x"][0] / s_mm
    hoop_c = fx + DIMS["hoop_x"][0] / s_mm
    topc = top.astype(float).copy()
    for c in range(c0, c1 + 1):
        if hoop_c - 40 <= c <= cowl_c:
            topc[c] = max(topc[c], BELTLINE_ROW_CLAMP)
    topc = smooth(topc[c0:c1 + 1], 7)

    plan = PS["plan_half_width"]
    x_plan_min = min(t[0] for t in plan); x_plan_max = max(t[0] for t in plan)

    verts, faces, rings = [], [], []
    for c in range(c0 + 2, c1 - 1, STEP_PX):
        x_mm = (c - fx) * s_mm
        if not (x_plan_min + 5 <= x_mm <= x_plan_max - 5):
            continue
        z_top = max((gr - topc[c - c0]) * s_mm, FLOOR_Z + 40)
        hw_plan = interp_table(plan, x_mm)
        # normalise the section template so the plan half-width is reached at the widest body height
        ring = []
        zs = [FLOOR_Z + (z_top - FLOOR_Z) * (i / N_SIDE) for i in range(N_SIDE + 1)]
        f_ref = max(section_fraction(z) for z in zs)
        def hw_at(z, i):
            frac = section_fraction(z) / f_ref
            if i == N_SIDE:                       # crown: round the top edge inward
                frac *= SECTION_Z_TOP_TAPER
            return hw_plan * min(1.0, frac)
        left = [(x_mm, -hw_at(z, i), z) for i, z in enumerate(zs)]
        right = [(x_mm, hw_at(z, i), z) for i, z in enumerate(zs)]
        loop = left + right[::-1]                 # floor-left → top-left → top-right → floor-right
        for (x, y, z) in loop:
            ring.append(len(verts)); verts.append((mm(x), mm(y), mm(z)))
        rings.append(ring)

    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(rings[0][::-1])); faces.append(tuple(rings[-1]))

    coll = bpy.data.collections.get(COLL_NAME)
    if coll:
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        coll = bpy.data.collections.new(COLL_NAME)
        bpy.context.scene.collection.children.link(coll)

    me = bpy.data.meshes.new("BLOCK_986_approx")
    me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new("BLOCK_986_approx", me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    ob.color = (0.35, 0.50, 0.42, 1.0)   # opaque, distinct from the grey cage; set alpha < 1 for see-through
    ob["statev_underlay"] = True
    ob["note"] = ("approx volume: side silhouette + plan half-width + front/rear section, all from CC-BY "
                  "blueprints (+-30 mm). NOT the real surface; no flanges/clearances from this")

    od = DIMS["tire_od"][0]; wb = DIMS["wheelbase"][0]
    tf, tr = DIMS["track_front"][0] / 2.0, DIMS["track_rear"][0] / 2.0
    for name, x, y, tw in (("FL", 0, tf, DIMS["tire_w_front"][0]), ("FR", 0, -tf, DIMS["tire_w_front"][0]),
                           ("RL", -wb, tr, DIMS["tire_w_rear"][0]), ("RR", -wb, -tr, DIMS["tire_w_rear"][0])):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm(od / 2 + ARCH_GAP), depth=mm(tw + ARCH_EXTRA_W),
                                            location=(mm(x), mm(y), mm(od / 2)), vertices=48)
        cyl = bpy.context.active_object
        cyl.name = f"_arch_cutter_{name}"; cyl.rotation_euler = (math.radians(90), 0, 0)
        for cc in cyl.users_collection:
            cc.objects.unlink(cyl)
        coll.objects.link(cyl)
        mod = ob.modifiers.new(f"arch_{name}", "BOOLEAN")
        mod.operation = "DIFFERENCE"; mod.object = cyl; mod.solver = "EXACT"
        cyl.hide_viewport = True; cyl.hide_render = True

    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    for o in [o for o in coll.objects if o.name.startswith("_arch_cutter_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    ob.display_type = "SOLID"
    bpy.ops.object.shade_smooth()
    dims = [round(v * 1000) for v in ob.dimensions]
    print(f"UNDERLAY_986 rebuilt: {len(verts)} verts, {len(faces)} faces, dims (mm) {dims}")
    return ob


build()
