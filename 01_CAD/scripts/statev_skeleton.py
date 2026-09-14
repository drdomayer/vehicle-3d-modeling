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
PFX = "STATEV_"          # every object this script owns carries it (prompt §6, §9)

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

# wheel arch apertures (msg1 §4): key -> (spec_x, radius, opening_width_y, tyre_od, tyre_width)
# radius is measured from the wheel centre; opening width is the axial size of the aperture.
ARCHES = {
    "FRONT": (0,    350, 350, 647, 235),
    "REAR":  (2415, 365, 370, 675, 275),
}

# diffuser central tunnel (msg1 §18): width 500 inside the 1500 wide diffuser
DIFFUSER_TUNNEL = (3145, 0, 230, 550, 500, 220)   # spec_x, y, z, size_x, size_y, size_z

# door character line (msg1 §11): the surface crease, front/middle/rear heights on the door
DOOR_CHAR_LINE_Z = {"front": 420, "middle": 500, "rear": 520}

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
    ("TAIL_H",      "04_LIGHTING", 3200,  620,  650,   50,  400,   40, "PLACED",
     "horizontal arm of the L; spec gives no X/Y/Z - put on the S13 shoulder"),
    ("TAIL_V",      "04_LIGHTING", 3200,  815,  590,   50,   40,  120, "PLACED",
     "vertical arm of the L, at the outboard end of the horizontal arm"),
    # --- front
    ("FRONT_CLAMSHELL", "02_BODY", -400,    0,  450, 1100, 1800,  660, "spec",
     "envelope X -950..150, Y +-900, Z 120..780; the panel itself comes from the loft"),
    ("HOOD",        "02_BODY",     -435,    0,  585, 1030, 1500,  270, "spec",
     "X -950..80, max width 1500, Z 450 at the front edge to 720 at the rear - envelope only"),
    ("FRONT_FENDER","02_BODY",     -200,  875,  490,  900,   50,  480, "spec",
     "X -650..250, Y 850..900, Z 250..730; a shell, not a flare over the OEM fender"),
    ("FRONT_MASK",  "02_BODY",     -870,    0,  310,  100,  650,  150, "spec", "mask panel envelope"),
    ("RAD_INTAKE",  "02_BODY",     -830,    0,  320,  140,  560,  140, "spec",
     "central opening: spec X -900..-760, Y +-280, Z 250..390"),
    ("RAD_DUCT",    "05_MECHANICAL",-755,   0,  320,  150,  500,  100, "spec",
     "duct behind the opening; real radiator position comes from the scan"),
    ("FENDER_CHANNEL","03_AERO",    325,  835,  500,  350,   90,  180, "PLACED",
     "hot-air exit behind the front wheel; spec gives X 150..500 and the section but no Z/Y centre"),
    # --- sides
    ("DOOR_SKIN",   "02_BODY",     1038,  850,  545, 1050,   30,  650, "spec",
     "spec says 1050 long; the donor door aperture (shut lines) is 1195 long - see check script. "
     "Z centre PLACED: spec only gives the character line at Z 420/500/520"),
    ("REAR_HAUNCH", "02_BODY",     2375,  887,  575,  950,   75,  550, "spec",
     "X 1900..2850, Y 850..925, Z 300..850; loft through 5-7 sections, not one sculpted blob"),
    ("REAR_DECK",   "02_BODY",     2575,    0,  750, 1450, 1850,  200, "spec",
     "X 1850..3300, width 1500..1850, Z 650..850; thin skin, must not box in the engine bay"),
    ("SIDE_INTAKE", "03_AERO",     1500,  887,  485,  600,   75,  270, "spec",
     "sculpted channel, spec envelope X 1200..1800, Y 850..925, Z 350..620 — does NOT reach the "
     "donor opening; see the check script"),
    ("INTAKE_INLET", "03_AERO",    1990,  870,  520,  180,  110,  180, "derived",
     "the DONOR opening: specX 1900..2080 from the side blueprint. This is the mouth that has to "
     "feed the engine; the sculpted channel must run into it"),
    ("INTAKE_DUCT",  "05_MECHANICAL", 2150, 650,  520,  320,  400,  180, "PROVISIONAL",
     "inlet -> engine bay. Path guessed; the real duct route comes from the scan of the engine bay"),
    ("INTAKE_OUTLET","05_MECHANICAL", 2300, 300,  600,  150,  300,  200, "PROVISIONAL",
     "connection to the intake plenum. Position guessed"),
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
DIFFUSER_FINS = ("DIFFUSER_FIN", "03_AERO", 7, 2870, 3420, None, 230, 550, 16, 200, "spec")

