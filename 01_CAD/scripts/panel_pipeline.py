"""
panel_pipeline.py — the road from a surface region to a print file, as tooling rather than as a
one-off. Runs inside Blender.

    surface region -> solid -> measured -> split -> oriented -> exported

Every stage that depends on a supplier answer is a parameter set to None with the docs/13 question
that fills it. A stage whose parameter is missing does not guess: it reports what it needs and
stops. That is the whole point — this script is written so that on the day the printer answers,
one dict changes and the pipeline runs to completion.

WHAT THIS IS NOT. It does not produce a finished panel. v019 is a Stage 01 blockout and docs/16
says plainly that the blockout is thrown away when real surfacing begins. Running this on v019 is
a DRY RUN: it proves the toolchain on real project geometry so that the toolchain is not being
written for the first time later, when the surfaces are expensive.

    import bpy; exec(open(".../panel_pipeline.py").read())      dry run on the rear zone
"""

import bmesh
import bpy
import math
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT_DIR = os.path.join(REPO, "03_PRINT", "dry_run")

# --------------------------------------------------------------------- supplier parameters
# None means "nobody has told us yet". Nothing downstream may invent a value for these.
PRINTER = {
    "technology":        None,   # docs/13 Q25   FDM / SLS / MJF / SLA / CF
    "build_x_mm":        None,   # docs/13 Q26   usable, not catalogue
    "build_y_mm":        None,   # docs/13 Q26
    "build_z_mm":        None,   # docs/13 Q26
    "material":          None,   # docs/13 Q27
    "survives_exotherm": None,   # docs/13 Q28   True/False — if False the whole plan changes
    "tolerance_mm":      None,   # docs/13 Q29   measured on a 500-800 mm part
    "min_wall_mm":       None,   # docs/13 Q30
    "max_flat_mm":       None,   # docs/13 Q31   largest area it lays without lifting
    "max_overhang_deg":  None,   # docs/13 Q32
    "supports_by":       None,   # docs/13 Q33   who removes them
    "split_planes":      None,   # docs/13 Q34   "flat" / "curved ok"
    "key_clearance_mm":  None,   # docs/13 Q35
    "bond_gap_mm":       None,   # docs/13 Q36
}

SHOP = {
    "laminate_mm":       None,   # docs/13 Q12   glass thickness over the print
    "flange_width_mm":   None,   # docs/13 Q15
    "panel_gap_mm":      None,   # docs/13 Q14   project has started from 4.0
}

# Our own working values until the suppliers answer. Marked as what they are.
WORKING = {
    "core_wall_mm": 3.0,         # DESIGN ASSUMPTION. CLAUDE.md says 3-4 mm walls for the print
                                 # master. Replaced by PRINTER["min_wall_mm"] when it arrives.
    "density_g_cm3": 1.24,       # ENGINEERING ASSUMPTION, generic PLA. Not measured, not quoted
                                 # by any supplier. Mass figures below are order-of-magnitude only.
}


def _log(stage, msg):
    print(f"  [{stage:<9}] {msg}")


def _need(stage, keys, where):
    missing = [k for k in keys if where.get(k) is None]
    if missing:
        _log(stage, "STOPPED — no value for: " + ", ".join(missing))
        return False
    return True


# --------------------------------------------------------------------- stages
def extract(src_name, region, name):
    """STAGE 1. Copy the source body and keep only faces whose centre lies inside `region`,
    a dict of spec-X / Y / Z ranges in millimetres. Spec X is +rearward; Blender X is +forward."""
    src = bpy.data.objects.get(src_name)
    if src is None:
        _log("extract", f"no object named {src_name}")
        return None
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        c = ob.matrix_world @ f.calc_center_median()
        sx, y, z = -c.x * 1000, c.y * 1000, c.z * 1000
        inside = (region["x"][0] <= sx <= region["x"][1]
                  and region["y"][0] <= abs(y) <= region["y"][1]
                  and region["z"][0] <= z <= region["z"][1])
        if not inside:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    _log("extract", f"{name}: {len(ob.data.polygons)} faces kept of {len(src.data.polygons)}")
    return ob if len(ob.data.polygons) else None


def solidify(ob, wall_mm):
    """STAGE 2. Give the surface the PRINT CORE wall. This is not the finished panel thickness:
    the stack is core + surface prep + laminate + local reinforcement (panel_architecture.py)."""
    m = ob.modifiers.new("core", "SOLIDIFY")
    m.thickness = wall_mm / 1000.0
    m.offset = -1.0            # grow inward, so the outer surface stays the design surface
    m.use_even_offset = True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    _log("solidify", f"wall {wall_mm} mm inward, {len(ob.data.polygons)} faces")
    return ob


