"""
glossy_renders.py — the body in the reference's own finish: dark metallic green, studio light.

    Blender:  import bpy; exec(open(".../glossy_renders.py").read())

WHY. Every review picture of this car has been grey clay with cavity shading, and the owner
judges it against a glossy dark-green render. Clay hides creases (the lip measures 67 degrees,
the undercut 70, the crest 61 -- none of them shows in grey) and exaggerates lumps. A crease
reads as a highlight break only under a reflection. So before deciding that the SURFACE is
wrong, the model is rendered the way the reference was: same colour, gloss, a large soft key
light and a bright ground bounce, from the four angles of ref-09. If it still reads soft here,
the shape is soft. If not, the clay was lying.

Same file names every run (rv_glossy_*.png in the review folder; set GLOSSY_SOURCE = "files"
before exec to render the printed files instead -- rv_glossy_files_*.png). Nothing in the scene is kept:
materials, lights, world and camera are created for the render and removed after it.
"""
import math
import os

import bpy
import mathutils

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) \
    if "__file__" in globals() else "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "statev_v01", "review")
SHOW = ("STATEV_MASTER", "STATEV_STAGE03")
WHEELS = "wheels"
VIEWS = [("side", (-1.2, 9.0, 0.7), (-1.2, 0.0, 0.45), 55, "PERSP"),
         ("front34", (4.6, 4.0, 1.9), (-0.8, 0.0, 0.4), 45, "PERSP"),
         ("rear34", (-6.8, 3.8, 1.9), (-1.5, 0.0, 0.4), 45, "PERSP"),
         ("front", (7.5, 0.0, 1.1), (-0.6, 0.0, 0.45), 60, "PERSP"),
         ("rear", (-9.5, 0.0, 1.1), (-1.6, 0.0, 0.45), 60, "PERSP"),
         # 2026-10-02: the remaining four of ref-09's seven panels, so every panel of the
         # reference has a model picture from the same side (review_sheets.py pairs them)
         ("top", (-1.2, 0.0, 12.0), (-1.2, 0.0, 0.0), 4.9, "ORTHO"),
         ("mask", (3.4, 0.0, 1.05), (0.85, 0.0, 0.40), 50, "PERSP"),
         ("taildetail", (-6.0, 0.0, 1.15), (-3.3, 0.0, 0.50), 50, "PERSP"),
         ("intake", (-1.05, 2.9, 0.80), (-2.05, 0.88, 0.55), 40, "PERSP")]


# the poster's two hero angles, rendered in the final mode only
HERO = [("hero_front", (4.4, 3.3, 0.85), (-1.0, 0.0, 0.42), 38, "PERSP"),
        ("hero_rear", (-6.2, 3.5, 1.25), (-2.0, 0.0, 0.48), 38, "PERSP")]


def principled(mat):
    mat.use_nodes = True
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def set_in(node, names, value):
    for nm in names:
        if nm in node.inputs:
            node.inputs[nm].default_value = value
            return True
    return False


