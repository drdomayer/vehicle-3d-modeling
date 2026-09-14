"""
statev_skeleton.py — STATEV 001 master surface skeleton v0.1 (design spec, not production CAD).

Builds the 15 master cross-sections S00–S14, longitudinal rails through them, and placeholder
envelopes for every discrete element of the v0.1 dimensional specification. Nothing here is a
surface: sections are curves, elements are wireframe boxes. Loft only after the wireframe is
judged correct (owner's call), per the agreed pipeline:
    sections -> rails -> visual check -> loft -> panel split -> thicken -> STL.

COORDINATES — the spec was written with +X toward the rear; this repo uses +X FORWARD
(see CLAUDE.md and cage_986.py). Every spec X is negated on import: x_repo = -x_spec.
Each object carries `spec_x_mm` so the original number stays traceable.
Y: repo +Y = LEFT (spec used +Y = right). Geometry is symmetric, so only the _L/_R naming differs.

Run after cage_986.py. Re-running rebuilds the STATEV_001 collection tree.
Status of every number: "spec" = from the v0.1 package, "derived" = computed here,
"PLACED" = position not given in the spec, chosen here and flagged for the owner.
"""

import bpy

COLL_ROOT = "STATEV_001"

# ---------------------------------------------------------------- package targets (mm)
PACKAGE = {
    "wheelbase": 2415,
    "length": 4370,
    "width_max_rear": 1850,
    "width_max_front": 1800,
    "height": 1285,
    "ground_clearance": 120,
    "front_overhang": 950,          # spec X of the front tip, negated -> repo +950
    "rear_overhang": 1005,
    "tyre_front": "235/35R19",
    "tyre_front_od": 647,
    "tyre_rear": "275/35R19",
    "tyre_rear_od": 675,
}

# ---------------------------------------------------------------- master cross-sections
# name: (spec_x, role, [(z, half_width_y), ...] bottom -> top)
SECTIONS = {
    "S00": (-950, "front tip",        [(120, 120), (250, 280), (350, 350), (450, 300)]),
    "S01": (-850, "front mask",       [(120, 300), (250, 470), (350, 550), (450, 580), (550, 500)]),
    "S02": (-700, "headlights",       [(120, 500), (250, 650), (400, 720), (550, 700), (650, 600)]),
    "S03": (-500, "front fender in",  [(120, 650), (250, 780), (400, 820), (550, 810), (700, 700)]),
    "S04": (-250, "ahead of arch",    [(120, 720), (250, 830), (400, 870), (550, 850), (700, 720)]),
    "S05": (0,    "FRONT AXLE",       [(120, 730), (250, 850), (400, 900), (550, 860), (700, 720)]),
    "S06": (350,  "behind front arch",[(120, 720), (250, 820), (400, 850), (550, 830), (700, 700)]),
    "S07": (800,  "door centre",      [(120, 700), (250, 800), (400, 850), (550, 875), (700, 820), (800, 700)]),
    "S08": (1200, "side intake start",[(120, 700), (250, 800), (400, 860), (550, 880), (700, 820), (800, 700)]),
    "S09": (1600, "side intake deep", [(120, 720), (250, 830), (400, 900), (550, 915), (700, 850), (800, 720)]),
    "S10": (2000, "rear haunch start",[(120, 730), (250, 850), (400, 900), (550, 925), (700, 920), (800, 850), (900, 700)]),
    "S11": (2415, "REAR AXLE",        [(120, 750), (250, 870), (400, 915), (550, 925), (700, 900), (800, 820), (900, 700)]),
    "S12": (2800, "behind rear wheel",[(120, 720), (250, 850), (400, 900), (550, 900), (700, 820), (800, 700), (900, 550)]),
    "S13": (3200, "rear fascia",      [(120, 650), (250, 780), (400, 820), (550, 780), (650, 650), (750, 500)]),
    "S14": (3420, "rear tip",         [(120, 350), (250, 500), (400, 550), (500, 450), (600, 300)]),
}

