"""
panel_production.py — take the proven panels the rest of the way: flange, split, key, orient, export.

Every earlier script in this chain stopped at a `None` and named the docs/13 question behind it. That
was right while the questions were open and it is wrong now, because it stops the work. The owner's
instruction is to take the best decision and correct it on the real car, so the blanks become
DECISIONS: written down in one block, argued for, and each one a single edit away from the supplier's
real answer. The chain re-runs from that block, so a number coming back from the shop costs one line,
not a rebuild.

What a decision is NOT. Nothing here invents a donor dimension. Mounting points are still absent and
still SCAN REQUIRED; the flange bonds our panel to OUR neighbouring panel, which is why it can be
drawn today. Where a value belongs to the printer or the shop it is written as ASSUMED with the
reason it was chosen and the question number that replaces it.

    import bpy; exec(open(".../panel_production.py").read())
"""

import bmesh
import bpy
import csv
import math
import mathutils
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "03_PRINT", "production")

# ----------------------------------------------------------------- THE DECISIONS
# One block. Everything downstream reads it and nothing downstream has its own copy of a number.
D = dict(
    # --- core
    wall_mm=3.0,
    # DECIDED. The print is the core and the glass goes over it, so the wall carries only the
    # lamination, not the part. 3 mm at full perimeters is enough to stay rigid over a 350 mm span
    # and thin enough not to waste filament on 11.5 m2 of car. Replaced by docs/13 Q30.
    density_g_cm3=1.24,
    # ASSUMED. PETG. Only the mass estimate depends on it, and the balance does not.

    # --- joints between OUR panels
    flange_w_mm=30.0,
    # DECIDED. A 30 mm bonded lap is the standard one-off glass joint: enough area for the bond to
    # be stronger than the laminate either side, narrow enough to follow curvature without
    # wrinkling. Replaced by docs/13 Q15.
    bond_line_mm=1.0,
    # DECIDED. The gap the adhesive fills between flange and overlapping panel.
    panel_gap_mm=4.0,
    # DECIDED. The visible gap at a shut line. Replaced by docs/13 Q16.

    # --- the printer
    bed_mm=(350.0, 350.0, 350.0),
    # ASSUMED, and the single most consequential guess here. 350 cubed is the common denominator of
    # the affordable large-format machines a print farm actually owns. split_sensitivity.py already
    # measured what other beds cost: this is the number docs/13 Q26 replaces, and re-running with
    # the real one changes nothing but the section count.
    bed_margin_mm=10.0,
    # DECIDED. Skirt and first-layer margin kept off the usable envelope.

    # --- splitting
    tab_mm=20.0,
    # DECIDED, and it replaces an earlier decision that was simply wrong. The first version located
    # sections on 6 mm dowel. You cannot put a 6 mm dowel through a 3 mm wall. What a thin printed
    # shell can carry is the same joint the panels use on each other: one section runs 20 mm past
    # the cut as a tab, dropped inward by a wall plus the bond line, and the next section lands on
    # it. Self-locating in two axes, no second part to buy, no tolerance stack to jam, and it is
    # the mechanism already proven at the panel seams.

    # --- print orientation
    orient="smallest dimension vertical",
    # DECIDED. Lay each section on its flattest face. For a laminating core the outer surface is
    # what matters and layer lines there are sanded anyway; what must not happen is a tall thin
    # section peeling off the bed. Replaced by docs/13 Q32 if the shop's overhang limit forbids it.
)

# Which panels carry a flange, and where. The rule: THE FLANGE BELONGS TO THE PANEL FITTED FIRST,
# and the panel fitted later lands on it. That is how the car actually goes together -- the first
# panel is bonded with its flange exposed, the next one lands on that flange and its own edge is the
# visible one, which is the edge you can still adjust at fit-up.
#
# So a panel whose neighbour is fitted earlier carries no flange here: its mating flange belongs to
# the neighbour. P28, P41 and P22 are in that position and are correct with bare edges.
#
#   panel: [(axis, plane, into, {neighbours})]
# The neighbour set is not decoration. Without it a strip is taken from anywhere on the car that
# happens to lie within the flange width of that plane -- a Z 300 seam at the nose swept up the
# rocker along the whole length and gave the front fascia a 4368 mm bounding box.
FLANGE_AT = {
    "P01": [("z", 300.0, "below", {"P28"})],     # step 3, before the splitter at step 4
    "P21": [("z", 330.0, "below", {"P22"})],     # step 19, before the diffuser at step 22
    "P39": [("x", 3000.0, "above", {"P22"})],    # step 8, before the diffuser at step 22
}
PANELS = ["P01", "P28", "P41", "P07", "P08", "P39", "P40", "P21", "P22"]
SCHEDULE = []
# P40 reads P39's seam through MIRROR_OF, so it is not listed in FLANGE_AT a second time.