# rear deck spine: (spec_x, z)
DECK_SPINE = [(1450, 760), (1900, 800), (2500, 760), (3200, 600)]

SUBCOLLS = ["00_DONOR_HARDPOINTS", "01_MASTER_SKELETON", "02_BODY", "03_AERO",
            "04_LIGHTING", "05_MECHANICAL", "06_ROOF", "07_INTERIOR", "99_DEBUG"]

# Parametric properties carried on the STATEV_001_ROOT empty (prompt §28). Editable; the build
# reads SECTIONS/BOXES, so changing a value here documents intent — rerun the script to apply.
ROOT_PROPS = {
    "wheelbase": 2415, "overall_length": 4370, "rear_width": 1850, "front_width": 1800,
    "target_height": 1285, "ground_clearance": 120,
    "front_track": 1465, "rear_track": 1528,          # donor, published — NOT a design variable
    "front_wheel_diameter": 647, "rear_wheel_diameter": 675,
    "front_tyre_width": 235, "rear_tyre_width": 275,
    "headlight_length": 650, "headlight_height": 65,
    "side_intake_length": 600, "side_intake_height": 220,
    "rear_fin_height": 350, "diffuser_width": 1500, "diffuser_length": 550,
    "exhaust_diameter": 95,
    # rim and offset are design variables; these are typical 986 19" values, PROVISIONAL until the
    # wheels are actually bought and the arch clearance is measured on the car.
    "front_rim": "8.5Jx19", "front_wheel_et": 50,
    "rear_rim": "10Jx19", "rear_wheel_et": 45,
    "wheel_et_status": "PROVISIONAL — ET sets how far the tyre sits inside the arch; verify on the car",
}

# Viewport materials for visualisation only (prompt §26): name -> (rgba, metallic, roughness)
MATERIALS = {
    "STATEV_BODY":     ((0.045, 0.115, 0.075, 1.0), 0.85, 0.25),   # dark metallic green
    "STATEV_WHEELS":   ((0.36, 0.24, 0.10, 1.0), 0.95, 0.35),      # bronze
    "STATEV_INTERIOR": ((0.42, 0.29, 0.17, 1.0), 0.00, 0.65),      # tan leather
    "STATEV_GLASS":    ((0.03, 0.03, 0.04, 0.25), 0.00, 0.05),
    "STATEV_CARBON":   ((0.02, 0.02, 0.02, 1.0), 0.40, 0.35),
    "STATEV_LIGHT":    ((1.0, 0.97, 0.90, 1.0), 0.00, 0.10),       # emissive
}


