"""
cage_986.py — regenerable hardpoint cage for the Porsche 986 donor (STATEV 001).

Run inside Blender (Text Editor → Run Script) or via Blender MCP execute_code.
Re-running deletes and rebuilds the CAGE_986 collection. Never hand-edit cage objects.

Axis convention:  X = forward,  Y = left,  Z = up.  Units: metres in Blender.
Origin:           front-axle centre projected on the ground (Z = 0 = road).

Status of every number is in DIMS: "published" | "approx" | "TODO".
Replace approx/TODO values after the blueprint (the-blueprints.com, 986 2002)
and, finally, the scan of the real car. Keep the dict as the single source of truth.
"""

import bpy
import math

# ---------------------------------------------------------------- dimensions (mm)
DIMS = {
    # donor — published
    "wheelbase":        (2416, "published"),
    "length_oem":       (4321, "published"),
    "width_oem":        (1781, "published"),
    "height_oem":       (1290, "published"),
    # donor — approximate, verify on blueprint / scan
    "front_overhang":   (1035, "approx"),
    "rear_overhang":    ( 870, "approx"),
    "track_front":      (1465, "approx"),
    "track_rear":       (1528, "approx"),
    "tire_od":          ( 640, "approx"),   # 18" 225/40 + 265/35 ≈ 637–643
    "tire_w_front":     ( 225, "approx"),
    "tire_w_rear":      ( 265, "approx"),
    "ground_clear_oem": ( 150, "approx"),
    # windshield / hoops — TODO until blueprint + scan
    "cowl_x":           (-1180, "TODO"),    # windshield base, x from front axle (negative = rearward)
    "cowl_z":           (  930, "TODO"),
    "ws_top_x":         (-1620, "TODO"),
    "ws_top_z":         ( 1240, "TODO"),
    "hoop_x":           (-1950, "TODO"),    # roll hoop centre plane
    "hoop_top_z":       ( 1150, "TODO"),
    "hoop_y":           (  380, "TODO"),    # lateral offset of each hoop from centreline
    "side_intake_x":    (-2000, "TODO"),    # leading edge of side intake
    # STATEV 001 targets (design envelope)
    "target_length":    (4400, "target"),
    "target_width":     (1850, "target"),
    "target_height":    (1260, "target"),
    "target_clearance": ( 120, "target"),
    "oem_buffer":       (  18, "target"),   # air to any OEM structure until scanned
}

COLL_NAME = "CAGE_986"


def mm(v):
    return v / 1000.0


def d(key):
    return mm(DIMS[key][0])


# ---------------------------------------------------------------- helpers
def get_or_reset_collection(name):
    coll = bpy.data.collections.get(name)
    if coll:
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for child in list(coll.children):
            for ob in list(child.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(child)
    else:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def sub_collection(parent, name):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


def link_only(ob, coll):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)


def tag(ob, key=None, note=""):
    ob["statev_cage"] = True
    if key:
        ob["source_status"] = DIMS[key][1]
    if note:
        ob["note"] = note


def make_box(name, coll, center, size, color, wire=True):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0], size[1], size[2])
    ob.display_type = "WIRE" if wire else "SOLID"
    ob.color = color
    ob.show_in_front = True
    link_only(ob, coll)
    return ob


def make_wheel(name, coll, x, y, od, width, color, z=None):
    """Cylinder with axis along Y. z defaults to od/2 (tyre on the ground); pass z
    explicitly for rings that must stay concentric with the wheel centre."""
    if z is None:
        z = od / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=od / 2, depth=width, location=(x, y, z))
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = (math.radians(90), 0, 0)  # axis along Y
    ob.display_type = "WIRE"
    ob.color = color
    ob.show_in_front = True
    link_only(ob, coll)
    return ob


def make_empty(name, coll, loc, size=0.15):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = size
    ob.location = loc
    coll.objects.link(ob)
    return ob


def make_line(name, coll, p1, p2, color):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([p1, p2], [(0, 1)], [])
    ob = bpy.data.objects.new(name, mesh)
    ob.color = color
    ob.show_in_front = True
    coll.objects.link(ob)
    return ob