_pm = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_map.py"), "__name__": "_pm"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pm)
panel_of, not_panel, NAME_OF = _pm["panel_of"], _pm["not_panel"], _pm["NAME_OF"]
split_on_boundaries = _pm["split_on_boundaries"]

_pp = {"__file__": os.path.join(REPO, "01_CAD/scripts/pilot_panel.py"), "__name__": "_pp", "PANEL": "P01"}
with open(os.path.join(REPO, "01_CAD/scripts/pilot_panel.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main():")[0], _pp)
SIDE_OF, MIRROR_OF = _pp["SIDE_OF"], _pp["MIRROR_OF"]


def gather(pid):
    """Panel faces, plus the neighbour's faces within the flange width across an own-line seam.
    Returns (verts, faces, flange_vert_indices)."""
    # A right-hand part is gathered on the LEFT and mirrored afterwards, so that a pair is one
    # part reflected rather than two independent extractions. The map answers under the left id.
    base = MIRROR_OF.get(pid, pid)
    side = SIDE_OF.get(base)
    seams = FLANGE_AT.get(base, [])
    verts, faces, flange = [], [], set()
    for src in [o for o in bpy.data.collections["STATEV_MASTER"].all_objects
                if o.type == "MESH" and "VOLUME" in o.name]:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        split_on_boundaries(bm)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            if f.calc_area() < 1e-9:
                continue
            c = src.matrix_world @ f.calc_center_median()
            n = (src.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            ny = -n.y if c.y > 0 else n.y
            if not_panel(sx, ay, z, n.z, ny):
                continue
            if side is not None and c.y * side <= 0:
                continue
            mine = panel_of(sx, ay, z) == base
            is_flange = False
            if not mine:
                who = panel_of(sx, ay, z)
                for axis, plane, into, neigh in seams:
                    if who not in neigh:
                        continue
                    v = sx if axis == "x" else z
                    d = (v - plane) if into == "above" else (plane - v)
                    if 0 < d <= D["flange_w_mm"]:
                        is_flange = True
                        break
                if not is_flange:
                    continue
            b = len(verts)
            for v in f.verts:
                verts.append((src.matrix_world @ v.co).copy())
            idx = tuple(range(b, b + len(f.verts)))
            if is_flange:
                flange.update(idx)
            faces.append(idx)
        bm.free()
    return verts, faces, flange


def build(pid):
    verts, faces, flange = gather(pid)
    if not faces:
        return None
    me = bpy.data.meshes.new(f"PROD_{pid}")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(f"PROD_{pid}_{NAME_OF.get(pid, 'PANEL')}", me)
    bpy.context.scene.collection.objects.link(ob)

    # Drop the flange strip below the outer surface so the panel that lands on it finishes flush.
    # RAMPED, not stepped: a vertex ON the seam plane does not move and the drop reaches full depth
    # at the outer edge of the flange. Dropping the whole strip by a constant tore it off the panel
    # -- the shared edge at the seam separated by 4 mm and remove_doubles could not close it, which
    # is why 56 of 66 sections came out as loose pieces.
    drop = (D["wall_mm"] + D["bond_line_mm"]) / 1000.0
    seams = FLANGE_AT.get(MIRROR_OF.get(pid, pid), [])
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    marked = {i for i in flange if i < len(bm.verts)}
    for i in marked:
        v = bm.verts[i]
        sx, z = -v.co.x * 1000, v.co.z * 1000
        t = 0.0
        for axis, plane, into, _n in seams:
            val = sx if axis == "x" else z
            d = (val - plane) if into == "above" else (plane - val)
            t = max(t, min(1.0, max(0.0, d) / D["flange_w_mm"]))
        v.co -= v.normal * (drop * t)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if pid in MIRROR_OF:
        mirror_in_place(ob)
    return ob, len(marked)


def mirror_in_place(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for v in bm.verts:
        v.co.y = -v.co.y
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def thicken(ob):
    m = ob.modifiers.new("core", "SOLIDIFY")
    m.thickness, m.offset, m.use_even_offset = D["wall_mm"] / 1000.0, -1.0, False
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    return ob


def plan_cuts(ob):
    """A grid of cuts on all three axes at once, from the part's own bounding box.

    The first version cut one axis, then recursed on the result. On a curved shell that does not
    terminate sensibly: a section whose width comes from curvature rather than from the cut is
    still "too big" on that axis, cutting it again yields a zero-width sliver plus the remainder,
    and the diffuser came out as 24 pieces of which twelve were 0 x 380 x 30 fragments. A grid
    planned once from the original box cannot do that -- every cell is smaller than the plate by
    construction, and empty cells simply produce no section.

    The cell is the usable plate less the tab, because a section runs one tab past its own cut."""
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    ext = [(min(p[i] for p in w) * 1000, max(p[i] for p in w) * 1000) for i in range(3)]
    size = [hi - lo for lo, hi in ext]
    cell = [b - 2 * D["bed_margin_mm"] - D["tab_mm"] for b in D["bed_mm"]]
    plan = {}
    for i in range(3):
        n = max(1, math.ceil(size[i] / cell[i]))
        if n > 1:
            step = size[i] / n
            plan[i] = [ext[i][0] + step * k for k in range(1, n)]
    return plan, size, ext


def cut_into_sections(ob, plan, pid):
    """Build the printed sections on the planned grid. A section runs to its cut and then one TAB
    past it, dropped inward by a wall plus the bond line, so the next section lands on that tab."""
    if not plan:
        return [ob]
    edges = {}
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    for i in range(3):
        lo = min(p[i] for p in w) * 1000 - 1.0
        hi = max(p[i] for p in w) * 1000 + 1.0
        edges[i] = [lo] + sorted(plan.get(i, [])) + [hi]

    drop = (D["wall_mm"] + D["bond_line_mm"]) / 1000.0
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # Cut on the grid planes before assigning, for the same reason the panel map cuts on its own
    # boundaries: a face assigned by its centre carries all of itself into one cell, so a large face
    # near a cut pushes that section past the plate. The cells are 320 mm and sections were still
    # coming out over 330 until this line existed.
    for i, planes in plan.items():
        no = [0.0, 0.0, 0.0]
        no[i] = 1.0
        for v in planes:
            co = [0.0, 0.0, 0.0]
            co[i] = v / 1000.0
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            if not geom:
                break
            bmesh.ops.bisect_plane(bm, geom=geom, plane_no=no, plane_co=co,
                                   clear_outer=False, clear_inner=False)
        # and again one tab past each cut, so the tab strip itself ends on a face edge
        for v in planes:
            co = [0.0, 0.0, 0.0]
            co[i] = (v + D["tab_mm"]) / 1000.0
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            if not geom:
                break
            bmesh.ops.bisect_plane(bm, geom=geom, plane_no=no, plane_co=co,
                                   clear_outer=False, clear_inner=False)
    bm.faces.ensure_lookup_table()
    cache = []
    for f in bm.faces:
        if f.calc_area() < 1e-9:
            continue
        c = ob.matrix_world @ f.calc_center_median()
        cache.append(([c.x * 1000, c.y * 1000, c.z * 1000],
                      [(ob.matrix_world @ v.co).copy() for v in f.verts]))
    bm.free()

    out = []
    import itertools
    for cell in itertools.product(*[range(len(edges[i]) - 1) for i in range(3)]):
        verts, faces, tab = [], [], set()
        for cc, vv in cache:
            keep, is_tab = True, False
            for i in range(3):
                lo, hi = edges[i][cell[i]], edges[i][cell[i] + 1]
                if lo <= cc[i] < hi:
                    continue
                if hi < edges[i][-1] and hi <= cc[i] < hi + D["tab_mm"]:
                    is_tab = True
                    continue
                keep = False
                break
            if not keep:
                continue
            b0 = len(verts)
            verts.extend(vv)
            idx = tuple(range(b0, b0 + len(vv)))
            if is_tab:
                tab.update(idx)
            faces.append(idx)
        if len(faces) < 3:
            continue
        name = f"SEC_{pid}_" + "".join(str(c + 1) for c in cell)
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        sec = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(sec)
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.normal_update()
        # Same ramp as the flange, same reason: a vertex on the cut plane must not move, or the tab
        # separates from the section it belongs to.
        for i in tab:
            if i >= len(bm.verts):
                continue
            v = bm.verts[i]
            t = 0.0
            for ax in range(3):
                hi = edges[ax][cell[ax] + 1]
                if hi >= edges[ax][-1]:
                    continue
                dd = v.co[ax] * 1000 - hi
                if dd > 0:
                    t = max(t, min(1.0, dd / D["tab_mm"]))
            v.co -= v.normal * (drop * t)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        # A cell is a box and the panel is a curved shell, so one cell can catch patches that do
        # not touch each other -- the nose wraps, and the front fascia's first cell came out as 29
        # separate pieces in one file. A printed section has to be ONE piece, so each connected
        # component becomes its own section here rather than being shipped in company.
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
        # The geometry is copied out as plain data while the bmesh is still alive; reading a
        # bmesh element after free() is reading freed memory.
        parts = []
        for g in groups:
            fl = [f for f in bm.faces if all(v in g for v in f.verts)]
            a = sum(f.calc_area() for f in fl)
            if a < 0.0005:          # under 5 cm2 of skin is a fragment, not a section
                continue
            ordered = sorted(g, key=lambda v: v.index)
            gi = {v: i for i, v in enumerate(ordered)}
            parts.append((a, [tuple(v.co) for v in ordered],
                          [tuple(gi[v] for v in f.verts) for f in fl]))
        bm.free()
        bpy.data.objects.remove(sec, do_unlink=True)
        bpy.data.meshes.remove(me)
        for pi, (a, pv, pf) in enumerate(sorted(parts, key=lambda t: -t[0]), 1):
            nm = f"{name}_{pi}" if len(parts) > 1 else name
            m2 = bpy.data.meshes.new(nm)
            m2.from_pydata(pv, [], pf)
            m2.update()
            o2 = bpy.data.objects.new(nm, m2)
            bpy.context.scene.collection.objects.link(o2)
            out.append(o2)
    return out


def lay_flat(ob):
    """Rotate the section so its smallest dimension is vertical, and drop it onto Z = 0."""
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    size = [max(p[i] for p in w) - min(p[i] for p in w) for i in range(3)]
    small = size.index(min(size))
    if small == 0:
        ob.rotation_euler = (0.0, math.radians(90), 0.0)
    elif small == 1:
        ob.rotation_euler = (math.radians(90), 0.0, 0.0)
    bpy.context.view_layer.update()
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    ob.location.z -= min(p.z for p in w)
    bpy.context.view_layer.update()
    # Bake the placement into the mesh. Left in the object matrix it survives the export, but the
    # rounding between the two does not: two diffuser offcuts came out sitting 2.9 mm above the
    # plate in their own files, which a slicer would either drop or print on air.
    ob.data.transform(ob.matrix_world)
    ob.matrix_world = mathutils.Matrix.Identity(4)
    ob.data.update()
    return ob


def one_piece(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen, n = set(), 0
    for v in bm.verts:
        if v in seen:
            continue
        n += 1
        st = [v]
        while st:
            u = st.pop()
            if u in seen:
                continue
            seen.add(u)
            st.extend(e.other_vert(u) for e in u.link_edges)
    bm.free()
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 104)
    print("PANEL PRODUCTION — the blanks become decisions, written down and argued for")
    print("=" * 104)
    print("\nTHE DECISIONS")
    for k, v in D.items():
        print(f"   {k:<18} {v}")
    print(f"\n   flange carried by the panel fitted FIRST: {', '.join(sorted(FLANGE_AT))}")
    print("   the later panel lands on it, and its own edge is the one adjustable at fit-up")

    print(f"\n{'part':<7}{'name':<20}{'flange v':>9}{'core cm3':>10}{'kg':>7}"
          f"{'L x W x H mm':>24}{'sections':>10}")
    total_m, total_s = 0.0, 0
    rows = []
    SCHEDULE.clear()
    for pid in PANELS:
        for o in list(bpy.data.objects):
            if o.name.startswith("PROD_"):
                bpy.data.objects.remove(o, do_unlink=True)
        built = build(pid)
        if built is None:
            print(f"{pid:<7}no faces")
            continue
        ob, nf = built
        thicken(ob)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        vol = abs(bm.calc_volume(signed=True)) * 1e9
        bm.free()
        mass = vol / 1000.0 * D["density_g_cm3"] / 1000.0
        plan, size, ext = plan_cuts(ob)
        secs = cut_into_sections(ob, plan, pid)
        made = []
        for j, sec in enumerate(secs, 1):
            thicken(sec)
            lay_flat(sec)
            w = [sec.matrix_world @ v.co for v in sec.data.vertices]
            ss = [(max(p[i] for p in w) - min(p[i] for p in w)) * 1000 for i in range(3)]
            fits = all(ss[i] <= D["bed_mm"][i] - 2 * D["bed_margin_mm"] for i in range(3))
            path = os.path.join(OUT, f"{pid}_{NAME_OF.get(pid,'PANEL')}_s{j:02d}.stl")
            bpy.ops.object.select_all(action="DESELECT")
            sec.select_set(True)
            bpy.context.view_layer.objects.active = sec
            try:
                bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True,
                                      global_scale=1000.0)
            except AttributeError:
                bpy.ops.export_mesh.stl(filepath=path, use_selection=True, global_scale=1000.0)
            made.append((j, ss, fits, path, one_piece(sec)))
        total_m += mass
        total_s += len(made)
        over = [m for m in made if not m[2]]
        split_files = [m for m in made if m[4] > 1]
        for j, ss, fits, path, np_ in made:
            SCHEDULE.append(dict(PANEL=pid, NAME=NAME_OF.get(pid, ""), SECTION=j,
                                 X_MM=round(ss[0], 1), Y_MM=round(ss[1], 1), Z_MM=round(ss[2], 1),
                                 FITS_BED="yes" if fits else "NO",
                                 PIECES_IN_FILE=np_,
                                 FILE=os.path.relpath(path, REPO)))
        note = ""
        if over:
            note += f"   {len(over)} over the bed"
        if split_files:
            note += f"   {len(split_files)} file(s) not a single piece"
        print(f"{pid:<7}{NAME_OF.get(pid,''):<20}{nf:>9}{vol/1000.0:>10.0f}{mass:>7.2f}"
              f"{f'{size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f}':>24}{len(made):>10}{note}")
        rows.append((pid, nf, vol / 1000.0, mass, size, made))
        for o in list(bpy.data.objects):
            if o.name.startswith("SEC_") or o.name.startswith("PROD_"):
                bpy.data.objects.remove(o, do_unlink=True)
    print(f"\n   9 parts   ~{total_m:.1f} kg of core   {total_s} printed sections on a "
          f"{D['bed_mm'][0]:.0f} mm bed")
    bad = [r for r in SCHEDULE if r["FITS_BED"] != "yes" or r["PIECES_IN_FILE"] > 1]
    small = [r for r in SCHEDULE if max(r["X_MM"], r["Y_MM"], r["Z_MM"]) < 60]
    print(f"   {len(SCHEDULE) - len(bad)} of {len(SCHEDULE)} sections are one piece on the plate")
    if bad:
        print(f"   {len(bad)} are not, and they are named in the schedule rather than shipped quietly:")
        for r in bad[:8]:
            print(f"      {r['FILE']}  {r['PIECES_IN_FILE']} piece(s), fits {r['FITS_BED']}")
    print(f"   {len(small)} sections are under 60 mm: printable, fiddly to handle, and acceptable")
    print("   here because each one is bonded in place and then laminated over.")
    sched = os.path.join(REPO, "04_ENGINEERING", "reports", "print_schedule.csv")
    with open(sched, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(SCHEDULE[0]))
        w.writeheader()
        w.writerows(SCHEDULE)
    print(f"\nwrote {sched}")
    return rows


main()