RAIL_LEVELS = [120, 250, 400, 550, 700, 800, 900]

# ---------------------------------------------------------------- discrete elements
# name: (collection, spec_x_centre, y_centre, z_centre, size_x, size_y, size_z, status, note)
# y_centre None -> mirrored pair is built at ±|y|
BOXES = [
    # --- lighting
    ("HEADLIGHT",   "04_LIGHTING", -700,  570,  570,  100,  650,   65, "spec",
     "housing; 650 along Y, 100 depth, 65 high. Earlier note said depth 110-140 - conflict, using 100"),
    ("DRL",         "04_LIGHTING", -700,  570,  600,   12,  570,   14, "spec",
     "light blade; 570 long, 14 high, 12 deep"),
    ("PROJECTOR",   "04_LIGHTING", -700,  420,  570,   75,  290,   80, "spec",
     "E-marked module cavity inside the housing, 290x80x75; Y PLACED at the inner end of the housing"),
    ("TAIL",        "04_LIGHTING", 3200,  620,  650,   50,  480,   40, "PLACED",
     "L-shape 400 horizontal + 120 vertical; spec gives no X/Y/Z - put on the S13 shoulder"),
    # --- front
    ("FRONT_MASK",  "02_BODY",     -870,    0,  310,  100,  650,  150, "spec", "mask panel envelope"),
    ("RAD_INTAKE",  "02_BODY",     -830,    0,  320,  140,  560,  140, "spec",
     "central opening: spec X -900..-760, Y +-280, Z 250..390"),
    ("RAD_DUCT",    "05_MECHANICAL",-755,   0,  320,  150,  500,  100, "spec",
     "duct behind the opening; real radiator position comes from the scan"),
    ("FENDER_CHANNEL","03_AERO",    325,  835,  500,  350,   90,  180, "PLACED",
     "hot-air exit behind the front wheel; spec gives X 150..500 and the section but no Z/Y centre"),
    # --- sides
    ("SIDE_INTAKE", "03_AERO",     1500,  887,  485,  600,   75,  270, "spec",
     "envelope X 1200..1800, Y 850..925, Z 350..620"),
    ("INTAKE_BLADE","03_AERO",     1500,  887,  485,  400,   30,  180, "spec",
     "vertical blade inside the intake, 180 high, 25-35 thick"),
    # --- rear
    ("AERO_FIN",    "03_AERO",     1825,  750,  675,  750,   42,  350, "spec",
     "X 1450..2200, height 350, thickness 35-50; Y given as a 650-850 range - centred at 750"),
    ("ENGINE_COVER","02_BODY",     2400,    0,  790,  800, 1050,  100, "spec", "cover envelope"),
    ("REAR_FASCIA", "02_BODY",     3310,    0,  520,  220, 1500,  500, "derived",
     "between S13 and S14; envelope only"),
    ("DIFFUSER",    "03_AERO",     3145,    0,  240,  550, 1500,  220, "spec",
     "X 2870..3420, width 1500, height 180-250, centre tunnel 500"),
    ("EXHAUST",     "05_MECHANICAL",3220,   65,  430,  200,   95,   95, "spec",
     "twin centre outlet, 90-100 dia, Y +-65"),
]

# repeating features: (name, collection, count, spec_x_start, spec_x_end, y, z, size_x, size_y, size_z, status)
LOUVERS = ("LOUVER", "02_BODY", 8, 2100, 2700, 0, 800, 40, 450, 12, "spec")
DIFFUSER_FINS = ("DIFFUSER_FIN", "03_AERO", 6, 2870, 3420, None, 230, 550, 16, 200, "spec")

# rear deck spine: (spec_x, z)
DECK_SPINE = [(1450, 760), (1900, 800), (2500, 760), (3200, 600)]