def donor_dims():
    """DIMS from cage_986.py — the donor hardpoints, published or blueprint-derived."""
    import os
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
        else "/Users/miroslavstatev/vehicle-3d-modeling/01_CAD/scripts"
    ns = {}
    with open(os.path.join(here, "cage_986.py"), "r", encoding="utf-8") as fh:
        head = fh.read().split("# ---------------------------------------------------------------- helpers")[0]
    exec(head.replace("import bpy", ""), ns)
    return {k: v[0] for k, v in ns["DIMS"].items()}


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
    name = name if name.startswith(PFX) else PFX + name
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
    name = name if name.startswith(PFX) else PFX + name
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
        ob = poly_curve(name, subs["01_MASTER_SKELETON"], pts, CYAN)
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
    spacing = 150            # 7 fins x 150 = 900 inside the 1500 wide diffuser
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
            w.name = PFX + nm + suffix
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

    D = donor_dims()

    # ---- wheel arch apertures: two arcs per wheel, at the inboard and outboard edge of the opening
    import math as _a
    for side_key, (spec_x, radius, open_w, tod, twid) in ARCHES.items():
        half_track = (D["track_front"] if side_key == "FRONT" else D["track_rear"]) / 2.0
        for suffix, sgn in (("_L", 1), ("_R", -1)):
            for edge, off in (("in", -open_w / 2), ("out", open_w / 2)):
                pts = []
                for i in range(25):                      # 180 deg over the top, front -> rear
                    a = _a.pi * i / 24
                    pts.append((mm(sx(spec_x) + radius * _a.cos(a)),
                                mm(sgn * (half_track + sgn * 0 + off) if sgn > 0 else sgn * half_track - off),
                                mm(tod / 2 + radius * _a.sin(a))))
                ob = poly_curve(f"ARCH_{side_key}{suffix}_{edge}", subs["02_BODY"], pts,
                                (0.20, 0.70, 0.90, 1.0))
                ob["status"] = "spec"
                ob["spec_x_mm"] = spec_x
                ob["arch_radius_mm"] = radius
                ob["arch_opening_width_mm"] = open_w
                ob["radial_gap_to_tyre_mm"] = round(radius - tod / 2, 1)
                ob["axial_gap_each_side_mm"] = round((open_w - twid) / 2.0, 1)
                ob["note"] = ("wheel arch aperture edge. Radius is from the wheel centre; the tyre "
                              "needs this gap at full bump AND full steer - only the scan settles it")

    # ---- diffuser central tunnel
    tx, ty, tz, tdx, tdy, tdz = DIFFUSER_TUNNEL
    box("DIFFUSER_TUNNEL", subs["03_AERO"], (sx(tx), ty, tz), (tdx, tdy, tdz),
        (0.85, 0.25, 0.65, 1.0),
        "central tunnel, 500 wide inside the 1500 diffuser; the fins sit either side of it",
        "spec", tx)

    # ---- door character line (the crease the spec describes by three heights)
    dc = DOOR_CHAR_LINE_Z
    dfx, drx = -D["door_front_x"], -D["door_rear_x"]          # spec X of the shut lines
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        pts = [(mm(sx(dfx)), mm(sgn * 850), mm(dc["front"])),
               (mm(sx((dfx + drx) / 2)), mm(sgn * 862), mm(dc["middle"])),
               (mm(sx(drx)), mm(sgn * 850), mm(dc["rear"]))]
        ob = poly_curve(f"DOOR_CHAR_LINE{suffix}", subs["02_BODY"], pts, (0.20, 0.70, 0.90, 1.0))
        ob["status"] = "spec"
        ob["heights_mm"] = [dc["front"], dc["middle"], dc["rear"]]
        ob["note"] = ("design crease on the door: Z 420 front, 500 middle, 520 rear. X taken from "
                      "the donor shut lines, Y from the section half-widths")

    # ---- 00_DONOR_HARDPOINTS: pointer only. The cage stays a separate top-level collection so
    #      donor reference geometry is never mixed into STATEV geometry (prompt §27, §33).
    ptr = bpy.data.objects.new(PFX + "DONOR_HARDPOINTS__see_CAGE_986", None)
    ptr.empty_display_type = "SPHERE"
    ptr.empty_display_size = 0.25
    subs["00_DONOR_HARDPOINTS"].objects.link(ptr)
    ptr["note"] = ("Donor hardpoints live in the CAGE_986 collection, rebuilt by cage_986.py. "
                   "Not duplicated here on purpose: one source of truth, never edited by hand.")
    ptr["locked"] = ("windshield frame and rake, A-pillars, header, door glass, door shut lines, "
                     "wheel centres, wheelbase, roll hoops, roof mechanism, side-intake hardpoint")
    for k in ("wheelbase", "track_front", "track_rear", "cowl_x", "cowl_z", "ws_top_x", "ws_top_z",
              "hoop_x", "hoop_top_z", "hoop_y", "door_front_x", "door_rear_x", "side_intake_x"):
        ptr[f"donor_{k}"] = D[k]

    # ---- 06_ROOF: clearance envelopes around the OEM soft top. PROVISIONAL — the fold path and
    #      the clamshell are unknown until the car is scanned; nothing here may be treated as fact.
    roof_boxes = [
        ("ROOF_CLOSED_ENVELOPE",
         (D["ws_top_x"] + D["hoop_x"]) / 2.0, 0, (D["ws_top_z"] + 900) / 2.0,
         abs(D["hoop_x"] - D["ws_top_x"]) + 300, 1400, D["ws_top_z"] - 900,
         "closed soft top between the windshield header and the hoops; the raised deck must meet "
         "this line without a step"),
        ("ROOF_FOLD_ENVELOPE",
         D["hoop_x"] - 260, 0, 850, 520, 1300, 300,
         "stowage volume behind the seats. Size and path are GUESSED - the real fold envelope is "
         "the single most important thing to capture on the scan"),
    ]
    for nm, x, y, z, dx, dy, dz, note in roof_boxes:
        b = box(nm, subs["06_ROOF"], (x, y, z), (dx, dy, dz), (0.95, 0.25, 0.25, 1.0),
                note, "PROVISIONAL")
        b["do_not_trust"] = True

    # ---- 07_INTERIOR: seat centrelines from the measured plan view; cabin fit for 190 cm needs the scan
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        e = bpy.data.objects.new(PFX + f"SEAT_CENTRELINE{suffix}", None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.3
        e.location = (mm(sx(1500)), mm(sgn * 357), mm(500))
        subs["07_INTERIOR"].objects.link(e)
        e["status"] = "derived"
        e["note"] = ("seat centreline +-357 measured on the 4-view plan; X is PLACED. "
                     "Owner is 190 cm - seat travel and headroom are a hard constraint, "
                     "checkable only on the real car")

    # ---- 99_DEBUG: dimension guides and provisional clearance envelopes (prompt §30)
    dbg = subs["99_DEBUG"]
    RED = (0.95, 0.25, 0.25, 1.0)

    def dim_line(name, p0, p1, label):
        ob = poly_curve(name, dbg, [tuple(mm(v) for v in p0), tuple(mm(v) for v in p1)], RED)
        ob["status"] = "derived"
        ob["label"] = label
        cu = bpy.data.curves.new(name + "_TXT", "FONT")
        cu.body = label
        cu.size = 0.06
        t = bpy.data.objects.new(name + "_TXT", cu)
        t.location = tuple(mm((a + b) / 2.0) for a, b in zip(p0, p1))
        t.rotation_euler = (1.5708, 0, 0)
        t.color = RED
        dbg.objects.link(t)
        return ob

    nose, tail = sx(-950), sx(3420)
    dim_line("DIM_length", (nose, 0, -250), (tail, 0, -250), f"length {PACKAGE['length']}")
    dim_line("DIM_wheelbase", (0, 0, -450), (sx(2415), 0, -450), f"wheelbase {PACKAGE['wheelbase']}")
    dim_line("DIM_width_rear", (sx(2415), -925, -250), (sx(2415), 925, -250),
             f"max width {PACKAGE['width_max_rear']}")
    dim_line("DIM_track_front", (0, -D["track_front"] / 2, -150), (0, D["track_front"] / 2, -150),
             f"front track {D['track_front']} (donor)")
    dim_line("DIM_track_rear", (sx(2415), -D["track_rear"] / 2, -350), (sx(2415), D["track_rear"] / 2, -350),
             f"rear track {D['track_rear']} (donor)")
    dim_line("DIM_height", (sx(1760), 1100, 0), (sx(1760), 1100, PACKAGE["height"]),
             f"height {PACKAGE['height']}")
    dim_line("DIM_ground_clearance", (sx(800), 1100, 0), (sx(800), 1100, PACKAGE["ground_clearance"]),
             f"clearance {PACKAGE['ground_clearance']}")

    # steering sweep, worst case: tyre footprint rotated +-35 deg about a vertical axis through the
    # wheel centre. The real kingpin axis is inboard and raked, so this over-states the outboard reach.
    import math as _m
    th = _m.radians(35)
    od, wd = PACKAGE["tyre_front_od"], 235
    swept_x = od * _m.cos(th) + wd * _m.sin(th)
    swept_y = od * _m.sin(th) + wd * _m.cos(th)
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        b = box(f"STEER_SWEEP{suffix}", dbg, (0, sgn * D["track_front"] / 2, od / 2),
                (swept_x + 2 * D["oem_buffer"], swept_y + 2 * D["oem_buffer"], od + 2 * D["oem_buffer"]),
                RED,
                f"worst-case +-35 deg sweep about the wheel centre, +{D['oem_buffer']} mm buffer. "
                "PROVISIONAL: kingpin axis unknown until the scan, so the true outboard reach is less.",
                "PROVISIONAL")
        b["do_not_trust"] = True

    # ---- engine bay and roll-hoop clearance (prompt §30)
    eng = box("ENGINE_BAY_ENVELOPE", dbg, (D["hoop_x"] - 440, 0, 600), (760, 900, 600), RED,
              "mid engine between the hoops and the rear axle. Engine mounts P9 are at Y +-188.5 "
              "(published); the box size around them is GUESSED. Nothing may close this volume in.",
              "PROVISIONAL")
    eng["do_not_trust"] = True
    eng["donor_engine_mount_y_total"] = D["jack_front_y_total"] and 377.0
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        h = box(f"ROLLHOOP_CLEARANCE{suffix}", dbg,
                (D["hoop_x"], sgn * D["hoop_y"], (600 + D["hoop_top_z"]) / 2.0),
                (120 + 2 * D["oem_buffer"], 120 + 2 * D["oem_buffer"],
                 D["hoop_top_z"] - 600 + D["oem_buffer"]), RED,
                "keep-out around the roll hoop tube. Tube diameter not measured yet — 120 mm "
                "assumed plus the standard buffer. The hoops are a locked safety structure.",
                "PROVISIONAL")
        h["do_not_trust"] = True

    # ---- warning objects: recomputed live, so a fixed number makes the marker disappear (prompt §30)
    WARN = (1.0, 0.15, 0.0, 1.0)

    def warn(name, centre, size, text):
        b = box(name, dbg, centre, size, WARN, text, "WARNING")
        b["WARNING"] = True
        cu = bpy.data.curves.new(PFX + name + "_TXT", "FONT")
        cu.body = "! " + text.split(".")[0]
        cu.size = 0.05
        t = bpy.data.objects.new(PFX + name + "_TXT", cu)
        t.location = (mm(centre[0]), mm(centre[1]), mm(centre[2] + size[2] / 2 + 60))
        t.rotation_euler = (1.5708, 0, 0)
        t.color = WARN
        dbg.objects.link(t)
        return b

    n_warn = 0
    # W1 — hub Y
    spec_hub_f = 875
    if abs(spec_hub_f - D["track_front"] / 2) > 5:
        warn("WARN_hub_Y", (0, (spec_hub_f + D["track_front"] / 2) / 2, PACKAGE["tyre_front_od"] / 2),
             (200, spec_hub_f - D["track_front"] / 2, 200),
             f"spec hub Y {spec_hub_f} vs donor {D['track_front']/2:.0f}: needs "
             f"{2*(spec_hub_f - D['track_front']/2):.0f} mm more track, impossible")
        n_warn += 1
    # W2 — headlight beyond the body
    hl = next(b for b in BOXES if b[0] == "HEADLIGHT")
    hl_out = abs(hl[3]) + hl[6] / 2
    body_at = half_width_at(SECTIONS["S02"][2], hl[4])
    if body_at and hl_out > body_at:
        for sgn in (1, -1):
            warn(f"WARN_headlight_{'L' if sgn > 0 else 'R'}",
                 (sx(hl[2]), sgn * (body_at + hl_out) / 2, hl[4]),
                 (hl[5], hl_out - body_at, hl[7]),
                 f"headlight reaches Y {hl_out:.0f}, body is {body_at:.0f} — "
                 f"{hl_out - body_at:.0f} mm outside the surface")
            n_warn += 1
    # W3 — side intake does not reach the donor opening
    si = next(b for b in BOXES if b[0] == "SIDE_INTAKE")
    si_end = si[2] + si[5] / 2
    donor_open = 1900
    if si_end < donor_open:
        for sgn in (1, -1):
            warn(f"WARN_intake_gap_{'L' if sgn > 0 else 'R'}",
                 (sx((si_end + donor_open) / 2), sgn * 870, 520),
                 (donor_open - si_end, 120, 180),
                 f"{donor_open - si_end:.0f} mm gap between the sculpted intake and the real opening — "
                 "as drawn it feeds nothing")
            n_warn += 1
    # W4 — door skin shorter than the aperture
    ds = next(b for b in BOXES if b[0] == "DOOR_SKIN")
    aperture = abs(D["door_rear_x"] - D["door_front_x"])
    if abs(ds[5] - aperture) > 20:
        for sgn in (1, -1):
            warn(f"WARN_door_skin_{'L' if sgn > 0 else 'R'}",
                 (sx(ds[2]), sgn * ds[3], ds[4]), (aperture, 60, ds[7]),
                 f"skin {ds[5]} vs door aperture {aperture:.0f} — {aperture - ds[5]:.0f} mm short of the shut lines")
            n_warn += 1
    # W5 — unassigned strip between hood and cowl
    hd = next(b for b in BOXES if b[0] == "HOOD")
    hd_rear, cowl_spec = hd[2] + hd[5] / 2, -D["cowl_x"]
    if cowl_spec - hd_rear > 50:
        warn("WARN_cowl_strip", (sx((hd_rear + cowl_spec) / 2), 0, D["cowl_z"] - 80),
             (cowl_spec - hd_rear, 1400, 120),
             f"{cowl_spec - hd_rear:.0f} mm between the hood's rear edge and the windshield base "
             "belongs to no panel")
        n_warn += 1
    # W6 — fins ahead of the hoops
    fin = next(b for b in BOXES if b[0] == "AERO_FIN")
    fin_start, hoop_spec = fin[2] - fin[5] / 2, -D["hoop_x"]
    if fin_start < hoop_spec:
        for sgn in (1, -1):
            warn(f"WARN_fin_ahead_{'L' if sgn > 0 else 'R'}",
                 (sx((fin_start + hoop_spec) / 2), sgn * abs(fin[3]), fin[4]),
                 (hoop_spec - fin_start, fin[6], fin[7]),
                 f"fin starts {hoop_spec - fin_start:.0f} mm ahead of the roll hoop, over the cabin aperture")
            n_warn += 1

    # ---- materials (visualisation only)
    for nm, (rgba, metal, rough) in MATERIALS.items():
        mat = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
        mat.use_nodes = True
        mat.diffuse_color = rgba
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = rgba
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = metal
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = rough
            if nm == "STATEV_LIGHT" and "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 3.0
                bsdf.inputs["Emission Color"].default_value = rgba
            if nm == "STATEV_GLASS":
                mat.blend_method = "BLEND"
                if "Alpha" in bsdf.inputs:
                    bsdf.inputs["Alpha"].default_value = 0.25

    # ---- assign materials to what they belong to (prompt §26)
    def assign(ob, mat_name):
        m = bpy.data.materials.get(mat_name)
        if m and ob.type == "MESH":
            ob.data.materials.clear()
            ob.data.materials.append(m)
    for ob in root.all_objects:
        n = ob.name
        if "_TXT" in n or n.startswith(PFX + "WARN") or ob.users_collection[0].name == "99_DEBUG":
            continue
        if "WHEEL_" in n:
            assign(ob, "STATEV_WHEELS")
        elif any(k in n for k in ("HEADLIGHT", "DRL", "TAIL_", "PROJECTOR")):
            assign(ob, "STATEV_LIGHT")
        elif any(k in n for k in ("BLADE", "FIN", "DIFFUSER", "SPLITTER", "CHANNEL")):
            assign(ob, "STATEV_CARBON")
        elif "SEAT" in n:
            assign(ob, "STATEV_INTERIOR")
        elif ob.users_collection[0].name == "06_ROOF":
            assign(ob, "STATEV_GLASS")
        elif ob.users_collection[0].name in ("02_BODY", "03_AERO"):
            assign(ob, "STATEV_BODY")

    # ---- diagnostic cameras (prompt §30)
    import math as _mm
    cam_defs = [
        ("CAM_side",  (12000, 0, 650),      (_mm.radians(90), 0, _mm.radians(90)),  "ORTHO", 5.2),
        ("CAM_front", (12000, 0, 650),      (_mm.radians(90), 0, 0),                "ORTHO", 2.6),
        ("CAM_rear",  (-12000, 0, 650),     (_mm.radians(90), 0, _mm.radians(180)), "ORTHO", 2.6),
        ("CAM_top",   (-1200, 0, 12000),    (0, 0, _mm.radians(90)),                "ORTHO", 5.2),
        ("CAM_three_quarter", (4200, 3400, 1900),
         (_mm.radians(72), 0, _mm.radians(129)), "PERSP", 0),
    ]
    for nm, loc, rot, typ, ortho in cam_defs:
        cd = bpy.data.cameras.new(PFX + nm)
        cd.type = typ
        if typ == "ORTHO":
            cd.ortho_scale = ortho
        else:
            cd.lens = 85
        c = bpy.data.objects.new(PFX + nm, cd)
        c.location = tuple(mm(v) for v in loc)
        c.rotation_euler = rot
        dbg.objects.link(c)
        c.hide_viewport = True      # kept out of the viewport so "frame selected" ignores them
        c["note"] = "diagnostic view; ortho cameras are for proportion checks, not renders"
    # CAM_side is the one a proportion judgement should be made from
    bpy.context.scene.camera = bpy.data.objects[PFX + "CAM_side"]

    # ---- parametric root
    rt = bpy.data.objects.new(PFX + "001_ROOT", None)
    rt.empty_display_type = "ARROWS"
    rt.empty_display_size = 0.5
    root.objects.link(rt)
    for k, v in ROOT_PROPS.items():
        rt[k] = v
    rt["spec"] = "STATEV 001 dimensional specification v0.1 (2026-09-14) — see docs/10"
    rt["axis"] = "repo convention: +X forward, +Y left, +Z up, origin = front axle on the ground"
    rt["spec_axis"] = "source spec used +X rearward, +Y right — every spec X is negated on import"
    rt["status"] = "design targets, not production CAD; the scan is master for all donor hardpoints"
    rt["front_track_locked"] = True
    rt["rear_track_locked"] = True
    for ob in root.all_objects:
        if ob is not rt and ob.parent is None:
            ob.parent = rt
            ob.matrix_parent_inverse = rt.matrix_world.inverted()

    n_obj = len(root.all_objects)
    print(f"{COLL_ROOT} rebuilt: {n_obj} objects in {len(SUBCOLLS)} collections | "
          f"{len(SECTIONS)} sections, {len(RAIL_LEVELS)} rail levels, {len(MATERIALS)} materials | "
          f"spec X negated to repo X (+X forward)")
    return root


build()
