"""
pilot_P21.py — the whole manufacturing chain on one panel: P21 REAR_FASCIA.

The point of this file is not to produce a rear fascia. It is to prove that the chain
surface -> solid -> thickness -> seams -> flange -> split -> interlock -> printable mesh -> export
runs end to end, and that when the scan and the supplier answers arrive they can be typed into
two dictionaries without the design surface being touched.

THE THREE KINDS OF NUMBER, kept apart on purpose:

    DESIGN      measured off v020. Ours. The scan cannot change these, only move the datum they
                sit on, which moves every panel alike. Nothing here is typed by hand.
    INTERFACE   what the real car will tell us. Every value is None and names what must be
                measured. No mounting point, hole, bracket or clearance is invented anywhere.
    SUPPLIER    what the printer and the composite shop will tell us. Every value is None and
                names its docs/13 question. Wall, laminate, split planes, keys, tolerances.

A value that is None is not a gap in the work. It is the work being honest about which half of the
problem it owns.

    import bpy; exec(open(".../pilot_P21.py").read())
"""

import bmesh
import bpy
import math
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT_DIR = os.path.join(REPO, "03_PRINT", "pilot_P21")
PANEL = "P21"

_pm = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_map.py"), "__name__": "_pm"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pm)
panel_of, not_panel = _pm["panel_of"], _pm["not_panel"]


# ---------------------------------------------------------------- INTERFACE: the real car only
# Every one of these is measured on the donor, never chosen here. The fascia hangs off the rear of
# the car; where it hangs from is not ours to decide.
INTERFACE = {
    "rear_crash_structure_x":      None,  # SCAN: how far forward the bumper beam sits
    "bumper_mount_points":         None,  # SCAN: positions and thread of the OEM bumper mounts
    "exhaust_hanger_positions":    None,  # SCAN: where the hangers are, so the fascia clears them
    "exhaust_tip_centres":         None,  # SCAN: two central tips, actual centres and diameter
    "rear_lamp_loom_route":        None,  # SCAN: where the loom can reach the light bar
    "boot_or_engine_lid_edge":     None,  # SCAN: the aperture the fascia must not foul
    "donor_quarter_surface_rear":  None,  # SCAN: the surface P15/P16 overlay, which P21 meets
    "ride_height_at_rear":         None,  # SCAN: measured, not the published 95 mm nominal
}

# ---------------------------------------------------------------- SUPPLIER: docs/13 answers only
SUPPLIER = {
    "technology":        None,  # Q25
    "build_x_mm":        None,  # Q26   usable, not catalogue
    "build_y_mm":        None,  # Q26
    "build_z_mm":        None,  # Q26
    "material":          None,  # Q27
    "survives_exotherm": None,  # Q28   if False the whole manufacturing plan changes
    "tolerance_mm":      None,  # Q29
    "min_wall_mm":       None,  # Q30
    "max_flat_mm":       None,  # Q31
    "max_overhang_deg":  None,  # Q32
    "supports_by":       None,  # Q33
    "split_planes":      None,  # Q34   flat only, or curved accepted
    "key_clearance_mm":  None,  # Q35
    "bond_gap_mm":       None,  # Q36
    "laminate_mm":       None,  # Q12
    "flange_width_mm":   None,  # Q15
    "panel_gap_mm":      None,  # Q14   project has started from 4.0
}

# ---------------------------------------------------------------- PROVISIONAL working values
# Used so the chain can run today. Each says what replaces it. None of these is a decision.
PROVISIONAL = {
    "core_wall_mm":    (3.0,  "replaced by SUPPLIER['min_wall_mm'], docs/13 Q30"),
    "flange_width_mm": (28.0, "replaced by SUPPLIER['flange_width_mm'], docs/13 Q15"),
    "overlap_mm":      (15.0, "replaced once the shop states its overlap, docs/13 Q15"),
    "panel_gap_mm":    (4.0,  "replaced by SUPPLIER['panel_gap_mm'], docs/13 Q14"),
    "key_clearance_mm": (0.25, "replaced by SUPPLIER['key_clearance_mm'], docs/13 Q35"),
    "bond_gap_mm":     (0.15, "replaced by SUPPLIER['bond_gap_mm'], docs/13 Q36"),
    "density_g_cm3":   (1.24, "generic PLA; replaced once SUPPLIER['material'] is known"),
    "trim_allowance_mm": (15.0, "material left on every donor-facing edge, trimmed at fit-test"),
}