SUBCOLLS = ["01_MASTER_SKELETON", "02_BODY", "03_AERO", "04_LIGHTING", "05_MECHANICAL"]


def mm(v):
    return v / 1000.0


def sx(spec_x):
    """spec X (+ = rearward) -> repo X (+ = forward)."""
    return -spec_x


def reset_tree():
    root = bpy.data.collections.get(COLL_ROOT)
    if root:
        for c in list(root.children):
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
        for ob in list(root.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        root = bpy.data.collections.new(COLL_ROOT)
        bpy.context.scene.collection.children.link(root)
    subs = {}
    for name in SUBCOLLS:
        c = bpy.data.collections.new(name)
        root.children.link(c)
        subs[name] = c
    return root, subs


def poly_curve(name, coll, points_m, color, cyclic=False, bevel=0.0):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points_m) - 1)
    for i, (x, y, z) in enumerate(points_m):
        sp.points[i].co = (x, y, z, 1.0)
    sp.use_cyclic_u = cyclic
    if bevel:
        cu.bevel_depth = bevel
    ob = bpy.data.objects.new(name, cu)
    ob.color = color
    ob.show_in_front = True
    coll.objects.link(ob)
    return ob


def box(name, coll, centre_mm, size_mm, color, note="", status="spec", spec_x=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=[mm(v) for v in centre_mm])
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = tuple(mm(s) for s in size_mm)
    ob.display_type = "WIRE"
    ob.color = color
    ob.show_in_front = True
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    ob["statev_v01"] = True
    ob["status"] = status
    ob["size_mm"] = list(size_mm)
    ob["centre_mm"] = list(centre_mm)
    if spec_x is not None:
        ob["spec_x_mm"] = spec_x
    if note:
        ob["note"] = note
    return ob


