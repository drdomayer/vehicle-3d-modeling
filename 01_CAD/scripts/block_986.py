"""
block_986.py — approximate 3D volume of the Porsche 986 donor for use as an underlay.

Built from: side silhouette of the CC-BY blueprint (04_ENGINEERING/reference/
getoutlines_986_2003_ccby.gif, calibrated in cage_986.py) × published width (1780)
× an ASSUMED plan-view taper × rounded (superellipse) cross-sections. Wheel arches
are cut with cylinders around the cage wheel centres.

Accuracy: side profile ±15 mm; width/plan/sections are assumptions, ±30–50 mm.
This is a VOLUME underlay for design. It is NOT the donor's real surface and must
never be used for flanges, mounting points or clearances — that is the scan's job.

Run after cage_986.py (needs DIMS/BLUEPRINT_SIDE). Re-running rebuilds UNDERLAY_986.
"""

import bpy
import math
import os
import numpy as np

# --- pull calibration + dims from the cage script (single source of truth)
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None
_cage = os.path.join(_here, "cage_986.py") if _here else "/Users/miroslavstatev/vehicle-3d-modeling/01_CAD/scripts/cage_986.py"
_ns = {}
with open(_cage, "r", encoding="utf-8") as f:
    src = f.read().split("# ---------------------------------------------------------------- helpers")[0]
exec(src, _ns)
DIMS, BLUEPRINT_SIDE = _ns["DIMS"], _ns["BLUEPRINT_SIDE"]

COLL_NAME = "UNDERLAY_986"

# --- assumptions (mm) — edit here, not in the mesh
FLOOR_Z = 130            # flat underside of the body block
BELTLINE_ROW_CLAMP = 88  # blueprint pixel row: nothing above this between cowl and rear deck (cabin cut)
HALF_W_MAX = DIMS["width_oem"][0] / 2.0
HALF_W_REAR_END = 720    # half-width at the rear bumper face
HALF_W_NOSE_END = 640    # half-width at the front bumper face
TAPER_REAR_PX = 190      # taper length behind the rear wheel, px
TAPER_NOSE_PX = 230      # taper length ahead of the front wheel, px
SECTION_EXP = 2.6        # superellipse exponent: 2 = ellipse, >2 = squarer
TUMBLEHOME = 0.90        # top width / max width
ARCH_GAP = 45            # radial gap tyre → arch, mm
ARCH_EXTRA_W = 120       # arch width beyond tyre width, mm
STEP_PX = 4              # section spacing, px
N_AROUND = 28            # points per half-section (both sides mirrored)


def mm(v):
    return v / 1000.0


def load_silhouette():
    path = None
    cands = [os.path.join(os.path.dirname(os.path.dirname(_here)), BLUEPRINT_SIDE["path"])] if _here else []
    cands.append(os.path.join("/Users/miroslavstatev/vehicle-3d-modeling", BLUEPRINT_SIDE["path"]))
    for c in cands:
        if os.path.exists(c):
            path = c
            break
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    grey = px[..., :3].mean(axis=2)
    dark = grey < 0.5
    dark = dark[::-1, :]  # Blender rows are bottom-up → flip to image row order (top-down)
    top = np.full(w, -1); bot = np.full(w, -1)
    for c in range(w):
        rows = np.where(dark[:, c])[0]
        if rows.size:
            top[c], bot[c] = rows.min(), rows.max()
    return w, h, top, bot


