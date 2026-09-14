"""
statev_preview_loft.py — a PREVIEW skin lofted through the master sections, so the proportions
can actually be judged. This is NOT the body surface and NOT manufacturing geometry.

What it is: each master section (already widened around the axles) is resampled to a fixed point
count, the sections are bridged into a closed shell, and the cabin aperture is cut between the
windshield base and the roll hoops. Curvature is whatever linear bridging gives — there is no
class-A work here, no tangency control, no panel split.

What it is for: answering one question — "does this read as STATEV 001 on a 986?" — before anyone
spends time on real surfaces. Change SECTIONS in statev_skeleton.py and re-run; never edit the mesh.

Run after statev_skeleton.py. Rebuilds the PREVIEW collection inside STATEV_001.
"""

import bpy
import math
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else os.path.join(REPO, "01_CAD/scripts")
_sk = {}
with open(os.path.join(_here, "statev_skeleton.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("def build(")[0], _sk)
SECTIONS, PFX, DECK_SPINE = _sk["SECTIONS"], _sk["PFX"], _sk["DECK_SPINE"]
HOOD_SPINE = _sk["HOOD_SPINE"]
widening, sx, mm = _sk["widening"], _sk["sx"], _sk["mm"]
D = _sk["donor_dims"]()

COLL = "PREVIEW"
N_HALF = 26          # resampled points per half-section
CROWN_FACTOR = 0.10  # how far the deck rises above the last data point, as a fraction of its width
                     # (the sections carry no data above their last Z; this is a preview assumption,
                     #  clamped to the spec's deck spine wherever that is defined)
CABIN_Y = 700        # half-width of the cabin aperture cut
CABIN_Z = 640        # cut everything above this between cowl and hoops


def resample(poly, n):
    """Even arc-length resample of a 2D polyline [(y, z), ...]."""
    d = [0.0]
    for i in range(1, len(poly)):
        d.append(d[-1] + math.dist(poly[i - 1], poly[i]))
    total = d[-1]
    out = []
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


def section_ring(spec_x, prof):
    """Closed (y, z) ring for one section: floor centre -> out -> up -> crown -> mirrored back."""
    pts = sorted(((z, y + widening(spec_x, z)) for z, y in prof), key=lambda t: t[0])
    z_floor, hw_floor = pts[0]
    z_top, hw_top = pts[-1]
    crown_z = z_top + hw_top * CROWN_FACTOR
    hx = [t[0] for t in HOOD_SPINE]
    if hx[0] <= spec_x <= hx[-1]:                    # ahead of the cabin: the hood line IS the crown
        for i in range(len(HOOD_SPINE) - 1):
            (x0, z0), (x1, z1) = HOOD_SPINE[i], HOOD_SPINE[i + 1]
            if x0 <= spec_x <= x1:
                f = 0.0 if x1 == x0 else (spec_x - x0) / (x1 - x0)
                crown_z = z0 + f * (z1 - z0)
                break
    xs = [t[0] for t in DECK_SPINE]
    if xs[0] <= spec_x <= xs[-1]:                    # inside the deck: the spec says how tall it is
        for i in range(len(DECK_SPINE) - 1):
            (x0, z0), (x1, z1) = DECK_SPINE[i], DECK_SPINE[i + 1]
            if x0 <= spec_x <= x1:
                f = 0.0 if x1 == x0 else (spec_x - x0) / (x1 - x0)
                crown_z = min(crown_z, z0 + f * (z1 - z0))
                break
    half = [(0.0, z_floor)] + [(hw, z) for z, hw in pts] + [(0.0, max(crown_z, z_top + 10))]
    half = resample(half, N_HALF)
    ring = list(half) + [(-y, z) for y, z in reversed(half[1:-1])]
    return ring


def build():
    root = bpy.data.collections["STATEV_001"]
    coll = bpy.data.collections.get(COLL)
    if coll:
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        coll = bpy.data.collections.new(COLL)
        root.children.link(coll)

    order = sorted(SECTIONS.items(), key=lambda kv: kv[1][0])
    verts, faces, rings = [], [], []
    for name, (spec_x, role, prof) in order:
        ring = section_ring(spec_x, prof)
        idx = []
        for y, z in ring:
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

    me = bpy.data.meshes.new("PREVIEW_SKIN")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(PFX + "PREVIEW_SKIN", me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    mat = bpy.data.materials.get("STATEV_BODY")
    if mat:
        me.materials.append(mat)
    ob.color = (0.045, 0.115, 0.075, 1.0)
    ob["status"] = "PREVIEW"
    ob["note"] = ("lofted straight through the master sections for proportion review only. "
                  "No tangency control, no class-A surface, no panel split, not for manufacturing. "
                  "Edit SECTIONS in statev_skeleton.py and re-run; never edit this mesh.")

    # --- cut the cabin aperture: between the windshield base and the roll hoops
    cowl_x, hoop_x = D["cowl_x"], D["hoop_x"]
    cx = (cowl_x + hoop_x) / 2.0
    length = abs(cowl_x - hoop_x)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm(cx), 0.0, mm(CABIN_Z + 400)))
    cut = bpy.context.active_object
    cut.name = "_cabin_cutter"
    cut.scale = (mm(length), mm(2 * CABIN_Y), mm(800))
    for c in cut.users_collection:
        c.objects.unlink(cut)
    coll.objects.link(cut)
    m = ob.modifiers.new("cabin", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cut
    m.solver = "EXACT"
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier="cabin")
    bpy.data.objects.remove(cut, do_unlink=True)
    bpy.ops.object.shade_smooth()

    dims = [round(v * 1000) for v in ob.dimensions]
    print(f"{COLL}: {len(me.vertices)} verts, {len(me.polygons)} faces, dims (mm) {dims} | "
          f"cabin cut specX {-cowl_x:.0f}..{-hoop_x:.0f}")
    return ob


build()
