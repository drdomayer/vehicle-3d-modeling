"""
pilot_panel.py — the chain validated on P21, made reusable and run on one panel at a time.

Same discipline, generalised. Three kinds of number stay apart: DESIGN measured off v020, INTERFACE
what the real car must tell us, SUPPLIER what the printer and shop must tell us. The separation is
proved by test on every run rather than claimed once. Nothing is invented; a value that cannot be
derived is None and names what would fill it.

One thing this adds beyond P21. Where two PROCEED panels meet, the seam LINE between them is
derivable today — both surfaces exist and neither moves with the scan — even though the flange
WIDTH is a supplier answer. So the chain now produces a real shared seam for such a pair, which is
the first panel-to-panel interface in this project that rests on nothing unknown.

    import bpy
    PANEL = "P22"; exec(open(".../pilot_panel.py").read())
"""

import bmesh
import bpy
import hashlib
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
PANEL = globals().get("PANEL", "P22")

# panel_map keys on |Y|, so a mirrored region answers for both sides of the car and extract() returns
# the pair as one object. P21, P22, P01 and P28 are centre panels and unaffected, which is why this
# never surfaced before P07. The repo convention is +Y left, so the side is a fact, not a choice.
SIDE_OF = {"P03": +1, "P04": -1, "P07": +1, "P08": -1, "P09": +1, "P10": -1,
           "P11": +1, "P12": -1, "P15": +1, "P16": -1, "P17": +1, "P18": -1}

_pm = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_map.py"), "__name__": "_pm"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pm)
panel_of, not_panel, NAME_OF, B = _pm["panel_of"], _pm["not_panel"], _pm["NAME_OF"], _pm["B"]

_p21 = {"__file__": os.path.join(REPO, "01_CAD/scripts/pilot_P21.py"), "__name__": "_p21"}
with open(os.path.join(REPO, "01_CAD/scripts/pilot_P21.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main():")[0], _p21)
PROVISIONAL = _p21["PROVISIONAL"]

# Per-panel interface lists. Every entry is a measurement on the real car, never a choice here.
INTERFACE_BY_PANEL = {
    "P22": {
        "ride_height_at_rear":       None,  # SCAN: measured, not the published 95 mm nominal
        "underbody_floor_surface":   None,  # SCAN: what the diffuser's top edge meets
        "rear_subframe_clearance":   None,  # SCAN: what it must not foul
        "exhaust_routing_silencer":  None,  # SCAN: where the pipework actually runs
        "lowest_safe_fin_z":         None,  # SCAN: how low before it is first to ground out
        "diffuser_mount_points":     None,  # SCAN: nothing to bolt to is known today
    },
    "P01": {
        "crash_beam_position":       None,  # SCAN
        "bumper_mount_points":       None,  # SCAN
        "radiator_front_face":       None,  # SCAN
        "ride_height_at_front":      None,  # SCAN
    },
    "P28": {
        "ride_height_at_front":      None,  # SCAN
        "lowest_safe_lip_z":         None,  # SCAN
        "fascia_lower_edge":         None,  # derivable once P01 is built, not a donor value
    },
    # The rocker joined PROCEED on 2026-09-16, when donor_exposure.py showed no approx donor value
    # moves its boundary. Its interface list is longer than the others and that is the point: being
    # provable does not make it independent of the car, it makes it independent of the four
    # approximate NUMBERS. Everything it has to physically meet is still a measurement on the donor.
    "P07": {
        "sill_outer_surface":        None,  # SCAN: what the rocker sits on for its whole length
        "jacking_points":            None,  # SCAN: must stay usable, and nothing may foul them
        "floor_pan_outer_edge":      None,  # SCAN: where the underside actually ends
        "door_bottom_edge":          None,  # SCAN: the gap the rocker closes under a shut door
        "ride_height_static":        None,  # SCAN: measured, not the published 95 mm nominal
        "sill_mount_points":         None,  # SCAN: nothing to bolt to is known today
        "exhaust_heat_path":         None,  # SCAN: how close the pipework runs behind it
    },
}