# ---------------------------------------------------------------- build
def build():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 1.0

    root = get_or_reset_collection(COLL_NAME)
    c_wheels = sub_collection(root, "wheels")
    c_env = sub_collection(root, "envelopes")
    c_hard = sub_collection(root, "hardpoints_TODO")

    GREY = (0.6, 0.6, 0.6, 1.0)
    ORANGE = (0.85, 0.35, 0.19, 1.0)
    RED = (0.9, 0.2, 0.2, 1.0)

    wb = d("wheelbase")
    fo = d("front_overhang")
    ro = d("rear_overhang")
    od = d("tire_od")

    # --- ground line (X axis from front bumper to rear bumper)
    make_line("ground_ref", c_env, (fo, 0, 0), (-(wb + ro), 0, 0), GREY)

    # --- wheels (tyre outer diameter cylinders)
    tf, tr = d("track_front") / 2, d("track_rear") / 2
    make_wheel("wheel_FL", c_wheels, 0.0, tf, od, d("tire_w_front"), GREY)
    make_wheel("wheel_FR", c_wheels, 0.0, -tf, od, d("tire_w_front"), GREY)
    make_wheel("wheel_RL", c_wheels, -wb, tr, od, d("tire_w_rear"), GREY)
    make_wheel("wheel_RR", c_wheels, -wb, -tr, od, d("tire_w_rear"), GREY)
    for n in ("FL", "FR", "RL", "RR"):
        tag(bpy.data.objects[f"wheel_{n}"], "tire_od", "wheel centre is FIXED")

    # --- OEM envelope box (published outer dimensions)
    L, W, H = d("length_oem"), d("width_oem"), d("height_oem")
    gc = d("ground_clear_oem")
    cx = fo - L / 2
    oem = make_box("ENV_986_OEM", c_env, (cx, 0, gc + (H - gc) / 2), (L, W, H - gc), GREY)
    tag(oem, "length_oem", "published outer box; overhang split is approx")

    # --- STATEV 001 target envelope
    Lt, Wt, Ht = d("target_length"), d("target_width"), d("target_height")
    gct = d("target_clearance")
    # keep same rear overhang, grow the nose (assumption — adjust in design)
    cxt = (-(wb + ro) + Lt / 2)
    tgt = make_box("ENV_STATEV_001_TARGET", c_env, (cxt, 0, gct + (Ht - gct) / 2), (Lt, Wt, Ht - gct), ORANGE)
    tag(tgt, "target_length", "design envelope target, not a limit")

    # --- wheel-centre empties + clearance rings (tire OD + 2*buffer)
    buf = d("oem_buffer")
    for name, x, y in (("FL", 0, tf), ("FR", 0, -tf), ("RL", -wb, tr), ("RR", -wb, -tr)):
        e = make_empty(f"WC_{name}", c_hard, (x, y, od / 2), 0.12)
        tag(e, "wheelbase", "wheel centre — FIXED hardpoint")
        ring = make_wheel(f"clearance_{name}", c_hard, x, y, od + 2 * buf, (d("tire_w_rear") if "R" in name[0] else d("tire_w_front")) + 2 * buf, RED, z=od / 2)
        ring.display_type = "WIRE"
        tag(ring, "oem_buffer", "static tyre + buffer; NOT full suspension travel/steer envelope")

    # --- windshield / hoops placeholders (TODO — from blueprint & scan)
    cowl = (d("cowl_x"), 0, d("cowl_z"))
    top = (d("ws_top_x"), 0, d("ws_top_z"))
    ws = make_line("WINDSHIELD_centreline_TODO", c_hard, cowl, top, RED)
    tag(ws, "cowl_x", "FIXED element, position TODO")
    hy = d("hoop_y")
    for s, y in (("L", hy), ("R", -hy)):
        h = make_line(f"ROLLHOOP_{s}_TODO", c_hard, (d("hoop_x"), y, 0.6), (d("hoop_x"), y, d("hoop_top_z")), RED)
        tag(h, "hoop_x", "FIXED element, position TODO")
    si = make_empty("SIDE_INTAKE_L_TODO", c_hard, (d("side_intake_x"), W / 2, 0.55), 0.1)
    tag(si, "side_intake_x", "functional engine intake; keep ahead of rear wheel")
    si2 = make_empty("SIDE_INTAKE_R_TODO", c_hard, (d("side_intake_x"), -W / 2, 0.55), 0.1)
    tag(si2, "side_intake_x", "functional engine intake; keep ahead of rear wheel")

    # --- headlamp minimum height reference plane (legal: >= 500 mm centre)
    hl = make_box("HEADLAMP_MIN_500mm_plane", c_hard, (fo - 0.3, 0, 0.5), (0.6, Wt, 0.002), RED)
    tag(hl, None, "legal: headlamp centre must be at or above this plane")

    # --- summary in custom props on the root object
    summ = make_empty("CAGE_INFO", root, (0, 0, 0), 0.3)
    for k, (v, st) in DIMS.items():
        summ[f"{k} [{st}]"] = v
    summ["axis"] = "X fwd, Y left, Z up; origin = front axle on ground"

    print("CAGE_986 rebuilt. TODO items:", [k for k, (_, s) in DIMS.items() if s == "TODO"])


build()
