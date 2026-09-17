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
           "P11": +1, "P12": -1, "P15": +1, "P16": -1, "P17": +1, "P18": -1,
           "P28": +1, "P41": -1, "P39": +1, "P40": -1,
           "P19": +1, "P42": -1}

# The right-hand half of each pair. Its interface list and its seams are its partner's, reflected;
# writing them out again would create two places for one answer to drift apart. panel_map returns
# the left id for both sides, so the right member is resolved through here before anything is read.
MIRROR_OF = {"P04": "P03", "P08": "P07", "P10": "P09", "P12": "P11", "P16": "P15",
             "P18": "P17", "P41": "P28", "P40": "P39", "P42": "P19",
             "P14": "P13", "P06": "P05", "P30": "P29",
             "P25": "P24", "P32": "P31"}

_pm = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_map.py"), "__name__": "_pm"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pm)
panel_of, not_panel, NAME_OF, B = _pm["panel_of"], _pm["not_panel"], _pm["NAME_OF"], _pm["B"]
split_on_boundaries = _pm["split_on_boundaries"]

_p21 = {"__file__": os.path.join(REPO, "01_CAD/scripts/pilot_P21.py"), "__name__": "_p21"}
with open(os.path.join(REPO, "01_CAD/scripts/pilot_P21.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main():")[0], _p21)
PROVISIONAL = _p21["PROVISIONAL"]
P21_INTERFACE = _p21["INTERFACE"]