def measure(ob):
    """STAGE 3. Bounding box, surface area, solid volume, mass estimate."""
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    sx = [-v.x * 1000 for v in vs]
    y = [v.y * 1000 for v in vs]
    z = [v.z * 1000 for v in vs]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    area = sum(f.calc_area() for f in bm.faces) * 1e6          # m2 -> mm2
    vol = abs(bm.calc_volume(signed=True)) * 1e9               # m3 -> mm3
    bm.free()
    mass = vol / 1000.0 * WORKING["density_g_cm3"]             # mm3 -> cm3 -> g
    d = dict(length=max(sx) - min(sx), width=max(y) - min(y), height=max(z) - min(z),
             area_mm2=area, volume_mm3=vol, mass_g=mass)
    _log("measure", f"bbox {d['length']:.0f} x {d['width']:.0f} x {d['height']:.0f} mm")
    _log("measure", f"surface {area/1e6:.3f} m2   solid {vol/1e3:.0f} cm3   "
                    f"mass ~{mass/1000:.2f} kg (ASSUMED density {WORKING['density_g_cm3']} g/cm3)")
    return d


def split(dims):
    """STAGE 4. How many sections, and why. Needs the printer's usable build volume."""
    if not _need("split", ["build_x_mm", "build_y_mm", "build_z_mm"], PRINTER):
        _log("split", "docs/13 Q26. Until then no split can be computed, and none is guessed.")
        return None
    need = [math.ceil(dims["length"] / PRINTER["build_x_mm"]),
            math.ceil(dims["width"] / PRINTER["build_y_mm"]),
            math.ceil(dims["height"] / PRINTER["build_z_mm"])]
    n = max(1, need[0] * need[1] * need[2])
    _log("split", f"{n} section(s): {need[0]} x {need[1]} x {need[2]} over the build volume")
    if PRINTER["max_flat_mm"] and max(dims["length"], dims["width"]) > PRINTER["max_flat_mm"]:
        _log("split", "a further split may be forced by warping, not by volume — docs/13 Q31")
    return n


def orient(dims):
    """STAGE 5. Print orientation. One rule can be applied now; the rest need Q32 and Q33."""
    _log("orient", "RULE the class-A face goes up or vertical, never down onto supports")
    _log("orient", "RULE a face that must be supported is a face that ends up inside the car")
    if not _need("orient", ["max_overhang_deg", "supports_by"], PRINTER):
        _log("orient", "docs/13 Q32 and Q33. No orientation is chosen without them.")
        return None
    _log("orient", f"max unsupported overhang {PRINTER['max_overhang_deg']} deg")
    return True


def export(ob, tag):
    """STAGE 6. Write the print file. STL for now; 3MF or STEP when the shop states a preference
    (docs/13 Q5)."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{tag}.stl")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True, global_scale=1000.0)
    kb = os.path.getsize(path) // 1024
    _log("export", f"{path}  ({kb} kB, millimetres)")
    return path


def run(src_name, region, tag):
    print(f"\n--- PIPELINE DRY RUN: {tag}")
    ob = extract(src_name, region, f"_pipe_{tag}")
    if ob is None:
        return None
    solidify(ob, WORKING["core_wall_mm"])
    dims = measure(ob)
    split(dims)
    orient(dims)
    path = export(ob, tag)
    bpy.data.objects.remove(ob, do_unlink=True)
    return dims, path


def main():
    print("=" * 96)
    print("STATEV 001 — PANEL PIPELINE, DRY RUN on v019.")
    print("v019 is a Stage 01 blockout. docs/16 says the blockout is discarded when surfacing")
    print("begins, so what is proven here is the TOOLCHAIN, not the panel.")
    print("=" * 96)
    unknown = [k for k, v in PRINTER.items() if v is None] + [k for k, v in SHOP.items() if v is None]
    print(f"\nsupplier values still unknown: {len(unknown)} of {len(PRINTER) + len(SHOP)}")
    print("  " + ", ".join(unknown))
    print("\nworking values, and what they are:")
    print(f"  core wall {WORKING['core_wall_mm']} mm      DESIGN ASSUMPTION (CLAUDE.md says 3-4 mm)")
    print(f"  density {WORKING['density_g_cm3']} g/cm3    ENGINEERING ASSUMPTION, generic PLA, unmeasured")
    # A region that is entirely OUR shape: the tail behind the rear arch, above the undercut.
    run("STATEV_REAR_VOLUME",
        dict(x=(2950, 3420), y=(0, 950), z=(300, 1050)), "tail_section")
    print("\nStages that produced real output: extract, solidify, measure, export.")
    print("Stages that correctly refused to guess: split, orient.")


main()