# Pairs where both panels are PROCEED, so the seam LINE can be derived. The Z is the boundary
# panel_map already uses to separate them, not a plane invented here.
# (a, b) -> (axis, plane, why). Axis "z" is a height, axis "x" is a spec-X station. Both kinds of
# boundary already exist in panel_map.B; the seam finder used to assume every seam was horizontal,
# which silently excluded every pair that meets across the car rather than along it.
SEAM_PAIRS = {
    ("P21", "P22"): ("z", B["rocker_top"],
                     "both PROCEED. The boundary is the rocker-line Z in panel_map.B, and neither "
                     "surface moves with the scan, so the seam line is derivable today."),
    ("P01", "P28"): ("z", B["splitter_top"],
                     "both PROCEED. panel_map separates them at the splitter line ahead of the "
                     "nose mouth; both surfaces are ours and neither moves with the scan."),
    ("P07", "P22"): ("x", B["fascia_front"],
                     "both PROCEED as of 2026-09-16. They meet across the car at the rear fascia "
                     "station, below the rocker line; the station is our own seam, not a donor "
                     "value, and donor_exposure.py measured neither panel to move with one."),
}


def extract(pid):
    side = SIDE_OF.get(pid)
    master = bpy.data.collections["STATEV_MASTER"]
    verts, faces = [], []
    for src in [o for o in master.all_objects if o.type == "MESH" and "VOLUME" in o.name]:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            c = src.matrix_world @ f.calc_center_median()
            n = (src.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            ny = -n.y if c.y > 0 else n.y
            if not_panel(sx, ay, z, n.z, ny) or panel_of(sx, ay, z) != pid:
                continue
            if side is not None and c.y * side <= 0:
                continue
            base = len(verts)
            for v in f.verts:
                verts.append(tuple(src.matrix_world @ v.co))
            faces.append(tuple(range(base, base + len(f.verts))))
        bm.free()
    if not faces:
        return None
    me = bpy.data.meshes.new(f"PILOT_{pid}")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(f"PILOT_{pid}_{NAME_OF.get(pid,'PANEL')}", me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob


def shells(ob):
    """How many disconnected pieces the region is in. A part that prints as two pieces is not one
    part, and the register is what decides whether it becomes two -- not this script."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    seen, n = set(), 0
    for v in bm.verts:
        if v in seen:
            continue
        n += 1
        stack = [v]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(e.other_vert(u) for e in u.link_edges)
    bm.free()
    return n


def surface_hash(pid):
    ob = extract(pid)
    if ob is None:
        return None, 0
    pts = sorted((round(v.co.x * 1000, 4), round(v.co.y * 1000, 4), round(v.co.z * 1000, 4))
                 for v in ob.data.vertices)
    h = hashlib.sha256(repr(pts).encode()).hexdigest()
    bpy.data.objects.remove(ob, do_unlink=True)
    return h, len(pts)


def prove_separation(pid, iface):
    before = surface_hash(pid)
    saved = dict(iface)
    for k in iface:
        iface[k] = 999.0
    after = surface_hash(pid)
    iface.update(saved)
    ok = before == after
    print("\nSEPARATION PROOF")
    print(f"   INTERFACE all None  {before[0][:32]}  {before[1]} verts")
    print(f"   INTERFACE all 999   {after[0][:32]}  {after[1]} verts")
    print(f"   {'PASS — nothing in the surface path reads the interface' if ok else 'FAIL'}")
    return ok


def seam_between(a, b, axis, plane, tol=8.0):
    """The shared edge of two panels: the vertices both carry on their common boundary plane.
    Derivable only where both panels are PROCEED; returns its extent, never a guessed flange."""
    oa, ob_ = extract(a), extract(b)
    if oa is None or ob_ is None:
        return None

    def on_plane(ob):
        out = set()
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            sx, y, z = -w.x * 1000, w.y * 1000, w.z * 1000
            if abs((sx if axis == "x" else z) - plane) >= tol:
                continue
            out.add((round(y, 1), round(z if axis == "x" else sx, 1)))
        return out

    shared = sorted(on_plane(oa) & on_plane(ob_))
    for o in (oa, ob_):
        bpy.data.objects.remove(o, do_unlink=True)
    if not shared:
        return None
    ys = [p[0] for p in shared]
    os_ = [p[1] for p in shared]
    return dict(points=len(shared), axis=axis, plane=plane,
                y_min=min(ys), y_max=max(ys), o_min=min(os_), o_max=max(os_),
                o_label="Z" if axis == "x" else "specX")


def main():
    pid = PANEL
    iface = INTERFACE_BY_PANEL.get(pid)
    if iface is None:
        print(f"no interface list for {pid} — add one before running the chain on it")
        return
    print("=" * 104)
    print(f"PILOT CHAIN — {pid} {NAME_OF.get(pid,'')}.  Validating, not producing.")
    print("=" * 104)
    if not prove_separation(pid, iface):
        print("   stopping: the chain's core claim does not hold for this panel")
        return

    ob = extract(pid)
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    sx = [-v.x * 1000 for v in vs]
    y = [v.y * 1000 for v in vs]
    z = [v.z * 1000 for v in vs]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    area = sum(f.calc_area() for f in bm.faces); bm.free()
    n_shell = shells(ob)
    print("\n1. DESIGN — measured, ours")
    print(f"   spec X {min(sx):.0f} .. {max(sx):.0f}   width {max(y)-min(y):.1f}   "
          f"Z {min(z):.0f} .. {max(z):.0f}")
    print(f"   outer surface {area:.3f} m2   {len(ob.data.polygons)} faces   "
          f"{n_shell} disconnected piece{'s' if n_shell != 1 else ''}")
    if n_shell != 1:
        print(f"\n   STOP. The register carries {pid} as ONE part and the mapped region is "
              f"{n_shell} separate")
        print("   pieces. On this panel the wheel openings cut through it, so what the map calls one")
        print("   part would print as several and bolt on as several. Which of these is the answer is")
        print("   a register decision and not one this script may take:")
        print("     - split the register entry, each piece its own part and its own seam, or")
        print("     - move a piece into the neighbouring part it is really a lobe of, or")
        print("     - keep one part and bridge the pieces above the opening, which changes the map.")
        print("   No STL is written for a region that is not a part.")
        return

    print("\n2. INTERFACE — the real car only")
    for k in iface:
        print(f"   {k:<28} None   SCAN REQUIRED")

    print("\n3. SEAMS to neighbours")
    touched = False
    for (a, b), (axis, plane, why) in SEAM_PAIRS.items():
        if pid not in (a, b):
            continue
        touched = True
        s = seam_between(a, b, axis, plane)
        print(f"   {a} <-> {b}: {why}")
        if s:
            print(f"      shared boundary: {s['points']} points at "
                  f"{'specX' if axis == 'x' else 'Z'} {plane:.0f}, "
                  f"Y {s['y_min']:.0f}..{s['y_max']:.0f}, "
                  f"{s['o_label']} {s['o_min']:.0f}..{s['o_max']:.0f}")
            print("      the seam LINE is derived. The flange WIDTH is not: docs/13 Q15.")
        else:
            print("      no shared boundary found at the mapped Z — seam not derivable this way")
    if not touched:
        print("   none: this panel has no neighbour that is also PROCEED, so no seam line can be")
        print("   derived today without leaning on something unmeasured.")

    wall = PROVISIONAL["core_wall_mm"][0]
    m = ob.modifiers.new("core", "SOLIDIFY")
    m.thickness, m.offset, m.use_even_offset = wall / 1000.0, -1.0, True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    vol = abs(bm.calc_volume(signed=True)) * 1e9; bm.free()
    mass = vol / 1000.0 * PROVISIONAL["density_g_cm3"][0] / 1000.0
    print(f"\n4. SOLID at the provisional {wall} mm wall")
    print(f"   {vol/1000.0:.0f} cm3   ~{mass:.2f} kg   {len(ob.data.polygons)} faces")

    print("\n5. STOPS — and what each is waiting for")
    print("   split        build volume unknown, docs/13 Q26")
    print("   orientation  overhang limit unknown, docs/13 Q32")
    print("   flange       width unknown, docs/13 Q15; the LINE is derived above")
    print("   mounting     nothing to bolt to is known; every point is SCAN REQUIRED")

    out = os.path.join(REPO, "03_PRINT", f"pilot_{pid}")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"{pid}_{NAME_OF.get(pid,'PANEL')}_core_PROVISIONAL.stl")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True, global_scale=1000.0)
    print(f"\n6. EXPORT  {path}  ({os.path.getsize(path)//1024} kB)")
    print("   PROVISIONAL: the design surface given a wall. No flanges, keys, mounting or split.")


main()