def smooth_by_angle(o, deg):
    """Smooth shading with edges over `deg` kept sharp: the printed files carry a 3 mm wall whose
    rim is a right angle, and plain smooth shading smeared it into dark bands at every panel edge."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    lim = math.radians(deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.smooth = False
        else:
            a, b = e.link_faces[0].normal, e.link_faces[1].normal
            e.smooth = not (a.length and b.length and a.angle(b) > lim)
    bm.to_mesh(o.data)
    bm.free()


def wheel_parts(sc, spec_x, od, wdt, half_track, sgn, sidewall):
    """A 19-inch ten-spoke wheel for the picture: tyre, bronze rim lip, ten spokes and hub, dark
    barrel, brake disc and a bronze caliper (ref-09 / the poster). Render-only, removed after."""
    out = []
    cx, cz = -spec_x / 1000.0, od / 2000.0
    rr = od / 2000.0 - sidewall / 1000.0               # rim radius
    yo = sgn * (half_track + wdt / 2.0 - 22.0) / 1000.0  # spoke face plane, just inside the tyre

    def add(name, verts, faces, tag):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        ob["glossy_tag"] = tag
        out.append(ob)
        return ob

    def disc(name, r_out, r_in, y0, y1, tag, n=72):
        v, f = [], []
        for k in range(n):
            a = 2 * math.pi * k / n
            for r in (r_out, r_in):
                for y in (y0, y1):
                    v.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
        for k in range(n):
            a, b = 4 * k, 4 * ((k + 1) % n)
            f += [(a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2), (a, a + 2, b + 2, b), (a + 1, b + 1, b + 3, a + 3)]
        ob = add(name, v, f, tag)
        for p in ob.data.polygons:
            p.use_smooth = True
        return ob
    t = 0.014
    tyre = disc("GLOSSY_TYREBAND", od / 2000.0, rr - 0.002, sgn * (half_track - wdt / 2.0) / 1000.0,
                sgn * (half_track + wdt / 2.0) / 1000.0, "rubber", 96)
    bv = tyre.modifiers.new("bevel", "BEVEL")
    bv.width, bv.segments, bv.limit_method = 0.03, 6, "ANGLE"
    disc("GLOSSY_RIMLIP", rr + 0.004, rr - 0.018, yo - sgn * 0.004, yo + sgn * 0.010, "bronze")
    disc("GLOSSY_BARREL", rr - 0.004, rr - 0.012, yo - sgn * 0.20, yo - sgn * 0.004, "dark")
    disc("GLOSSY_HUB", 0.062, 0.018, yo - sgn * 0.02, yo + sgn * 0.012, "bronze", 36)
    disc("GLOSSY_BRAKEDISC", rr - 0.05, 0.07, yo - sgn * 0.075, yo - sgn * 0.050, "disc")
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.1
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa, ca
        w0, w1 = 0.016, 0.011
        r0, r1 = 0.058, rr - 0.012
        v = []
        for r, w in ((r0, w0), (r1, w1)):
            for s_ in (-1, 1):
                for y in (yo - sgn * t, yo + sgn * 0.004):
                    v.append((cx + r * ca + s_ * w * tx, y, cz + r * sa + s_ * w * tz))
        f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        add("GLOSSY_SPOKE", v, f, "bronze")
    # caliper: a block at the rear-upper quadrant of the disc
    a = math.radians(120 if spec_x < 1000 else 60)
    ccx, ccz = cx + (rr - 0.07) * math.cos(a), cz + (rr - 0.07) * math.sin(a)
    yc0, yc1 = yo - sgn * 0.10, yo - sgn * 0.035
    v = [(ccx + dx, y, ccz + dz) for dx in (-0.06, 0.06) for y in (yc0, yc1) for dz in (-0.035, 0.035)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    add("GLOSSY_CALIPER", v, f, "caliper")
    return out


def import_files():
    """The printed files put back on the car (placement.json), as render_panels.py does. They are
    the smoothed, thickened parts the shop receives -- the honest picture. The loft itself is a
    60-sample, 40 mm-station quad mesh and under a reflection its shading ripples about one
    station long (tested 2026-09-29: the ripples vanish under Catmull-Clark x2, and the surface
    probe reads the same 3.968 either way), so the body is not what to judge gloss on."""
    import json
    out = []
    for tier in ("production", "shape_only"):
        d = os.path.join(REPO, "03_PRINT", tier)
        pj = os.path.join(d, "placement.json")
        if not os.path.exists(pj):
            continue
        with open(pj, encoding="utf-8") as f:
            parts = json.load(f)["parts"]
        for fn, mat in parts.items():
            path = os.path.join(d, fn)
            if not os.path.exists(path):
                continue
            before = set(bpy.data.objects)
            try:
                bpy.ops.wm.stl_import(filepath=path, global_scale=0.001)
            except AttributeError:
                bpy.ops.import_mesh.stl(filepath=path, global_scale=0.001)
            for o in [o for o in bpy.data.objects if o not in before]:
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                bpy.context.scene.collection.objects.link(o)
                o.matrix_world = mathutils.Matrix(mat) @ mathutils.Matrix.Diagonal(
                    (0.001, 0.001, 0.001, 1.0))
                o.name = "GLOSSY_FILE_" + fn
                smooth_by_angle(o, 35.0)
                out.append(o)
    return out


# CLEAN MODE, 2026-09-29 (v051), after the owner's review ("parasitic elements"). The printed
# files carry 30 mm overlaps (shape-only neighbours), joint tabs, housings, ducts and sails, and
# a render of all of them together reads as clutter that the car will never show. "clean" renders
# the BODY volumes with every opening cut, under a temporary Catmull-Clark x2 with creases on the
# real edges (so the loft's shading ripples go and the creases stay), plus only the elements a
# person standing next to the car would see. Housings, ducts and the shape-only sails are not
# hidden from the files, only from this picture.
CLEAN_SHOW = ("INTAKE_BLADE", "FENDER_CHANNEL", "FRONT_MASK", "DIFFUSER_FIN")
CLEAN_CREASE_DEG = float(globals().get("GLOSSY_CREASE_DEG", 30.0))


def clean_bodies():
    """Body volumes with a temporary subdivision; returns the modifiers to remove afterwards."""
    import bmesh
    import math as _m
    added = []
    c = bpy.data.collections.get("STATEV_MASTER")
    if not c:
        return [], set()
    names = set()
    for o in c.all_objects:
        if o.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        cl = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
        for e in bm.edges:
            if len(e.link_faces) == 2:
                a, b = e.link_faces[0].normal, e.link_faces[1].normal
                e[cl] = 1.0 if (a.length > 0 and b.length > 0
                                and _m.degrees(a.angle(b)) > CLEAN_CREASE_DEG) else 0.0
        bm.to_mesh(o.data)
        bm.free()
        m = o.modifiers.new("GLOSSY_SUBD", "SUBSURF")
        m.levels, m.render_levels = 2, 2
        added.append((o, m))
        names.add(o.name)
    s3 = bpy.data.collections.get("STATEV_STAGE03")
    if s3:
        for o in s3.all_objects:
            if o.type == "MESH" and any(k in o.name for k in CLEAN_SHOW):
                names.add(o.name)
    return added, names


# the pockets whose inside is black on the car (v056); read from panel_map, not retyped
INTERIOR_BLACK = ("X_MOUTH", "X_CORNER", "X_INTAKE", "X_TAIL_CORNER", "X_LOUVRE", "X_FENDER_SLOT",
                  "X_BADGE", "X_EYE")
_pmg = {"__name__": "_pm"}
with open(os.path.join(REPO, "01_CAD", "scripts", "panel_map.py"), encoding="utf-8") as _f:
    exec(_f.read().split("\ndef main(")[0], _pmg)
_POCKETS, _in_poly = _pmg["POCKETS"], _pmg["in_poly"]
_prg = {"__name__": "_prg", "__file__": os.path.join(REPO, "01_CAD", "scripts", "panel_registry.py")}
with open(_prg["__file__"], encoding="utf-8") as _f:
    exec(_f.read().split("\ndef main(")[0], _prg)
FINISH_ZONES = _prg.get("FINISH_ZONES", {})
_skg = {}
with open(os.path.join(REPO, "01_CAD", "scripts", "statev_skeleton.py"), encoding="utf-8") as _f:
    exec(_f.read().split("\ndef build(")[0], _skg)


def zone_hit(zones, finish, ay, z):
    """True when (|Y|, Z) mm lies in one of the part's FINISH_ZONES of that finish."""
    for f_, rule, val, _w in zones:
        if f_ != finish:
            continue
        if rule == "z_below" and z < val:
            return True
        if rule == "below_drl" and z < _skg["table_z"](_skg["DRL_Z"], ay) - val:
            return True
    return False