_sk = {"__file__": os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), "__name__": "_sk"}
with open(os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef build(")[0], _sk)
ARCHES = _sk["ARCHES"]

# Per-panel interface lists. Every entry is a measurement on the real car, never a choice here.
INTERFACE_BY_PANEL = {
    # P21 keeps its list where the pilot wrote it; it is imported rather than retyped so the two
    # scripts cannot drift into two different answers about the same panel.
    "P21": P21_INTERFACE,
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
    # The severed corner behind the rear wheel. Shorter list than the sill because it meets less of
    # the car, but every entry is still a measurement on the donor and not a choice here.
    "P39": {
        "floor_pan_outer_edge":      None,  # SCAN: where the underside actually ends behind the wheel
        "rear_wheelarch_liner":      None,  # SCAN: what sits inboard of it
        "exhaust_routing_silencer":  None,  # SCAN: the pipework runs out right behind this corner
        "ride_height_static":        None,  # SCAN: measured, not the published 95 mm nominal
        "corner_mount_points":       None,  # SCAN: nothing to bolt to is known today
    },
    # Stage 03 elements, built 2026-09-17. Their SHAPE is ours on our own surface, which is why they
    # could be built before the scan; everything they have to physically meet is still absent.
    "P24": {
        "front_structure_to_bolt_to":  None,  # SCAN
        "module_heat_path":            None,  # SCAN: a sealed housing round an LED needs air out
        "loom_route_to_the_module":    None,  # SCAN
    },
    "P31": {
        "plenum_position":             None,  # SCAN: where the duct actually has to arrive
        "real_opening_shape":          None,  # SCAN
        "duct_mount_points":           None,  # SCAN
    },
    "P29": {
        "front_structure_to_bolt_to":  None,  # SCAN
        "beam_aim_on_the_real_car":    None,  # SCAN: legality is checked on the car, not here
        "loom_route_to_the_module":    None,  # SCAN
    },
    "P34": {
        "rear_crash_structure":        None,  # SCAN
        "bumper_mount_points":         None,  # SCAN
    },
    "P35": {
        "exhaust_tip_centres":         None,  # SCAN: two central tips, actual centres and diameter
        "exhaust_hanger_positions":    None,  # SCAN
        "heat_gap_to_the_tips":        None,  # SCAN: a composite surround needs a measured gap
    },
    "P36": {
        "plate_lamp_position":         None,  # SCAN / legality: the plate must be lit
        "rear_crash_structure":        None,  # SCAN
    },
    "P13": {
        "intake_opening_shape":      None,  # SCAN: the real aperture the blade stands in
        "duct_route_to_plenum":      None,  # SCAN: where the air actually has to go
        "blade_mount_points":        None,  # SCAN
    },
    "P05": {
        "wheelhouse_liner_clearance": None,  # SCAN: what the slot vents into
        "fender_mount_points":        None,  # SCAN
        "water_path_out_of_the_slot": None,  # SCAN: a vent that fills with water is a bucket
    },
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
    # This pair was written as P07 <-> P22 before the rocker was split. The piece that actually
    # meets the diffuser is the severed corner, not the sill; the sill stops 878 mm short of it at
    # the rear arch and never reaches the fascia station.
    ("P39", "P22"): ("x", B["fascia_front"],
                     "both PROCEED. They meet across the car at the rear fascia station, below the "
                     "rocker line; the station is our own seam, not a donor value, and "
                     "donor_exposure.py measured neither panel to move with one."),
}


def extract(pid):
    # A Stage 03 element is already its own object carrying its part id; there is nothing to cut out
    # of the skin for it, so it is copied rather than mapped.
    s03 = bpy.data.collections.get("STATEV_STAGE03")
    if s03:
        for src in s03.objects:
            if src.get("panel_id") == pid:
                cp = src.copy()
                cp.data = src.data.copy()
                cp.name = f"PILOT_{pid}_{NAME_OF.get(pid, 'PANEL')}"
                bpy.context.scene.collection.objects.link(cp)
                return cp
    side = SIDE_OF.get(pid)
    pid = MIRROR_OF.get(pid, pid)      # the map answers under the left id for both sides
    master = bpy.data.collections["STATEV_MASTER"]
    verts, faces = [], []
    for src in [o for o in master.all_objects if o.type == "MESH" and "VOLUME" in o.name]:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        split_on_boundaries(bm)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            c = src.matrix_world @ f.calc_center_median()
            n = (src.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            ny = -n.y if c.y > 0 else n.y
            if f.calc_area() < 1e-9:
                continue          # zero-area sliver left where a boundary plane grazed flat geometry
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


def mirror_in_place(ob):
    """Reflect the object across Y = 0 and flip the winding so normals still point outward."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for v in bm.verts:
        v.co.y = -v.co.y
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def pieces(ob):
    """The region's disconnected parts, each with its extents. A part that prints in two pieces is
    not one part, and the register is what decides what to do about it -- not this script."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen, groups = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        g, stack = set(), [v]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            g.add(u)
            stack.extend(e.other_vert(u) for e in u.link_edges)
        groups.append(g)
    out = []
    for g in groups:
        w = [ob.matrix_world @ v.co for v in g]
        out.append(dict(
            x=(min(-p.x * 1000 for p in w), max(-p.x * 1000 for p in w)),
            y=(min(p.y * 1000 for p in w), max(p.y * 1000 for p in w)),
            z=(min(p.z * 1000 for p in w), max(p.z * 1000 for p in w)),
            area=sum(f.calc_area() for f in bm.faces if all(v in g for v in f.verts))))
    bm.free()
    return sorted(out, key=lambda d: d["x"][0])


def severed_by(ps):
    """Which opening left the gap between two pieces. Derived from the gap's own position against
    the cutters the build actually uses, so it names a cause or says it cannot."""
    if len(ps) != 2:
        return None
    for ax, lbl in (("x", "spec X"), ("y", "Y"), ("z", "Z")):
        a, b = sorted((ps[0][ax], ps[1][ax]))
        if a[1] >= b[0]:
            continue
        lo, hi = a[1], b[0]
        for key, (cx, radius, _ow, tod, _tw) in ARCHES.items():
            if ax == "x" and cx - radius <= lo and hi <= cx + radius and tod / 2 - radius < 0:
                return (f"the {key.lower()} wheel opening. Its centre is Z {tod/2:.1f} with radius "
                        f"{radius}, so the cut reaches {tod/2 - radius:.1f} and passes below ground "
                        f"-- it severs the region rather than notching it")
        if ax == "y" and lo < 0 < hi:
            return ("the nose mouth, which is cut on the centreline and reaches down into this "
                    f"region: the gap runs Y {lo:.0f} to {hi:.0f}")
        return f"a gap in {lbl} from {lo:.0f} to {hi:.0f}; the cause is not identified here"
    return None


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


def seam_between(a, b, axis, plane, tol=8.0, side=None):
    """The shared edge of two panels: the vertices both carry on their common boundary plane.
    Derivable only where both panels are PROCEED; returns its extent, never a guessed flange."""
    # A pair member is extracted on the side being reported; a centre panel has no side.
    oa = extract(a if side is None or SIDE_OF.get(a) is None else
                 next((k for k, v in MIRROR_OF.items() if v == a and SIDE_OF[k] == side), a))
    ob_ = extract(b if side is None or SIDE_OF.get(b) is None else
                  next((k for k, v in MIRROR_OF.items() if v == b and SIDE_OF[k] == side), b))
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
    twin = MIRROR_OF.get(pid)
    iface = INTERFACE_BY_PANEL.get(twin or pid)
    if iface is None:
        print(f"no interface list for {pid} — add one before running the chain on it")
        return
    print("=" * 104)
    print(f"PILOT CHAIN — {pid} {NAME_OF.get(pid,'')}.  Validating, not producing.")
    print("=" * 104)
    if twin:
        print(f"   right-hand half of the {twin}/{pid} pair. Its interface list and its seams are")
        print(f"   {twin}'s, read through MIRROR_OF rather than written out a second time.")
    if not prove_separation(pid, iface):
        print("   stopping: the chain's core claim does not hold for this panel")
        return

    if twin:
        # The right-hand half is BUILT as the mirror of the left, not extracted on its own.
        #
        # The car is mirror-symmetric by construction -- every locked dimension is symmetric about
        # Y = 0 and the master volumes are lofted from half sections -- so the two halves of a pair
        # are the same part reflected, and building them separately can only introduce differences
        # that should not exist. It does: extracted independently, eight of the nine pairs agree on
        # area to within 0.4%, and P28/P41 disagrees by 30%. The splitter's boundary is a Z line at
        # 300, the map assigns by face centre, and the nose-mouth boolean tessellated the two sides
        # differently, so coarse faces straddling that line fall on one side here and the other
        # side there. Two parts that differ by 30% are not a pair and will not fit as one.
        #
        # The independent extraction is still made and compared, so the symmetry is asserted out
        # loud rather than assumed silently. If the design ever becomes deliberately asymmetric,
        # this is where it will show up.
        ob = mirror_in_place(extract(twin))
        chk = extract(pid)
        if chk is not None:
            bm = bmesh.new(); bm.from_mesh(ob.data)
            a_m = sum(f.calc_area() for f in bm.faces); bm.free()
            bm = bmesh.new(); bm.from_mesh(chk.data)
            a_d = sum(f.calc_area() for f in bm.faces); bm.free()
            bpy.data.objects.remove(chk, do_unlink=True)
            d = (a_d - a_m) / a_m * 100 if a_m else 0.0
            note = "agrees" if abs(d) < 1.0 else "DISAGREES -- the mirror is what is exported"
            print(f"\n   mirror of {twin}: {a_m:.3f} m2.  Extracted independently: {a_d:.3f} m2, "
                  f"{d:+.1f}%.  {note}")
    else:
        ob = extract(pid)
    ob.name = f"PILOT_{pid}_{NAME_OF.get(pid, 'PANEL')}"
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    sx = [-v.x * 1000 for v in vs]
    y = [v.y * 1000 for v in vs]
    z = [v.z * 1000 for v in vs]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    area = sum(f.calc_area() for f in bm.faces); bm.free()
    ps = pieces(ob)
    n_shell = len(ps)
    print("\n1. DESIGN — measured, ours")
    print(f"   spec X {min(sx):.0f} .. {max(sx):.0f}   width {max(y)-min(y):.1f}   "
          f"Z {min(z):.0f} .. {max(z):.0f}")
    print(f"   outer surface {area:.3f} m2   {len(ob.data.polygons)} faces   "
          f"{n_shell} disconnected piece{'s' if n_shell != 1 else ''}")
    if n_shell != 1:
        print(f"\n   STOP. The register carries {pid} as ONE part and the mapped region is "
              f"{n_shell} separate")
        print("   pieces, so what the map calls one part would print as several and bolt on as")
        print("   several.")
        for i, d in enumerate(ps, 1):
            print(f"      piece {i}: specX {d['x'][0]:.0f}..{d['x'][1]:.0f}   "
                  f"Y {d['y'][0]:.0f}..{d['y'][1]:.0f}   Z {d['z'][0]:.0f}..{d['z'][1]:.0f}   "
                  f"{d['area']:.3f} m2")
        cause = severed_by(ps)
        if cause:
            print(f"      severed by {cause}")
        print("   Which of these is the answer is a register decision and not one this script may")
        print("   take:")
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
        if pid not in (a, b) and (twin or pid) not in (a, b):
            continue
        touched = True
        # On the right-hand half the seam is looked up under the left ids and reported as the
        # same line: the boundary plane is shared, the run of points is the mirror of the left's.
        s = seam_between(a, b, axis, plane, side=SIDE_OF.get(pid))
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

    # Bounding box of the DESIGN surface, kept before the wall goes on. A core is the surface plus
    # a few millimetres; anything that escapes this box by more than the wall is not a core.
    box0 = (min(sx), max(sx), min(y), max(y), min(z), max(z))

    wall = PROVISIONAL["core_wall_mm"][0]
    m = ob.modifiers.new("core", "SOLIDIFY")
    # Offset along the normal, NOT even offset. Even offset divides by the cosine of the half-angle
    # at each vertex, so where a surface folds back on itself that cosine goes to zero and the
    # offset goes to infinity. P01 has six vertices with near-opposite adjacent normals, left by the
    # nose-mouth boolean, and its first exported core carried a vertex at spec X 41159, Y 9074 -- a
    # 41 metre spike in a 4.4 metre car, in a file that was otherwise valid and passed a
    # single-shell check.
    #
    # thickness_clamp does not help: measured on P01 it leaves the spike exactly where it is at
    # every setting and destroys the wall instead, 2595 cm3 falling to 934 at clamp 1.0 against an
    # ideal 2685. Normal offset gives a core whose bounding box is the design surface's own, spec X
    # -951..-654 against -950..-655, and 2413 cm3 -- about 10% under ideal, which is the expected
    # shortfall of measuring along the normal rather than perpendicular through a curve.
    #
    # For this process that is also the right wall. The print IS the core and the glass goes over
    # its outer face, so the outer surface must be exact and the inner face is what gives.
    m.thickness, m.offset, m.use_even_offset = wall / 1000.0, -1.0, False
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    vol = abs(bm.calc_volume(signed=True)) * 1e9; bm.free()
    mass = vol / 1000.0 * PROVISIONAL["density_g_cm3"][0] / 1000.0
    print(f"\n4. SOLID at the provisional {wall} mm wall")
    print(f"   {vol/1000.0:.0f} cm3   ~{mass:.2f} kg   {len(ob.data.polygons)} faces")

    # The gate. A clamp is a parameter and can be wrong; this is the guarantee.
    w2 = [ob.matrix_world @ v.co for v in ob.data.vertices]
    box1 = (min(-v.x * 1000 for v in w2), max(-v.x * 1000 for v in w2),
            min(v.y * 1000 for v in w2), max(v.y * 1000 for v in w2),
            min(v.z * 1000 for v in w2), max(v.z * 1000 for v in w2))
    slack = wall * 2.0 + 1.0
    esc = [(n, a, b) for n, a, b in
           (("specX min", box0[0], box1[0]), ("specX max", box0[1], box1[1]),
            ("Y min", box0[2], box1[2]), ("Y max", box0[3], box1[3]),
            ("Z min", box0[4], box1[4]), ("Z max", box0[5], box1[5]))
           if abs(b - a) > slack]
    if esc:
        print(f"\n   STOP. The core escapes the design surface by more than the {slack:.0f} mm a "
              f"{wall} mm wall can explain:")
        for n, a, b in esc:
            print(f"      {n:<10} design {a:>10.1f}   core {b:>10.1f}   out by {abs(b-a):>9.1f} mm")
        print("   That is a solidify artefact, not a panel. No STL is written.")
        return

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
