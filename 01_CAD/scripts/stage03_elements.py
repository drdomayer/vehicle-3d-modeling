"""
stage03_elements.py — the layered form. Real openings and separate parts, on top of the core.

The body in statev_master_volumes is ONE closed lofted volume with scalar fields applied to its
sections. It carries the proportion, the packaging and the panel map, and all of that stays. What it
cannot carry is the form language CLAUDE.md actually specifies -- layered panels with negative space,
floating fenders, thin light blades, an open rear structure -- because a single loft cannot make a
panel stand proud of another with a gap behind it, or a blade, or an opening with a sharp lip. What
it makes instead is a DENT: the side intake is a dent, the door channel is a dent, the buttress is a
bump on the deck. Measured against the render's outline that reads 3 mm. Looked at, it reads as one
bar of soap with dents in it, which is what the owner said and he is right.

So this builds the other half. Openings are cut as POCKETS with vertical walls and a sharp lip, which
is both what the render shows and what a real intake is -- an intake feeds a duct, it is not
see-through. Blades and lips are separate objects with air behind them, because that air is the
entire point of the layering.

NOTHING HERE TOUCHES A LOCKED VALUE. Every element is placed inside the existing surface, inside
4370 x 1850, and the checks at the end prove it rather than promise it. Mounting points stay absent
and stay SCAN REQUIRED; a shape on our own surface does not need the donor, which is why these can be
built now and the owner has said to leave mounting for later.

    import bpy; exec(open(".../stage03_elements.py").read())
"""

import math
import os

import bmesh
import bpy

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"