def half_width_at(profile, z):
    """Interpolate a section's half-width at height z. Returns None above the section's top."""
    zs = [p[0] for p in profile]
    ys = [p[1] for p in profile]
    if z < zs[0] or z > zs[-1]:
        return None
    for i in range(len(zs) - 1):
        if zs[i] <= z <= zs[i + 1]:
            t = 0.0 if zs[i + 1] == zs[i] else (z - zs[i]) / (zs[i + 1] - zs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


def build():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 1.0

    root, subs = reset_tree()
    CYAN = (0.15, 0.75, 0.85, 1.0)
    YELL = (0.95, 0.75, 0.15, 1.0)
    MAG = (0.85, 0.25, 0.65, 1.0)
    GREEN = (0.35, 0.80, 0.40, 1.0)
    WHITE = (0.90, 0.90, 0.90, 1.0)

    # ---- cross-sections: left side bottom->top, across the top, right side top->bottom
    for name, (spec_x, role, prof) in SECTIONS.items():
        x = mm(sx(spec_x))
        pts = [(x, mm(y), mm(z)) for z, y in prof]                       # left (+Y)
        pts += [(x, mm(-y), mm(z)) for z, y in reversed(prof)]           # right (-Y)
        ob = poly_curve(f"{name}_{role.replace(' ', '_')}", subs["01_MASTER_SKELETON"], pts, CYAN)
        ob["statev_v01"] = True
        ob["status"] = "spec"
        ob["spec_x_mm"] = spec_x
        ob["repo_x_mm"] = sx(spec_x)
        ob["role"] = role
        ob["profile_z_halfwidth_mm"] = [list(p) for p in prof]
        ob["note"] = "open at the floor (underside not specified) and flat across the top of the data"

    # ---- longitudinal rails at constant Z through every section that reaches that height
    order = sorted(SECTIONS.items(), key=lambda kv: kv[1][0])
    for z in RAIL_LEVELS:
        for side, sgn in (("L", 1), ("R", -1)):
            pts = []
            for name, (spec_x, role, prof) in order:
                hw = half_width_at(prof, z)
                if hw is not None:
                    pts.append((mm(sx(spec_x)), mm(sgn * hw), mm(z)))
            if len(pts) > 1:
                ob = poly_curve(f"RAIL_Z{z:04d}_{side}", subs["01_MASTER_SKELETON"], pts, YELL)
                ob["statev_v01"] = True
                ob["status"] = "derived"
                ob["z_mm"] = z
                ob["sections"] = len(pts)

    # ---- rear deck spine (centreline)
    ob = poly_curve("DECK_SPINE", subs["02_BODY"],
                    [(mm(sx(x)), 0.0, mm(z)) for x, z in DECK_SPINE], GREEN)
    ob["statev_v01"] = True
    ob["status"] = "spec"
    ob["points_specx_z_mm"] = [list(p) for p in DECK_SPINE]

    # ---- discrete element envelopes
    colors = {"02_BODY": WHITE, "03_AERO": MAG, "04_LIGHTING": YELL, "05_MECHANICAL": GREEN}
    for (nm, coll, spec_x, y, z, sxx, sy, sz, status, note) in BOXES:
        c = subs[coll]
        col = colors[coll]
        if y in (0, None):
            box(nm, c, (sx(spec_x), 0, z), (sxx, sy, sz), col, note, status, spec_x)
        else:
            for suffix, sgn in (("_L", 1), ("_R", -1)):
                box(nm + suffix, c, (sx(spec_x), sgn * abs(y), z), (sxx, sy, sz), col, note, status, spec_x)

    # ---- louvers in the rear deck
    nm, coll, n, x0, x1, y, z, sxx, sy, sz, status = LOUVERS
    step = (x1 - x0) / (n - 1)
    for i in range(n):
        spec_x = x0 + i * step
        box(f"{nm}_{i+1:02d}", subs[coll], (sx(spec_x), y, z), (sxx, sy, sz), WHITE,
            "real opening, follows the deck curve once lofted", status, round(spec_x, 1))

    # ---- diffuser fins
    nm, coll, n, x0, x1, _, z, sxx, sy, sz, status = DIFFUSER_FINS
    spec_x = (x0 + x1) / 2.0
    spacing = 150
    for i in range(n):
        y = (i - (n - 1) / 2.0) * spacing
        box(f"{nm}_{i+1:02d}", subs[coll], (sx(spec_x), y, z), (sxx, sy, sz), MAG,
            "5-7 fins, 120-180 spacing; centre tunnel 500 wide", status, spec_x)

    # ---- STATEV 19" wheels at the DONOR track (spec's Y hub numbers are not usable — see check script)
    import math
    for nm, spec_x, od, wdt, half_track in (
        ("WHEEL_F", 0, PACKAGE["tyre_front_od"], 235, 732.5),
        ("WHEEL_R", 2415, PACKAGE["tyre_rear_od"], 275, 764.0),
    ):
        for suffix, sgn in (("_L", 1), ("_R", -1)):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=mm(od / 2), depth=mm(wdt), vertices=48,
                location=(mm(sx(spec_x)), mm(sgn * half_track), mm(od / 2)))
            w = bpy.context.active_object
            w.name = nm + suffix
            w.rotation_euler = (math.radians(90), 0, 0)
            w.display_type = "WIRE"
            w.color = WHITE
            w.show_in_front = True
            for c in w.users_collection:
                c.objects.unlink(w)
            subs["05_MECHANICAL"].objects.link(w)
            w["statev_v01"] = True
            w["status"] = "derived"
            w["note"] = ("STATEV 19in tyre at the DONOR track (1465/1528). The v0.1 spec's hub Y of "
                         "875/900 would need a +285/+272 mm wider track — not possible on the 986.")

    n_obj = len(root.all_objects)
    print(f"{COLL_ROOT} rebuilt: {n_obj} objects | {len(SECTIONS)} sections, "
          f"{len(RAIL_LEVELS)} rail levels | spec X negated to repo X (+X forward)")
    return root


build()