def smooth(a, k=9):
    ker = np.ones(k) / k
    pad = np.pad(a, (k // 2, k // 2), mode="edge")
    return np.convolve(pad, ker, mode="valid")


def build():
    w_px, h_px, top, bot = load_silhouette()
    fx, _ = BLUEPRINT_SIDE["px_front_wc"]; rx, _ = BLUEPRINT_SIDE["px_rear_wc"]
    gr = BLUEPRINT_SIDE["px_ground_row"]
    s_mm = DIMS["wheelbase"][0] / (fx - rx)

    def px_to_x(c):  # mm, x from front axle
        return (c - fx) * s_mm

    def row_to_z(r):  # mm above ground
        return (gr - r) * s_mm

    valid = np.where(top >= 0)[0]
    c0, c1 = int(valid.min()), int(valid.max())

    # cabin clamp: from just behind the hoops to the cowl → cut everything above the beltline
    cowl_c = fx + DIMS["cowl_x"][0] / s_mm
    hoop_c = fx + DIMS["hoop_x"][0] / s_mm
    topc = top.astype(float).copy()
    for c in range(c0, c1 + 1):
        if hoop_c - 40 <= c <= cowl_c:
            topc[c] = max(topc[c], BELTLINE_ROW_CLAMP)
    topc = smooth(topc[c0:c1 + 1], 7)

    # plan-view half-width (assumed)
    def half_w(c):
        rear_start = rx - TAPER_REAR_PX
        nose_start = fx + TAPER_NOSE_PX
        if c <= rear_start:
            t = (c - c0) / max(1.0, rear_start - c0)
            return HALF_W_REAR_END + (HALF_W_MAX - HALF_W_REAR_END) * (0.5 - 0.5 * math.cos(math.pi * t))
        if c >= nose_start:
            t = (c1 - c) / max(1.0, c1 - nose_start)
            return HALF_W_NOSE_END + (HALF_W_MAX - HALF_W_NOSE_END) * (0.5 - 0.5 * math.cos(math.pi * t))
        return HALF_W_MAX

    verts, faces = [], []
    ring_ids = []
    cols = list(range(c0 + 2, c1 - 1, STEP_PX))
    for c in cols:
        z_top = row_to_z(topc[c - c0])
        z_bot = FLOOR_Z
        if z_top < z_bot + 40:
            z_top = z_bot + 40
        hw = half_w(c)
        x = mm(px_to_x(c))
        zc = (z_top + z_bot) / 2.0
        zh = (z_top - z_bot) / 2.0
        ring = []
        # superellipse around (y, z) from bottom-left, over the top, to bottom-right (open at the floor)
        for i in range(N_AROUND + 1):
            t = math.pi * i / N_AROUND  # 0 → π
            cs, sn = math.cos(t), math.sin(t)
            y = -hw * math.copysign(abs(cs) ** (2 / SECTION_EXP), cs)
            z = zc + zh * math.copysign(abs(sn) ** (2 / SECTION_EXP), sn)
            # tumblehome: narrow toward the top
            k = 1.0 - (1.0 - TUMBLEHOME) * max(0.0, (z - z_bot) / (z_top - z_bot))
            ring.append(len(verts)); verts.append((x, mm(y * k), mm(z)))
        # floor edge points to close the section
        ring.append(len(verts)); verts.append((x, mm(hw), mm(z_bot)))
        ring.append(len(verts)); verts.append((x, mm(-hw), mm(z_bot)))
        ring_ids.append(ring)

    n = len(ring_ids[0])
    for a, b in zip(ring_ids[:-1], ring_ids[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(ring_ids[0][::-1]))
    faces.append(tuple(ring_ids[-1]))

    # --- collection
    coll = bpy.data.collections.get(COLL_NAME)
    if coll:
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        coll = bpy.data.collections.new(COLL_NAME)
        bpy.context.scene.collection.children.link(coll)

    me = bpy.data.meshes.new("BLOCK_986_approx")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("BLOCK_986_approx", me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    ob.color = (0.55, 0.6, 0.65, 0.35)
    ob["statev_underlay"] = True
    ob["note"] = ("approx volume: side silhouette (CC BY blueprint) x published width x assumed plan/sections; "
                  "+-30-50 mm; NOT the real surface; no flanges/clearances from this")

    # --- wheel arches: boolean cut with cylinders around the cage wheel centres
    od = DIMS["tire_od"][0]
    wb = DIMS["wheelbase"][0]
    tf, tr = DIMS["track_front"][0] / 2.0, DIMS["track_rear"][0] / 2.0
    for name, x, y, tw in (("FL", 0, tf, DIMS["tire_w_front"][0]), ("FR", 0, -tf, DIMS["tire_w_front"][0]),
                           ("RL", -wb, tr, DIMS["tire_w_rear"][0]), ("RR", -wb, -tr, DIMS["tire_w_rear"][0])):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm(od / 2 + ARCH_GAP), depth=mm(tw + ARCH_EXTRA_W),
                                            location=(mm(x), mm(y), mm(od / 2)), vertices=48)
        cyl = bpy.context.active_object
        cyl.name = f"_arch_cutter_{name}"
        cyl.rotation_euler = (math.radians(90), 0, 0)
        for c in cyl.users_collection:
            c.objects.unlink(cyl)
        coll.objects.link(cyl)
        mod = ob.modifiers.new(f"arch_{name}", "BOOLEAN")
        mod.operation = "DIFFERENCE"; mod.object = cyl; mod.solver = "EXACT"
        cyl.hide_viewport = True; cyl.hide_render = True

    # apply booleans so the object is a plain mesh; remove cutters
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
