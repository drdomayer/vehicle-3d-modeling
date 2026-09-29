"""
review_renders.py — the body as built, from the angles the owner judges it from.

    Blender:  import bpy; exec(open(".../review_renders.py").read())

Four workbench renders of STATEV_MASTER + STATEV_STAGE03 (+ the wheels): nose 3/4, front 3/4,
nose low, dead ahead. Written 2026-09-29, the day the nose became a chamfered box: until then
these pictures were made by ad-hoc code in whichever session needed them, so the "before" of
every visual comparison was whatever that session had left behind. Same file names every run,
so `git diff` on the PNGs is the before/after.

They are PICTURES, not measurements: the numbers are silhouette_overlay, plan_overlay,
endview_overlay, highlight_test and edge_test. Nothing in the scene is changed by this.
"""
import os

import bpy
import mathutils

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) \
    if "__file__" in globals() else "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "statev_v01", "review")
SHOW = ("STATEV_MASTER", "STATEV_STAGE03", "wheels")
# (tag, camera location, look-at, lens) in repo metres: +X forward, nose at x = +0.95
VIEWS = [("nose34", (3.2, 2.6, 0.9), (0.55, 0.15, 0.42), 50),
         ("front34", (4.2, 3.6, 2.0), (-0.9, 0.0, 0.45), 45),
         ("nose_low", (3.4, 1.9, 0.35), (0.6, 0.1, 0.35), 45),
         ("front", (6.0, 0.0, 0.55), (-0.5, 0.0, 0.45), 60),
         ("rear34", (-6.4, 3.4, 1.8), (-1.6, 0.0, 0.45), 45),
         ("side", (-1.2, 7.5, 0.6), (-1.2, 0.0, 0.5), 50)]


def main():
    sc = bpy.context.scene
    show = set()
    for cn in SHOW:
        c = bpy.data.collections.get(cn)
        if c:
            show.update(o.name for o in c.all_objects if o.type == "MESH")
    if not show:
        print("  nothing to render: build the body first")
        return
    hidden = [(o, o.hide_render) for o in bpy.data.objects]
    for o, _ in hidden:
        o.hide_render = o.name not in show
    old_engine = sc.render.engine
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "SINGLE"
    sh.single_color = (0.45, 0.47, 0.46)
    sh.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = False
    sc.world.color = (0.75, 0.75, 0.75)
    sh.background_type = "WORLD"
    cd = bpy.data.cameras.new("RV_CAM")
    cam = bpy.data.objects.new("RV_CAM", cd)
    sc.collection.objects.link(cam)
    old_cam = sc.camera
    sc.camera = cam
    cd.clip_start, cd.clip_end = 0.01, 100.0
    os.makedirs(OUT, exist_ok=True)
    for tag, loc, target, lens in VIEWS:
        cd.type, cd.lens = "PERSP", lens
        cam.location = loc
        dv = mathutils.Vector(target) - mathutils.Vector(loc)
        cam.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, f"rv_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print(f"  wrote {sc.render.filepath}")
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cd)
    sc.camera = old_cam
    sc.render.engine = old_engine
    for o, h in hidden:
        try:
            o.hide_render = h
        except ReferenceError:
            pass


main()