# Neighbours, and whether a flange to each can be defined at all today.
NEIGHBOURS = {
    "P22 DIFFUSER":     ("category 1, ours", "flange CAN be defined; both surfaces exist and "
                                             "neither moves with the scan"),
    "P19 REAR_DECK":    ("BLOCKED, roof envelope", "flange CANNOT be defined; the deck height is "
                                                   "not known until scan session S2"),
    "P15/P16 HAUNCH":   ("category 3, donor overlay", "flange CANNOT be defined; the haunch's own "
                                                      "form is the donor quarter"),
    "P34 CENTRE_MASK":  ("Stage 03, no geometry", "aperture reserved, flange deferred"),
    "P36 PLATE_RECESS": ("Stage 03, no geometry", "aperture reserved, flange deferred"),
    "TAIL_BAR / TAIL_END": ("lighting, placed", "aperture must be cut for it; see the design table"),
}


def extract():
    master = bpy.data.collections["STATEV_MASTER"]
    bodies = [o for o in master.all_objects if o.type == "MESH" and "VOLUME" in o.name]
    verts, faces = [], []
    for src in bodies:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            c = src.matrix_world @ f.calc_center_median()
            n = (src.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            ny = -n.y if c.y > 0 else n.y
            if not_panel(sx, ay, z, n.z, ny) or panel_of(sx, ay, z) != PANEL:
                continue
            base = len(verts)
            for v in f.verts:
                verts.append(tuple(src.matrix_world @ v.co))
            faces.append(tuple(range(base, base + len(f.verts))))
        bm.free()
    me = bpy.data.meshes.new("PILOT_P21_surface")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("PILOT_P21_REAR_FASCIA", me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob


def design_facts(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    sx = [-v.x * 1000 for v in vs]
    y = [v.y * 1000 for v in vs]
    z = [v.z * 1000 for v in vs]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    area = sum(f.calc_area() for f in bm.faces)
    bm.free()
    return dict(x_min=min(sx), x_max=max(sx), y_span=max(y) - min(y),
                z_min=min(z), z_max=max(z), area_m2=area, faces=len(ob.data.polygons))


def solidify(ob, wall):
    m = ob.modifiers.new("core", "SOLIDIFY")
    m.thickness, m.offset, m.use_even_offset = wall / 1000.0, -1.0, True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    return ob


def split_plan(d):
    if SUPPLIER["build_x_mm"] is None:
        return None
    return None


def prove_separation():
    """Prove, rather than assert, that the design surface does not depend on the interface values.

    The claim this pilot rests on is that when the scan arrives its numbers go into INTERFACE and
    the class-A surface is untouched. That is only true if no code path reads INTERFACE into the
    surface. So: extract with everything None, extract again with every value filled with nonsense,
    and compare the two surfaces vertex for vertex. If the hashes differ, the separation is a story
    rather than a fact and the pilot has to be rebuilt."""
    import hashlib

    def surface_hash():
        ob = extract()
        pts = sorted((round(v.co.x * 1000, 4), round(v.co.y * 1000, 4), round(v.co.z * 1000, 4))
                     for v in ob.data.vertices)
        h = hashlib.sha256(repr(pts).encode()).hexdigest()
        bpy.data.objects.remove(ob, do_unlink=True)
        return h, len(pts)

    before = surface_hash()
    saved = dict(INTERFACE)
    for k in INTERFACE:
        INTERFACE[k] = 999.0          # deliberately wrong values, to see if anything listens
    after = surface_hash()
    INTERFACE.update(saved)
    ok = before == after
    print("\n0. SEPARATION PROOF — does the design surface depend on the interface values?")
    print(f"   INTERFACE all None    {before[0][:32]}  {before[1]} verts")
    print(f"   INTERFACE all 999     {after[0][:32]}  {after[1]} verts")
    print(f"   identical: {ok}  ->  {'PASS' if ok else 'FAIL — the separation is not real'}")
    return ok


def main():
    print("=" * 104)
    print("PILOT — P21 REAR_FASCIA.  Validating the chain, not producing a part.")
    print("=" * 104)
    if not prove_separation():
        print("   stopping: the pilot's core claim does not hold")
        return None, None
    ob = extract()
    d = design_facts(ob)

    print("\n1. DESIGN — measured off v020, ours, unaffected by the scan")
    print(f"   spec X span        {d['x_min']:.0f} .. {d['x_max']:.0f} mm")
    print(f"   width              {d['y_span']:.1f} mm")
    print(f"   Z span             {d['z_min']:.0f} .. {d['z_max']:.0f} mm")
    print(f"   outer surface area {d['area_m2']:.3f} m2   {d['faces']} faces")
    print("   shape source       ring() from SECTIONS, the character fields, DECK_SPINE and")
    print("                      REAR_UNDERCUT_FIELD. All ours. Only the datum moves with the scan.")

    print("\n2. APERTURES this panel must carry")
    print("   TAIL_BAR   specX 3200, Z 593..631, 1440 wide   placed on the built body, verified")
    print("   TAIL_END   specX 3120, Z 593..631              shares the bar's Z, one continuous light")
    print("   exhaust    two central tips — centres and diameter are INTERFACE, not chosen here")
    print("   plate      P36 recess — Stage 03, aperture reserved")

    print("\n3. INTERFACE — what the real car must tell us. Nothing invented.")
    for k, v in INTERFACE.items():
        print(f"   {k:<30} {str(v):<6} SCAN REQUIRED")

    print("\n4. SUPPLIER — what the printer and shop must tell us")
    for k, v in SUPPLIER.items():
        print(f"   {k:<22} {str(v)}")

    print("\n5. PROVISIONAL working values, so the chain can run today")
    for k, (v, why) in PROVISIONAL.items():
        print(f"   {k:<20} {v:<7} {why}")

    print("\n6. NEIGHBOURS and whether a flange can be defined at all")
    for k, (status, verdict) in NEIGHBOURS.items():
        print(f"   {k:<22} {status:<28} {verdict}")

    wall = PROVISIONAL["core_wall_mm"][0]
    solidify(ob, wall)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    vol = abs(bm.calc_volume(signed=True)) * 1e9
    bm.free()
    mass = vol / 1000.0 * PROVISIONAL["density_g_cm3"][0] / 1000.0
    print(f"\n7. SOLID at the provisional {wall} mm core wall")
    print(f"   volume {vol/1000.0:.0f} cm3   mass ~{mass:.2f} kg   {len(ob.data.polygons)} faces")

    print("\n8. SPLIT — not computed")
    print("   The printer's usable build volume is unknown (docs/13 Q26) and nothing here guesses")
    print("   it. split_sensitivity.py shows this panel is 3 to 24 sections across plausible")
    print("   machines. The split PLANE choice is also deferred: docs/13 Q34 decides whether the")
    print("   printer accepts curved splits, and a flat split across this fascia would cross the")
    print("   light bar, which is the one place a visible joint must not land.")

    print("\n9. ORIENTATION — rule applied, value deferred")
    print("   The class-A face is the outer surface and goes up or vertical. The inner face carries")
    print("   any support. Which way up that leaves the light aperture depends on Q32's overhang")
    print("   limit, so the orientation is not fixed here.")

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "P21_REAR_FASCIA_core_PROVISIONAL.stl")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True, global_scale=1000.0)
    print(f"\n10. EXPORT  {path}  ({os.path.getsize(path)//1024} kB)")
    print("    PROVISIONAL in the filename because it is: no flanges, no keys, no mounting, no")
    print("    split. It is the design surface given a wall, which is exactly as far as the chain")
    print("    can honestly go before the two dictionaries above are filled in.")
    return ob, d


main()
