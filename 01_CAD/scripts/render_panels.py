"""
render_panels.py — the printed files put back on the car, one colour per part, as pictures.

    Blender:  import bpy; exec(open(".../render_panels.py").read())

assembly_check.py measures the re-assembled files against the surface; this shows them. Every .stl
in 03_PRINT/production and 03_PRINT/shape_only is imported, placed by its placement.json matrix,
given a colour by part id (shape-only parts in a lighter tint), rendered from four views with the
workbench engine, and removed again. Nothing in the scene is changed by it.

Written 2026-09-26, the day production went to WHOLE PANELS: the question "are these real, large,
whole panels" has a picture as its answer, not only a file count.
"""
import colorsys
import json
import os

import bpy
import mathutils

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) \
    if "__file__" in globals() else "/Users/miroslavstatev/vehicle-3d-modeling"
TIERS = (("production", 0.85), ("shape_only", 0.45))
OUT = os.path.join(REPO, "04_ENGINEERING", "statev_v01", "review")


def main():
    sc = bpy.context.scene
    imported = []
    mats = {}
    hidden = [(o, o.hide_render) for o in bpy.data.objects]
    for o, _ in hidden:
        o.hide_render = True
    for tier, sat in TIERS:
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
            new = [o for o in bpy.data.objects if o not in before]
            pid = fn.split("_")[0]
            if pid not in mats:
                k = (int(pid[1:]) * 0.618034) % 1.0
                r, g, b = colorsys.hsv_to_rgb(k, sat, 0.9)
                m = bpy.data.materials.get(f"RVP_{pid}") or bpy.data.materials.new(f"RVP_{pid}")
                m.diffuse_color = (r, g, b, 1.0)
                mats[pid] = m
            for o in new:
                # the importer links to the ACTIVE collection, which may be excluded from the
                # view layer or hidden -- the first run rendered four empty frames that way.
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                sc.collection.objects.link(o)
                o.hide_viewport = False
                # the importer keeps its global_scale as the OBJECT's scale, and the placement
                # matrix assumes millimetres already turned into metres: compose, or the part
                # lands 1000x too big (the second empty render).
                o.matrix_world = mathutils.Matrix(mat) @ mathutils.Matrix.Diagonal(
                    (0.001, 0.001, 0.001, 1.0))
                o.data.materials.clear()
                o.data.materials.append(mats[pid])
                o.hide_render = False
                imported.append(o)
    if not imported:
        print("  nothing to render: run panel_production.py first")
        return
    old_engine = sc.render.engine
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_cavity = False
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = False
    sc.world.color = (0.85, 0.85, 0.85)
    sh.background_type = "WORLD"
    cam_data = bpy.data.cameras.new("RVP_CAM")
    cam = bpy.data.objects.new("RVP_CAM", cam_data)
    sc.collection.objects.link(cam)
    old_cam = sc.camera
    sc.camera = cam
    cam_data.clip_start, cam_data.clip_end = 0.01, 100.0
    c = (-1.235, 0.0, 0.45)

    def shot(tag, loc, target, ortho=None, lens=45):
        if ortho:
            cam_data.type, cam_data.ortho_scale = "ORTHO", ortho
        else:
            cam_data.type, cam_data.lens = "PERSP", lens
        cam.location = loc
        dv = mathutils.Vector(target) - mathutils.Vector(loc)
        cam.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, f"rv_panels_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print(f"  wrote {sc.render.filepath}")

    os.makedirs(OUT, exist_ok=True)
    shot("front34", (c[0] + 5.2, -5.0, 2.2), (c[0] + 0.3, 0.0, 0.45))
    shot("rear34", (c[0] - 5.2, -5.0, 2.2), (c[0] - 0.3, 0.0, 0.45))
    shot("side", (c[0], -10.0, c[2]), c, ortho=4.9)
    shot("top", (c[0], 0.0, 10.0), c, ortho=4.9)
    for o in imported:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(me)
    for m in mats.values():
        bpy.data.materials.remove(m)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)
    sc.camera = old_cam
    sc.render.engine = old_engine
    for o, hr in hidden:
        try:
            o.hide_render = hr
        except ReferenceError:
            pass
    print(f"  {len(imported)} files rendered in {len(mats)} colours")


main()
