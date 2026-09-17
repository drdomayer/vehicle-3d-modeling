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
    fs = [(-235, 700, 980), (-110, 700, 985), (40, 700, 985), (165, 700, 975)]
    for sgn in (1, -1):
        c = prism(f"CUT_FENDER_SLOT_{'L' if sgn > 0 else 'R'}", coll,
                  [(s[0], s[1], s[2]) for s in fs], sgn * 660, sgn * 470)
        cuts.append(c)
    print(f"  fender slot: spec X {fs[0][0]}..{fs[-1][0]}, Y 470..660, cut down from Z 985 to 700")
    # the channel's own liner, a shallow U standing inside the slot: registered P05 / P06
    for sgn in (1, -1):
        lin = blade(f"FENDER_CHANNEL_{'L' if sgn > 0 else 'R'}", coll,
                    [(fs[0][0] + 20, sgn * 476, 712, 968), (-110, sgn * 476, 716, 974),
                     (40, sgn * 476, 716, 974), (fs[-1][0] - 20, sgn * 476, 712, 962)], 14.0)
        lin["panel_id"] = "P05" if sgn > 0 else "P06"
        lin["stage"] = "03 element — shape ours, mounting SCAN REQUIRED"
        made.append(lin)
    print("  fender channel liner: a 14 mm wall inside the slot -> registered P05 / P06")

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