def bisect_zones(o, zones):
    """Cut the render copy along a FINISH_ZONES line so the colour change is a line, not the
    saw-tooth of whole triangles either side of it (v079: the file's triangles under the DRL span
    the line, and a face-centre test painted green teeth into the black). Render only: the print
    file is untouched, on the car the line is the paint shop's tape along the groove."""
    import bmesh
    # sampled every 20 mm through table_z (PCHIP since v052): the face test below uses the same
    # curve, and a chord between the table's knots would leave a sliver either side of it
    tz_, knots = _skg["table_z"], _skg["DRL_Z"]
    ys_ = [knots[0][0] + 20.0 * k for k in range(int((knots[-1][0] - knots[0][0]) / 20.0) + 1)]
    drl = [(y, tz_(knots, y) - v) for f_, r_, v, _w in zones if r_ == "below_drl" for y in ys_]
    flat = [v for f_, r_, v, _w in zones if r_ == "z_below"]
    if not drl and not flat:
        return
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    planes = [((0.0, 0.0, v / 1000.0), (0.0, 0.0, 1.0), None) for v in flat]
    for (y0, z0), (y1, z1) in zip(drl, drl[1:]):
        for sgn in (1.0, -1.0):
            n_ = mathutils.Vector((0.0, -(z1 - z0), sgn * (y1 - y0))).normalized()
            planes.append(((0.0, sgn * y0 / 1000.0, z0 / 1000.0), tuple(n_), (sgn, y0, y1)))
    for co, no, band in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        if band:
            sgn, y0, y1 = band
            fs = [f for f in bm.faces
                  if any(v.co.y * sgn * 1000.0 >= y0 - 5 for v in f.verts)
                  and any(v.co.y * sgn * 1000.0 <= y1 + 5 for v in f.verts)]
            geom = list({e for f in fs for e in f.edges}) + fs + list({v for f in fs for v in f.verts})
        if geom:
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no)
    bm.transform(o.matrix_world.inverted())
    bm.to_mesh(o.data)
    bm.free()
_POCKETS_XZ = _pmg.get("POCKETS_XZ", [])


