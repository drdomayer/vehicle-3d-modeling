"""
statev_master_volumes.py — STAGE 01: the master exterior volumes.

Supersedes statev_preview_loft.py. That one was a single global loft through every section, which
is the thing the surface specification forbids; it existed only to judge proportion and it failed
its own highlight test because the car's three negative-space regions did not exist in it.

This builds the DESIGN MASTER: the large volumes, with the voids cut as real geometry, split into
per-zone objects that can be adjusted independently. It is NOT production geometry — no seams, no
thickness, no flanges, no fasteners. Class-A surfacing remains manual work on top of this.

What it does:
  1. skin lofted from the master sections, crowned by HOOD_SPINE at the front and DECK_SPINE behind
  2. per-zone shaping so the front, the door and the haunch do not share one character
  3. FIVE void families cut as booleans — the whole point of this stage:
       cabin aperture, wheel arches, fender channels, door channel into the side intake,
       rear lower undercut
  4. buttresses as separate masses around the roof envelope
  5. split into STATEV_FRONT / STATEV_SIDE / STATEV_REAR

Donor hardpoints are read, never written. Nothing here moves a wheel, the screen or a shut line.
"""

import bpy
import bmesh
import math
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else os.path.join(REPO, "01_CAD/scripts")
_sk = {}
with open(os.path.join(_here, "statev_skeleton.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("\ndef build():")[0], _sk)
SECTIONS, PFX = _sk["SECTIONS"], _sk["PFX"]
HOOD_SPINE, DECK_SPINE, ARCHES = _sk["HOOD_SPINE"], _sk["DECK_SPINE"], _sk["ARCHES"]
widening, sx, mm, half_width_at = _sk["widening"], _sk["sx"], _sk["mm"], _sk["half_width_at"]
D = _sk["donor_dims"]()

ROOT = "STATEV_MASTER"
ZONES = {"STATEV_FRONT": (-1000, 340), "STATEV_SIDE": (340, 1900), "STATEV_REAR": (1900, 3500)}

N_HALF = 40
SUBDIV = 6        # sub-stations between master sections; 6 gives ~85 rings over the car
CROWN_FACTOR = 0.10

# ---- void families. Each is a list of (spec_x, half_depth_into_body, z_lo, z_hi) stations.
#      The cutter is lofted through them and sits outboard, so the difference eats INTO the side.
FENDER_CHANNEL = [(140, 0, 420, 560), (240, 95, 400, 580), (400, 105, 400, 580), (520, 0, 420, 560)]
DOOR_CHANNEL = [(560, 0, 470, 600), (760, 55, 450, 620), (1100, 95, 430, 640),
                (1450, 130, 410, 650), (1750, 150, 400, 650), (1980, 165, 390, 640),
                (2090, 60, 420, 600)]
# z_lo is 90, below the body floor at 120, on purpose: a cutter face coplanar with the body floor
# makes the EXACT solver collapse the whole mesh. Never let a cutter boundary sit exactly on one.
REAR_UNDERCUT = [(2350, 0, 90, 300), (2600, 70, 90, 330), (2950, 95, 90, 340),
                 (3250, 60, 90, 320), (3400, 0, 90, 280)]

CABIN_Y, CABIN_Z = 700, 640
BUTTRESS = dict(x0=1760, x1=2600, y=600, w=210, z_lo=800, z_hi=1090)


def section_profile(spec_x):
    items = sorted(((v[0], v[2]) for v in SECTIONS.values()), key=lambda t: t[0])
    xs = [i[0] for i in items]
    if spec_x <= xs[0]:
        base = items[0][1]
    elif spec_x >= xs[-1]:
        base = items[-1][1]
    else:
        base = None
        for i in range(len(xs) - 1):
            if xs[i] <= spec_x <= xs[i + 1]:
                t = (spec_x - xs[i]) / (xs[i + 1] - xs[i])
                a, b = items[i][1], items[i + 1][1]
                zs = sorted({z for z, _ in a} | {z for z, _ in b})
                base = []
                for z in zs:
                    ya, yb = half_width_at(a, z), half_width_at(b, z)
                    if ya is not None and yb is not None:
                        base.append((z, ya + t * (yb - ya)))
                break
    return [(z, y + widening(spec_x, z)) for z, y in base]


def spine_z(table, spec_x):
    xs = [t[0] for t in table]
    if not (xs[0] <= spec_x <= xs[-1]):
        return None
    for i in range(len(table) - 1):
        (x0, z0), (x1, z1) = table[i], table[i + 1]
        if x0 <= spec_x <= x1:
            f = 0.0 if x1 == x0 else (spec_x - x0) / (x1 - x0)
            return z0 + f * (z1 - z0)
    return table[-1][1]


def resample(poly, n):
    d = [0.0]
    for i in range(1, len(poly)):
        d.append(d[-1] + math.dist(poly[i - 1], poly[i]))
    total, out = d[-1], []
    for i in range(n):
        t = total * i / (n - 1)
        for j in range(len(d) - 1):
            if d[j] <= t <= d[j + 1]:
                f = 0.0 if d[j + 1] == d[j] else (t - d[j]) / (d[j + 1] - d[j])
                out.append((poly[j][0] + f * (poly[j + 1][0] - poly[j][0]),
                            poly[j][1] + f * (poly[j + 1][1] - poly[j][1])))
                break
        else:
            out.append(poly[-1])
    return out


def smoothstep(a, b, x):
    if a == b:
        return 0.0 if x < a else 1.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)



# ---------------------------------------------------------------- character fields
# Five design elements, each a tunable field rather than hand-sculpted geometry, so a note like
# "the shoulder should rise 200 mm later" is a number change and not a remodel.

# 1. The one main side line: front fender -> door -> rear haunch. (spec_x, z) of its trajectory.
SHOULDER_TRAJECTORY = [(-950, 470), (-700, 505), (-250, 545), (0, 565), (350, 578),
                       (800, 592), (1200, 612), (1600, 648), (2000, 700), (2415, 735),
                       (2800, 712), (3200, 648), (3420, 600)]
SHOULDER_GAIN = 13.0      # mm of local width gained at the line
SHOULDER_W_BELOW = 42.0   # tight below: this is what makes it read as a crease, not a bulge
SHOULDER_W_ABOVE = 95.0   # soft release above

# 2. Tension over the front wheel: a shoulder that starts low ahead of it, peaks above it, releases
FENDER_GAIN = 20.0
FENDER_X, FENDER_XW = -40.0, 470.0
FENDER_Z, FENDER_ZW = 545.0, 120.0

# 3. The rocker as its own element: the body tucks in below a defined sill line between the arches
ROCKER_TUCK = 30.0        # mm the sill draws in
ROCKER_EDGE_Z = 315.0     # the sill line itself
ROCKER_X0, ROCKER_X1 = 330.0, 1820.0

# 4. The tail drawn out instead of ending in a wall
TAIL_START, TAIL_END_X = 2800.0, 3420.0
TAIL_NARROW = 0.86        # half-width multiplier reached at the very tail
TAIL_DROP = 90.0          # mm the crown falls over the same run

# 5. Buttress crest (used in the blade loft): top width as a fraction of base
BUTTRESS_TOP_FRAC = 0.20


def table_z(table, spec_x):
    xs = [t[0] for t in table]
    if spec_x <= xs[0]:
        return table[0][1]
    if spec_x >= xs[-1]:
        return table[-1][1]
    for i in range(len(table) - 1):
        (x0, z0), (x1, z1) = table[i], table[i + 1]
        if x0 <= spec_x <= x1:
            f = (spec_x - x0) / (x1 - x0)
            return z0 + f * (z1 - z0)
    return table[-1][1]


def character(spec_x, z):
    """Millimetres added to (or taken off) the half-width at this station and height."""
    add = 0.0
    # main side line
    zs = table_z(SHOULDER_TRAJECTORY, spec_x)
    w = SHOULDER_W_BELOW if z < zs else SHOULDER_W_ABOVE
    add += SHOULDER_GAIN * math.exp(-((z - zs) / w) ** 2)
    # front fender tension
    add += (FENDER_GAIN * math.exp(-((spec_x - FENDER_X) / FENDER_XW) ** 2)
            * math.exp(-((z - FENDER_Z) / FENDER_ZW) ** 2))
    # rocker tuck, with a defined edge at ROCKER_EDGE_Z
    if ROCKER_X0 <= spec_x <= ROCKER_X1 and z < ROCKER_EDGE_Z:
        ends = min(smoothstep(ROCKER_X0, ROCKER_X0 + 260, spec_x),
                   1.0 - smoothstep(ROCKER_X1 - 260, ROCKER_X1, spec_x))
        add -= ROCKER_TUCK * ends * (1.0 - smoothstep(ROCKER_EDGE_Z - 55, ROCKER_EDGE_Z, z))
    return add


def tail_factor(spec_x):
    t = smoothstep(TAIL_START, TAIL_END_X, spec_x)
    return 1.0 - (1.0 - TAIL_NARROW) * t, TAIL_DROP * t


ZONE_BLEND = 420      # mm over which one zone's character hands over to the next


def zone_shape(spec_x, z, hw, z_top):
    """Per-zone character, BLENDED. The first version switched character with if/elif at specX 340
    and 1900, which put a step in the surface exactly where the shoulder line crosses — that is
    where the kinks in the stage-01 side view came from. All three characters are now evaluated
    and mixed with smoothstep weights, so nothing changes abruptly at a zone boundary."""
    t = 0.0 if z_top <= 130 else (z - 120) / (z_top - 120)
    f_front = 1.0 + 0.020 * math.sin(math.pi * t) - 0.030 * t ** 3          # tense, flat-topped
    f_side = 1.0 - 0.045 * max(0.0, t - 0.55) / 0.45                        # upper half draws in
    # muscular over the wheel, then released toward the tail rather than ending in a vertical wall
    peak = math.exp(-((spec_x - 2415) / 700.0) ** 2)                        # centred on the rear axle
    f_rear = 1.0 + (0.030 + 0.038 * peak) * math.sin(math.pi * min(1.0, t * 1.15))
    w_side = smoothstep(340 - ZONE_BLEND, 340 + ZONE_BLEND, spec_x)
    w_rear = smoothstep(1900 - ZONE_BLEND, 1900 + ZONE_BLEND, spec_x)
    f = f_front * (1 - w_side) + f_side * (w_side - w_rear) + f_rear * w_rear
    return hw * f


def ring(spec_x):
    prof = sorted(section_profile(spec_x), key=lambda p: p[0])
    z_floor = prof[0][0]
    z_top, hw_top = prof[-1]
    # Crown handover. HOOD_SPINE ends at the cowl (specX 420, Z 970) and DECK_SPINE starts at the
    # hoop plane (1760, Z 960). Between them is the cabin, where the top of the body is the beltline.
    # The first version fell straight from 970 to the beltline in one millimetre — a step exactly
    # where the shoulder line crosses, and the single biggest kink in the stage-01 side view.
    crown = spine_z(HOOD_SPINE, spec_x)
    if crown is None:
        crown = spine_z(DECK_SPINE, spec_x)
    if crown is None:
        x0, z0 = HOOD_SPINE[-1]
        x1, z1 = DECK_SPINE[0]
        belt = z_top + hw_top * CROWN_FACTOR
        a = smoothstep(x0, x0 + 320, spec_x)          # release out of the cowl
        b = smoothstep(x1 - 320, x1, spec_x)          # gather into the deck
        crown = z0 * (1 - a) + belt * (a - b) + z1 * b
    narrow, drop = tail_factor(spec_x)
    crown = max(crown - drop, z_top + 10)
    half = ([(0.0, z_floor)]
            + [(max(20.0, (zone_shape(spec_x, z, hw, z_top) + character(spec_x, z)) * narrow), z)
               for z, hw in prof]
            + [(0.0, crown)])
    half = resample(half, N_HALF)
    return list(half) + [(-y, z) for y, z in reversed(half[1:-1])]


def make_cutter(name, stations, coll, mirror=True):
    """Loft a cutter from (spec_x, depth, z_lo, z_hi). It sits outboard of the body and eats in."""
    objs = []
    for sgn in ((1, -1) if mirror else (1,)):
        verts, faces, rings = [], [], []
        for spec_x, depth, z_lo, z_hi in stations:
            prof = section_profile(spec_x)
            hw = max(y for _, y in prof)
            y_out, y_in = hw + 60, hw - depth
            quad = [(y_out, z_lo), (y_in, z_lo), (y_in, z_hi), (y_out, z_hi)]
            if sgn < 0:
                quad.reverse()      # mirroring by negating Y reverses the winding; undo it here,
                                    # by construction, instead of hoping recalc_face_normals fixes it
            idx = []
            for y, z in quad:
                idx.append(len(verts))
                verts.append((mm(sx(spec_x)), mm(sgn * y), mm(z)))
            rings.append(idx)
        for a, b in zip(rings[:-1], rings[1:]):
            for i in range(4):
                j = (i + 1) % 4
                faces.append((a[i], a[j], b[j], b[i]))
        faces.append(tuple(reversed(rings[0])))
        faces.append(tuple(rings[-1]))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new(f"_cut_{name}_{'L' if sgn > 0 else 'R'}", me)
        coll.objects.link(ob)
        objs.append(ob)   # NOT hidden: a hidden operand is dropped from the depsgraph and the
                          # boolean then differences against nothing, which corrupts the result
    return objs


def fix_normals(ob, label=""):
    """Loft winding comes out inside-out, which makes a boolean DIFFERENCE eat the body instead of
    the void. Recalculate outward and verify by signed volume."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # clean before judging: a chain of booleans leaves slivers and doubled verts, and the next
    # EXACT operation chokes on them. This is what made the 15th cut collapse the whole body.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    vol = bm.calc_volume(signed=True)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    if label and (vol <= 0 or nonman):
        print(f"    ! {label}: volume {vol:.4f}, non-manifold edges {nonman}")
    return vol


def boolean(target, cutters):
    """One cutter at a time, with normals re-fixed between each. A chain of booleans applied in one
    go flips the output winding partway through and the next difference then eats the body instead
    of the void — that is how this first came out as 52 faces."""
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    for c in cutters:
        m = target.modifiers.new(c.name, "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", c, "EXACT"
        n_before = len(target.data.polygons)
        bpy.ops.object.modifier_apply(modifier=m.name)
        fix_normals(target)
        n_after = len(target.data.polygons)
        if n_after < 200:
            raise RuntimeError(f"boolean with {c.name} collapsed the body: "
                               f"{n_before} -> {n_after} faces")
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)


def build():
    scene = bpy.context.scene
    root = bpy.data.collections.get(ROOT)
    if root:
        for c in list(root.children):
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
        for o in list(root.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        root = bpy.data.collections.new(ROOT)
        scene.collection.children.link(root)
    subs = {}
    for n in list(ZONES) + ["STATEV_ROOF", "STATEV_DETAILS", "_WORK"]:
        c = bpy.data.collections.new(n)
        root.children.link(c)
        subs[n] = c

    # ---- 1. skin
    order = sorted(v[0] for v in SECTIONS.values())
    stations = []
    for i in range(len(order) - 1):
        stations += [order[i] + (order[i + 1] - order[i]) * k / SUBDIV for k in range(SUBDIV)]
    stations.append(order[-1])

    # Faceting comes from the control data, not from shading. Smooth each ring point ALONG X
    # before building, so the fix is in the geometry rather than a smooth modifier over a bad shape.
    raw = [ring(x) for x in stations]
    npts = len(raw[0])
    smooth_rings = []
    for i, r in enumerate(raw):
        row = []
        for k in range(npts):
            acc_y = acc_z = wsum = 0.0
            for d, wgt in ((-2, 1), (-1, 4), (0, 6), (1, 4), (2, 1)):
                j = min(len(raw) - 1, max(0, i + d))
                acc_y += raw[j][k][0] * wgt
                acc_z += raw[j][k][1] * wgt
                wsum += wgt
            row.append((acc_y / wsum, acc_z / wsum))
        smooth_rings.append(row)

    verts, faces, rings = [], [], []
    for spec_x, r in zip(stations, smooth_rings):
        idx = []
        for y, z in r:
            idx.append(len(verts))
            verts.append((mm(sx(spec_x)), mm(y), mm(z)))
        rings.append(idx)
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))

    me = bpy.data.meshes.new("MASTER_SKIN")
    me.from_pydata(verts, [], faces)
    me.update()
    skin = bpy.data.objects.new(PFX + "MASTER_SKIN", me)
    subs["_WORK"].objects.link(skin)
    for p in me.polygons:
        p.use_smooth = True
    print(f"  skin volume before booleans: {fix_normals(skin):.3f} m3")

    # ---- 2. the five void families
    cuts = []
    # cabin
    bpy.ops.mesh.primitive_cube_add(size=1.0,
                                    location=(mm((D["cowl_x"] + D["hoop_x"]) / 2.0), 0, mm(CABIN_Z + 400)))
    cab = bpy.context.active_object
    cab.name = "_cut_cabin"
    cab.scale = (mm(abs(D["cowl_x"] - D["hoop_x"])), mm(2 * CABIN_Y), mm(800))
    for c in cab.users_collection:
        c.objects.unlink(cab)
    subs["_WORK"].objects.link(cab)
    cuts.append(cab)
    # wheel arches
    for key, (ax, radius, open_w, tod, _tw) in ARCHES.items():
        ht = (D["track_front"] if key == "FRONT" else D["track_rear"]) / 2.0
        for sgn in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(radius=mm(radius), depth=mm(open_w + 400),
                                                vertices=56,
                                                location=(mm(sx(ax)), mm(sgn * (ht + 200)), mm(tod / 2)))
            cyl = bpy.context.active_object
            cyl.name = f"_cut_arch_{key}_{'L' if sgn > 0 else 'R'}"
            cyl.rotation_euler = (math.radians(90), 0, 0)
            for c in cyl.users_collection:
                c.objects.unlink(cyl)
            subs["_WORK"].objects.link(cyl)
            cuts.append(cyl)
    # the three negative-space regions
    # ORDER MATTERS. The three channel voids must be cut BEFORE the wheel arches and the cabin.
    # The other way round, the fifteenth boolean collapses the whole body to 52 faces — the arch
    # cylinders leave geometry the later channel cuts cannot resolve. Do not reorder casually.
    cuts = (make_cutter("rear_undercut", REAR_UNDERCUT, subs["_WORK"])
            + make_cutter("door_channel", DOOR_CHANNEL, subs["_WORK"])
            + make_cutter("fender_channel", FENDER_CHANNEL, subs["_WORK"])
            + cuts)
    for c in cuts:
        fix_normals(c, c.name)
    boolean(skin, cuts)
    print(f"  skin volume after booleans:  {fix_normals(skin):.3f} m3, "
          f"{len(skin.data.polygons)} faces")

    # ---- 3. buttresses, lofted as blades rather than boxes.
    # The first version was literally a cube. A buttress reads as: rising -> tightening -> blade ->
    # merging into the deck, so it is built from stations along X with a varying height and width.
    b = BUTTRESS
    buttresses = []
    for sgn in (1, -1):
        verts, faces, brings = [], [], []
        for f in [i / 10.0 for i in range(11)]:
            x = b["x0"] + (b["x1"] - b["x0"]) * f
            rise = math.sin(math.pi * min(1.0, f * 1.35)) ** 0.7        # low -> peak -> release
            z_top = b["z_lo"] + (b["z_hi"] - b["z_lo"]) * rise
            wid = b["w"] * (0.45 + 0.55 * math.sin(math.pi * min(1.0, 0.25 + f * 0.9)))
            z_base = b["z_lo"] - 260      # reaches down INTO the haunch so the union merges
            quad = [(b["y"] - wid / 2, z_base), (b["y"] + wid / 2, z_base),
                    (b["y"] + wid / 2 * BUTTRESS_TOP_FRAC, z_top),
                    (b["y"] - wid / 2 * BUTTRESS_TOP_FRAC, z_top)]
            if sgn < 0:
                quad.reverse()
            idx = []
            for y, z in quad:
                idx.append(len(verts))
                verts.append((mm(sx(x)), mm(sgn * y), mm(z)))
            brings.append(idx)
        for a2, b2 in zip(brings[:-1], brings[1:]):
            for i in range(4):
                j = (i + 1) % 4
                faces.append((a2[i], a2[j], b2[j], b2[i]))
        faces.append(tuple(reversed(brings[0])))
        faces.append(tuple(brings[-1]))
        bme = bpy.data.meshes.new("BUTTRESS")
        bme.from_pydata(verts, [], faces)
        bme.update()
        bt = bpy.data.objects.new(PFX + f"BUTTRESS_VOLUME_{'L' if sgn > 0 else 'R'}", bme)
        subs["_WORK"].objects.link(bt)
        for pf in bme.polygons:
            pf.use_smooth = True
        fix_normals(bt)
        buttresses.append(bt)
    # union the blades into the skin so the buttress reads as the body rising, not a box placed on it
    bpy.ops.object.select_all(action="DESELECT")
    skin.select_set(True)
    bpy.context.view_layer.objects.active = skin
    for bt in buttresses:
        m = skin.modifiers.new(bt.name, "BOOLEAN")
        m.operation, m.object, m.solver = "UNION", bt, "EXACT"
        bpy.ops.object.modifier_apply(modifier=m.name)
        fix_normals(skin)
    for bt in buttresses:
        bpy.data.objects.remove(bt, do_unlink=True)
    print(f"  buttresses merged into the skin: {len(skin.data.polygons)} faces")

    # ---- 4. split the skin into zones
    bpy.ops.object.select_all(action="DESELECT")
    skin.select_set(True)
    bpy.context.view_layer.objects.active = skin
    made = []
    for zname, (x0, x1) in ZONES.items():
        cp = skin.copy()
        cp.data = skin.data.copy()
        cp.name = PFX + zname.replace("STATEV_", "") + "_VOLUME"
        subs[zname].objects.link(cp)
        bm = bmesh.new()
        bm.from_mesh(cp.data)
        kill = [f for f in bm.faces if not (x0 <= -f.calc_center_median().x * 1000 <= x1)]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(cp.data)
        bm.free()
        cp["status"] = "MASTER_VOLUME"
        cp["stage"] = "01 — design master, not production geometry"
        mat = bpy.data.materials.get("STATEV_BODY")
        if mat:
            cp.data.materials.clear()
            cp.data.materials.append(mat)
        cp.color = (0.045, 0.115, 0.075, 1.0)
        made.append((cp.name, len(cp.data.polygons)))
    bpy.data.objects.remove(skin, do_unlink=True)
    for o in list(subs["_WORK"].objects):
        bpy.data.objects.remove(o, do_unlink=True)

    print(f"{ROOT}: " + " | ".join(f"{n} {f}f" for n, f in made))
    print("voids cut: cabin, 4 wheel arches, fender channels, door channel into the intake, "
          "rear undercut")
    return root


build()
