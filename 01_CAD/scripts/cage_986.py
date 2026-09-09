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
    # donor — published (Porsche workshop manual Group 0a "Dimensions and weights", 1996/1999 editions)
    "wheelbase":        (2415, "published"),
    "length_oem":       (4315, "published"),  # RoW; USA bumpers 4340
    "width_oem":        (1780, "published"),
    "height_oem":       (1290, "published"),
    "track_front":      (1465, "published"),  # 16"/18" wheels; 17" = 1455
    "track_rear":       (1528, "published"),  # 16"; 17" = 1508; 18" = 1504
    "ground_clear_oem": (  95, "published"),  # RoW at permissible gross weight; USA 105
    # donor — from CC-BY blueprint (getoutlines.com, 986 2003 S, scaled on wheelbase; ±15 mm)
    "front_overhang":   (1007, "approx"),     # blueprint 1028 (USA bumper) − (4340−4315)
    "rear_overhang":    ( 893, "approx"),
    "tire_od":          ( 640, "approx"),     # 16" ≈ 632; 17" ≈ 637; 18" 225/40+265/35 ≈ 637–643
    "tire_w_front":     ( 225, "approx"),
    "tire_w_rear":      ( 265, "approx"),
    "cowl_x":           (-420, "approx"),     # windshield base (glass meets hood), x from front axle
    "cowl_z":           ( 970, "approx"),
    "ws_top_x":         (-1055, "approx"),    # windshield header, outer top edge
    "ws_top_z":         (1255, "approx"),
    "hoop_x":           (-1760, "approx"),    # roll hoop tube centre plane
    "hoop_top_z":       (1235, "approx"),
    "door_front_x":     (-440, "approx"),     # door shut line at A-pillar
    "door_rear_x":      (-1635, "approx"),    # door shut line at B-pillar
    "side_intake_x":    (-2080, "approx"),    # leading edge of side intake (trailing edge ≈ -1900; z ≈ 535–700)
    # donor — TODO until scan
    "hoop_y":           ( 380, "TODO"),       # tube lateral offset; body screw points below are wider
    # donor — published structure points (workshop manual Group 5 "Structure dimensions", p. 5-11..5-13)
    "rollbar_mount_front_y_total": (1132.0, "published"),   # P10 L–R, roll-over bar front screw points (M8)
    "rollbar_mount_rear_y_total":  (1104.5, "published"),   # P13 L–R, roll-over bar rear screw points (M8)
    "softtop_pos_point_y_total":   ( 954.5, "published"),   # P21 L–R, convertible-top positioning points (M6)
    "softtop_lock_y_total":        (1110.0, "published"),   # P22 L–R, convertible-top lock points (M6)
    "jack_front_y_total":          (1330.0, "published"),   # P8 L–R
    "jack_rear_y_total":           (1375.0, "published"),   # P11 L–R
    "jack_front_to_rear_x":        (1375.0, "published"),   # P8 → P11 longitudinal
    # STATEV 001 targets (design envelope)
    "target_length":    (4400, "target"),
    "target_width":     (1850, "target"),
    "target_height":    (1260, "target"),
    "target_clearance": ( 120, "target"),
    "oem_buffer":       (  18, "target"),   # air to any OEM structure until scanned
}

# Side-view blueprint (CC BY 4.0, getoutlines.com) — pixel calibration measured 2026-09-09:
# rear wheel centre px (220, 237), front wheel centre px (801.5, 237), ground row 314, image 1055×321.
BLUEPRINT_SIDE = {
    "path": "04_ENGINEERING/reference/getoutlines_986_2003_ccby.gif",
    "px_front_wc": (801.5, 237.0),
    "px_rear_wc":  (220.0, 237.0),
    "px_ground_row": 314.0,
    "px_size": (1055, 321),
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


def add_blueprint_side(coll, y_plane=-1.0, alpha=0.6):
    """Side-view blueprint as an image empty in the XZ plane, scaled so wheel centres match the cage."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) if "__file__" in globals() else None
    cand = [BLUEPRINT_SIDE["path"]]
    if root:
        cand.insert(0, os.path.join(root, BLUEPRINT_SIDE["path"]))
    if bpy.data.filepath:
        cand.append(os.path.join(os.path.dirname(bpy.data.filepath), BLUEPRINT_SIDE["path"]))
    path = next((c for c in cand if os.path.exists(c)), None)
    if not path:
        print("blueprint not found:", cand); return None
    img = bpy.data.images.load(path, check_existing=True)
    fx, fz = BLUEPRINT_SIDE["px_front_wc"]; rx, _ = BLUEPRINT_SIDE["px_rear_wc"]
    w_px, h_px = BLUEPRINT_SIDE["px_size"]
    s_mm = DIMS["wheelbase"][0] / (fx - rx)                      # mm per pixel
    ob = bpy.data.objects.new("BLUEPRINT_side_ccby", None)
    ob.empty_display_type = "IMAGE"; ob.data = img
    ob.empty_display_size = mm(w_px * s_mm)                      # image width in metres
    ob.empty_image_offset = (0.0, 0.0)                           # origin = bottom-left pixel corner
    ob.use_empty_image_alpha = True; ob.color = (1, 1, 1, alpha)
    ob.empty_image_side = "DOUBLE_SIDED"; ob.show_empty_image_perspective = True  # visible in any view
    ob.rotation_euler = (math.radians(90), 0, 0)                 # local X → +X (forward), local Y → +Z (up)
    x0 = mm(-fx * s_mm)                                          # pixel column 0 → world x
    z0 = mm(-(h_px - BLUEPRINT_SIDE["px_ground_row"]) * s_mm)    # bottom pixel row → world z (below ground)
    ob.location = (x0, y_plane, z0)
    coll.objects.link(ob)
    ob["statev_cage"] = True; ob["note"] = f"CC BY 4.0 getoutlines.com; {s_mm:.3f} mm/px; wheel centres calibrated"
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
    ws = make_line("WINDSHIELD_centreline", c_hard, cowl, top, RED)
    tag(ws, "cowl_x", "FIXED element; x/z from blueprint (±15 mm) until scan")
    hy = d("hoop_y")
    for s, y in (("L", hy), ("R", -hy)):
        h = make_line(f"ROLLHOOP_{s}", c_hard, (d("hoop_x"), y, 0.6), (d("hoop_x"), y, d("hoop_top_z")), RED)
        tag(h, "hoop_x", "FIXED element; x/z from blueprint, y TODO (body mounts: 1132/1104.5 total)")
    for s, y in (("L", 1), ("R", -1)):
        for nm, key in (("DOOR_FRONT", "door_front_x"), ("DOOR_REAR", "door_rear_x")):
            ln = make_line(f"{nm}_{s}", c_hard, (d(key), y * W / 2, 0.35), (d(key), y * W / 2, 0.95), RED)
            tag(ln, key, "door shut line — FIXED; from blueprint (±15 mm)")
    si = make_empty("SIDE_INTAKE_L", c_hard, (d("side_intake_x"), W / 2, 0.62), 0.1)
    tag(si, "side_intake_x", "functional engine intake leading edge; z 535–700; keep ahead of rear wheel")
    si2 = make_empty("SIDE_INTAKE_R", c_hard, (d("side_intake_x"), -W / 2, 0.62), 0.1)
    tag(si2, "side_intake_x", "functional engine intake leading edge; z 535–700; keep ahead of rear wheel")

    # --- side-view blueprint underlay
    add_blueprint_side(c_env)

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
