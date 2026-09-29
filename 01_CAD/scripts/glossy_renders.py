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
         ("rear", (-9.5, 0.0, 1.1), (-1.6, 0.0, 0.45), 60, "PERSP")]


def principled(mat):
    mat.use_nodes = True
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def set_in(node, names, value):
    for nm in names:
        if nm in node.inputs:
            node.inputs[nm].default_value = value
            return True
    return False


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
                for p in o.data.polygons:
                    p.use_smooth = True
                out.append(o)
    return out


# CLEAN MODE, 2026-09-29 (v051), after the owner's review ("parasitic elements"). The printed
# files carry 30 mm overlaps (shape-only neighbours), joint tabs, housings, ducts and sails, and
# a render of all of them together reads as clutter that the car will never show. "clean" renders
# the BODY volumes with every opening cut, under a temporary Catmull-Clark x2 with creases on the
# real edges (so the loft's shading ripples go and the creases stay), plus only the elements a
# person standing next to the car would see. Housings, ducts and the shape-only sails are not
# hidden from the files, only from this picture.
CLEAN_SHOW = ("INTAKE_BLADE", "FENDER_CHANNEL", "FRONT_MASK", "REAR_CENTRE_MASK", "PLATE_RECESS",
              "EXHAUST_SURROUND", "DIFFUSER_FIN", "HEADLIGHT_SURROUND")
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


def main():
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
    set_in(p, ("Base Color",), (0.012, 0.055, 0.028, 1.0))
    set_in(p, ("Metallic",), 0.55)
    set_in(p, ("Roughness",), 0.22)
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
    saved = {}
    for n in body:
        o = bpy.data.objects[n]
        saved[n] = [m for m in o.data.materials]
        o.data.materials.clear()
        o.data.materials.append(paint)
    for t in tyres:
        t.data.materials.append(rubber if t.name.startswith("GLOSSY_TYRE") else bronze)
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
    # lights: a large soft key above-front-left, a fill, a rim
    made = [ground]
    for nm, loc, energy, size in (("GLOSSY_KEY", (2.0, -5.0, 6.0), 4000.0, 6.0),
                                  ("GLOSSY_FILL", (-4.0, 6.0, 4.0), 1500.0, 8.0),
                                  ("GLOSSY_RIM", (-8.0, -2.0, 3.0), 1200.0, 4.0)):
        ld = bpy.data.lights.new(nm, "AREA")
        ld.energy, ld.size = energy, size
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
    bg.inputs["Strength"].default_value = 1.0
    sc.world = world
    old_engine = sc.render.engine
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    if sc.render.engine == "CYCLES":
        sc.cycles.samples = 64
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
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
    for tag, loc, target, lens, kind in VIEWS:
        cd.type, cd.lens = kind, lens
        cam.location = loc
        dv = mathutils.Vector(target) - mathutils.Vector(loc)
        cam.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
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
        bpy.data.meshes.remove(me)
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
    for m in (paint, rubber, bronze, gmat):
        bpy.data.materials.remove(m)
    sc.render.engine = old_engine
    for o, h in hidden:
        try:
            o.hide_render = h
        except ReferenceError:
            pass


main()