def finish_map():
    """FINISH per part id, from the register's CSV (panel_registry.py --csv)."""
    import csv
    p = os.path.join(REPO, "04_ENGINEERING", "reports", "panel_bom.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return {r["ID"]: r.get("FINISH", "paint") for r in csv.DictReader(f)}


def ctx_objects(sc):
    """The donor and the lamps, for the PICTURE only (2026-10-02): the windscreen frame and the roll
    hoops are the donor's and stay; seats; the deck zone between the buttresses (BLOCKED until scan
    S2) as a dark field where ref-09 has the louvred cover; the DRL and the tail light bars lit.
    Without them the review compared a car with a cockpit, glass and lights to an open tub."""
    out = []

    def mesh(name, verts, faces):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        out.append(ob)
        return ob

    def tube(name, pts, r):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", r, 4
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
        ob = bpy.data.objects.new(name, cu)
        sc.collection.objects.link(ob)
        out.append(ob)
        return ob

    def P_(sx, y, z):
        return (-sx / 1000.0, y / 1000.0, z / 1000.0)
    tags = {}
    # windscreen (donor): base at the cowl (420, Z 970), header (1055, Z 1255)
    g = mesh("GLOSSY_CTX_GLASS", [P_(420, -650, 968), P_(420, 650, 968), P_(1055, 570, 1255),
                                  P_(1055, -570, 1255)], [(0, 1, 2, 3)])
    tags[g.name] = "glass"
    tags[tube("GLOSSY_CTX_FRAME", [P_(420, -650, 968), P_(1055, -570, 1255), P_(1055, 570, 1255),
                                   P_(420, 650, 968)], 0.022).name] = "gloss black"
    for sgn in (1, -1):
        y = sgn * 350.0
        tags[tube("GLOSSY_CTX_HOOP", [P_(1760, y - 180, 880), P_(1760, y - 170, 1200),
                                      P_(1760, y - 120, 1235), P_(1760, y + 120, 1235),
                                      P_(1760, y + 170, 1200), P_(1760, y + 180, 880)], 0.028).name] = "gloss black"
        x0, x1 = 1250.0, 1680.0
        s_ = mesh("GLOSSY_CTX_SEAT", [P_(x0, y - 240, 650), P_(x0, y + 240, 650), P_(x1, y + 240, 660),
                                      P_(x1, y - 240, 660), P_(x1 + 60, y - 240, 1180),
                                      P_(x1 + 60, y + 240, 1180), P_(x1 - 40, y + 240, 1180),
                                      P_(x1 - 40, y - 240, 1180)],
                  [(0, 1, 2, 3), (3, 2, 5, 4), (7, 6, 1, 0), (4, 5, 6, 7), (0, 3, 4, 7), (1, 6, 5, 2)])
        tags[s_.name] = "tan"
    # deck zone between the buttresses: BLOCKED geometry, drawn as a dark field at the spine
    sk = {}
    with open(os.path.join(REPO, "01_CAD", "scripts", "statev_skeleton.py"), encoding="utf-8") as f:
        exec(f.read().split("\ndef build(")[0], sk)
    spine, tz = sk["DECK_SPINE"], sk["table_z"]
    xs = [1790 + k * 60 for k in range(23)]
    vs, fs = [], []
    for i, x in enumerate(xs):
        z = tz(spine, x) - 6
        vs += [P_(x, -560, z), P_(x, 560, z)]
        if i:
            fs.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    tags[mesh("GLOSSY_CTX_DECK", vs, fs).name] = "gloss black"
    # DRL along DRL_PATH at DRL_Z, both sides joined on the centreline
    # v056: on the GROOVE's axis (stage03 stores it), not on DRL_PATH as written -- that path's
    # spec X is 60 mm inside the nose face, so the line was inside the body in every render
    sc = bpy.context.scene
    if "statev_drl_axis_L" in sc and "statev_drl_axis_R" in sc:
        def trip(k):
            a = list(sc[k])
            return [tuple(a[i:i + 3]) for i in range(0, len(a), 3)]
        L_, R_ = trip("statev_drl_axis_L"), trip("statev_drl_axis_R")
        mid = tuple((L_[0][i] + R_[0][i]) / 2.0 for i in range(3))
        pts = list(reversed(R_)) + [mid] + L_
    else:
        path = sk["DRL_PATH"]
        side = [(x, y, tz(sk["DRL_Z"], abs(y))) for x, y in path]
        pts = [P_(x, -y, z) for x, y, z in reversed(side)] + [P_(path[0][0] - 2, 0, tz(sk["DRL_Z"], 0))] + \
              [P_(x, y, z) for x, y, z in side]
    tags[tube("GLOSSY_CTX_DRL", pts, 0.006).name] = "light white"
    # v068: the DRL's run on along the outboard eye bezel's lower edge (stage03 5e stores the axis)
    for side in ("L", "R"):
        k = f"statev_drl_eye_axis_{side}"
        if k in sc:
            a = list(sc[k])
            tags[tube(f"GLOSSY_CTX_DRL_EYE_{side}", [tuple(a[i:i + 3]) for i in range(0, len(a), 3)],
                      0.006).name] = "light white"
    # tail light bar and its L ends (the LOCKED envelopes), lit at the face
    # v057: lit only OUTBOARD of |Y| 430, a black band between -- ref-09's rear view (1.68 mm/px):
    # each lamp runs from ~857 in to ~428, and the centre is a dark band carrying the badge. Legal
    # sense too: the position/stop functions belong near the outer edges (Hella Shapeline modules
    # in the outer slots); the blade itself stays one slot across the car, as docs/14 locks it.
    for sgn in (1, -1):
        tags[mesh("GLOSSY_CTX_TAIL", [P_(3212, sgn * 430, 600), P_(3212, sgn * 720, 600),
                                      P_(3212, sgn * 720, 624), P_(3212, sgn * 430, 624)],
                  [(0, 1, 2, 3)]).name] = "light red"
    tags[mesh("GLOSSY_CTX_TAILBAND", [P_(3211, -430, 597), P_(3211, 430, 597), P_(3211, 430, 627),
                                      P_(3211, -430, 627)], [(0, 1, 2, 3)]).name] = "gloss black"
    return out, tags


def main():
    """Runs the render and ALWAYS puts the scene back. 2026-10-02: a render that failed half-way
    left hide_render on every object it had hidden, panel_production then copied the Stage-03
    parts with that flag, and the STL exporter wrote nine of them EMPTY while reporting success."""
    snap = {o.name: o.hide_render for o in bpy.data.objects}
    sc = bpy.context.scene
    cam0, world0, eng0 = sc.camera, sc.world, sc.render.engine
    try:
        _main()
    finally:
        for o in list(bpy.data.objects):
            if o.name.startswith("GLOSSY_"):
                d = o.data
                bpy.data.objects.remove(o, do_unlink=True)
                for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras):
                    if d is not None and d.name in coll and coll[d.name] == d and d.users == 0:
                        coll.remove(d)
            else:
                if o.name in snap:
                    o.hide_render = snap[o.name]
                for m in [m for m in o.modifiers if m.name == "GLOSSY_SUBD"]:
                    o.modifiers.remove(m)
        for m in [m for m in bpy.data.materials if m.name.startswith("GLOSSY_") and m.users == 0]:
            bpy.data.materials.remove(m)
        if sc.camera is None or sc.camera.name not in bpy.data.objects:
            sc.camera = cam0 if (cam0 is not None and cam0.name in bpy.data.objects) else None
        try:
            sc.render.engine = eng0
        except TypeError:
            pass
        if sc.world is not None and sc.world.name.startswith("GLOSSY_"):
            w = sc.world
            sc.world = world0 if (world0 is not None and not world0.name.startswith("GLOSSY_")) else None
            if w.users == 0:
                bpy.data.worlds.remove(w)


