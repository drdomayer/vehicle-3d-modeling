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
import mathutils

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
    # A ray from above, since 2026-09-26. The vertex search within `tol` found nothing at the top
    # wherever the rings were sparse and fell through to the FLOOR vertices at Z 120 -- and it
    # did so silently: the louvre comb was built 681 mm tall, down to Z 108, on a body whose slot
    # had already been cut by a previous run of this script. The ray answers "where is the skin
    # at this (X, Y)" for any tessellation. It still answers with the slot floor on a body this
    # script has already cut -- so run statev_master_volumes.build() first, always.
    best = None
    for o in body_objects():
        inv = o.matrix_world.inverted()
        origin = inv @ mathutils.Vector((-mm(spec_x), mm(y), 3.0))
        d = inv.to_3x3() @ mathutils.Vector((0.0, 0.0, -1.0))
        h, loc, n, i = o.ray_cast(origin, d)
        if h:
            z = (o.matrix_world @ loc).z * 1000.0
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
    # NOT triangulated -- tried 2026-09-29 and it made things worse. When the intake's leading
    # edge was made to lean, the build came out 1998.9 wide: the cutter's own outer face (Y 999)
    # was left in a body volume. Twisted quads were the first suspect and triangulating them
    # was the first fix; measured in isolation the triangulated prism FAILS on the rear volume
    # (max |Y| 999) where the plain one cuts cleanly (925). The real cause is in cut(): the
    # cutter overlapped the side/rear split plane by 8 mm and the EXACT solver misbehaves on
    # such a sliver. Left as quads, which is what every clean cut so far has used.
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


def surface_hit(target, toward):
    """Nearest skin point and normal to `target` (metres, repo axes), probing from `toward` side."""
    best = None
    for o in body_objects():
        inv = o.matrix_world.inverted()
        for off in toward:
            origin = target + mathutils.Vector(off)
            d = (target - origin).normalized()
            h, loc, n, i = o.ray_cast(inv @ origin, (inv.to_3x3() @ d).normalized())
            if h:
                w = o.matrix_world @ loc
                nw = (o.matrix_world.to_3x3() @ n).normalized()
                dist = (w - target).length
                if best is None or dist < best[0]:
                    best = (dist, w, nw)
    return (best[1], best[2]) if best else (None, None)


def ribbon(name, coll, targets, toward, width, depth_out, depth_in):
    """A ridge that FOLLOWS THE SKIN: at each target (spec X, Y, Z) the skin point and normal are
    read by ray, and a rectangle `width` across the path by (depth_out + depth_in) along the
    normal is lofted through them. blade() offsets in Y only and slab() extrudes in Z, and on the
    nose face -- which leans 30-50 mm between Z 400 and 500 -- both stood half buried, half in
    the air (2026-09-29). This is the element the diagonal strakes needed."""
    frames = []
    for sx, y, z in targets:
        p, n = surface_hit(mathutils.Vector((-mm(sx), mm(y), mm(z))), toward)
        if p is not None:
            frames.append((p, n))
    if len(frames) < 2:
        return None
    verts, faces = [], []
    for i, (p, n) in enumerate(frames):
        q = frames[min(i + 1, len(frames) - 1)][0] - frames[max(i - 1, 0)][0]
        d = q.normalized()
        t = n.cross(d).normalized()          # across the path, in the skin
        for a in (-width / 2.0, width / 2.0):
            for b in (-depth_in, depth_out):
                verts.append(p + t * mm(a) + n * mm(b))
    k = 4
    for i in range(len(frames) - 1):
        a, b = i * k, (i + 1) * k
        faces += [(a + 0, a + 1, b + 1, b + 0), (a + 2, a + 3, b + 3, b + 2),
                  (a + 0, a + 2, b + 2, b + 0), (a + 1, a + 3, b + 3, b + 1)]
    faces += [(0, 1, 3, 2)]
    last = (len(frames) - 1) * k
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


SLIVER_MM = 10.0   # a cutter that overlaps a body volume by less than this along X is not applied to it


