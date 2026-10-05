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


def yz_prism(name, coll, x0, x1, poly):
    """A convex polygon in Y-Z (spec mm) swept along spec X from x0 to x1. The corner intakes are
    not rectangles in the front view, and a box cannot lean an edge."""
    n = len(poly)
    v = [(-mm(x), mm(y), mm(z)) for x in (x0, x1) for (y, z) in poly]
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    f += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
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


def inset_poly(poly, d):
    """A convex polygon (u, v) moved inward by d (negative: outward), corner by corner."""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    lines = []
    for i in range(n):
        (a, b), (c, e) = poly[i], poly[(i + 1) % n]
        L = math.hypot(c - a, e - b)
        nx, ny = -(e - b) / L * sgn, (c - a) / L * sgn      # inward normal
        lines.append(((a + nx * d, b + ny * d), (c - a, e - b)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def _inside(poly, u, v):
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    for i in range(n):
        (a, b), (c, e) = poly[i], poly[(i + 1) % n]
        if ((c - a) * (v - b) - (e - b) * (u - a)) * (1 if area > 0 else -1) < 0:
            return False
    return True


def hex_grille(name, coll, poly, rim, pitch, bar, thick, to_world):
    """A hexagonal mesh as ONE printable plate: the convex outline `poly` in a local (u, v) frame,
    `thick` deep, with a hexagonal hole wherever a whole hexagon fits at least `rim` inside the
    outline -- so the edge is a continuous frame and nothing is a loose bar. Built flat in (u, v, w)
    and mapped to the car by the AFFINE `to_world(u, v, w) -> (spec_x, y, z)` after the boolean,
    which keeps a planar grid planar and a slanted one slanted (2026-10-03, v058)."""
    def prism_mesh(nm, pts2, w0, w1):
        k = len(pts2)
        v = [(u / 1000.0, vv / 1000.0, w0 / 1000.0) for u, vv in pts2] + \
            [(u / 1000.0, vv / 1000.0, w1 / 1000.0) for u, vv in pts2]
        f = [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))] + \
            [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
        return v, f
    pv, pf = prism_mesh(name, poly, -thick / 2.0, thick / 2.0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(pv, [], pf)
    me.update()
    plate = bpy.data.objects.new(name, me)
    coll.objects.link(plate)
    inner = inset_poly(poly, rim)
    r = (pitch - bar) / math.sqrt(3.0)              # hole circumradius, pointy-top
    us = [q[0] for q in poly]
    vs = [q[1] for q in poly]
    cv, cf, holes = [], [], 0
    row = 0
    v0 = min(vs)
    while v0 + row * pitch * math.sqrt(3.0) / 2.0 <= max(vs):
        vc = v0 + row * pitch * math.sqrt(3.0) / 2.0
        uc = min(us) + (pitch / 2.0 if row % 2 else 0.0)
        while uc <= max(us):
            hexp = [(uc + r * math.cos(math.radians(90 + 60 * k)),
                     vc + r * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
            if all(_inside(inner, a, b) for a, b in hexp):
                hv, hf = prism_mesh("h", hexp, -thick, thick)
                base = len(cv)
                cv += hv
                cf += [tuple(base + i for i in f) for f in hf]
                holes += 1
            uc += pitch
        row += 1
    if holes:
        cm = bpy.data.meshes.new(name + "_holes")
        cm.from_pydata(cv, [], cf)
        cm.update()
        cut_o = bpy.data.objects.new(name + "_holes", cm)
        coll.objects.link(cut_o)
        for o_ in (plate, cut_o):
            bm = bmesh.new()
            bm.from_mesh(o_.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(o_.data)
            bm.free()
        m = plate.modifiers.new("holes", "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", cut_o, "EXACT"
        bpy.context.view_layer.objects.active = plate
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(cut_o, do_unlink=True)
    for vtx in plate.data.vertices:
        sx, y, z = to_world(vtx.co.x * 1000.0, vtx.co.y * 1000.0, vtx.co.z * 1000.0)
        vtx.co = (-sx / 1000.0, y / 1000.0, z / 1000.0)
    plate.data.update()
    bm = bmesh.new()
    bm.from_mesh(plate.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(plate.data)
    bm.free()
    plate["holes"] = holes
    return plate


def hexa(name, coll, pts):
    """A closed six-faced solid from 8 spec-mm corners: 0-3 one end, 4-7 the other, same order."""
    v = [(-mm(x), mm(y), mm(z)) for x, y, z in pts]
    f = [(0, 1, 2, 3), (7, 6, 5, 4)] + [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)]
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


def shell(name, coll, x0, x1, y0, y1, z0, z1, wall, open_face, clip=False):
    """A closed box with its inside taken out and one face opened -- a lamp housing. `open_face` is
    the spec-X end left off, because that is the end the lamp looks out of. With clip the OUTER
    solid is first intersected with the inset skin, so the housing follows the inside of the body;
    both operands are closed then, which is the only kind of boolean that has held in this file."""
    outer = box(name, coll, x0, x1, y0, y1, z0, z1)
    if clip:
        sk = inset_skin(coll, x0, x1)
        clip_to(outer, sk)
        bpy.data.objects.remove(sk, do_unlink=True)
    ix0 = x0 - 8 if open_face == "front" else x0 + wall
    ix1 = x1 - wall if open_face == "front" else x1 + 8
    inner = box(name + "_void", coll, ix0, ix1, y0 + wall, y1 - wall, z0 + wall, z1 - wall)
    m = outer.modifiers.new("void", "BOOLEAN")
    m.operation, m.object, m.solver = "DIFFERENCE", inner, "EXACT"
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(inner, do_unlink=True)
    return outer


INSET_MM = 3.0   # a housing or duct stays this far inside the skin (the laminate and the bond)


def inset_skin(coll, x0, x1):
    """A closed copy of the body volume that holds spec X x0..x1, every vertex moved INWARD along
    its normal by INSET_MM. Intersected with a housing's or a duct's outer solid, it makes the part
    follow the inside of the skin, as a real housing bonded behind a panel does (2026-10-02: the
    headlamp housings stood 39 mm above the bonnet at their outer rear corner, the tail housings
    32 mm out of the narrowed tail, the duct ran through the rear wheel opening)."""
    best, ov = None, -1.0
    for o in body_objects():
        xs = [-(o.matrix_world @ v.co).x * 1000.0 for v in o.data.vertices]
        o_ = min(max(xs), x1) - max(min(xs), x0)
        if o_ > ov:
            best, ov = o, o_
    cp = best.copy()
    cp.data = best.data.copy()
    cp.name = "_inset_" + best.name
    for m in list(cp.modifiers):
        cp.modifiers.remove(m)
    coll.objects.link(cp)
    bm = bmesh.new()
    bm.from_mesh(cp.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    d = INSET_MM / 1000.0
    moves = [(v, v.normal.copy()) for v in bm.verts]
    for v, n in moves:
        v.co -= n * d
    bm.to_mesh(cp.data)
    bm.free()
    return cp


def clip_to(ob, cutter):
    m = ob.modifiers.new("clip", "BOOLEAN")
    m.operation, m.object, m.solver = "INTERSECT", cutter, "EXACT"
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)


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
    # the outer tube follows the inside of the skin and stays out of the wheel opening (2026-10-02)
    sk = inset_skin(coll, stations[0][0], stations[-1][0])
    clip_to(ob, sk)
    bpy.data.objects.remove(sk, do_unlink=True)
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
PARASITIC = False  # 2026-09-29: the corner bars, strakes and tail corner blades are retired (owner's review)
SAILS = False      # 2026-10-05: the buttress boards P17/P18 are retired (owner's review; see section 10)


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
    # 2026-10-02: the bottom edge is kept 12 mm above the REAR ARCH (centre 2415 / Z 337.5,
    # radius 365, the cutter in statev_master_volumes): its rear-bottom corner stood 67 mm into
    # the wheel opening, visible in the well (check_floating.py).
    ax_, rad_ = _sk["ARCHES"]["REAR"][0], _sk["ARCHES"]["REAR"][1]
    zc_ = _sk["ARCHES"]["REAR"][3] / 2.0

    def above_arch(x, z):
        dx = abs(x - ax_)
        return z if dx >= rad_ else max(z, zc_ + math.sqrt(rad_ * rad_ - dx * dx) + 12.0)
    for sgn in (1, -1):
        b = blade(f"INTAKE_BLADE_{'L' if sgn > 0 else 'R'}", coll,
                  [(sx_, sgn * (y_surf - yo), above_arch(sx_, z0_), z1_) for sx_, yo, z0_, z1_ in
                   ((1975, 30, 470, 686), (2030, 46, 455, 696), (2075, 50, 452, 694),
                    (2120, 44, 470, 680))],
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
        for sx in (-215, -161, -107, -53, 1, 55, 145):
            # the lowest skin along the whole slat, not at the slot centre: measured at Y 465
            # the outboard end of each slat stood 6.5 mm above the bonnet (check_floating.py)
            ts = [t for t in (surface_z(sx, 391), surface_z(sx, 465), surface_z(sx + 90, 539),
                              surface_z(sx, 539)) if t]
            tops[sx] = (min(ts) - 12.0) if ts else 860.0
        z_top_rail = min(tops.values())
        # two rails along the slot walls, 4 mm off them, and four diagonal slats between
        comb = slab(f"FENDER_CHANNEL_{tag}", (-225.0, sgn * 391.0), (155.0, sgn * 391.0),
                    712.0, z_top_rail, 6.0)
        parts = [slab(f"_rail2_{tag}", (-225.0, sgn * 539.0), (155.0, sgn * 539.0),
                      712.0, z_top_rail, 6.0)]
        # v059: SIX slats at a 54 mm pitch instead of four at 90 -- ref-09's vent carries 5..6;
        # the first and last stay where they were, so the comb still ends inside the slot
        for sx in (-215, -161, -107, -53, 1, 55):
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
    print("  fender vent: a louvre comb -- six diagonal 6 mm slats on two rails, one part -> P05 / P06")


    # ---- 4. the rear. In ref-05 the tail is not a wall: a recessed centre mask sits between the
    # light bar's two ends, the exhausts come through their own surrounds, and the plate drops into
    # a recess below. Each of those is a pocket with a part standing in it, and each is a register
    # entry that has been BLOCKED for want of geometry.
    #
    # NOTHING HERE GOES NEAR THE ROOF. P17, P18, P19, P42, P20, P23 and P33 are ROOF_BLOCKED and
    # stay untouched; the fold envelope is guessed at spec X 1240 to 1760 and everything below is
    # behind 3300.
    # 2026-09-30 (v053), owner's review, second pass: the centre mask pocket with its frame, the
    # plate recess frame and the exhaust bar were three nested rectangles hanging in their own
    # pockets under the light bar. ref-09's tail is a plain panel there with exactly two round
    # tips in the diffuser centre (docs/14 lock). So: no centre mask (P34 retired); the plate
    # keeps a SHALLOW recess because a plate has to sit somewhere legal, but no frame part (P36
    # retired); the exhausts are two ROUND openings on the EXHAUST envelope (spec X 3220, Y +-65,
    # Z 430, 95 dia) cut straight through the tail, tips bought, no surround part (P35 retired).
    cuts.append(box("CUT_PLATE", coll, 3395, 3425, -255, 255, 250, 372))
    for sgn in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm(52.0), depth=mm(300.0), vertices=48,
                                            location=(-mm(3300.0), mm(sgn * 65.0), mm(430.0)))
        cy = bpy.context.active_object
        cy.name = f"CUT_EXHAUST_{'L' if sgn > 0 else 'R'}"
        cy.rotation_euler = (0.0, math.radians(90.0), 0.0)
        for c in list(cy.users_collection):
            c.objects.unlink(cy)
        coll.objects.link(cy)
        bpy.context.view_layer.update()
        cuts.append(cy)
    print("  rear: a 30 mm plate recess and two round 104 mm exhaust openings on the EXHAUST envelope;")
    print("    the centre mask (P34), the plate frame (P36) and the exhaust surround (P35) are retired")

    # ---- 5. the headlamp as a blade, not a cavity. A slot across the nose with a thin frame in it,
    # so what shows is a line of light behind a frame -- which is what "thin light blades" means and
    # the only road-legal way to get it, since the E-marked module itself may never be modified.
    # 2026-09-29: at the CORNER (PROJECTOR moved, see statev_skeleton): the slot is cut in from
    # the corner face (which sits at spec X ~-800 at Y 650 / Z 550) back to the housing front,
    # and the frame stands just inside the face. The DRL line ends inside this slot.
    for sgn in (1, -1):
        cuts.append(box(f"CUT_LAMP_{'L' if sgn > 0 else 'R'}", coll,
                        -900, -620, min(sgn * 590, sgn * 700), max(sgn * 590, sgn * 700), 505, 625))
    # RETIRED 2026-09-30 (v053), owner's review, second pass ("flying elements"): the 18 mm frame
    # stood in the lamp slot with air all round it and read as a box floating at the corner. The
    # slot is the lamp's aperture and stays; the housing (P24/P25) stands behind it and is what
    # the aperture shows. The frame's code stays behind PARASITIC.
    for sgn in ((1, -1) if PARASITIC else ()):
        # -760..-732, not -790..-762: the corner face recedes from -803 at Y 600 to -774 at Y 700
        # (Z 550), and at -790 the frame's outer end stood 16 mm ahead of the skin. Measured.
        ob = frame(f"HEADLIGHT_SURROUND_{'L' if sgn > 0 else 'R'}", coll,
                   -760, -732, min(sgn * 596, sgn * 694), max(sgn * 596, sgn * 694), 511, 619, 18.0)
        ob["panel_id"] = "P29" if sgn > 0 else "P30"
        ob["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(ob)
    print("  headlamp: a slot across the nose, the housing's face showing in it (the frame P29/P30 is retired)")


    # ---- 6. the lamp housing behind the blade. PROJECTOR is a DECIDED envelope at spec X -600,
    # Y +-560, Z 570, 150 x 110 x 110 for one Hella 90 mm bi-LED module, and the module itself may
    # never be modified -- so the housing is built around it with a wall and 6 mm of air, open at
    # the front where the P29 frame is.
    for sgn in (1, -1):
        h = shell(f"HEADLIGHT_HOUSING_{'L' if sgn > 0 else 'R'}", coll,
                  -686, -514, min(sgn * 584, sgn * 706), max(sgn * 584, sgn * 706),
                  499, 621, 5.0, "front", clip=True)
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
    # z0 340 -> 352 (v052): at 340 the pocket floor sat 4 mm above the undercut edge (Z ~336 at
    # 3220) and the boolean left a one-face sliver 10 x 12 mm each side, which panel_extract
    # counted as P21's second and third piece and the pilot refused to export the fascia.
    TC = dict(x_floor=3180.0, y_in=690.0, y_out=760.0, z0=352.0, z1=575.0)
    for sgn in (1, -1):
        cuts.append(box(f"CUT_TAIL_CORNER_{'L' if sgn > 0 else 'R'}", coll,
                        TC["x_floor"], 3500.0, min(sgn * TC["y_in"], sgn * TC["y_out"]),
                        max(sgn * TC["y_in"], sgn * TC["y_out"]), TC["z0"], TC["z1"]))
    for sgn in ((1, -1) if PARASITIC else ()):   # retired 2026-09-29, see the corner bars
        bl = blade(f"TAIL_CORNER_BLADE_{'L' if sgn > 0 else 'R'}", coll,
                   [(3060.0, sgn * 850.0, 150.0, 600.0), (3150.0, sgn * 850.0, 150.0, 600.0),
                    (3230.0, sgn * 840.0, 190.0, 560.0)], 30.0)
        bl["panel_id"] = "P52" if sgn > 0 else "P53"
        bl["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(bl)
    print(f"  tail corner pockets: cut from behind to a floor at {TC['x_floor']:.0f}, Y {TC['y_in']:.0f}.."
          f"{TC['y_out']:.0f}, Z {TC['z0']:.0f}..{TC['z1']:.0f}, open to the side;")
    if PARASITIC:
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
        sk = inset_skin(coll, TE["x0"], TB["x1"])
        for tgt, src, op in ((o1, o2, "UNION"), (o1, sk, "INTERSECT"), (i1, i2, "UNION"),
                             (o1, i1, "DIFFERENCE")):
            m = tgt.modifiers.new("b", "BOOLEAN")
            m.operation, m.object, m.solver = op, src, "EXACT"
            bpy.context.view_layer.objects.active = tgt
            bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(sk, do_unlink=True)
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
    print("  P23 REAR_SPOILER retired (v060): the ducktail is the tail profile itself, not a part")

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
    # 2026-10-02 (v056): the inner edge LEANS. Measured on ref-09's front view (dark runs per row,
    # 1.814 mm/px across the 1850 body): the corner intake is widest at its top, Y ~440..776 under
    # the lamp, and its inner edge moves outboard going down, to Y ~590 at the bottom. Between it
    # and the mouth that leaves a painted wedge pointing UP -- the V the front is read by. The
    # outer edge stays at 745: at 770 the box ran out through the side of the chamfered corner
    # (v048). Same floor, same heights; panel_map tests the same quad (X_CORNER).
    CORNER_POLY = [(450.0, 480.0), (745.0, 480.0), (745.0, 240.0), (590.0, 240.0)]
    for sgn in (1, -1):
        cuts.append(yz_prism(f"CUT_CORNER_{'L' if sgn > 0 else 'R'}", coll, -1000.0, CORNER["x_floor"],
                             [(sgn * y, z) for (y, z) in CORNER_POLY]))
    # RETIRED 2026-09-29 (v051), owner's review: "parasitic elements". The bars in the corner
    # intakes, the cheekbone strakes and the tail corner blades were separate solids stuck on
    # the skin; in ref-09 the corresponding features are the body's own edges and creases, not
    # parts. Kept as code behind PARASITIC so the register decision is reversible in one line.
    for sgn in ((1, -1) if PARASITIC else ()):
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
    print(f"  corner intakes: quad pockets in the chamfer face, Y 450..745 at the top / 590..745 at the "
          f"bottom, Z {CORNER['z0']:.0f}..{CORNER['z1']:.0f}, floor at {CORNER['x_floor']:.0f}")

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
    def floor_z(sx, yy=0.0):
        best = None
        for o in body_objects():
            inv = o.matrix_world.inverted()
            origin = inv @ mathutils.Vector((-mm(sx), mm(yy), -1.0))
            d = inv.to_3x3() @ mathutils.Vector((0.0, 0.0, 1.0))
            h, loc, n, i = o.ray_cast(origin, d)
            if h:
                z = (o.matrix_world @ loc).z * 1000.0
                best = z if best is None else min(best, z)
        return best
    # v059: re-spaced 150/330 -> 120/255 so three fit EVENLY in the flat tunnel, which is
    # measured flat only to |Y| ~400..450 (outboard of that the floor drops into the legs' wall)
    for pid_l, pid_r, y, x_end, nm in (("P44", "P45", 120.0, 3400.0, "INNER"),
                                       ("P46", "P47", 255.0, 3300.0, "OUTER")):
        xs = [3000.0 + k * (x_end - 3000.0) / 4.0 for k in range(5)]
        for sgn in (1, -1):
            st = []
            for x in xs:
                fz = floor_z(x)
                if fz is None:
                    continue
                # v055: the fin's lower edge on the legs' line, so it stands IN the tunnel
                # between the legs instead of hanging 150-190 mm below a raised floor
                st.append((x, sgn * y, _sk["table_z"](_sk["DIFFUSER_LEGS"]["leg_z"], x), fz + 12.0))
            if len(st) < 2:
                continue
            b = blade(f"DIFFUSER_FIN_{nm}_{'L' if sgn > 0 else 'R'}", coll, st, 16.0)
            b["panel_id"] = pid_l if sgn > 0 else pid_r
            b["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
            made.append(b)
    # v059, 2026-10-03: a THIRD pair. ref-09's rear view carries three fins each side of the
    # exhaust box; ours had two. Y 490 was tried first and the tunnel is not flat there at any
    # station (measured: 23 mm lower at 3000). At Y 390 it is, as far back as the tail's narrowing
    # allows: the fin runs from 3000 to the last station where the floor at its outer face (Y 398)
    # is within 3 mm of the centre floor -- read off the body, not typed.
    st_e = {1: [], -1: []}
    for k in range(9):
        x = 3000.0 + k * 50.0
        f0, fy = floor_z(x), floor_z(x, 398.0)
        if f0 is None or fy is None or abs(fy - f0) > 3.0:
            break
        for sgn in (1, -1):
            st_e[sgn].append((x, sgn * 390.0, _sk["table_z"](_sk["DIFFUSER_LEGS"]["leg_z"], x), f0 + 12.0))
    for sgn in (1, -1):
        if len(st_e[sgn]) >= 3:
            b = blade(f"DIFFUSER_FIN_EDGE_{'L' if sgn > 0 else 'R'}", coll, st_e[sgn], 16.0)
            b["panel_id"] = "P58" if sgn > 0 else "P59"
            b["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
            made.append(b)
    x_e = st_e[1][-1][0] if st_e[1] else None
    print("  diffuser fins: six 16 mm blades in the tunnel between the legs, bottoms on the leg line")
    print(f"    -> P44 / P45 inner at Y +-120, P46 / P47 outer at Y +-255, P58 / P59 edge at Y +-390 "
          f"(3000..{x_e:.0f})" if x_e else "    -> edge pair NOT built: the tunnel is not flat at Y 390")

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
        # the groove's axis, kept for the picture (glossy_renders): the render's light line used to
        # follow DRL_PATH as written, whose spec X (-888 at the centre) is 60 mm INSIDE the nose
        # face at -950 -- the front's signature line was in every render and visible in none
        bpy.context.scene[f"statev_drl_axis_{'L' if sgn > 0 else 'R'}"] = [c for v in pts for c in (v.x, v.y, v.z)]
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
    # RETIRED 2026-10-05 (v062). The owner: "the sides behind the seats do not look right". ref-09's
    # top and side views, read together, show what these were standing in for: not thin sails but a
    # HUMP behind each seat -- as tall as the hoop, as wide as the seat, sloping back into the louvre
    # tray -- and from above, deck surface right up to the seat backs with no wall at the cabin edge.
    # A 40 mm board 950 mm long at Y 705 matched neither view. The humps sit exactly in the volume
    # the soft top folds into, so they wait on scan S2 with the deck (docs/14 J, superseded).
    for sgn in (() if not SAILS else (1, -1)):
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
    print("  buttress boards P17 / P18 retired (v062): ref-09 has humps behind the seats there, which")
    print("    wait on scan S2 with the deck")

    # ---- 10a. THE HUMPS BEHIND THE SEATS, 2026-10-05 (v063). The owner, after the boards were
    # retired: "continue with the humps behind the seats". ref-09, side and top read together: one
    # hump behind each seat, as tall as the hoop's shoulder, as wide as the seat, its top flat for
    # ~200 mm and then falling into the louvre tray. Built as a SHELL (4 mm, open underneath, its
    # rim 25 mm into the deck) so the print is a fairing, not 40 litres of plastic. SHAPE ONLY in the
    # strongest sense: it stands where the 986 stows its top under a lid behind the seats. The
    # precedent is the Boxster Spyder, whose humps are ON that lid and lift with it -- whether ours
    # can do the same is scan S2's answer, and nothing here is a part to bond before it.
    HUMP = dict(yc=345.0, wall=4.0, sink=25.0,
                st=[(1772.0, 1175.0, 215.0), (1850.0, 1175.0, 225.0), (1950.0, 1160.0, 222.0),
                    (2040.0, 1110.0, 210.0), (2120.0, 1040.0, 190.0), (2185.0, 985.0, 165.0)])

    def hump_solid(name, sgn, inset):
        rings = []
        n_ = 28
        for sx, ztop, w in HUMP["st"]:
            base = min([z_ for z_ in (surface_z(sx, sgn * (HUMP["yc"] + d)) for d in (-w, 0.0, w))
                        if z_ is not None] or [900.0]) - HUMP["sink"] - (8.0 if inset else 0.0)
            ztop_ = max(ztop, base + 40.0) - inset
            w_ = w - inset
            zm, hz = (ztop_ + base) / 2.0, (ztop_ - base) / 2.0
            ring = []
            for k in range(n_):
                t = 2.0 * math.pi * k / n_
                c_, s_ = math.cos(t), math.sin(t)
                yy = HUMP["yc"] + w_ * math.copysign(abs(c_) ** (2.0 / 3.5), c_)
                zz = zm + hz * math.copysign(abs(s_) ** (2.0 / 3.5), s_)
                ring.append((sx, sgn * yy, zz))
            rings.append(ring)
        if inset:   # the cavity stops short of both end caps, so the shell is closed at the ends
            rings[0] = [(x + inset, y, z) for x, y, z in rings[0]]
            rings[-1] = [(x - inset, y, z) for x, y, z in rings[-1]]
        verts = [(-mm(x), mm(y), mm(z)) for ring in rings for x, y, z in ring]
        faces = []
        for i in range(len(rings) - 1):
            for k in range(n_):
                a, b = i * n_ + k, i * n_ + (k + 1) % n_
                faces.append((a, b, b + n_, a + n_))
        faces.append(tuple(range(n_ - 1, -1, -1)))
        last = (len(rings) - 1) * n_
        faces.append(tuple(range(last, last + n_)))
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
    for sgn in (1, -1):
        outer = hump_solid(f"SEAT_HUMP_{'L' if sgn > 0 else 'R'}", sgn, 0.0)
        inner = hump_solid("_hump_void", sgn, HUMP["wall"])
        m = outer.modifiers.new("void", "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", inner, "EXACT"
        bpy.context.view_layer.objects.active = outer
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(inner, do_unlink=True)
        # open underneath: the shell is cut 10 mm under the deck surface, following it along X,
        # so its rim is buried in the deck and nothing below it is printed
        under = prism("_hump_under", coll,
                      [(sx - (6.0 if i == 0 else -6.0 if i == len(HUMP["st"]) - 1 else 0.0), 500.0,
                        (surface_z(sx, sgn * HUMP["yc"]) or 900.0) - 10.0)
                       for i, (sx, _zt, _w) in enumerate(HUMP["st"])],
                      sgn * 640.0, sgn * 50.0)
        m = outer.modifiers.new("under", "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", under, "EXACT"
        bpy.context.view_layer.objects.active = outer
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(under, do_unlink=True)
        outer["panel_id"] = "P63" if sgn > 0 else "P64"
        outer["stage"] = ("03 element — SHAPE ONLY: stands where the 986 stows its top; whether it "
                          "lifts with the lid (Boxster Spyder) is scan S2's answer")
        made.append(outer)
    print(f"  seat humps: {HUMP['wall']:.0f} mm shells at Y +-{HUMP['yc']:.0f}, spec X "
          f"{HUMP['st'][0][0]:.0f}..{HUMP['st'][-1][0]:.0f}, tops {HUMP['st'][0][1]:.0f} -> "
          f"{HUMP['st'][-1][1]:.0f} -> P63 / P64 (SHAPE ONLY, scan S2)")

    # ---- 10b. THE ENGINE-COVER LOUVRES, 2026-10-02 (v056). The owner: "the rear cover is very
    # different". It was not different, it was ABSENT: the deck and the cover are BLOCKED on the
    # roof (DECK_SPINE), no file carried them, and the assembled car had a hole behind the hoops.
    # ref-09's top view (6.51 mm/px, car 25..696 px = 4370 mm): a black louvre field spec X
    # ~2207..2891, centred, half-width ~384, between the haunches; its rear view shows the same
    # field as stacked horizontal bars -- transverse slats stepping down with the falling cover --
    # and the top view shows longitudinal lines, so the honest read of both is a CRATE. Built as
    # an aperture (a pocket whose walls print with P20 and whose floor does not: the louvres
    # vent the engine bay, AIRFLOW "engine_cooling") and a one-piece crate standing in it, tops
    # 8 mm under the skin. The deck's HEIGHT is not touched: everything here is under the
    # surface that already exists, and all of it is SHAPE ONLY on the roof question.
    LOUVRE = dict(x0=2210.0, x1=2890.0, hw=385.0, depth=95.0, crate=60.0, under=8.0, t=6.0)
    lx = [LOUVRE["x0"] + k * 56.67 for k in range(13)]
    lst = []
    for sx in lx:
        zs = [surface_z(sx, y) for y in (0.0, 190.0, LOUVRE["hw"])]
        zs = [z for z in zs if z is not None]
        if not zs:
            continue
        lst.append((sx, min(zs) - LOUVRE["depth"], max(zs) + 150.0))
    if len(lst) >= 3:
        cuts.append(prism("CUT_LOUVRE", coll, lst, LOUVRE["hw"], -LOUVRE["hw"]))

        def top_at(sx, ys):
            zs = [surface_z(sx, y) for y in ys]
            zs = [z for z in zs if z is not None]
            return (min(zs) - LOUVRE["under"]) if zs else None
        ribs_y = [0.0, 125.0, -125.0, 250.0, -250.0, 378.0, -378.0]
        x_in0, x_in1 = LOUVRE["x0"] + 4.0, LOUVRE["x1"] - 4.0
        # the crate's floor line: one bottom per station, under the LOWEST top at that station, so
        # every element reaches it and the union is one connected part
        bot = {}
        for sx in lx:
            t = top_at(sx, (0.0, 125.0, 250.0, 378.0))
            if t is not None:
                bot[sx] = t - LOUVRE["crate"]
        def bot_at(sx):
            ks = sorted(bot)
            if sx <= ks[0]:
                return bot[ks[0]]
            for a, b in zip(ks, ks[1:]):
                if a <= sx <= b:
                    return bot[a] + (bot[b] - bot[a]) * (sx - a) / (b - a)
            return bot[ks[-1]]
        crate = None
        parts = []
        for y in ribs_y:
            st = []
            for sx in [x_in0] + lx[1:-1] + [x_in1]:
                t = top_at(sx, (abs(y),))
                if t is not None:
                    st.append((sx, y, bot_at(sx) - 4.0, t))
            if len(st) >= 3:
                parts.append(blade(f"_rib_{y:.0f}", coll, st, LOUVRE["t"]))
        # the slats sit 22 mm BELOW the rib tops: from above the ribs are the lines (ref-09's plan
        # shows longitudinal lines), from behind the slats step down with the cover (its rear
        # view shows stacked bars). At one height the plan read as a chessboard (v056 first pass).
        n_sl = 7
        for k in range(1, n_sl + 1):
            sx = LOUVRE["x0"] + k * (LOUVRE["x1"] - LOUVRE["x0"]) / (n_sl + 1)
            t = top_at(sx, (0.0, 125.0, 250.0, 378.0))
            if t is not None:
                parts.append(slab(f"_slat_{k}", (sx, -378.0), (sx, 378.0), bot_at(sx), t - 22.0, LOUVRE["t"]))
        for sx in (x_in0 + 3.0, x_in1 - 3.0):
            t = top_at(sx, (0.0, 125.0, 250.0, 378.0))
            if t is not None:
                parts.append(slab(f"_end_{sx:.0f}", (sx, -381.0), (sx, 381.0), bot_at(sx) - 4.0, t, LOUVRE["t"]))
        if parts:
            crate = parts[0]
            for p_ in parts[1:]:
                m = crate.modifiers.new("u", "BOOLEAN")
                m.operation, m.object, m.solver = "UNION", p_, "EXACT"
                bpy.context.view_layer.objects.active = crate
                bpy.ops.object.modifier_apply(modifier=m.name)
                bpy.data.objects.remove(p_, do_unlink=True)
            crate.name = "ENGINE_LOUVRES"
            crate.data.name = "ENGINE_LOUVRES"
            crate["panel_id"] = "P33"
            crate["stage"] = ("03 element — SHAPE ONLY: stands in the engine cover's aperture; the "
                              "cover's height waits on scan S2 (roof fold envelope)")
            made.append(crate)
        print(f"  engine-cover louvres: aperture spec X {LOUVRE['x0']:.0f}..{LOUVRE['x1']:.0f}, |Y| < "
              f"{LOUVRE['hw']:.0f}, {LOUVRE['depth']:.0f} deep; a crate of {n_sl} transverse slats on "
              f"{len(ribs_y)} ribs, tops {LOUVRE['under']:.0f} under the skin -> P33 (SHAPE ONLY)")

    # ---- 12. THE GRILLES, 2026-10-03 (v058). Owner: "continue with the bumpers, grilles". ref-09
    # closes every front opening with a HEXAGONAL MESH -- the central mouth, both corner intakes --
    # and puts the same mesh in the vertical vents at the rear corners. Ours were open holes. Each
    # is one flat printed plate standing in its pocket, outline 2 mm INTO the pocket walls so it is
    # carried by them, never hanging: the central one is the P43 frame's own infill (one part),
    # the corners are P54 / P55, the tail vents P56 / P57. Hexagons only where a whole one fits
    # inside a continuous rim, so there is no loose bar to print. Gloss black. This decides the
    # owner's open item (b) as PRINTED; a bought mesh drops into the same frame if preferred.
    fm_ = next((o_ for o_ in made if o_.name.startswith("FRONT_MASK")), None)
    mpoly = [(-MOUTH["hw_lo"], MOUTH["z_lo"]), (MOUTH["hw_lo"], MOUTH["z_lo"]),
             (MOUTH["hw_hi"], MOUTH["z_hi"]), (-MOUTH["hw_hi"], MOUTH["z_hi"])]
    mg = hex_grille("FRONT_MASK_GRILLE", coll, inset_poly(mpoly, 22.0), 6.0, 34.0, 5.0, 6.0,
                    lambda u, v, w: (-841.0 + w, u, v))
    if fm_ is not None:
        m = fm_.modifiers.new("grille", "BOOLEAN")
        m.operation, m.object, m.solver = "UNION", mg, "EXACT"
        bpy.context.view_layer.objects.active = fm_
        bpy.ops.object.modifier_apply(modifier=m.name)
        print(f"  mouth grille: {mg['holes']} hexagons, pitch 34, bars 5, 6 deep, in the P43 frame (one part)")
        bpy.data.objects.remove(mg, do_unlink=True)
    # the corner grilles: a plane 30 mm behind the chamfered face, leaning with it (the face runs
    # from spec X ~-945 at the inner edge to ~-790 at the outer), and never closer than 8 mm to
    # the pocket floor at -750
    def face_x(yy):
        xs = []
        for zt in (300.0, 360.0, 420.0):
            p_, n_ = surface_hit(mathutils.Vector((mm(1000.0), mm(yy), mm(zt))), [(1.5, 0.0, 0.0)])
            if p_ is not None:
                xs.append(-p_.x * 1000.0)
        return max(xs) if xs else None
    ya, yb = CORNER_POLY[0][0], CORNER_POLY[1][0]
    fa, fb = face_x(ya + 15.0), face_x(yb - 15.0)
    xa = min((fa if fa is not None else -900.0) + 30.0, CORNER["x_floor"] - 8.0)
    xb = min((fb if fb is not None else -790.0) + 30.0, CORNER["x_floor"] - 8.0)
    k_ = (xb - xa) / (yb - ya)
    nn = math.hypot(1.0, k_)
    cpoly = inset_poly(CORNER_POLY, -2.0)
    for sgn in (1, -1):
        cg = hex_grille(f"CORNER_GRILLE_{'L' if sgn > 0 else 'R'}", coll, cpoly, 6.0, 44.0, 5.0, 6.0,
                        lambda u, v, w, sgn=sgn: (xa + k_ * (u - ya) + w / nn, sgn * (u - w * k_ / nn), v))
        cg["panel_id"] = "P54" if sgn > 0 else "P55"
        cg["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(cg)
    print(f"  corner grilles: {cg['holes']} hexagons each, pitch 44, a plane from spec X {xa:.0f} (Y {ya:.0f}) "
          f"to {xb:.0f} (Y {yb:.0f}), 30 mm behind the face -> P54 / P55")
    # the tail corner vents: a rearward-facing plate 15 mm behind the pocket's floor
    # outer edge 4 mm inside the SKIN, not the pocket: the pocket runs out through the narrowing
    # tail (hw ~765 at 3200), and with the outer edge at the pocket's 762 the plate stood 8 mm
    # proud at its lower outer corner (check_floating, first run)
    ys_ = [surface_y(TC["x_floor"] + 15.0, zz) for zz in (TC["z0"] - 2.0, 360.0, 420.0, 480.0, 540.0, TC["z1"] + 2.0)]
    y_out_ = min([TC["y_out"] + 2.0] + [y_ - 4.0 for y_ in ys_ if y_])
    tpoly = [(TC["y_in"] - 2.0, TC["z0"] - 2.0), (y_out_, TC["z0"] - 2.0),
             (y_out_, TC["z1"] + 2.0), (TC["y_in"] - 2.0, TC["z1"] + 2.0)]
    for sgn in (1, -1):
        tg = hex_grille(f"TAIL_VENT_GRILLE_{'L' if sgn > 0 else 'R'}", coll, tpoly, 5.0, 26.0, 4.0, 6.0,
                        lambda u, v, w, sgn=sgn: (TC["x_floor"] + 15.0 + w, sgn * u, v))
        tg["panel_id"] = "P56" if sgn > 0 else "P57"
        tg["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(tg)
    print(f"  tail vent grilles: {tg['holes']} hexagons each, pitch 26, at spec X {TC['x_floor'] + 15:.0f} -> P56 / P57")

    # ---- 13. THE MASK FACETS, 2026-10-05 (v060). ref-09's mask is built from PLANES: the painted
    # wedge between the mouth and each corner intake is a facet turned in toward the mouth, which is
    # what reads as the "V" of the front. Ours lay in the flat face. A planar cut gives the wedge
    # that facet: 40 mm deep at the mouth's edge, zero at the corner intake's inner edge, so the
    # plane meets the chamfer where the face already runs back -- a crease along its top and bottom
    # edges, no step anywhere else. Planar by construction (a linear depth on a quad), so the print
    # smoothing has nothing to round. Only Z 220..480: the DRL, the lamp slot and the lip are untouched.
    # The quad's corners lie INSIDE the two pockets, so its edges cross the pockets' walls in
    # T-junctions at least 21 mm from any pocket corner. Drawn first with its corners ON the pocket
    # corners, it pinched the fascia at four points and P01 went to print as three files.
    # Crossings (computed): mouth wall at Y 326 Z 242 and Y 372 Z 404; corner wall at Y 580 Z 257
    # and Y 462 Z 459. Depth is linear in Y alone, so the cut face stays one plane.
    FACET = [(300.0, 240.0), (350.0, 390.0), (480.0, 470.0), (640.0, 260.0)]
    FACET_DEPTH = 40.0
    def facet_x(yy):
        return -950.0 + FACET_DEPTH * (1.0 - (yy - 340.0) / (520.0 - 340.0))
    for sgn in (1, -1):
        pts = [(-1000.0, sgn * y_, z_) for y_, z_ in FACET] + [(facet_x(y_), sgn * y_, z_) for y_, z_ in FACET]
        cuts.append(hexa(f"CUT_FACET_{'L' if sgn > 0 else 'R'}", coll, pts))
    print(f"  mask facets: the mouth-to-corner wedges turned in by a plane, {FACET_DEPTH:.0f} mm at the "
          f"mouth edge to 0 at the corner intake")

    # ---- 14. THE SPLITTER END PLATES, 2026-10-05 (v060). Withheld on 2026-10-03 as the kind of proud
    # element retired on 09-29; the owner: "do all the outstanding things". A 10 mm carbon fence
    # under each corner intake at Y +-600: front edge at spec X -930 (20 mm inside the locked tip),
    # 40..85 mm ahead of the chamfered face there (measured -846..-887 at Z 125..240), its rear
    # 80 mm embedded in the corner so it is carried, top raked back from Z 175 to 238 -- under the
    # corner intake's floor at 240 -- and its foot at Z 122 over the 120 clearance.
    for sgn in (1, -1):
        ep = blade(f"SPLITTER_END_{'L' if sgn > 0 else 'R'}", coll,
                   [(-930.0, sgn * 600.0, 122.0, 175.0), (-880.0, sgn * 600.0, 122.0, 238.0),
                    (-800.0, sgn * 600.0, 122.0, 238.0)], 10.0)
        ep["panel_id"] = "P61" if sgn > 0 else "P62"
        ep["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(ep)
    print("  splitter end plates: 10 mm fences at Y +-600, spec X -930..-800, Z 122..238 -> P61 / P62")

    # ---- 15. THE BADGE BAND AND THE BADGE, 2026-10-05 (v060). ref-09: between the two lamps a dark
    # band about as tall as the lamps' housings, the word STATEV across its middle. Ours had the lamp
    # slot only, and at the centre the tail's own top covers most of it from behind. So: a 20 mm
    # recess in the tail face across |Y| < 430 (the lamps are lit outboard of that), Z 585..645,
    # its floor parallel to the sloping face (measured at Y 0: spec X 3331 at Z 580, 3233 at 650),
    # and the badge lying in it -- letters 4 mm proud of a 2 mm backing, one printed part, P60.
    def tail_x(zz):
        p_, n_ = surface_hit(mathutils.Vector((-mm(4000.0), 0.0, mm(zz))), [(-1.5, 0.0, 0.0)])
        return -p_.x * 1000.0 if p_ is not None else None
    BAND = dict(hw=430.0, z0=585.0, z1=645.0, depth=20.0)
    xb0, xb1 = tail_x(BAND["z0"]), tail_x(BAND["z1"])
    if xb0 and xb1:
        fb = (xb0 - BAND["depth"], BAND["z0"])
        ft = (xb1 - BAND["depth"], BAND["z1"])
        pts = [(3600.0, -BAND["hw"], BAND["z0"]), (3600.0, BAND["hw"], BAND["z0"]),
               (3600.0, BAND["hw"], BAND["z1"]), (3600.0, -BAND["hw"], BAND["z1"]),
               (fb[0], -BAND["hw"], fb[1]), (fb[0], BAND["hw"], fb[1]),
               (ft[0], BAND["hw"], ft[1]), (ft[0], -BAND["hw"], ft[1])]
        cuts.append(hexa("CUT_BADGE_BAND", coll, pts))
        # the badge, built flat (u across the car, v up the band, w out of it), then laid on the floor
        sx_, sz_ = ft[0] - fb[0], ft[1] - fb[1]
        L_ = math.hypot(sx_, sz_)
        s_ = (sx_ / L_, sz_ / L_)                  # up the floor, in (spec X, Z)
        n_ = (s_[1], -s_[0])                       # out of the floor: rearward and up
        c_ = ((fb[0] + ft[0]) / 2.0, (fb[1] + ft[1]) / 2.0)
        tc = bpy.data.curves.new("BADGE_TXT", "FONT")
        tc.body = "STATEV"
        tc.size = 0.046                            # ~300 mm across with the tracking, as ref-09's
        tc.space_character = 1.9
        tc.align_x, tc.align_y = "CENTER", "CENTER"
        tc.extrude = 0.002                         # 4 mm deep in total, centred on the curve plane
        to_ = bpy.data.objects.new("BADGE_TXT", tc)
        coll.objects.link(to_)
        bpy.context.view_layer.objects.active = to_
        for o_ in bpy.context.selected_objects:
            o_.select_set(False)
        to_.select_set(True)
        bpy.ops.object.convert(target="MESH")
        badge = bpy.context.view_layer.objects.active
        badge.name = "BADGE_REAR"
        xs_ = [v.co.x for v in badge.data.vertices]
        ys_ = [v.co.y for v in badge.data.vertices]
        w2, h2 = (max(xs_) - min(xs_)) * 500.0 + 12.0, (max(ys_) - min(ys_)) * 500.0 + 8.0
        bm = bmesh.new()
        bm.from_mesh(badge.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        for v in bm.verts:
            v.co.z += 0.004                        # letters stand on the backing: w 2..6 mm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(badge.data)
        bm.free()
        back = bpy.data.meshes.new("BADGE_BACK")
        back.from_pydata([(sx * w2 / 1000.0, sy * h2 / 1000.0, sz) for sz in (0.0, 0.0025)
                          for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))], [],
                         [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
        back.update()
        bo = bpy.data.objects.new("BADGE_BACK", back)
        coll.objects.link(bo)
        m = badge.modifiers.new("back", "BOOLEAN")
        m.operation, m.object, m.solver = "UNION", bo, "EXACT"
        bpy.context.view_layer.objects.active = badge
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(bo, do_unlink=True)
        for v in badge.data.vertices:
            u, vv, w = v.co.x * 1000.0, v.co.y * 1000.0, v.co.z * 1000.0
            v.co = (-mm(c_[0] + vv * s_[0] + w * n_[0]), mm(-u), mm(c_[1] + vv * s_[1] + w * n_[1]))
        badge.data.update()
        bm = bmesh.new()
        bm.from_mesh(badge.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(badge.data)
        bm.free()
        badge["panel_id"] = "P60"
        badge["stage"] = "03 element — shape ours"
        made.append(badge)
        print(f"  badge band: a {BAND['depth']:.0f} mm recess across |Y| < {BAND['hw']:.0f}, Z {BAND['z0']:.0f}.."
              f"{BAND['z1']:.0f}, floor parallel to the face; STATEV {2 * w2:.0f} x {2 * h2:.0f} mm on it -> P60")

    # ---- 11. THE STRAKES AND THE SPLITTER LIP, 2026-09-29. ref-09's mask is faceted: from each
    # lamp's inner end a crease runs down and inward to the mouth's upper corner (the cheekbone),
    # and under the mouth the splitter lip stands ahead of the face. The cheekbone is a ridge that
    # follows the skin (ribbon), 24 wide, 12 proud, 12 embedded -> P50 / P51. The lip: the length
    # is locked at 4370 so nothing may stand ahead of the tip; instead the face is RECESSED 40 mm
    # just above the lip (Z 150..200), which leaves the lip standing 40 mm proud of the face
    # above it -- the same read, inside the locked box. Printed with P01/P28 as pocket walls.
    for sgn in ((1, -1) if PARASITIC else ()):   # retired 2026-09-29, see the corner bars
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
    print("  splitter lip: the face recessed 40 mm over Z 150..200 so the lip stands proud inside the locked length")

    # the skin as it was BEFORE any Stage-03 opening, kept hidden for check_floating.py: an element
    # sitting in a pocket is outside the cut body by design, and only the uncut skin can say
    # whether it stands PROUD of the car (2026-10-02)
    unc = bpy.data.collections.get("_STAGE03_UNCUT")
    if unc:
        for o in list(unc.objects):
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(me)
    else:
        unc = bpy.data.collections.new("_STAGE03_UNCUT")
        bpy.context.scene.collection.children.link(unc)
    for o in body_objects():
        cp = o.copy()
        cp.data = o.data.copy()
        cp.name = "UNCUT_" + o.name
        for m in list(cp.modifiers):
            cp.modifiers.remove(m)
        unc.objects.link(cp)
        cp.hide_render = True
        cp.hide_viewport = True
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