def _main():
    sc = bpy.context.scene
    source = globals().get("GLOSSY_SOURCE", "body")
    files = import_files() if source == "files" else []
    body = set(o.name for o in files)
    subd = []
    if source == "clean":
        subd, body = clean_bodies()
    if not files and not body:
        for cn in SHOW:
            c = bpy.data.collections.get(cn)
            if c:
                body.update(o.name for o in c.all_objects if o.type == "MESH")
    if not body:
        print("  nothing to render: build the body first")
        return
    tag_prefix = {"files": "rv_glossy_files_", "clean": "rv_glossy_clean_"}.get(source, "rv_glossy_")
    if globals().get("GLOSSY_FINAL"):
        tag_prefix = "rv_glossy_car_"
    # PRESENTATION, 2026-10-06: the same files under ref-09's own studio, not the diagnostic light.
    # The diagnostic renders keep a light world and floor ON PURPOSE (every flaw shows); ref-09 is a
    # studio photograph -- a light grey seamless to the camera, a dark room in the reflections, long
    # softboxes. Comparing the two setups mixed the light into the verdict on the shape.
    PRESENT = bool(globals().get("GLOSSY_PRESENT"))
    if PRESENT:
        tag_prefix = "rv_glossy_present_"
    # TYRES AND RIMS, 2026-09-29 (v051). The cage's wheel cylinders (48 flat sides, grey) made every
    # render read as a toy and the owner said so. Four tyres are built for the render only: the
    # 19" sizes and the donor tracks from the skeleton, rounded shoulders, dark rubber, a bronze
    # rim inset. Removed after the render like everything else here.
    hidden = [(o, o.hide_render) for o in bpy.data.objects]
    for o, _ in hidden:
        o.hide_render = o.name not in body
    wheels = set()
    tyres = []
    for spec_x, od, wdt, half_track in ((0.0, 647.0, 235.0, 732.5), (2415.0, 675.0, 275.0, 764.0)):
        for sgn in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(radius=od / 2000.0, depth=wdt / 1000.0, vertices=96,
                                                location=(-spec_x / 1000.0, sgn * half_track / 1000.0, od / 2000.0))
            t = bpy.context.active_object
            t.name = "GLOSSY_TYRE"
            t.rotation_euler = (math.radians(90), 0, 0)
            bv = t.modifiers.new("bevel", "BEVEL")
            bv.width, bv.segments = 0.028, 6
            for p in t.data.polygons:
                p.use_smooth = True
            if globals().get("GLOSSY_FINAL"):
                # the capped cylinder hid the spokes: in the final mode the tyre is a ring
                me_ = t.data
                bpy.data.objects.remove(t, do_unlink=True)
                bpy.data.meshes.remove(me_)
                tyres += wheel_parts(sc, spec_x, od, wdt, half_track, sgn, 82.0 if spec_x < 1000 else 96.0)
                continue
            bpy.ops.mesh.primitive_cylinder_add(radius=od / 2000.0 - 0.105, depth=wdt / 1000.0 - 0.02, vertices=96,
                                                location=(-spec_x / 1000.0, sgn * (half_track + 12.0) / 1000.0, od / 2000.0))
            r = bpy.context.active_object
            r.name = "GLOSSY_RIM"
            r.rotation_euler = (math.radians(90), 0, 0)
            tyres += [t, r]
    for t in tyres:
        for c in list(t.users_collection):
            c.objects.unlink(t)
        sc.collection.objects.link(t)
        wheels.add(t.name)
    # materials: paint, and dark rubber for the wheel cylinders
    paint = bpy.data.materials.new("GLOSSY_PAINT")
    p = principled(paint)
    # dark metallic green, as ref-09 and the brand decision (CLAUDE.md); was a mid green that
    # read as a toy next to the reference
    set_in(p, ("Base Color",), (0.006, 0.026, 0.014, 1.0))
    set_in(p, ("Metallic",), 0.35 if globals().get("GLOSSY_FINAL") else 0.6)
    set_in(p, ("Roughness",), 0.24)
    set_in(p, ("Coat Weight", "Clearcoat"), 1.0)
    set_in(p, ("Coat Roughness", "Clearcoat Roughness"), 0.05)
    rubber = bpy.data.materials.new("GLOSSY_RUBBER")
    r = principled(rubber)
    set_in(r, ("Base Color",), (0.03, 0.03, 0.03, 1.0))
    set_in(r, ("Roughness",), 0.6)
    bronze = bpy.data.materials.new("GLOSSY_BRONZE")
    b = principled(bronze)
    set_in(b, ("Base Color",), (0.42, 0.28, 0.12, 1.0))
    set_in(b, ("Metallic",), 0.9)
    set_in(b, ("Roughness",), 0.35)
    def mat(name, col, metal, rough, emit=None):
        m = bpy.data.materials.new(name)
        q = principled(m)
        set_in(q, ("Base Color",), col)
        set_in(q, ("Metallic",), metal)
        set_in(q, ("Roughness",), rough)
        if emit:
            set_in(q, ("Emission Color", "Emission"), emit)
            set_in(q, ("Emission Strength",), 12.0)
        return m
    finmats = {"paint": paint,
            "carbon": mat("GLOSSY_CARBON", (0.018, 0.018, 0.02, 1.0), *globals().get("GLOSSY_CARBON_MR", (0.3, 0.32))),
            "gloss black": mat("GLOSSY_GBLACK", (0.008, 0.008, 0.009, 1.0), 0.1, 0.12),
            "satin silver": mat("GLOSSY_SILVER", (0.75, 0.75, 0.76, 1.0), 1.0, 0.25),
            "hidden": mat("GLOSSY_HIDDEN", (0.02, 0.02, 0.02, 1.0), 0.0, 0.6),
            "tan": mat("GLOSSY_TAN", (0.42, 0.21, 0.09, 1.0), 0.0, 0.55),
            "glass": mat("GLOSSY_GLASS", (0.01, 0.012, 0.012, 1.0), 0.0, 0.03),
            "light white": mat("GLOSSY_LW", (1, 1, 1, 1), 0.0, 0.3, (0.9, 0.95, 1.0, 1.0)),
            "light red": mat("GLOSSY_LR", (1, 0, 0, 1), 0.0, 0.3, (1.0, 0.03, 0.02, 1.0))}
    fin = finish_map()
    saved = {}
    for n in body:
        o = bpy.data.objects[n]
        saved[n] = [m for m in o.data.materials]
        o.data.materials.clear()
        pid = o.get("panel_id") or (n[len("GLOSSY_FILE_"):][:3] if n.startswith("GLOSSY_FILE_") else None)
        o.data.materials.append(finmats.get(fin.get(pid, "paint"), paint))
        if globals().get("GLOSSY_DEBUG"):
            print("   mat", n, pid, fin.get(pid, "paint"), o.data.materials[0].name)
        # v060: the badge is one printed part, letters standing 4 mm on a 2 mm backing -- the
        # backing reads black (it lies in the black band), the letters silver
        if fin.get(pid) == "satin silver":
            o.data.materials.clear()
            o.data.materials.append(finmats["gloss black"])
            o.data.materials.append(finmats["satin silver"])
            M3 = o.matrix_world.to_3x3()
            # the backing's own plane: the normal of its largest face (an area-weighted mean is zero
            # on a closed solid), turned to face rearward, which is repo -X
            big_ = max(o.data.polygons, key=lambda q: q.area)
            nrm = (M3 @ big_.normal).normalized()
            if nrm.x > 0:
                nrm = -nrm
            ds = [(o.matrix_world @ poly.center).dot(nrm) for poly in o.data.polygons]
            dmin = min(ds) if ds else 0.0
            for poly, d_ in zip(o.data.polygons, ds):
                poly.material_index = 1 if (d_ - dmin) * 1000.0 > 3.0 else 0
        # v056: an opening's INSIDE is black on the real car (satin black or behind a mesh), not
        # body colour -- a painted corner intake read as a green dent in every front render
        if n.startswith("GLOSSY_FILE_") and fin.get(pid, "paint") == "paint":
            o.data.materials.append(finmats["gloss black"])
            inv = o.matrix_world
            zones = FINISH_ZONES.get(pid, [])
            if zones:
                bisect_zones(o, zones)
            for poly in o.data.polygons:
                c = inv @ poly.center
                sx, ay, z = -c.x * 1000.0, abs(c.y * 1000.0), c.z * 1000.0
                # a two-tone part (panel_registry.FINISH_ZONES); only the gloss black split exists
                if zone_hit(zones, "gloss black", ay, z):
                    poly.material_index = 1
                    continue
                # v069: side openings outlined in X-Z (the scoop); its floor looks along Y and must be
                # strictly inside, its walls get the smoothing's slack
                ny_ = abs((inv.to_3x3() @ poly.normal).normalized().y)
                if any(nm in INTERIOR_BLACK and y0 <= ay <= y1 and
                       _in_poly(sx, z, pl, 0.0 if ny_ > 0.5 else 15.0)
                       for nm, y0, y1, pl, _t in _POCKETS_XZ):
                    poly.material_index = 1
                    continue
                for nm, x0, x1, y0, y1, z0, z1, *pl in _POCKETS:
                    if nm not in INTERIOR_BLACK:
                        continue
                    # a WALL lies on the polygon's edge (15 mm: the print smoothing rounds it); a face
                    # looking along X is skin or the floor and must be strictly inside -- with the
                    # slack, the fascia's own faces beside the mouth's slanted sides came out black
                    # as a saw-tooth
                    nx_ = abs((inv.to_3x3() @ poly.normal).normalized().x)
                    tol_ = 15.0 if nx_ < 0.5 else 0.0
                    if x0 <= sx <= x1 and y0 <= ay <= y1 and z0 <= z <= z1 and \
                            (not pl or _in_poly(ay, z, pl[0], tol_)):
                        poly.material_index = 1
                        break
    ctx, ctx_tags = ctx_objects(sc) if globals().get("GLOSSY_CONTEXT", True) else ([], {})
    for o in ctx:
        o.data.materials.append(finmats[ctx_tags[o.name]])
        tyres.append(o)
    wheelmats = {"bronze": bronze, "rubber": rubber,
                 "dark": mat("GLOSSY_DARK", (0.015, 0.015, 0.015, 1.0), 0.2, 0.5),
                 "disc": mat("GLOSSY_DISC", (0.25, 0.25, 0.26, 1.0), 0.9, 0.35),
                 "caliper": mat("GLOSSY_CALIPER", (0.55, 0.30, 0.10, 1.0), 0.6, 0.3)}
    finmats.update({k: v for k, v in wheelmats.items() if k not in finmats})
    for t in tyres:
        if t.name.startswith(("GLOSSY_TYRE", "GLOSSY_RIM")):
            t.data.materials.append(rubber if t.name.startswith("GLOSSY_TYRE") else bronze)
        elif t.get("glossy_tag") in wheelmats and not t.data.materials:
            t.data.materials.append(wheelmats[t["glossy_tag"]])
    # ground plane, big and light grey, for the bounce and the shadow
    gm = bpy.data.meshes.new("GLOSSY_GROUND")
    gm.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("GLOSSY_GROUND", gm)
    sc.collection.objects.link(ground)
    gmat = bpy.data.materials.new("GLOSSY_GROUND")
    g = principled(gmat)
    set_in(g, ("Base Color",), (0.62, 0.62, 0.62, 1.0))
    set_in(g, ("Roughness",), 0.9)
    gm.materials.append(gmat)

    def camera_split(nt, out_node, cam_shader, other_shader):
        """camera rays see `cam_shader`, every other ray (reflections, bounce) sees `other_shader`"""
        lp = nt.nodes.new("ShaderNodeLightPath")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
        nt.links.new(other_shader, mx.inputs[1])
        nt.links.new(cam_shader, mx.inputs[2])
        nt.links.new(mx.outputs[0], out_node.inputs[0])
    if PRESENT:
        # the floor: light grey seamless to the camera, a dark studio floor in the car's reflections
        nt = gmat.node_tree
        outn = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        # camera branch DIFFUSE: a principled floor's own specular at grazing angles mirrored the dark
        # room and drew a black band along the horizon (first presentation render)
        # ... plus a faint emission: lit only by the dark room and the local lights, the far floor
        # went black (second render). The emission keeps the seamless light; the diffuse keeps the
        # car's shadow on it.
        seam = nt.nodes.new("ShaderNodeBsdfDiffuse")
        seam.inputs["Color"].default_value = (0.70, 0.70, 0.71, 1.0)
        glow = nt.nodes.new("ShaderNodeEmission")
        glow.inputs["Color"].default_value = (0.70, 0.70, 0.71, 1.0)
        glow.inputs["Strength"].default_value = 0.55
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(seam.outputs[0], add.inputs[0])
        nt.links.new(glow.outputs[0], add.inputs[1])
        dark = nt.nodes.new("ShaderNodeBsdfDiffuse")
        dark.inputs["Color"].default_value = (0.03, 0.03, 0.03, 1.0)
        camera_split(nt, outn, add.outputs[0], dark.outputs[0])
    # lights: a large soft key above-front-left, a fill, a rim -- or, for the presentation, a long
    # softbox overhead and two strip lights along the sides, as ref-09's long highlights read
    made = [ground]
    rig = ((("GLOSSY_KEY", (2.0, -5.0, 6.0), 4000.0, 6.0, None),
            ("GLOSSY_FILL", (-4.0, 6.0, 4.0), 1500.0, 8.0, None),
            ("GLOSSY_RIM", (-8.0, -2.0, 3.0), 1200.0, 4.0, None)) if not PRESENT else
           # the top box higher and weaker (6.0 / 900, was 4.2 / 1500): from the front and from above
           # it lay on the bonnet as one white sheet, where ref-09 shows a soft gradient
           (("GLOSSY_TOP", (-1.2, 0.0, 6.0), 900.0, 7.0, 1.8),
            ("GLOSSY_STRIP_L", (-1.2, 4.5, 1.6), 750.0, 6.5, 0.6),
            ("GLOSSY_STRIP_R", (-1.2, -4.5, 1.6), 750.0, 6.5, 0.6),
            ("GLOSSY_FRONT", (5.0, 0.0, 1.2), 350.0, 3.0, 1.5)))
    for nm, loc, energy, size, size_y in rig:
        ld = bpy.data.lights.new(nm, "AREA")
        ld.energy, ld.size = energy, size
        if size_y is not None:
            ld.shape, ld.size_y = "RECTANGLE", size_y
        lo = bpy.data.objects.new(nm, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        dv = mathutils.Vector((-1.2, 0.0, 0.4)) - mathutils.Vector(loc)
        lo.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
        made.append(lo)
    old_world = sc.world
    world = bpy.data.worlds.new("GLOSSY_WORLD")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.75, 0.76, 0.78, 1.0)
    bg.inputs["Strength"].default_value = 0.35 if globals().get("GLOSSY_FINAL") else 1.0
    if PRESENT:
        # the seamless to the camera, a dark room everywhere else
        wout = next(n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD")
        bg.inputs["Color"].default_value = (0.70, 0.70, 0.71, 1.0)
        bg.inputs["Strength"].default_value = 1.0
        bg_dark = world.node_tree.nodes.new("ShaderNodeBackground")
        bg_dark.inputs["Color"].default_value = (0.02, 0.02, 0.022, 1.0)
        bg_dark.inputs["Strength"].default_value = 1.0
        camera_split(world.node_tree, wout, bg.outputs[0], bg_dark.outputs[0])
    sc.world = world
    old_engine = sc.render.engine
    engines = ("CYCLES",) if globals().get("GLOSSY_FINAL") else ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES")
    for eng in engines:
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    if sc.render.engine == "CYCLES":
        sc.cycles.samples = int(globals().get("GLOSSY_SAMPLES", 64))
        try:
            sc.cycles.use_denoising = True
            sc.cycles.device = "GPU"
        except Exception:
            pass
    sc.render.resolution_x, sc.render.resolution_y = (1920, 1080) if globals().get("GLOSSY_FINAL") else (1600, 900)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    cd = bpy.data.cameras.new("GLOSSY_CAM")
    cam = bpy.data.objects.new("GLOSSY_CAM", cd)
    sc.collection.objects.link(cam)
    old_cam = sc.camera
    sc.camera = cam
    cd.clip_start, cd.clip_end = 0.01, 100.0
    os.makedirs(OUT, exist_ok=True)
    only = globals().get("GLOSSY_ONLY")
    for tag, loc, target, lens, kind in VIEWS + HERO:
        if only and tag not in only:
            continue
        if tag in dict((h[0], 1) for h in HERO) and not globals().get("GLOSSY_FINAL"):
            continue
        cd.type = kind
        if kind == "ORTHO":
            cd.ortho_scale = lens
        else:
            cd.lens = lens
        cam.location = loc
        dv = mathutils.Vector(target) - mathutils.Vector(loc)
        q_ = dv.to_track_quat("-Z", "Y")
        if tag == "top":
            # ref-09's plan has the nose on the LEFT; rolled 180 so the sheets compare like for like
            q_ = q_ @ mathutils.Quaternion((0.0, 0.0, 1.0), math.pi)
        cam.rotation_euler = q_.to_euler()
        sc.render.filepath = os.path.join(OUT, f"{tag_prefix}{tag}.png")
        bpy.ops.render.render(write_still=True)
        print(f"  wrote {sc.render.filepath}")
    # put everything back
    for n, mats in saved.items():
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)
    for o in files + tyres:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(me, bpy.types.Mesh):
            bpy.data.meshes.remove(me)
        elif me is not None:
            bpy.data.curves.remove(me)
    for o, m in subd:
        o.modifiers.remove(m)
    for o in made:
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(d, bpy.types.Mesh):
            bpy.data.meshes.remove(d)
        else:
            bpy.data.lights.remove(d)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cd)
    sc.camera = old_cam
    sc.world = old_world
    bpy.data.worlds.remove(world)
    for m in {id(x): x for x in (rubber, bronze, gmat, *finmats.values())}.values():
        bpy.data.materials.remove(m)
    sc.render.engine = old_engine
    for o, h in hidden:
        try:
            o.hide_render = h
        except ReferenceError:
            pass


main()