def cut(target, cutter):
    # THE SLIVER GUARD, 2026-09-29 (v050). The body is three volumes split on planes (front/side
    # at ~340, side/rear at ~1933) and every cutter is applied to all three. A cutter that
    # crosses a split plane by a few millimetres meets that volume as a thin slab against its
    # end cap, and the EXACT solver's answer to that is undefined: measured, the intake mouth
    # starting at 1925 against a side volume ending at 1933 came back UNCHANGED in isolation and,
    # in the full build, came back with the cutter's own outer face (Y 999) welded on -- width
    # 1998.9 against the locked 1850, and "vertices of skin inside the rear arch". A cut that
    # would remove less than SLIVER_MM of X is skipped and said so; the neighbouring volume
    # carries the whole opening.
    tx = [(target.matrix_world @ v.co).x for v in target.data.vertices]
    cx = [(cutter.matrix_world @ v.co).x for v in cutter.data.vertices]
    overlap = (min(max(tx), max(cx)) - max(min(tx), min(cx))) * 1000.0
    if overlap < SLIVER_MM:
        if overlap > 0.0:
            print(f"    {cutter.name} skipped on {target.name}: {overlap:.1f} mm of X overlap is a sliver")
        n = len(target.data.polygons)
        return n, n
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
    # 2026-09-29 (v050): the leading edge LEANS BACK at the top, as ref-09's scoop does (its front
    # edge runs from the bottom-front corner up and back to the top). The mouth cannot move
    # forward: the donor's own opening is at spec X 1900..2080 (cage side_intake_x) and ahead of
    # it the OEM quarter is solid under a 30 mm overlay -- the render's scoop begins on the door
    # because its cabin sits 240 mm further forward than the 986's (docs/14 I). So the bottom-front
    # corner comes forward to 1925 and the top arrives at 2000.
    st = [(1925, 455, 500), (1960, 450, 610), (2000, 447, 700), (2090, 445, 700), (2165, 470, 672)]
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
    # 2026-09-26: the single 14 mm liner became a LOUVRE COMB. ref-09 shows this opening on every
    # view -- four slats, set diagonally in plan (outer-rear to inner-front), in a vent about
    # 430 x 230 at Y 380..608, spec X -400..+40 read off the top view at 6.5 mm/px. Our slot is
    # 385..545 by -235..165: the same opening, one lath in it. The lath was the honest minimum on
    # 2026-09-17; the reference's read is the slats. Four 6 mm slats across the slot at ~60 degrees
    # to the car's axis, tops 12 mm under the surface, joined by two 6 mm rails along the slot's
    # walls so the part is ONE piece -- the union is of closed solids, which is the only union
    # that has ever held in this file.
    def slab(name, p0, p1, z0, z1, thick):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L_ = math.hypot(dx, dy)
        nx, ny = -dy / L_ * thick / 2.0, dx / L_ * thick / 2.0
        corners = [(p0[0] - nx, p0[1] - ny), (p0[0] + nx, p0[1] + ny),
                   (p1[0] - nx, p1[1] - ny), (p1[0] + nx, p1[1] + ny)]
        v = [(-mm(x), mm(y), mm(z)) for (x, y) in corners for z in (z0, z1)]
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
    for sgn in (1, -1):
        tag = "L" if sgn > 0 else "R"
        tops = {}
        for sx in (-215, -125, -35, 55, 145):
            t = surface_z(sx, 465)
            tops[sx] = (t - 12.0) if t else 860.0
        z_top_rail = min(tops.values())
        # two rails along the slot walls, 4 mm off them, and four diagonal slats between
        comb = slab(f"FENDER_CHANNEL_{tag}", (-225.0, sgn * 391.0), (155.0, sgn * 391.0),
                    712.0, z_top_rail, 6.0)
        parts = [slab(f"_rail2_{tag}", (-225.0, sgn * 539.0), (155.0, sgn * 539.0),
                      712.0, z_top_rail, 6.0)]
        for sx in (-215, -125, -35, 55):
            parts.append(slab(f"_slat_{tag}_{sx}", (sx, sgn * 391.0), (sx + 90.0, sgn * 539.0),
                              712.0, tops[sx], 6.0))
        for p in parts:
            m = comb.modifiers.new("u", "BOOLEAN")
            m.operation, m.object, m.solver = "UNION", p, "EXACT"
            bpy.context.view_layer.objects.active = comb
            bpy.ops.object.modifier_apply(modifier=m.name)
            bpy.data.objects.remove(p, do_unlink=True)
        comb["panel_id"] = "P05" if sgn > 0 else "P06"
        comb["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(comb)
    print("  fender vent: a louvre comb -- four diagonal 6 mm slats on two rails, one part -> P05 / P06")


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
    # 2026-09-29: at the CORNER (PROJECTOR moved, see statev_skeleton): the slot is cut in from
    # the corner face (which sits at spec X ~-800 at Y 650 / Z 550) back to the housing front,
    # and the frame stands just inside the face. The DRL line ends inside this slot.
    for sgn in (1, -1):
        cuts.append(box(f"CUT_LAMP_{'L' if sgn > 0 else 'R'}", coll,
                        -900, -620, min(sgn * 590, sgn * 700), max(sgn * 590, sgn * 700), 505, 625))
    for sgn in (1, -1):
        # -760..-732, not -790..-762: the corner face recedes from -803 at Y 600 to -774 at Y 700
        # (Z 550), and at -790 the frame's outer end stood 16 mm ahead of the skin. Measured.
        ob = frame(f"HEADLIGHT_SURROUND_{'L' if sgn > 0 else 'R'}", coll,
                   -760, -732, min(sgn * 596, sgn * 694), max(sgn * 596, sgn * 694), 511, 619, 18.0)
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
                  -686, -514, min(sgn * 584, sgn * 706), max(sgn * 584, sgn * 706),
                  499, 621, 5.0, "front")
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
    # ---- 5b. THE TAIL CORNER POCKETS, 2026-09-29 (v049). ref-09's rear view: the flat tail
    # panel ends at half-width ~810 and OUTBOARD of it, under each L-end of the light bar, is a
    # dark vertical opening (hw ~700..810, from the diffuser top to just under the lamp) with the
    # body's corner standing outboard of it as a blade down to the diffuser. The same construction
    # as the nose corners in v048: a box cut from BEHIND into the boxed tail (S13/S13b), stopping
    # at a floor so the corner keeps its outer skin. Z stops 18 mm under the tail-end housing.
    # Measured after the first cut (Y 690..800): the boxed tail's skin at 3200 sits at hw ~765
    # and at 3250 at ~685, so a box to 800 had no outer wall anywhere and the corner was a notch
    # open to the side, exactly the v047 nose corner. ref-09 shows the corner open to the side too
    # (the tall dark slot at the rear corner of its side view), with the BLADE outboard of it as
    # its own element standing proud of the skin -- which is what the render's corner is, not a
    # wall. So: the pocket keeps Y 690..760 (a 5..10 mm lip at 3200, none behind it), and the
    # blade is a separate part, P52 / P53 TAIL_CORNER_BLADE, standing at Y +-850 from the haunch
    # skin (hw ~835 at 3080) back to 3230, Z 150..600, 30 mm thick, flaring nothing: the skin
    # behind 3100 is inboard of it, so the blade is in the air with the pocket between it and
    # the tail panel, as in the reference.
    TC = dict(x_floor=3180.0, y_in=690.0, y_out=760.0, z0=340.0, z1=575.0)
    for sgn in (1, -1):
        cuts.append(box(f"CUT_TAIL_CORNER_{'L' if sgn > 0 else 'R'}", coll,
                        TC["x_floor"], 3500.0, min(sgn * TC["y_in"], sgn * TC["y_out"]),
                        max(sgn * TC["y_in"], sgn * TC["y_out"]), TC["z0"], TC["z1"]))
    for sgn in (1, -1):
        bl = blade(f"TAIL_CORNER_BLADE_{'L' if sgn > 0 else 'R'}", coll,
                   [(3060.0, sgn * 850.0, 150.0, 600.0), (3150.0, sgn * 850.0, 150.0, 600.0),
                    (3230.0, sgn * 840.0, 190.0, 560.0)], 30.0)
        bl["panel_id"] = "P52" if sgn > 0 else "P53"
        bl["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(bl)
    print(f"  tail corner pockets: cut from behind to a floor at {TC['x_floor']:.0f}, Y {TC['y_in']:.0f}.."
          f"{TC['y_out']:.0f}, Z {TC['z0']:.0f}..{TC['z1']:.0f}, open to the side;")
    print("    tail corner blades: 30 mm fins at Y +-850, spec X 3060..3230, Z 150..600 -> P52 / P53")

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

    # ---- 6b. THE ROCKER CHANNEL, 2026-09-28. A DECIDED envelope since 2026-09-14 (deep undercut
    # along the sill, full door aperture, ref-08) that was never built. Now that the rocker stands
    # out as a blade (statev_master_volumes ROCKER_BLADE), the undercut is a prism pocket cut in
    # from the blade's face: Z 195..285, 68 deep, so its floor sits ~850 against a donor sill of
    # ~818 -- 32 mm of air, inside the rule. Walls vertical, so it reads as a shelf with a lip.
    for sgn in (1, -1):
        y_face = surface_y(1000.0, 240.0) or 918.0
        st = [(470.0, 195.0, 285.0), (1000.0, 195.0, 285.0), (1610.0, 195.0, 285.0)]
        c = prism(f"CUT_ROCKER_CHANNEL_{'L' if sgn > 0 else 'R'}", coll, st,
                  sgn * (y_face + 60.0), sgn * (y_face - 68.0))
        cuts.append(c)
    print(f"  rocker channel: undercut along the sill, spec X 470..1610, Z 195..285, 68 mm in from Y {y_face:.0f}")

    # ---- 6c. THE CORNER INTAKES AS BOXES, 2026-09-29. statev_master_volumes carves them as
    # rounded bites (NOSE_MOUTH); ref-09's corners are angular boxes with a vertical bar in each.
    # A box pocket gives the bite vertical walls and a flat ceiling under the lamp slot, and a
    # 20 mm blade stands in it. Functional: these are the brake-duct inlets (BRAKE_DUCT_F).
    # 2026-09-29 (v048): a POCKET, not a notch. The Y 600..820 box ran out through the corner
    # skin (which sat at 600..740 there), so the corner was cut away sideways and had no outer
    # wall -- ref-09's corner intake is an opening IN the chamfered corner face, half-width
    # 578..773 in the front view, with the body's corner edge outboard of it running down to the
    # splitter. With the nose now a chamfered box (S00..S02: 508 -> 765 across -950..-780) the
    # corner face carries hw 585..745 between -920 and -790, and an axis-aligned box in X from
    # ahead of the tip to a floor at -750 opens it 40 mm deep at the outer end and ~170 at the
    # inner, leaving 20-35 mm of skin outboard. Z 240..480: the same height as the mouth, the top
    # 25 mm under the lamp slot (505).
    CORNER = dict(x_floor=-750.0, y_in=585.0, y_out=745.0, z0=240.0, z1=480.0)
    for sgn in (1, -1):
        cuts.append(box(f"CUT_CORNER_{'L' if sgn > 0 else 'R'}", coll,
                        -1000.0, CORNER["x_floor"], min(sgn * CORNER["y_in"], sgn * CORNER["y_out"]),
                        max(sgn * CORNER["y_in"], sgn * CORNER["y_out"]), CORNER["z0"], CORNER["z1"]))
    for sgn in (1, -1):
        # the bar stands in the pocket's lateral middle (Y 665), from 10 mm inside the floor to
        # the face; the chamfer face at Y 665 sits near -845, and the bar's front end is read off
        # the built skin so it never stands ahead of it.
        yb = sgn * 665.0
        xf = None
        for zt in (300.0, 360.0, 420.0):
            # probed from AHEAD of the car (repo +X is forward): the origin sits 1.5 m ahead
            # of the target and the ray runs back into the face. Written the other way round
            # the ray started inside the car and the bar's front end landed at spec X +342.
            p, n = surface_hit(mathutils.Vector((mm(1000.0), mm(yb), mm(zt))),
                               [(1.5, 0.0, 0.0)])
            if p is not None:
                xf = -p.x * 1000.0 if xf is None else max(xf, -p.x * 1000.0)
        x_front = (xf + 6.0) if xf is not None else -830.0
        bl = blade(f"CORNER_BLADE_{'L' if sgn > 0 else 'R'}", coll,
                   [(x_front, yb, CORNER["z0"] + 10.0, CORNER["z1"] - 10.0),
                    (CORNER["x_floor"] - 20.0, yb, CORNER["z0"] + 10.0, CORNER["z1"] - 10.0)], 20.0)
        bl["panel_id"] = "P48" if sgn > 0 else "P49"
        bl["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(bl)
    print(f"  corner intakes: pockets in the chamfer face, Y {CORNER['y_in']:.0f}..{CORNER['y_out']:.0f}, "
          f"Z {CORNER['z0']:.0f}..{CORNER['z1']:.0f}, floor at {CORNER['x_floor']:.0f}, a 20 mm bar in each -> P48 / P49")

    # ---- 7. THE CENTRAL MOUTH, 2026-09-26. docs/14 locks "a large central opening to the
    # radiators" and the body never had one: what statev_master_volumes called NOSE_MOUTH eats in
    # from the SIDE and was two corner bites. Read off ref-09's front view: a trapezoid right under
    # the DRL, half-width 357 at the top and 467 at the bottom, about 190 tall, a splitter lip under
    # it, and the corner intakes outboard of a ~140 mm painted strake. Built like the rear mask: a
    # pocket with vertical walls to a floor plane, and a frame standing in it as the mask part.
    # The FRONT_MASK envelope in the skeleton (spec X -920..-820, Y +-325, Z 235..385) sits inside it.
    # What the opening FEEDS is a donor question (the 986 carries its radiators in the corners):
    # the shape is ours, the duct behind the floor is not drawn.
    def trap(name, x0, x1, hw_lo, z_lo, hw_hi, z_hi):
        v = [(-mm(x), mm(y), mm(z)) for x in (x0, x1)
             for (y, z) in ((-hw_lo, z_lo), (-hw_hi, z_hi), (hw_lo, z_lo), (hw_hi, z_hi))]
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
    # 2026-09-29 (v048): the trapezoid was read UPSIDE DOWN on 2026-09-26. Re-read on the front
    # view enlarged 3x (car 1520 px = 1850 mm; vertical scale from the splitter's underside at
    # Z 120 to the DRL centre at 500): the mouth is WIDER AT THE TOP -- half-width ~380 at the top
    # edge, ~320 at the bottom, Z ~220..430, 70 mm of face left under the DRL. The old
    # 450-bottom / 340-top mouth was the render's shape mirrored about its own mid-height.
    MOUTH = dict(x_face=-1050.0, x_floor=-820.0, hw_lo=320.0, z_lo=220.0, hw_hi=380.0, z_hi=430.0)
    cuts.append(trap("CUT_MOUTH", MOUTH["x_face"], MOUTH["x_floor"],
                     MOUTH["hw_lo"], MOUTH["z_lo"], MOUTH["hw_hi"], MOUTH["z_hi"]))
    fm = trap("FRONT_MASK", -852.0, -830.0, MOUTH["hw_lo"], MOUTH["z_lo"], MOUTH["hw_hi"], MOUTH["z_hi"])
    fv = trap("FRONT_MASK_void", -858.0, -824.0, MOUTH["hw_lo"] - 26.0, MOUTH["z_lo"] + 26.0,
              MOUTH["hw_hi"] - 26.0, MOUTH["z_hi"] - 26.0)
    m = fm.modifiers.new("void", "BOOLEAN")
    m.operation, m.object, m.solver = "DIFFERENCE", fv, "EXACT"
    bpy.context.view_layer.objects.active = fm
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(fv, do_unlink=True)
    fm["panel_id"] = "P43"
    fm["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
    made.append(fm)
    print(f"  central mouth: trapezoid pocket {2*MOUTH['hw_hi']:.0f} wide at the top / {2*MOUTH['hw_lo']:.0f} at the "
          f"bottom x {MOUTH['z_hi']-MOUTH['z_lo']:.0f} tall (Z {MOUTH['z_lo']:.0f}..{MOUTH['z_hi']:.0f}) to a floor at spec X {MOUTH['x_floor']:.0f},")
    print("    a 26 mm frame standing in it -> P43 FRONT_MASK; the corner bites became corner intakes")

    # ---- 8. DIFFUSER FINS, 2026-09-26. ref-09's rear detail: a rising floor with four tall fins,
    # two each side of the exhaust housing. The floor now rises (DIFFUSER_FLOOR in
    # statev_master_volumes); each fin is a 16 mm blade standing in it, its top 12 mm inside the
    # floor surface and its bottom at Z 125 -- the body's own floor is Z 120, so the 120 mm road
    # clearance is untouched. The tail narrows to ~260 mm at spec X 3420, so the outer pair stops
    # at 3300 where the underside is still ~960 wide; the inner pair runs to 3400.
    def floor_z(sx):
        a = [(-mm(sx), mm(0.0), mm(-1.0))]
        best = None
        for o in body_objects():
            inv = o.matrix_world.inverted()
            origin = inv @ mathutils.Vector((-mm(sx), 0.0, -1.0))
            d = inv.to_3x3() @ mathutils.Vector((0.0, 0.0, 1.0))
            h, loc, n, i = o.ray_cast(origin, d)
            if h:
                z = (o.matrix_world @ loc).z * 1000.0
                best = z if best is None else min(best, z)
        return best
    for pid_l, pid_r, y, x_end, nm in (("P44", "P45", 150.0, 3400.0, "INNER"),
                                       ("P46", "P47", 330.0, 3300.0, "OUTER")):
        xs = [3000.0 + k * (x_end - 3000.0) / 4.0 for k in range(5)]
        for sgn in (1, -1):
            st = []
            for x in xs:
                fz = floor_z(x)
                if fz is None:
                    continue
                st.append((x, sgn * y, 125.0, fz + 12.0))
            if len(st) < 2:
                continue
            b = blade(f"DIFFUSER_FIN_{nm}_{'L' if sgn > 0 else 'R'}", coll, st, 16.0)
            b["panel_id"] = pid_l if sgn > 0 else pid_r
            b["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
            made.append(b)
    print("  diffuser fins: four 16 mm blades standing in the rising floor, bottoms at Z 125")
    print("    -> P44 / P45 inner at Y +-150, P46 / P47 outer at Y +-330")

    # ---- 9. THE DRL GROOVE, 2026-09-28. The DRL blade had been a curve in 04_LIGHTING since
    # 2026-09-14 and nothing was ever cut for it -- the front's strongest signature in ref-09, a
    # continuous thin line of light across the nose, existed as an envelope only. The Hella
    # LEDayFlex strip mounts in a channel, so the housing IS a groove in the fascia: a tube of
    # radius 8 swept along DRL_PATH, its axis 4 mm inside the skin (so the groove is ~12 deep for
    # the 14 x 12 element), cut from the body. Height from DRL_Z (skeleton): 420 at the centre,
    # 490 at the corner, above the mouth and under the projector slot. No separate part: the
    # groove's walls print with P01, exactly as the mouth's do.
    DRL_PATH, DRL_Z = _sk["DRL_PATH"], _sk["DRL_Z"]
    tz_ = _sk["table_z"]
    for sgn in (1, -1):
        pts = []
        for spec_x, ty in DRL_PATH:
            z = tz_(DRL_Z, abs(ty))
            target = mathutils.Vector((-mm(spec_x), mm(sgn * ty), mm(z)))
            best = None
            for o in body_objects():
                inv = o.matrix_world.inverted()
                for origin_off in ((-1.5, 0.0, 0.0), (0.0, sgn * 1.5, 0.0), (-1.0, sgn * 1.0, 0.0)):
                    origin = target + mathutils.Vector(origin_off)
                    d = (target - origin).normalized()
                    h, loc, n, i = o.ray_cast(inv @ origin, (inv.to_3x3() @ d).normalized())
                    if h:
                        w = o.matrix_world @ loc
                        nw = (o.matrix_world.to_3x3() @ n).normalized()
                        dist = (w - target).length
                        if best is None or dist < best[0]:
                            best = (dist, w, nw)
            if best is None:
                continue
            _, w, nw = best
            # axis ON the skin (2026-09-29), not 4 mm inside it: with the axis inside, the
            # channel was wider inside than at its mouth -- an undercut whose lip faces pointed
            # backward, so solidify built their wall OUTWARD and the fascia file reached 953
            # against the locked 950. A half-round channel cannot undercut.
            pts.append(w)
        if len(pts) < 3:
            continue
        cu = bpy.data.curves.new(f"CUT_DRL_{'L' if sgn > 0 else 'R'}", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, v in zip(sp.points, pts):
            p.co = (v.x, v.y, v.z, 1.0)
        cu.bevel_depth = 0.007   # 14 wide, 7 deep: the 14 x 12 element sits proud by 5, a line of light
        cu.bevel_resolution = 4
        cu.use_fill_caps = True
        co = bpy.data.objects.new(cu.name, cu)
        coll.objects.link(co)
        bpy.context.view_layer.objects.active = co
        co.select_set(True)
        bpy.ops.object.convert(target="MESH")
        cm = bpy.context.view_layer.objects.active
        bm = bmesh.new()
        bm.from_mesh(cm.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(cm.data)
        bm.free()
        cuts.append(cm)
    print("  DRL groove: a radius-7 half-round along DRL_PATH, axis on the skin, Z 420 centre .. 490 corner, cut from the fascia")

    # ---- 10. THE BUTTRESS BLADES, 2026-09-29, as SHAPE-ONLY masters. docs/14 blocks the deck:
    # its height sits in the volume the soft top folds into, and only scan S2 can say where that
    # volume is. What is NOT blocked by that is a blade standing OUTBOARD of the fold envelope:
    # the guessed ROOF_FOLD_ENVELOPE ends at Y 650, and these stand at Y 685..725 on the built
    # quarter top, spec X 1800..2750, tops from 1120 behind the hoops to the deck at the tail.
    # The reference's sails, read off ref-09's rear view: tall, thin, just under the hoop tops.
    # Everything about them that is not the blade -- the deck between them, their feet -- stays
    # BLOCKED; the blade goes to the shape-only tier with that written on it, so the rear can be
    # judged against the render as a whole and nothing here is a part to bond before S2.
    BUT_TOP = [(1800, 1120), (2000, 1120), (2200, 1110), (2415, 1090), (2600, 1040), (2750, 990)]
    for sgn in (1, -1):
        st = []
        for sx, ztop in BUT_TOP:
            foot = surface_z(sx, sgn * 705.0)
            if foot is None:
                continue
            st.append((float(sx), sgn * 705.0, foot - 14.0, float(ztop)))
        if len(st) < 3:
            continue
        bl = blade(f"BUTTRESS_{'L' if sgn > 0 else 'R'}", coll, st, 40.0)
        bl["panel_id"] = "P17" if sgn > 0 else "P18"
        bl["stage"] = ("03 element — SHAPE ONLY: stands outboard of the GUESSED roof fold envelope "
                       "(Y 650); the deck between the blades and the blade's own foot wait on scan S2")
        made.append(bl)
    print("  buttress blades: 40 mm sails at Y +-705, spec X 1800..2750, tops 1120 -> 990, outboard of the")
    print("    guessed fold envelope -> P17 / P18 as SHAPE ONLY; the deck between them stays BLOCKED")

    # ---- 11. THE STRAKES AND THE SPLITTER LIP, 2026-09-29. ref-09's mask is faceted: from each
    # lamp's inner end a crease runs down and inward to the mouth's upper corner (the cheekbone),
    # and under the mouth the splitter lip stands ahead of the face. The cheekbone is a ridge that
    # follows the skin (ribbon), 24 wide, 12 proud, 12 embedded -> P50 / P51. The lip: the length
    # is locked at 4370 so nothing may stand ahead of the tip; instead the face is RECESSED 40 mm
    # just above the lip (Z 150..200), which leaves the lip standing 40 mm proud of the face
    # above it -- the same read, inside the locked box. Printed with P01/P28 as pocket walls.
    for sgn in (1, -1):
        rb = ribbon(f"STRAKE_{'L' if sgn > 0 else 'R'}", coll,
                    # ends at Y 500, not at the mouth corner (Y 365): the face is flat at the locked
                    # tip (-950) inboard of Y ~450, and a ridge 12 mm proud there stood at -962 --
                    # the length read 4382 against 4370. Proud 10 from Y 500 out, where the face
                    # already sits behind -936. Nothing may stand ahead of the tip.
                    # v048: over the corner pocket (Y 585..745, top 480) the ridge must clear the
                    # pocket's ceiling -- its lower edge is 12 under the path, so the path stays
                    # above 495 there; it comes down to 460 only inboard of the pocket (Y 545),
                    # and stops at Y 545 where the chamfer face still sits behind -936.
                    [(-775.0, sgn * 660.0, 525.0), (-830.0, sgn * 600.0, 505.0), (-885.0, sgn * 545.0, 462.0)],
                    # v048: probed from AHEAD only. With the forward-from-inside and sideways
                    # probes the nearest hit for the two outer targets was the FLANK (Y 769 /
                    # 689), so the ridge started on the corner's side, not under the lamp; the
                    # inside probe itself hits the cabin cut at spec X +285 and never the face.
                    [(1.5, 0.0, 0.0)], 24.0, 10.0, 14.0)
        if rb is not None:
            rb["panel_id"] = "P50" if sgn > 0 else "P51"
            rb["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
            made.append(rb)
    # top at 194, not 200: at 200 the recess's ceiling coincided with the mouth's floor over
    # |Y| < 450 and the boolean left a 40 x 438 x 3 strip and 8 open edges in P01's file.
    cuts.append(box("CUT_LIP_RECESS", coll, -1000.0, -910.0, -620.0, 620.0, 150.0, 194.0))
    print("  strakes: skin-following ridges from the lamp ends to the mouth's corners -> P50 / P51;")
    print("    splitter lip: the face recessed 40 mm over Z 150..200 so the lip stands proud inside the locked length")

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