_sk = {"__file__": os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), "__name__": "_sk"}
with open(os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef build(")[0], _sk)
PACKAGE = _sk["PACKAGE"]

COLL = "STATEV_STAGE03"


def mm(v):
    return v / 1000.0


def body_objects():
    return [o for o in bpy.data.collections["STATEV_MASTER"].all_objects
            if o.type == "MESH" and "VOLUME" in o.name]


def surface_y(spec_x, z, tol=28.0):
    """The body's own half-width at this station and height, so an element can be placed ON the
    surface instead of at a number someone guessed."""
    best = None
    for o in body_objects():
        M = o.matrix_world
        for v in o.data.vertices:
            w = M @ v.co
            if abs(-w.x * 1000 - spec_x) < tol and abs(w.z * 1000 - z) < tol:
                y = abs(w.y * 1000)
                if best is None or y > best:
                    best = y
    return best


def surface_z(spec_x, y, tol=26.0):
    """The body's own top at this station and lateral position. An element that has to sit INSIDE
    the surface needs to know where the surface is, not a number typed from memory."""
    best = None
    for o in body_objects():
        M = o.matrix_world
        for v in o.data.vertices:
            w = M @ v.co
            if abs(-w.x * 1000 - spec_x) < tol and abs(abs(w.y * 1000) - abs(y)) < tol:
                z = w.z * 1000
                if best is None or z > best:
                    best = z
    return best


def prism(name, coll, stations, y_out, y_in):
    """A pocket cutter: a lofted prism running along spec X, from outboard of the surface inward.
    `stations` is [(spec_x, z_lo, z_hi)] and the walls are vertical, which is what gives the lip."""
    verts, faces = [], []
    for sx, z0, z1 in stations:
        base = len(verts)
        for y in (y_out, y_in):
            for z in (z0, z1):
                verts.append((-mm(sx), mm(y), mm(z)))
        del base
    n = 4
    for i in range(len(stations) - 1):
        a, b = i * n, (i + 1) * n
        faces += [(a + 0, a + 1, b + 1, b + 0), (a + 2, a + 3, b + 3, b + 2),
                  (a + 0, a + 2, b + 2, b + 0), (a + 1, a + 3, b + 3, b + 1)]
    faces += [(0, 1, 3, 2)]
    last = (len(stations) - 1) * n
    faces += [(last + 0, last + 2, last + 3, last + 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return ob


def blade(name, coll, stations, thick):
    """A thin standing blade: same station form, given a thickness, as its own object with air
    behind it. This is the layer a loft cannot make."""
    verts, faces = [], []
    for sx, y, z0, z1 in stations:
        for dy in (-thick / 2.0, thick / 2.0):
            for z in (z0, z1):
                verts.append((-mm(sx), mm(y + dy), mm(z)))
    n = 4
    for i in range(len(stations) - 1):
        a, b = i * n, (i + 1) * n
        faces += [(a + 0, a + 1, b + 1, b + 0), (a + 2, a + 3, b + 3, b + 2),
                  (a + 0, a + 2, b + 2, b + 0), (a + 1, a + 3, b + 3, b + 1)]
    faces += [(0, 1, 3, 2)]
    last = (len(stations) - 1) * n
    faces += [(last + 0, last + 2, last + 3, last + 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return ob


def box(name, coll, x0, x1, y0, y1, z0, z1):
    """An axis-aligned box in spec coordinates. Used both as a pocket cutter and, given two of them,
    as the frame of a surround."""
    v = [(-mm(x), mm(y), mm(z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return ob


def frame(name, coll, x0, x1, y0, y1, z0, z1, wall):
    """A rectangular surround: the outer box with the inner one taken out of it, so what is left is
    a thin frame standing in the pocket. This is the 'thin light blade' read -- the lamp sits behind
    a frame, not in a hole."""
    outer = box(name, coll, x0, x1, y0, y1, z0, z1)
    inner = box(name + "_void", coll, x0 - 6, x1 + 6, y0 + wall, y1 - wall, z0 + wall, z1 - wall)
    m = outer.modifiers.new("void", "BOOLEAN")
    m.operation, m.object, m.solver = "DIFFERENCE", inner, "EXACT"
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(inner, do_unlink=True)
    return outer


def shell(name, coll, x0, x1, y0, y1, z0, z1, wall, open_face):
    """A closed box with its inside taken out and one face opened -- a lamp housing. `open_face` is
    the spec-X end left off, because that is the end the lamp looks out of."""
    outer = box(name, coll, x0, x1, y0, y1, z0, z1)
    ix0 = x0 - 8 if open_face == "front" else x0 + wall
    ix1 = x1 - wall if open_face == "front" else x1 + 8
    inner = box(name + "_void", coll, ix0, ix1, y0 + wall, y1 - wall, z0 + wall, z1 - wall)
    m = outer.modifiers.new("void", "BOOLEAN")
    m.operation, m.object, m.solver = "DIFFERENCE", inner, "EXACT"
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(inner, do_unlink=True)
    return outer


def duct(name, coll, stations, wall):
    """A lofted rectangular duct through (spec_x, y_c, z_c, half_w, half_h) stations, hollow."""
    def tube(shrink):
        v, f = [], []
        for sx, yc, zc, hw, hh in stations:
            for dy, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v.append((-mm(sx), mm(yc + dy * (hw - shrink)), mm(zc + dz * (hh - shrink))))
        n = 4
        for i in range(len(stations) - 1):
            a, b = i * n, (i + 1) * n
            for k in range(4):
                k2 = (k + 1) % 4
                f.append((a + k, a + k2, b + k2, b + k))
        f.append((0, 1, 2, 3))
        last = (len(stations) - 1) * n
        f.append((last + 3, last + 2, last + 1, last + 0))
        return v, f
    vo, fo = tube(0.0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vo, [], fo)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    vi, fi = tube(wall)
    mi = bpy.data.meshes.new(name + "_void")
    mi.from_pydata(vi, [], fi)
    mi.update()
    inner = bpy.data.objects.new(name + "_void", mi)
    coll.objects.link(inner)
    for o in (ob, inner):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    m = ob.modifiers.new("void", "BOOLEAN")
    m.operation, m.object, m.solver = "DIFFERENCE", inner, "EXACT"
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(inner, do_unlink=True)
    return ob


def cut(target, cutter):
    m = target.modifiers.new(cutter.name, "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    before = len(target.data.polygons)
    bpy.ops.object.modifier_apply(modifier=m.name)
    return before, len(target.data.polygons)


def main():
    old = bpy.data.collections.get(COLL)
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(coll)

    print("=" * 96)
    print("STAGE 03 — the layered form: real openings with lips, and blades with air behind them")
    print("=" * 96)

    made, cuts = [], []

    # ---- 1. the side intake as a real mouth. The depth field already puts a valley here; this
    # gives it vertical walls and a sharp lip, which is the difference between a dent and a mouth.
    st = [(1955, 470, 690), (2010, 452, 700), (2090, 448, 700), (2165, 470, 672)]
    y_surf = max(surface_y(s[0], (s[1] + s[2]) / 2) or 0 for s in st)
    for sgn in (1, -1):
        c = prism(f"CUT_INTAKE_{'L' if sgn > 0 else 'R'}", coll,
                  st, sgn * (y_surf + 80), sgn * 430)
        cuts.append(c)
    print(f"  side intake mouth: spec X {st[0][0]}..{st[-1][0]}, Z {min(s[1] for s in st)}.."
          f"{max(s[2] for s in st)}, cut from the surface at Y {y_surf:.0f} inward to 430")

    # ---- 2. the blade standing in that mouth, the vertical element ref-05 puts across the intake
    for sgn in (1, -1):
        b = blade(f"INTAKE_BLADE_{'L' if sgn > 0 else 'R'}", coll,
                  [(1975, sgn * (y_surf - 30), 470, 686), (2030, sgn * (y_surf - 46), 455, 696),
                   (2100, sgn * (y_surf - 52), 452, 694), (2150, sgn * (y_surf - 40), 474, 668)],
                  22.0)
        b["panel_id"] = "P13" if sgn > 0 else "P14"
        b["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(b)
    print("  intake blade: a 22 mm wall standing inside the mouth with air behind it"
          "  -> registered P13 / P14 INTAKE_BLADE")

    # ---- 3. the fender channel as a real slot through the fender top into the wheel well. This one
    # IS a through-cut: it vents the arch, which is what AIRFLOW in statev_skeleton says it does.
    # MOVED INBOARD 2026-09-17, after the overlay caught it. At Y 470 to 660 the slot straddled the
    # fender CREST, which sits at Y 590, so it ate 18 mm off the crown line -- the very line the
    # crest field was added in v021 to get right. A fender vent belongs inboard of the crown, on the
    # inner shoulder, venting down into the arch. Y 385 to 545 puts it there.
    fs = [(-235, 700, 980), (-110, 700, 985), (40, 700, 985), (165, 700, 975)]
    for sgn in (1, -1):
        c = prism(f"CUT_FENDER_SLOT_{'L' if sgn > 0 else 'R'}", coll,
                  [(s[0], s[1], s[2]) for s in fs], sgn * 545, sgn * 385)
        cuts.append(c)
    print(f"  fender slot: spec X {fs[0][0]}..{fs[-1][0]}, Y 385..545, cut down from Z 985 to 700")
    # the channel's own liner, a shallow U standing inside the slot: registered P05 / P06
    # The liner's top FOLLOWS THE SURFACE and sits 12 mm under it. Written as a fixed 974 it stood
    # 75 to 109 mm proud of a body whose crown there is 865 to 899 -- a fin out of the bonnet, which
    # the silhouette overlay read as the car's own top line and scored as the front regressing from
    # 3 mm to 21. A liner that pokes out of the panel it lines is not a liner.
    for sgn in (1, -1):
        st = []
        for sx in (fs[0][0] + 20, -110, 40, fs[-1][0] - 20):
            top = surface_z(sx, 465)
            st.append((sx, sgn * 465, 712, (top - 12.0) if top else 860.0))
        lin = blade(f"FENDER_CHANNEL_{'L' if sgn > 0 else 'R'}", coll, st, 14.0)
        lin["panel_id"] = "P05" if sgn > 0 else "P06"
        lin["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(lin)
    print("  fender channel liner: a 14 mm wall inside the slot -> registered P05 / P06")


    # ---- 4. the rear. In ref-05 the tail is not a wall: a recessed centre mask sits between the
    # light bar's two ends, the exhausts come through their own surrounds, and the plate drops into
    # a recess below. Each of those is a pocket with a part standing in it, and each is a register
    # entry that has been BLOCKED for want of geometry.
    #
    # NOTHING HERE GOES NEAR THE ROOF. P17, P18, P19, P42, P20, P23 and P33 are ROOF_BLOCKED and
    # stay untouched; the fold envelope is guessed at spec X 1240 to 1760 and everything below is
    # behind 3300.
    rear_pockets = [("CUT_CENTRE_MASK", 3330, 3425, -300, 300, 395, 595),
                    ("CUT_PLATE", 3345, 3425, -255, 255, 250, 372),
                    ("CUT_EXHAUST_L", 3300, 3425, 8, 122, 375, 489),
                    ("CUT_EXHAUST_R", 3300, 3425, -122, -8, 375, 489)]
    for nm, a, b_, c, d, e, f_ in rear_pockets:
        cuts.append(box(nm, coll, a, b_, c, d, e, f_))
    print(f"  rear: {len(rear_pockets)} pockets — centre mask, plate recess, two exhaust openings")

    for pid, nm, a, b_, c, d, e, f_, w in (
            ("P34", "REAR_CENTRE_MASK", 3352, 3372, -296, 296, 399, 591, 26.0),
            ("P36", "PLATE_RECESS", 3366, 3382, -251, 251, 254, 368, 20.0)):
        ob = frame(nm, coll, a, b_, c, d, e, f_, w)
        ob["panel_id"] = pid
        ob["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(ob)

    # The exhaust surround is ONE part in the register, so it is built as one: a bar across both
    # tips with the two openings taken out of it. Two separate rings would be one part in two
    # pieces, which the connectivity gate in pilot_panel would refuse -- correctly.
    es = box("EXHAUST_SURROUND", coll, 3322, 3346, -140, 140, 371, 493)
    for sgn in (1, -1):
        v = box("_es_void", coll, 3316, 3352, sgn * 12, sgn * 118, 383, 481)
        m = es.modifiers.new("void", "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", v, "EXACT"
        bpy.context.view_layer.objects.active = es
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(v, do_unlink=True)
    es["panel_id"] = "P35"
    es["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
    made.append(es)
    print("  rear parts: centre mask P34, plate recess P36, exhaust surround P35 (one bar, two holes)")

    # ---- 5. the headlamp as a blade, not a cavity. A slot across the nose with a thin frame in it,
    # so what shows is a line of light behind a frame -- which is what "thin light blades" means and
    # the only road-legal way to get it, since the E-marked module itself may never be modified.
    for sgn in (1, -1):
        cuts.append(box(f"CUT_LAMP_{'L' if sgn > 0 else 'R'}", coll,
                        -700, -540, sgn * 400, sgn * 690, 505, 625))
    for sgn in (1, -1):
        ob = frame(f"HEADLIGHT_SURROUND_{'L' if sgn > 0 else 'R'}", coll,
                   -676, -648, min(sgn * 406, sgn * 684), max(sgn * 406, sgn * 684), 509, 621, 18.0)
        ob["panel_id"] = "P29" if sgn > 0 else "P30"
        ob["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(ob)
    print("  headlamp: a slot across the nose with an 18 mm frame in it -> P29 / P30")


    # ---- 6. the lamp housing behind the blade. PROJECTOR is a DECIDED envelope at spec X -600,
    # Y +-560, Z 570, 150 x 110 x 110 for one Hella 90 mm bi-LED module, and the module itself may
    # never be modified -- so the housing is built around it with a wall and 6 mm of air, open at
    # the front where the P29 frame is.
    for sgn in (1, -1):
        h = shell(f"HEADLIGHT_HOUSING_{'L' if sgn > 0 else 'R'}", coll,
                  -681, -519, min(sgn * 499, sgn * 621), max(sgn * 499, sgn * 621),
                  509, 631, 5.0, "front")
        h["panel_id"] = "P24" if sgn > 0 else "P25"
        h["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(h)
    print("  lamp housing: a 5 mm shell around the module envelope, open at the front -> P24 / P25")

    # ---- 6b. THE TAIL BLADE. docs/14 locks it as "тънко широко хоризонтално острие през
    # задницата, с остри L-образни външни краища", and explicitly not a triangular supercar lamp --
    # and until 2026-09-21 the single most identifiable element of the rear did not exist in the
    # geometry at all. The envelopes were there and enclosed (check_lighting passes them), but
    # nothing was cut for them: check_packaging reads TAIL_BAR at 115.5 mm INSIDE the surface and
    # TAIL_END at 20.6, which is correct for a cavity and useless without an aperture.
    #
    # Every number below comes from the skeleton's LOCKED envelopes, not from a guess:
    #   TAIL_BAR  spec X 3200, Y 0,     Z 612, 45 x 1440 x 38   -> X 3177.5..3222.5, Y +-720
    #   TAIL_END  spec X 3120, Y +-700, Z 612, 120 x 40 x 38    -> X 3060..3180, Y 680..720
    # The slot is those two, opened out to the surface; the housing is a 5 mm shell around them
    # with 6 mm of air, the same construction the headlamp housing uses, because the E-marked
    # module may never be modified.
    TB = dict(x0=3177.5, x1=3222.5, y=720.0, z0=593.0, z1=631.0)
    TE = dict(x0=3060.0, x1=3180.0, y0=680.0, y1=720.0, z0=593.0, z1=631.0)
    for sgn in (1, -1):
        L = sgn > 0
        # the bar half: cut from the lamp face outward past the skin
        cuts.append(box(f"CUT_TAIL_BAR_{'L' if L else 'R'}", coll,
                        TB["x0"], TB["x1"] + 60,
                        min(0.0, sgn * TB["y"]), max(0.0, sgn * TB["y"]),
                        TB["z0"], TB["z1"]))
        # the L end, wrapping the corner
        cuts.append(box(f"CUT_TAIL_END_{'L' if L else 'R'}", coll,
                        TE["x0"], TE["x1"],
                        min(sgn * TE["y0"], sgn * (TE["y1"] + 60)),
                        max(sgn * TE["y0"], sgn * (TE["y1"] + 60)),
                        TE["z0"], TE["z1"]))
    print(f"  tail blade: a slot {TB['z1']-TB['z0']:.0f} mm tall across the rear at spec X "
          f"{TB['x0']:.0f}, with L ends wrapping forward to {TE['x0']:.0f}")

    for sgn in (1, -1):
        L = sgn > 0
        nm = f"TAIL_HOUSING_{'L' if L else 'R'}"
        # bar half, 6 mm of air round the module and a 5 mm wall outside that, open to the REAR
        # An L needs two boxes, and the ORDER of the booleans matters. The first version made two
        # shell()s and unioned them -- but shell() returns an OPEN solid, one face deliberately
        # missing, and an EXACT union of two open meshes does not reliably join: P26 and P27 came
        # out as two disconnected pieces and panel_extract said so. Union the CLOSED outers, union
        # the CLOSED inners, subtract once. Every boolean then runs on a closed solid.
        w, air = 5.0, 6.0
        o1 = box(nm + "_o1", coll, TB["x0"] - w - air, TB["x1"] + w + air,
                 min(0.0, sgn * (TB["y"] + w + air)), max(0.0, sgn * (TB["y"] + w + air)),
                 TB["z0"] - w - air, TB["z1"] + w + air)
        o2 = box(nm + "_o2", coll, TE["x0"] - w - air, TE["x1"] + w + air,
                 min(sgn * (TE["y0"] - w - air), sgn * (TE["y1"] + w + air)),
                 max(sgn * (TE["y0"] - w - air), sgn * (TE["y1"] + w + air)),
                 TE["z0"] - w - air, TE["z1"] + w + air)
        i1 = box(nm + "_i1", coll, TB["x0"] - air, TB["x1"] + w + air + 8,
                 min(0.0, sgn * (TB["y"] + air)), max(0.0, sgn * (TB["y"] + air)),
                 TB["z0"] - air, TB["z1"] + air)
        i2 = box(nm + "_i2", coll, TE["x0"] - air, TE["x1"] + air,
                 min(sgn * (TE["y0"] - air), sgn * (TE["y1"] + w + air + 8)),
                 max(sgn * (TE["y0"] - air), sgn * (TE["y1"] + w + air + 8)),
                 TE["z0"] - air, TE["z1"] + air)
        for tgt, src, op in ((o1, o2, "UNION"), (i1, i2, "UNION"), (o1, i1, "DIFFERENCE")):
            m = tgt.modifiers.new("b", "BOOLEAN")
            m.operation, m.object, m.solver = op, src, "EXACT"
            bpy.context.view_layer.objects.active = tgt
            bpy.ops.object.modifier_apply(modifier=m.name)
        for dead in (o2, i1, i2):
            bpy.data.objects.remove(dead, do_unlink=True)
        h1 = o1
        h1.name = nm
        h1["panel_id"] = "P26" if L else "P27"
        h1["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(h1)
    print("  tail housing: a 5 mm shell around TAIL_BAR and TAIL_END, open to the rear -> P26 / P27")

    # ---- P23 REAR_SPOILER: NOT BUILT, and the measurement says why rather than a preference.
    # check_packaging puts its envelope 125.7 mm BELOW the surface and 108.8 mm inboard at spec X
    # 3120 -- it is entirely buried in the body. A blade built there would sit inside the bodywork.
    # That agrees with what the project already decided and recorded: "spoiler-ът стана ducktail",
    # meaning the form moved into the body's own tail profile, where TAIL_DROP carries it. P23 is a
    # leftover in the register rather than a part waiting to be modelled, and the register is where
    # it gets resolved.
    print("  NOT built: P23 REAR_SPOILER — its envelope is 125.7 mm inside the body. The ducktail")
    print("    is in the tail profile already; P23 is a register question, not a modelling one.")

    # ---- 7. the intake duct, from the mouth to the plenum. It runs through the three envelopes the
    # skeleton already carries -- INTAKE_INLET derived, INTAKE_DUCT and INTAKE_OUTLET PROVISIONAL --
    # and PROVISIONAL is the honest word: where the plenum actually sits is the donor's answer, so
    # the duct's SHAPE is ours and its ROUTE is not.
    for sgn in (1, -1):
        d = duct(f"INTAKE_DUCT_{'L' if sgn > 0 else 'R'}", coll,
                 [(1990, sgn * 870, 520, 55, 90), (2070, sgn * 800, 520, 70, 90),
                  (2150, sgn * 650, 520, 90, 90), (2230, sgn * 470, 560, 90, 95),
                  (2300, sgn * 300, 600, 75, 100)], 4.0)
        d["panel_id"] = "P31" if sgn > 0 else "P32"
        d["stage"] = "03 element — shape ours, ROUTE provisional, mounting SCAN REQUIRED"
        made.append(d)
    print("  intake duct: mouth to plenum through the three existing envelopes -> P31 / P32")

    # ---- NOT BUILT, and the reason is the point. P37 / P38 MIRROR_CAP clip onto the OEM mirror
    # body, and there is no MIRROR box anywhere in statev_skeleton -- no envelope, no position, no
    # size. Building one would mean inventing where the donor's mirror is, which is exactly the kind
    # of number this project does not invent. It stays BLOCKED until the scan.
    print("  NOT built: P37 / P38 MIRROR_CAP — the skeleton has no mirror envelope at all, so its")
    print("    position is the donor's and inventing it is not an option")

    # cut them all out of the body
    for c in cuts:
        for o in body_objects():
            a, b = cut(o, c)
            if b < a * 0.5:
                print(f"    WARNING {o.name} lost more than half its faces to {c.name}: {a} -> {b}")
        bpy.data.objects.remove(c, do_unlink=True)

    # ---- checks, rather than promises
    P = []
    for o in body_objects():
        M = o.matrix_world
        for v in o.data.vertices:
            w = M @ v.co
            P.append((-w.x * 1000, w.y * 1000, w.z * 1000))
    for ob in made:
        M = ob.matrix_world
        for v in ob.data.vertices:
            w = M @ v.co
            P.append((-w.x * 1000, w.y * 1000, w.z * 1000))
    X = [p[0] for p in P]
    Y = [abs(p[1]) for p in P]
    Z = [p[2] for p in P]
    print(f"\n  {len(made)} separate elements, {len(cuts)} openings cut")
    print(f"  LOCKED  length {max(X)-min(X):.1f} (4370)   width {2*max(Y):.1f} (1850)   "
          f"Z {min(Z):.0f}..{max(Z):.0f}")
    ok = abs((max(X) - min(X)) - PACKAGE["length"]) < 1.0 and abs(2 * max(Y) - 1850) < 1.0
    print(f"  {'locked values intact' if ok else 'LOCKED VALUES MOVED — do not keep this build'}")
    return made


main()
