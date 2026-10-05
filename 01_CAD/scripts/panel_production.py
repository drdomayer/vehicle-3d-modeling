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
import json as _json
import math
import mathutils
import os
import time

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "03_PRINT", "production")
SHAPE_OUT = os.path.join(REPO, "03_PRINT", "shape_only")

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
    split="whole",
    # DECIDED BY THE OWNER on 2026-09-26: "not many small pieces -- real, large, whole panels."
    # One file per part. The 350 mm grid that stood here from 2026-09-16 was an assumption about
    # a print farm's bed, and it produced 425 files of which 73 were flakes under 40 mm and 57
    # under 60; a panel in 20 bonded pieces is a jigsaw, not a panel, and every joint is a place
    # for the shape to go wrong. The grid is kept as split="grid" for the day a shop's bed is
    # known (docs/13 Q26) and smaller than the parts; nothing else about the chain changes.
    bed_mm=(1800.0, 600.0, 1800.0),
    # REFERENCE, not a decision: the Modix BIG-180X class CLAUDE.md names as the eventual own
    # machine. In whole mode it only FLAGS which parts would not fit it, sorted-dimension against
    # sorted-dimension, so the shop can rotate in plane. docs/13 Q26 replaces it.
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
    # The planes are NAMES resolved against panel_map (plane_at), not numbers. v056 moved the
    # splitter line 300 -> 194 and this table kept 300: P01's flange onto P28 was silently gone,
    # because no P28 face lies in 270..300 any more, and every file still read clean.
    "P01": [("z", "splitter_top", "below", {"P28"})],     # step 3, before the splitter at step 4
    "P21": [("z", "diffuser_top_at", "below", {"P22"})],  # step 19, before the diffuser at step 22
    "P39": [("x", "DIFFUSER_FRONT", "above", {"P22"})],    # step 8, before the diffuser at step 22 (v055: 3000 -> 2870, the tunnel start)
}
PANELS = ["P01", "P28", "P41", "P07", "P08", "P39", "P40", "P21", "P22",
          "P05", "P06", "P13", "P14", "P43",
          "P44", "P45", "P46", "P47",   # P17 / P18 are SHAPE ONLY; P48..P53 retired 2026-09-29
          "P54", "P55", "P56", "P57",   # v058: the grilles
          "P58", "P59",                 # v059: the third fin pair
          "P60", "P61", "P62",          # v060: the badge and the splitter end fences
          "P24", "P25", "P31", "P32",
          # 2026-09-21: the tail blade's housings. They were BLOCKED for having no geometry, not
          # for waiting on the car -- docs/14 locks the lamp as a thin wide blade with sharp L
          # ends and the envelopes were in the skeleton all along, enclosed and unopened.
          "P26", "P27"]
# SHAPE ONLY, added 2026-09-21. Six panels whose OUTER FORM is ours and fully defined, and which
# were producing nothing at all because the audit marks them SCAN REQUIRED or CONDITIONAL. The
# audit is right about what it measures and wrong as a production gate, because the three reasons
# are not the same thing:
#
#   P09/P10 DOOR_SKIN and P15/P16 REAR_HAUNCH -- "overlay; its INNER form is the donor's skin".
#       The outer shape is ours. Only the face that sits on the OEM panel needs the car.
#   P03/P04 FRONT_FENDER -- "boundary moves with door_front_x". The shape is ours; what moves is
#       where it is trimmed, by the 15 to 30 mm that blueprint value carries.
#   P17..P20, P42 -- "roof fold envelope, which exists nowhere as data". That is a different kind
#       of unknown: the SHAPE itself is unknown, and building it would be inventing. NOT here.
#
# CLAUDE.md records the decision this implements: "цялата наша форма и панелна архитектура се
# строят сега, а сканът остава като последен fitting/validation етап. Монтажният интерфейс се
# строи ПОСЛЕДЕН и отделно от формата на панела." Withholding these was the pipeline not doing
# what the project had already decided.
#
# They go to their own directory with their own schedule, and they are NOT in the supplier package
# or the "quote this now" list. A shape master for fitting and a part ready to bond are different
# things and mixing them in one folder is how someone bonds the wrong one.
# Trim allowance carried across a DONOR shut line, shape-only tier only. (axis, plane, side the
# neighbour is on, neighbour ids, width). The planes are panel_map.B's, by name, so they cannot
# drift from the panel boundaries. 30 mm covers the +-15..30 mm the blueprint value carries; the
# scan then says where to cut, and the cut is a trim, not a remodel.
TRIM_W_MM = 30.0


def trim_at(base):
    """The allowances for a base panel. A function, because panel_map (and its B) is loaded
    further down this file and a table here would read it before it exists."""
    B = _pm["B"]
    return {
        "P03": [("x", B["door_front"], "above", {"P09"}, TRIM_W_MM)],
        "P09": [("x", B["door_front"], "below", {"P03"}, TRIM_W_MM),
                ("x", B["door_rear"], "above", {"P15"}, TRIM_W_MM)],
        "P15": [("x", B["door_rear"], "below", {"P09"}, TRIM_W_MM)],
    }.get(base, [])

SHAPE_ONLY = {
    "P03": "outer form ours; the inner face is the donor's fender line. Carries a 30 mm TRIM "
           "ALLOWANCE past the door shut line (overlaps P09 by 30 mm): the line moves with "
           "door_front_x by +-15..30 mm and the scan says where to cut.",
    "P04": "mirror of P03, same note",
    "P09": "outer form ours; the inner face is currently just the outer offset by the wall and is "
           "NOT the OEM door skin. Carries a 30 mm TRIM ALLOWANCE past both shut lines (overlaps "
           "P03 and P15). Fit and bond surface come from the scan.",
    "P10": "mirror of P09, same note",
    "P15": "outer form ours; overlay on the welded quarter, inner face provisional as P09. "
           "Carries a 30 mm TRIM ALLOWANCE past the rear shut line (overlaps P09).",
    "P16": "mirror of P15, same note",
    # 2026-09-26: the hood joins the tier. It was PROCEED "on an artefact" and left out of every
    # run: the built surface ends at spec X ~385 where the cabin cutter starts to bite, 35 mm
    # short of the donor cowl at 420. That gap IS the donor's scuttle; where the hood's rear
    # edge really lands is the scan's answer, like the fenders' door line. Outer form ours.
    # 2026-09-28: the side-intake surround joins, on the same footing as the haunch overlay --
    # its outer form is ours, what governs it is the real opening behind it, which is the scan's.
    "P11": "outer form ours (the intake surround, spec X 1780..2300 above the rocker); the real "
           "opening behind it and the duct route are the donor's. Fit and bond surface come from "
           "the scan, as for P15.",
    "P12": "mirror of P11, same note",
    # 2026-09-29: the buttress blades, standing outboard of the GUESSED roof fold envelope. The
    # rear cannot be judged against the render without them; nothing about them is settled.
    "P17": "SHAPE ONLY in the strongest sense: a 40 mm sail at Y 685..725 on the quarter top, "
           "outboard of a roof fold envelope that is itself a guess (06_ROOF, PROVISIONAL). Its "
           "foot, the deck between the blades and whether it can exist at all wait on scan S2. "
           "Print it to look at the rear, not to bond.",
    "P18": "mirror of P17, same note",
    # 2026-10-02 (v056): THE DECK AND THE ENGINE COVER, on the footing of P17/P18. The assembled
    # car had a hole behind the hoops -- the surface exists in the body (Z 920..1020) but no file
    # carried it, because all three are BLOCKED on the roof fold envelope. That reason stands and
    # is written on every one of them; the files exist so the rear can be judged as a whole.
    "P19": "SHAPE ONLY in the strongest sense: the deck from the hoop plane to the fascia, around "
           "the engine cover. Its HEIGHT is the roof question (docs/14, DECK_SPINE BLOCKED): scan S2 "
           "decides whether it stays, moves with the clamshell or drops. Print to look, not to bond.",
    "P42": "mirror of P19, same note",
    "P20": "SHAPE ONLY in the strongest sense: the engine cover with the louvre aperture, spec X "
           "2000..3000, |Y| < 560. Height as P19 (roof); the hinge, the latch and the real engine "
           "lid opening are the donor's. Print to look, not to bond.",
    "P33": "SHAPE ONLY: the louvre crate standing in P20's aperture -- seven transverse slats on "
           "seven longitudinal ribs, tops 8 mm under the cover's skin. Goes with P20.",
    "P02": "outer form ours between the fender crests (|Y| < 380). Rear edge: the file ends at "
           "spec X ~385, 35 mm short of the donor cowl (420) -- no allowance can be carried across "
           "the cabin cut, so the real rear edge, the hinges and the frunk aperture come from "
           "the scan.",
}

# Stage 03 elements are built by stage03_elements.py as closed solids in their own right -- a blade
# already HAS its thickness -- so they skip both the map and the wall and go straight to sectioning.
STAGE03 = {"P05", "P06", "P13", "P14", "P43",
           "P44", "P45", "P46", "P47", "P17", "P18", "P54", "P55", "P56", "P57", "P58", "P59", "P60", "P61", "P62",
           "P24", "P25", "P31", "P32", "P26", "P27", "P33"}
SCHEDULE = []
PLACEMENT = {}   # printed file -> the 4x4 that puts it back on the car
SHAPE_SCHEDULE = []
SHAPE_PLACEMENT = {}
TIER_EXTRA = []   # filled in main() from SHAPE_ONLY
SECT_CACHE = {}   # base panel -> its section meshes, so its mirror reuses them
CRUMB_AREA_MM2 = 600.0   # a fan smaller than ~25 x 25 mm at a pinch is deleted, not detached
MIN_SECTION_MM = 40.0    # below this span a piece is not handleable; a fan this small at a
                         # pinch stays attached rather than becoming a flake
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


def plane_at(plane, ay):
    """A FLANGE_AT plane: a number, a key of panel_map.B, or a panel_map function of |Y|."""
    if isinstance(plane, str):
        v = _pm[plane] if plane in _pm else _pm["B"][plane]
        return v(ay) if callable(v) else v
    return plane


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
            tag = not_panel(sx, ay, z, n.z, ny)
            # X_LOUVRE (v056): the aperture's WALLS print with the cover, as every pocket's do, but
            # not its floor -- the louvres vent into the engine bay; a floor would make a tray
            wall_only = tag == "X_LOUVRE" and abs(n.z) > 0.5
            if tag and not (tag in ("X_INTAKE", "X_FENDER_SLOT", "X_MOUTH", "X_ROCKER_CHANNEL", "X_CORNER", "X_LIP", "X_TAIL_CORNER", "X_LOUVRE", "X_BADGE")
                            and not wall_only and panel_of(sx, ay, z) == base):
                # a pocket's walls are PRINTED with the panel the pocket is cut into: they are
                # its recess, even though the skin accounting rightly does not count them as
                # exterior. Without this the fender file had a hole where the vent slot is.
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
                    pl = plane_at(plane, ay)
                    d = (v - pl) if into == "above" else (pl - v)
                    if 0 < d <= D["flange_w_mm"]:
                        is_flange = True
                        break
                if not is_flange:
                    # TRIM ALLOWANCE across a DONOR line, for the shape-only tier. A flange is
                    # carried across a seam that is ours; a donor shut line is not ours and until
                    # 2026-09-26 nothing was carried across it -- so a fender core ended exactly on
                    # a line the blueprint places to +-15..30 mm, with no material to trim to the
                    # real one. The allowance is the neighbour's surface within TRIM_W past the
                    # plane, NOT ramped like a flange: it is skin at full height, cut off on the
                    # car. Consequence, stated in the schedule: shape-only neighbours overlap each
                    # other by TRIM_W at every donor shut line.
                    for axis, plane, into, neigh, w in trim_at(base):
                        if who not in neigh:
                            continue
                        v = sx if axis == "x" else z
                        d = (v - plane) if into == "above" else (plane - v)
                        if 0 < d <= w:
                            is_flange = None      # taken, but not a flange: no ramp
                            break
                    if is_flange is not True and is_flange is not None:
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
    if pid in STAGE03:
        s03 = bpy.data.collections.get("STATEV_STAGE03")
        for src in (s03.objects if s03 else []):
            if src.get("panel_id") == pid:
                cp = src.copy()
                cp.data = src.data.copy()
                cp.name = f"PROD_{pid}_{NAME_OF.get(pid, 'PANEL')}"
                # a copy inherits the source's visibility, and the STL exporter skips an object
                # hidden from render while still reporting success: nine Stage-03 files were
                # written EMPTY on 2026-10-02 that way. The production copy is always visible.
                cp.hide_render = False
                cp.hide_viewport = False
                cp.hide_set(False)
                bpy.context.scene.collection.objects.link(cp)
                return cp, 0
        return None
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
            pl = plane_at(plane, abs(v.co.y * 1000))
            d = (val - pl) if into == "above" else (pl - val)
            t = max(t, min(1.0, max(0.0, d) / D["flange_w_mm"]))
        v.co -= v.normal * (drop * t)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    # A PANEL IS ONE CONNECTED SURFACE. Measured on 2026-09-26 when the grid went away and every
    # part became one file: P21 came out as 23 files, and 22 of them were single triangles at the
    # undercut seam, 5 to 4600 mm2 each, Z 300..320 -- the region rule hands the boundary slivers
    # of a bisected face to this panel while everything they touch belongs to the neighbour. P03
    # carried two lone loft faces of 2 x 10^4 mm2 at the fender slot. None of these is a part; a
    # print farm would print them and nobody could say where they go. Anything not connected to
    # the main surface and under a tenth of its area is residue: dropped here and COUNTED, so the
    # schedule says how much skin is missing from the core rather than shipping it as parts.
    comps = []
    seen = set()
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, fs = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            fs.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        comps.append(fs)
    comps.sort(key=lambda fs: -sum(f.calc_area() for f in fs))
    dropped_n, dropped_mm2 = 0, 0.0
    if len(comps) > 1:
        main_a = sum(f.calc_area() for f in comps[0])
        gone = []
        for fs in comps[1:]:
            a = sum(f.calc_area() for f in fs)
            if a < 0.10 * main_a:
                gone += fs
                dropped_n += 1
                dropped_mm2 += a * 1e6
        if gone:
            bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob["dropped_islands"] = dropped_n
    ob["dropped_mm2"] = round(dropped_mm2)
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


def face_outward(ob):
    """Make the shell's normals consistent and point them OUT of the car, before any solidify.

    Solidify with offset -1 builds the wall on the side AWAY from the normal, so a face that points
    inward builds its wall outward -- into the air the panel is supposed to end at. Measured on
    2026-09-21: 5 to 15 percent of the faces of every extracted panel pointed the wrong way (P01
    84.9% outward, P21 90.1, P15 93.2, P03 94.7), and the consequence showed up in the reassembled
    car as a half-width of 928.5 mm against the LOCKED 925 at the front fender. Three and a half
    millimetres of core, plus laminate and filler on top of it, outside a dimension that is not
    allowed to move.

    The region is an open shell, so consistency alone does not say which way is out; the mean dot
    with the outward radial direction does, and the whole shell is flipped on it if needed."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # A CLOSED mesh answers this exactly and the radial guess must not be asked. The signed volume
    # of a closed surface is positive when its normals face out, full stop. The radial version is a
    # heuristic for open shells -- "away from the body's axis" -- and on 2026-09-21 it flipped two
    # already-solid stage 03 pieces, P13 and P14's second loose part, which then went through
    # solidify inverted and exported with a volume of -700.9 cm3. A slicer would print the
    # complement of that part.
    closed = not any(len(e.link_faces) == 1 for e in bm.edges)
    if closed:
        flip = bm.calc_volume(signed=True) < 0.0
    else:
        acc = 0.0
        for f in bm.faces:
            c = f.calc_center_median()
            r = mathutils.Vector((0.0, c.y, c.z - 0.570))
            if r.length < 1e-6:
                continue
            acc += f.normal.normalized().dot(r.normalized()) * f.calc_area()
        flip = acc < 0.0
    if flip:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def cap_cuts(ob):
    """Close the faces the grid cut opened, WITHOUT adding material.

    The panel is already a closed 3 mm core before it is cut; a section of it is open only where
    the cut planes passed. Until 2026-09-21 that was closed by running solidify a SECOND time on
    every section, and it worked in the sense that the section came out watertight -- but a second
    solidify does not know it is being asked to cap a hole, so it built another wall, and on the
    outer surface it built it OUTWARD. Traced on P15: the extracted surface and the walled panel
    both sit exactly on the locked half-width of 925.00; the section before the second pass reads
    925.21, and after it 928.14. Three and a half millimetres of core outside a dimension that is
    not allowed to move, with laminate and filler still to go on top.

    Filling the boundary loops does the one thing that was wanted and nothing else."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    holes = [e for e in bm.edges if len(e.link_faces) == 1]
    if holes:
        bmesh.ops.holes_fill(bm, edges=holes, sides=0)
        still = [e for e in bm.edges if len(e.link_faces) == 1]
        if still:
            # a loop holes_fill would not take; triangulating its edge net closes it
            bmesh.ops.triangle_fill(bm, use_beauty=True, edges=still)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def split_pinch(ob):
    """Separate the shell where its own boundary pinches to a single vertex.

    Traced on 2026-09-21, and the correspondence is exact: the number of vertices where more than
    two boundary edges meet equals the number of non-manifold edges the wall then produces. P01 has
    2 and 2, P21 has 9 and 9, P07, P22 and P28 have 0 and 0. A panel region extracted from the body
    can touch itself at a point; solidify runs its rim through that point twice and the result is an
    edge with four faces on it, which no slicer handles predictably.

    Splitting it is not a workaround, it is the honest shape: two areas joined at a single point
    cannot be printed as one part and would fall apart if they were. The pipeline already exports
    each loose piece of a section separately, so they come out as the two parts they are."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    split = 0
    for v in list(bm.verts):
        # deleting a crumb fan can remove vertices this loop has not reached yet
        if not v.is_valid:
            continue
        # Every vertex is tested for more than one fan. The first version only looked at vertices
        # with more than two BOUNDARY edges, and that misses the bowtie where one of the two fans
        # is wholly interior at the vertex -- two boundary edges, two fans. Measured on P21 on
        # 2026-09-26: 21 flakes survived the crumb rule, all of them single faces solidify had cut
        # loose at exactly such vertices. Counting fans is the test; the boundary count was a proxy.
        if len(v.link_faces) < 2:
            continue
        # group this vertex's faces into fans, walking only through interior edges
        faces = list(v.link_faces)
        fans, seen = [], set()
        for f in faces:
            if f in seen:
                continue
            fan, stack = [], [f]
            while stack:
                g = stack.pop()
                if g in seen:
                    continue
                seen.add(g)
                fan.append(g)
                for e in g.edges:
                    if v not in e.verts or len(e.link_faces) != 2:
                        continue
                    for h in e.link_faces:
                        if h is not g and h not in seen:
                            stack.append(h)
            fans.append(fan)
        if len(fans) < 2:
            continue
        # A tiny fan is not a part, it is a crumb. Splitting it off makes it a separate loose
        # piece, and solidify then turns a one- or two-face crumb into a 6-to-10-vertex prism a
        # few millimetres across. Measured on P21 on 2026-09-26: with this split in place the panel
        # produced 118 parts of which 45 were under 40 mm; with it disabled, 65 parts and 3 -- but
        # 78 non-manifold edges instead of 8. The 149 flakes across the whole set were THIS, not the
        # grid, and the note on cut_into_sections that blamed the grid was wrong about the cause.
        # A fan below CRUMB_AREA_MM2 is deleted instead of detached: what is left is a notch in the
        # shell edge a few millimetres wide, which the laminate never sees.
        fans.sort(key=lambda fn: -sum(g.calc_area() for g in fn))
        for fan in fans[1:]:
            area = sum(g.calc_area() for g in fan) * 1e6
            if area < CRUMB_AREA_MM2:
                bmesh.ops.delete(bm, geom=[g for g in fan if g.is_valid], context="FACES")
                split += 1
                continue
            # SMALL BUT REAL: one or two faces of a 38 mm mesh, 27 to 40 mm across. Detached they
            # become flakes nobody can handle; deleted they leave a notch that wide in the panel's
            # own edge, which is geometry lost. So they stay ATTACHED and the vertex stays a pinch:
            # one non-manifold edge, which print_qc reports and most slicers repair. Measured on
            # P21 on 2026-09-26, this is the whole of the 23 flakes that survived the crumb rule.
            pts = [x.co for g in fan for x in g.verts]
            fspan = max(max(c[i] for c in pts) - min(c[i] for c in pts) for i in range(3)) * 1000.0
            # ...in GRID mode. In WHOLE mode (2026-09-28) the fan is detached regardless: the
            # loose-piece crumb rule then drops it (under 2% of the part and under 5000 mm2) and
            # COUNTS it in DROPPED_MM2, so the notch is on record and the file is manifold. A
            # pinch kept for the sake of 30 mm of skin cost P21 31 non-manifold edges.
            if fspan < MIN_SECTION_MM and D["split"] != "whole":
                continue
            nv = bm.verts.new(v.co)
            for g in fan:
                vs = [nv if x is v else x for x in g.verts]
                try:
                    nf = bm.faces.new(vs)
                    nf.normal_update()
                except ValueError:
                    continue
            bmesh.ops.delete(bm, geom=fan, context="FACES")
            split += 1
        bm.verts.ensure_lookup_table()
    if split:
        bm.normal_update()
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return split


SMOOTH_LEVELS = 2       # Catmull-Clark levels on the printed surface; 0 switches it off
SMOOTH_CREASE_DEG = 25  # a dihedral this hard is a designed edge and is creased, not rounded


def smooth_for_print(ob):
    """Subdivide the panel's SURFACE so the print is smooth where the design is smooth.

    Measured 2026-09-29 on v043: the median dihedral between neighbouring faces of the skin above
    Z 400 is 3.7-5.9 degrees, with ring spacing of ~38 mm. A core printed from that carries a
    visible facet every 38 mm, 1-4 mm of sagitta on the tighter radii, and the laminate follows
    the core. The loft's resolution is a measurement choice (every metric this repo keeps is read
    off that mesh), so it stays; the PRINT is subdivided instead, here, per panel, before the wall
    goes on. Edges harder than SMOOTH_CREASE_DEG -- the lip, the crest, the shelf, every pocket
    wall -- are creased so the designed breaks stay breaks; the panel's outline is kept
    (PRESERVE_CORNERS), so seams still meet. assembly_check measures the result against the
    un-subdivided master: the limit surface sits inside the facets by the sagitta, ~1 mm."""
    if SMOOTH_LEVELS <= 0:
        return 0
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # v057: a boolean leaves a CONCAVE n-gon around every opening (the face that held the hole,
    # bridged to it). Catmull-Clark puts a new vertex at the n-gon's centroid, and for a ring-like
    # n-gon that centroid lies INSIDE the hole: measured on P22, the two 104 mm exhaust openings
    # came out of the print file with vertices at r 38..44 -- irregular polygons ~80 mm across,
    # partly skinned over. Triangulated first, every new vertex lies on the face it came from.
    # CONCAVE n-gons only. Measured three ways on v057: every n-gon over 6 sides fixed the
    # exhausts (r 51.9 against 52) but put spikes 0.4..2.1 m long into P01 at the lamp slot corner
    # (-750, 700, 558) -- thin triangles out of a CONVEX n-gon there, which the wall then throws
    # out; dissolving degenerate triangles afterwards changed nothing. Only the n-gons whose
    # centroid lies outside them kept P01 closed but left the exhausts at r 43.8. Catmull-Clark
    # is well defined on a convex face, so a convex n-gon stays as it is.
    def concave(f):
        n = f.normal
        vs = [v.co for v in f.verts]
        k = len(vs)
        for i in range(k):
            a_, b_, c_ = vs[i - 1], vs[i], vs[(i + 1) % k]
            if (b_ - a_).cross(c_ - b_).dot(n) < -1e-12:
                return True
        return False
    def chord_exists(f):
        # Two NON-adjacent corners of the n-gon already joined by an edge of another face: a
        # triangulation that picks that diagonal reuses the edge and gives it a third face.
        # That is what broke P01 (8 edges with three faces at the lamp slot n-gons, 42/48
        # sides, after smoothing; 0 before) and the wall then threw spikes 0.4..2.1 m long.
        vs = list(f.verts)
        k = len(vs)
        for i in range(k):
            for j in range(i + 2, k - (1 if i == 0 else 0)):
                if bm.edges.get((vs[i], vs[j])) is not None:
                    return True
        return False
    big = [f for f in bm.faces if len(f.verts) > 6 and concave(f) and not chord_exists(f)]
    if big:
        bmesh.ops.triangulate(bm, faces=big, quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.normal_update()
    layer = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    creased = 0
    for e in bm.edges:
        if len(e.link_faces) == 2:
            try:
                hard = math.degrees(e.calc_face_angle()) >= SMOOTH_CREASE_DEG
            except ValueError:
                hard = False
        else:
            hard = True    # boundary: the seam, kept as drawn
        e[layer] = 1.0 if hard else 0.0
        creased += hard
    bm.to_mesh(ob.data)
    bm.free()
    m = ob.modifiers.new("smooth", "SUBSURF")
    m.subdivision_type = "CATMULL_CLARK"
    m.levels = m.render_levels = SMOOTH_LEVELS
    m.use_creases = True
    m.boundary_smooth = "PRESERVE_CORNERS"
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    return creased


def thicken(ob):
    split_pinch(ob)
    smooth_for_print(ob)
    face_outward(ob)
    m = ob.modifiers.new("core", "SOLIDIFY")
    m.thickness, m.offset, m.use_even_offset = D["wall_mm"] / 1000.0, -1.0, False
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    # THE LOCKED HALF-WIDTH IS A WALL, 2026-09-30. Solidify offsets each vertex along its own
    # normal, and on the lip where a pocket's ceiling meets the skin at a right angle the vertex
    # normal is the average of the two -- so the wall vertex at that lip moves half outward. P11's
    # second piece (the intake mouth's walls) carried eleven such vertices at Y 927.8 on the lip at
    # Z 700, and the assembled car read 1855.6 wide against the locked 1850. Nothing the shop
    # prints may stand outside +-925: those vertices are set back onto the plane, at most 3 mm,
    # counted and printed. The cut edge itself is where the panel meets its neighbour, and the
    # laminate bridges it.
    lim = 925.0 / 1000.0
    M, Mi = ob.matrix_world, ob.matrix_world.inverted()
    n_clamped, worst = 0, 0.0
    for v in ob.data.vertices:
        w = M @ v.co
        if abs(w.y) > lim:
            worst = max(worst, (abs(w.y) - lim) * 1000.0)
            w.y = lim if w.y > 0 else -lim
            v.co = Mi @ w
            n_clamped += 1
    if n_clamped and worst > 0.05:   # float noise at exactly 925 is not worth a line
        print(f"    {ob.name}: {n_clamped} wall vertices stood up to {worst:.1f} mm outside the "
              f"locked half-width and were set back onto +-925")
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
    if D["split"] == "whole":
        # WHOLE, BUT NOT LARGER THAN THE PLATE (2026-09-29). A part that cannot fit the reference
        # bed in any orientation is split along X into the fewest equal pieces whose sorted
        # dimensions fit the sorted usable bed -- the fender (829 tall, taller than the bed is
        # deep) becomes two of 578 x 925 x 829, the rocker (1831) two of 916. Everything else
        # stays one file. The tab joint is the one every section used to carry.
        usable = sorted(b - 2 * D["bed_margin_mm"] for b in D["bed_mm"])
        # no wall term: the wall goes INWARD (offset -1), so the outer surface's box is the
        # part's box. With +2 walls the fender needed 3 cuts and came out in 7 pieces, and the
        # haunch (579 tall against 580 usable) was split for 6 mm it never occupied.
        # The axis is chosen too: cutting the fender along X never made its smallest dimension
        # (the 833 height) smaller until the slices were under 580 long -- three cuts, seven
        # pieces once the arch opening split each slice. One cut along Y does it. Fewest pieces
        # wins; on a tie Y (a seam along the top), then X, then Z (a seam across the flank).
        best = None
        for axis in (1, 0, 2):
            for n in range(1, 8):
                piece = list(size)
                piece[axis] = size[axis] / n + (D["tab_mm"] if n > 1 else 0.0)
                if all(a <= b for a, b in zip(sorted(piece), usable)):
                    if best is None or n < best[0]:
                        best = (n, axis)
                    break
        plan = {}
        if best and best[0] > 1:
            n, axis = best
            step = size[axis] / n
            plan[axis] = [ext[axis][0] + step * k for k in range(1, n)]
        return plan, size, ext
    # The cell also has to reserve the WALL. Everything that happens to a section after the grid is
    # planned makes it bigger: it runs one tab past its cut, and then thicken() puts a wall on it,
    # which pushes the bbox out by up to one wall on each side. Without that term P21's section 16
    # came out 333.9 mm against 330 usable and the schedule said FITS_BED=NO — the script asserting
    # an invariant it had not reserved room for. Same family as the two diffuser offcuts that
    # exported 2.9 mm above the plate.
    cell = [b - 2 * D["bed_margin_mm"] - D["tab_mm"] - 2 * D["wall_mm"] for b in D["bed_mm"]]
    plan = {}
    for i in range(3):
        n = max(1, math.ceil(size[i] / cell[i]))
        if n > 1:
            step = size[i] / n
            plan[i] = [ext[i][0] + step * k for k in range(1, n)]
    return plan, size, ext


def cut_into_sections(ob, plan, pid):
    """Build the printed sections on the planned grid. A section runs to its cut and then one TAB
    past it, dropped inward by a wall plus the bond line, so the next section lands on that tab.

    KNOWN AND NOT FIXED: THE GRID MAKES FLAKES. Measured on 2026-09-26 across the whole set, 149 of
    531 sections are under 40 mm in their largest dimension and 68 are under 20. A twelve-millimetre
    flake of a 3 mm wall is not a part -- it cannot be handled, aligned or bonded, and a farm given
    149 of them will lose some. Worst on P21 (45), P01 (18) and P03/P04 (17 each).

    The cause is geometric rather than a bug: a 3D grid laid over a thin curved shell leaves a
    corner fragment in every cell the shell merely clips, and no spacing removes that.

    MERGING SLIVER CELLS WAS TRIED ON 2026-09-26 AND MADE IT WORSE -- 311 sections became 623, and
    440 of those were under 60 mm. The shape of the mistake is worth keeping. Merging has to be done
    as GROUPS of cells rather than by gluing objects together afterwards, because the plane between
    two merged cells stops being a cut, and a tab ramped there would press a groove into the middle
    of a continuous panel. That part was right.

    WHY IT BROKE IS NOT ESTABLISHED, and the first write-up of this note said it was. It blamed the
    tab gather. The more likely mechanism, on reflection, is that a corner flake is usually a
    separate ISLAND of the shell inside its own cell, attached to the rest only across a cut plane
    -- so merging its faces into "the neighbour with the most faces" does nothing to connect them
    unless that neighbour is the one it hangs off, and loose_pieces splits it straight back out,
    now with tab faces from further cells as more loose pieces. A fix would have to merge by
    CONNECTIVITY across the plane, not by grid adjacency. Unverified; the numbers above are the
    only facts.

    The real cure is probably not a 3D grid at all. A shell wants cutting along its own two surface
    directions, not the world's three axes, and that is a larger change than a merge."""
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


def class_a_normal(ob):
    """Area-weighted mean normal of the section's CLASS-A faces, in the car frame.

    The section's mesh is in car coordinates with an identity matrix at this point, so the same
    radial test face_outward() uses -- pointing away from the body's axis at mid height -- picks
    the outer skin, and the inner face of the wall, whose normal points the other way, is left out."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    acc = mathutils.Vector((0.0, 0.0, 0.0))
    for f in bm.faces:
        c = f.calc_center_median()
        r = mathutils.Vector((0.0, c.y, c.z - 0.570))
        if r.length < 1e-6:
            continue
        n = f.normal.normalized()
        if n.dot(r.normalized()) > 0.0:
            acc += n * f.calc_area()
    bm.free()
    return acc


def lay_flat(ob):
    """Rotate the section so its smallest dimension is vertical, put the CLASS-A face UP, and
    drop it onto Z = 0.

    WHICH SIDE UP was never decided until 2026-09-26. lay_flat chose "smallest dimension vertical"
    and left the sign to chance, so roughly half the sections printed with the outer skin face
    down -- on supports for a curved shell, which is the worst surface a printer makes and the one
    that then needs the most filler. overhang_report measured the other half of the cost: 222
    litres of support volume across the ready-to-bond tier as laid, with 43 files that would need
    markedly less turned over. The rule is not "least support"; it is class-A up, because the
    outer face is the one that gets laminated and finished, and a support scar there is paid for
    twice. The support that costs is then a Q32/Q33 conversation with real numbers."""
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    size = [max(p[i] for p in w) - min(p[i] for p in w) for i in range(3)]
    small = size.index(min(size))
    n_a = class_a_normal(ob)
    if small == 0:
        ob.rotation_euler = (0.0, math.radians(90), 0.0)
    elif small == 1:
        ob.rotation_euler = (math.radians(90), 0.0, 0.0)
    bpy.context.view_layer.update()
    if n_a.length > 1e-9:
        up = (ob.matrix_world.to_3x3() @ n_a).z
        if up < 0.0:
            # turn it over about the plate's own X axis, on top of whatever laid it flat
            ob.rotation_euler = (mathutils.Matrix.Rotation(math.pi, 3, "X")
                                 @ ob.matrix_world.to_3x3()).to_euler()
            bpy.context.view_layer.update()
    ob["class_a_up"] = "yes" if n_a.length > 1e-9 else "unknown"
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    ob.location.z -= min(p.z for p in w)
    bpy.context.view_layer.update()
    # Bake the placement into the mesh. Left in the object matrix it survives the export, but the
    # rounding between the two does not: two diffuser offcuts came out sitting 2.9 mm above the
    # plate in their own files, which a slicer would either drop or print on air.
    #
    # RETURN THE MATRIX, added 2026-09-21. Baking it and throwing it away meant the 248 printed
    # files carried no record of where they belong on the car: lay_flat rotates the section onto
    # its flattest face and drops it to Z 0, and after the bake nothing remembers the rotation.
    # Someone bonding these together has to work it out from the shape, and the question the owner
    # actually asks -- does the assembly come out 1:1 with the render -- cannot even be posed,
    # because the parts cannot be put back. The inverse of this matrix returns a printed part to
    # its place in the body.
    m = ob.matrix_world.copy()
    ob.data.transform(m)
    ob.matrix_world = mathutils.Matrix.Identity(4)
    ob.data.update()
    return m


def loose_pieces(ob):
    """Split a section into one object per connected piece.

    WHY. A section is a cell of a 3D grid laid over a thin curved shell, so a cell can legitimately
    contain two separate patches of that shell -- the fascia folds back under its own undercut edge
    and the cell catches both branches. Until 2026-09-18 those were written to ONE .stl and listed as
    a named exception; P21 went from 6 such files to 34 when the undercut edge was sharpened. A file
    holding two disconnected solids is not a part, and naming it does not make it one. They are two
    parts, they print separately and they bond separately, so they get a file each.
    """
    if one_piece(ob) <= 1:
        return [ob]
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    before = set(bpy.data.objects)
    bpy.ops.mesh.separate(type="LOOSE") if False else None
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    out = [ob] + [o for o in bpy.data.objects if o not in before]
    # Drop the empties. separate(LOOSE) can leave an object with no geometry, and those were being
    # exported as 0-triangle STLs: six of them on 2026-09-21, which assembly_check found only
    # because it tried to read them back. A file with no triangles is not a part, and a print farm
    # given one has no way to tell whether something was lost.
    dead = [o for o in out if len(o.data.polygons) == 0]
    for o in dead:
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    out = [o for o in out if o not in dead]
    # Drop the CRUMBS too. split_pinch deletes a fan under CRUMB_AREA_MM2 instead of detaching it,
    # but a pinch that only becomes a separate piece AFTER thicken() never met that rule: on
    # 2026-09-26 P03 s14b was a 12-triangle box 15 x 6 x 15 mm at the top of the fender wall, and
    # because its skin has two faces of nearly equal area face_outward() had no majority to go by,
    # so it was thickened OUTWARD and put the assembled width at 1853.6 against the locked 1850.
    # The same rule as the fan rule, on the same number: half the solid's surface is its skin, and
    # a skin under 25 x 25 mm is not a part.
    skin = {o.name: sum(p.area for p in o.data.polygons) * 1e6 / 2.0 for o in out}
    big = max(skin.values()) if skin else 0.0
    # ...and in whole mode the same judgement at the part's own scale: a detached fan of a few
    # faces beside a 1.5 m2 fascia is not a second part, it is a hole in the core the laminate
    # bridges. Under 2% of the main piece AND under 5000 mm2 it is dropped and its area is counted
    # into the part's DROPPED_MM2, never shipped as a file of its own.
    def sliver(o):
        # a piece whose box is no thicker than the wall itself is a detached strip of skin (the
        # floor of the lip recess came out as 40 x 438 x 3 on 2026-09-29), not a part
        bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        dims = sorted((max(v[i] for v in bb) - min(v[i] for v in bb)) * 1000.0 for i in range(3))
        return dims[0] < D["wall_mm"] + 1.0 and skin[o.name] < 0.10 * big
    crumbs = [o for o in out if o is not ob and (skin[o.name] < CRUMB_AREA_MM2 or
              (D["split"] == "whole" and skin[o.name] < 0.02 * big and skin[o.name] < 5000.0) or
              (D["split"] == "whole" and sliver(o)))]
    for o in crumbs:
        ob["dropped_mm2"] = ob.get("dropped_mm2", 0) + round(skin[o.name])
        ob["dropped_islands"] = ob.get("dropped_islands", 0) + 1
        bpy.data.objects.remove(o, do_unlink=True)
    out = [o for o in out if o not in crumbs]
    if not out:
        return []
    # biggest first, so a section's own numbering runs from its main piece outward
    out.sort(key=lambda o: -len(o.data.vertices))
    return out


FLAP_MAX_MM2 = 25.0


def tidy_for_export(ob):
    """Triangulate ourselves, and drop the triangles the exporter would have doubled.

    Measured 2026-09-28 on P21: the walled mesh in Blender has no duplicate face and only 3 edges
    that merge to more than two faces by position, yet the .stl print_qc reads has 34, and 31 of
    those carry two COINCIDENT triangles. The mesh carries ngons of up to 48 vertices -- boolean
    pocket floors and the wall's rim -- some of them touching themselves at a vertex position, and
    the STL exporter's tessellation of such an ngon lays two identical triangles down. Triangulate
    here with the beauty method, then remove any triangle that is degenerate or a positional
    duplicate of another, so the file is what the mesh is."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # 2026-09-30: P21's file carried one needle -- two vertices 0.0004 mm apart on the tail's
    # undercut lip -- which print_qc read as 2 open edges and 1 non-manifold. Merging vertices
    # closer than 0.001 mm collapses it. The first version also dropped triangles under 0.01 mm2
    # and that OPENED nine files (P01 alone 230 open edges): slivers that small are real
    # connectors along boolean seams, and a slicer copes with them. Area threshold left at the
    # degenerate limit.
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    seen, gone = set(), []
    for f in bm.faces:
        k = frozenset(tuple(round(c * 1e6) for c in v.co) for v in f.verts)
        if len(k) < 3 or f.calc_area() < 1e-12 or k in seen:
            gone.append(f)
        else:
            seen.add(k)
    if gone:
        bmesh.ops.delete(bm, geom=gone, context="FACES_ONLY")
    # FLAPS, 2026-10-02: a lone triangle hinged on an edge of the surface -- that edge carries three
    # faces, the flap's other two edges carry one -- is what print_qc reads as "2 open, 1 non-
    # manifold". Measured on P21 (tail-lamp slot corner, sides 0.6 / 1.2 / 1.3 mm) and P22 (tail
    # tip at the fascia seam, 0.9 / 1.2 / 2.1 mm). Removed only when under FLAP_MAX_MM2: nothing a
    # 0.4 mm nozzle draws, and never a real surface.
    flaps = 0
    for _ in range(4):
        doomed = set()
        for e in bm.edges:
            if len(e.link_faces) <= 2:
                continue
            for f in e.link_faces:
                if f.calc_area() * 1e6 < FLAP_MAX_MM2 and any(
                        len(e2.link_faces) == 1 for e2 in f.edges if e2 is not e):
                    doomed.add(f)
        if not doomed:
            break
        bmesh.ops.delete(bm, geom=list(doomed), context="FACES_ONLY")
        flaps += len(doomed)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return len(gone) + flaps


def has_open_edge(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = any(len(e.link_faces) == 1 for e in bm.edges)
    bm.free()
    return n


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
    os.makedirs(SHAPE_OUT, exist_ok=True)
    # The output directories are REGENERATED, not appended to. Until 2026-09-26 an export only
    # wrote the files it made, and every file from an earlier numbering stayed: 288 files in
    # production against 213 in placement.json, and print_qc.py read all 288 as if they were
    # the car -- 75 of its "files" were sections that no longer existed. placement.json is the
    # list of parts; a file not in it is not a part, and it is removed before the new ones land.
    stale = 0
    for d_ in (OUT, SHAPE_OUT):
        for fn in os.listdir(d_):
            if fn.lower().endswith(".stl"):
                os.remove(os.path.join(d_, fn))
                stale += 1
    print(f"  cleared {stale} .stl file(s) from the two output directories before exporting")
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
    SHAPE_SCHEDULE.clear()
    SHAPE_PLACEMENT.clear()
    TIER_EXTRA[:] = [p for p in SHAPE_ONLY if p not in PANELS]
    SECT_CACHE.clear()
    os.makedirs(SHAPE_OUT, exist_ok=True)
    for pid in list(PANELS) + list(TIER_EXTRA):
        for o in list(bpy.data.objects):
            if o.name.startswith("PROD_"):
                bpy.data.objects.remove(o, do_unlink=True)
        built = build(pid)
        if built is None:
            print(f"{pid:<7}no faces")
            continue
        ob, nf = built
        # CUT THE SURFACE, WALL ONCE. Until 2026-09-21 the panel was walled first and then every
        # section was walled AGAIN, because a section of a solid comes out open at the cut planes
        # and the second solidify closed it. It did close it, and it cost two things. The outer
        # face moved: the reassembled car measured a half-width of 928.5 mm against the LOCKED 925.
        # And the wall was DOUBLE: measured on one section of P01, 924,837 cm3 against 460,478,
        # and of P07, 464,439 against 240,065. Every mass and volume this script has reported was
        # about twice what it should be.
        #
        # Capping the cut faces instead was tried and is worse than either -- holes_fill on the
        # 3 mm-wide boundary loops of a shell produced 352 non-manifold edges and a nonsense
        # volume, against 16 for the double wall. That attempt is withdrawn.
        #
        # The order that needs neither: cut the SURFACE, then give each section its one wall. A
        # solidify on an open shell with outward normals closes it by construction, goes inward,
        # and leaves the outer face exactly where the design put it.
        if pid not in STAGE03:
            face_outward(ob)
        else:
            # stage03_elements already builds these as closed solids, so a section of one is open
            # at the cut and still needs closing. They keep the second solidify for now, which
            # means these 13 small parts carry an extra wall; the proper cure is a bisect that
            # fills, and it is not this commit.
            face_outward(ob)
        # The panel is now a SURFACE at this point, so its own enclosed volume means nothing. The
        # core's volume and the bbox that has to fit the plate both come from a throwaway walled
        # copy; the object that gets cut stays a surface so each section takes its one wall later.
        probe = ob.copy()
        probe.data = ob.data.copy()
        bpy.context.scene.collection.objects.link(probe)
        if pid not in STAGE03 or has_open_edge(probe):
            thicken(probe)
        bm = bmesh.new()
        bm.from_mesh(probe.data)
        vol = abs(bm.calc_volume(signed=True)) * 1e9
        bm.free()
        mass = vol / 1000.0 * D["density_g_cm3"] / 1000.0
        plan, size, ext = plan_cuts(probe)
        bpy.data.objects.remove(probe, do_unlink=True)
        # A MIRRORED PANEL IS THE MIRROR OF ITS BASE'S SECTIONS, not a second independent cut.
        #
        # Measured on 2026-09-26: P07 and P08 come out of build() identical -- 366 vertices, 314
        # faces, the same bounding box to a tenth of a millimetre -- and plan_cuts gives them the
        # same grid, 5 cuts in X and 1 in Y. P07 then yields 17 sections and P08 yields 13. The
        # left and right of a symmetric car were being cut into different numbers of parts.
        #
        # The cause is in the cell test: a cell takes its neighbour's faces as a TAB only in the
        # PLUS direction of each axis, `hi <= cc < hi + tab`. That direction is absolute, so on the
        # left it reaches outboard and on the right inboard, and a thin cell that survives the
        # `len(faces) < 3` guard on one side is dropped on the other.
        #
        # Making the tab direction relative would change every existing file. Mirroring is both
        # smaller and more correct: the car is symmetric by construction, panel_map already builds
        # the right half as a mirror of the left, and two sides that differ are a manufacturing
        # nuisance rather than a design. The base is always processed first -- PANELS lists it that
        # way -- and its section meshes are kept until its mirror has used them.
        base = MIRROR_OF.get(pid)
        if base is not None and base in SECT_CACHE:
            secs = []
            for k, md in enumerate(SECT_CACHE[base]):
                cp = bpy.data.objects.new(f"SEC_{pid}_m{k}", md.copy())
                bpy.context.scene.collection.objects.link(cp)
                mirror_in_place(cp)
                secs.append(cp)
        else:
            secs = cut_into_sections(ob, plan, pid)
            if any(pid == b for b in MIRROR_OF.values()):
                SECT_CACHE[pid] = [o.data.copy() for o in secs]
        made = []
        for j, sec in enumerate(secs, 1):
            face_outward(sec)
            # A closed solid is not walled again. stage03 builds its parts as closed solids; a
            # SECTION of one is open at the cut and needs the wall to close it, but a WHOLE one is
            # already a body, and solidify on a closed body makes a second shell inside the first:
            # every stage-03 part exported as two files in whole mode, the second an inverted
            # inner skin. Walled only if it has an open edge.
            if not (pid in STAGE03 and not has_open_edge(sec)):
                thicken(sec)
            for pc, part in enumerate(loose_pieces(sec)):
                # Orientation is settled PER PIECE, here, because a section holding two pieces can
                # have a positive signed volume overall while one of them is inverted -- which is
                # exactly what P13 and P14's second piece did, exporting at -700.9 cm3 after the
                # section as a whole had passed. A slicer given that prints the complement.
                face_outward(part)
                place = lay_flat(part)
                tidy_for_export(part)
                w = [part.matrix_world @ v.co for v in part.data.vertices]
                ss = [(max(p[i] for p in w) - min(p[i] for p in w)) * 1000 for i in range(3)]
                # sorted against sorted: the shop can turn a part in plane, so 600 x 1200 fits a
                # 1200 x 600 bed. lay_flat has already put the smallest dimension vertical.
                fits = all(a <= b - 2 * D["bed_margin_mm"]
                           for a, b in zip(sorted(ss), sorted(D["bed_mm"])))
                if D["split"] == "whole" and not plan:
                    sfx = "whole" if pc == 0 else f"whole_{chr(ord('a') + pc)}"
                else:
                    sfx = f"s{j:02d}" if pc == 0 else f"s{j:02d}{chr(ord('a') + pc)}"
                d_ = SHAPE_OUT if pid in TIER_EXTRA else OUT
                path = os.path.join(d_, f"{pid}_{NAME_OF.get(pid,'PANEL')}_{sfx}.stl")
                bpy.ops.object.select_all(action="DESELECT")
                part.select_set(True)
                bpy.context.view_layer.objects.active = part
                try:
                    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True,
                                          global_scale=1000.0)
                except AttributeError:
                    bpy.ops.export_mesh.stl(filepath=path, use_selection=True, global_scale=1000.0)
                # an 84-byte STL is a header and no triangles; the exporter reports success anyway
                if os.path.getsize(path) <= 84:
                    print(f"    ERROR {os.path.basename(path)} was written EMPTY -- the part was not "
                          f"exportable (hidden?); this file must not go to the shop")
                made.append((sfx, ss, fits, path, one_piece(part), place,
                             part.get("class_a_up", "unknown"),
                             # in whole mode the section IS the panel object, so count it once
                             (ob.get("dropped_mm2", 0) if pc == 0 else 0)
                             + (sec.get("dropped_mm2", 0) if (sec is not ob and pc == 0) else 0)))
        total_m += mass
        total_s += len(made)
        over = [m for m in made if not m[2]]
        split_files = [m for m in made if m[4] > 1]
        for sfx, ss, fits, path, np_, place, cau, dropped in made:
            inv = place.inverted()
            o = inv @ mathutils.Vector((0.0, 0.0, 0.0))
            e = inv.to_euler()
            (SHAPE_SCHEDULE if pid in TIER_EXTRA else SCHEDULE).append(
                dict(PANEL=pid, NAME=NAME_OF.get(pid, ""), SECTION=sfx,
                                 X_MM=round(ss[0], 1), Y_MM=round(ss[1], 1), Z_MM=round(ss[2], 1),
                                 FITS_BED="yes" if fits else "NO",
                                 PIECES_IN_FILE=np_,
                                 CLASS_A_UP=cau,
                                 # skin that belonged to this region but was not connected to it
                                 # (seam slivers, lone loft faces, detached fans): NOT in any
                                 # file. The laminate bridges it; the number says how much.
                                 DROPPED_MM2=int(dropped),
                                 # where the printed file goes back on the car: rotate by these
                                 # degrees about X, Y, Z, then move the file's origin to this point.
                                 PLACE_RX=round(math.degrees(e.x), 2),
                                 PLACE_RY=round(math.degrees(e.y), 2),
                                 PLACE_RZ=round(math.degrees(e.z), 2),
                                 PLACE_X_MM=round(o.x * 1000.0, 1),
                                 PLACE_Y_MM=round(o.y * 1000.0, 1),
                                 PLACE_Z_MM=round(o.z * 1000.0, 1),
                     WHAT_IS_MISSING=SHAPE_ONLY.get(pid, ""),
                     FILE=os.path.relpath(path, REPO)))
            (SHAPE_PLACEMENT if pid in TIER_EXTRA else PLACEMENT)[
                os.path.basename(path)] = [list(r) for r in inv]
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
    n_prod = len({r["PANEL"] for r in SCHEDULE})
    n_shape = len({r["PANEL"] for r in SHAPE_SCHEDULE})
    if D["split"] == "whole":
        print(f"\n   READY TO BOND   {n_prod} parts, {len(SCHEDULE)} files -- WHOLE PANELS, one file "
              f"per part; FITS_BED is against the {D['bed_mm'][0]:.0f} x {D['bed_mm'][1]:.0f} x "
              f"{D['bed_mm'][2]:.0f} reference bed")
    else:
        print(f"\n   READY TO BOND   {n_prod} parts, {len(SCHEDULE)} sections on a "
              f"{D['bed_mm'][0]:.0f} mm bed")
    print(f"   SHAPE ONLY      {n_shape} parts, {len(SHAPE_SCHEDULE)} sections "
          f"(fitting masters, interface still to come from the car)")
    print(f"   ~{total_m:.1f} kg of core across both, at the provisional wall")
    sbad = [r for r in SHAPE_SCHEDULE if r["FITS_BED"] != "yes" or r["PIECES_IN_FILE"] > 1]
    if SHAPE_SCHEDULE:
        print(f"   {len(SHAPE_SCHEDULE) - len(sbad)} of {len(SHAPE_SCHEDULE)} shape-only sections "
              f"are one piece on the plate")
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
    # The placement file. The CSV carries the same numbers in degrees and millimetres for a human;
    # this is the exact matrix, for assembly_check.py and for anyone re-assembling in CAD.
    pl = os.path.join(OUT, "placement.json")
    with open(pl, "w", encoding="utf-8") as f:
        _json.dump({"note": ("4x4 in METRES, repo axes. Apply to the STL's own coordinates, which "
                             "are in millimetres, after scaling by 0.001, to put the printed part "
                             "back where it belongs on the car."),
                    "parts": PLACEMENT}, f, indent=1)
    print(f"wrote {pl}  ({len(PLACEMENT)} parts)")
    # What a print farm needs to know, as data. print_qc.py turns this plus its own result into
    # 03_PRINT/README.md, so the document a farm reads is generated from the run that made the
    # files and cannot drift from them the way a hand-written one would.
    hand = {"when": time.time(),
            "decisions": {k: (list(v) if isinstance(v, tuple) else v) for k, v in D.items()},
            "ready_to_bond": {"parts": sorted({r["PANEL"] for r in SCHEDULE}),
                              "sections": len(SCHEDULE),
                              "one_piece": sum(1 for r in SCHEDULE if r["PIECES_IN_FILE"] == 1),
                              "fits_bed": sum(1 for r in SCHEDULE if r["FITS_BED"] == "yes")},
            "shape_only": {"parts": sorted({r["PANEL"] for r in SHAPE_SCHEDULE}),
                           "sections": len(SHAPE_SCHEDULE),
                           "one_piece": sum(1 for r in SHAPE_SCHEDULE if r["PIECES_IN_FILE"] == 1),
                           "fits_bed": sum(1 for r in SHAPE_SCHEDULE if r["FITS_BED"] == "yes"),
                           "missing": SHAPE_ONLY},
            "core_kg": round(total_m, 1),
            "dropped_skin_mm2": int(sum(r["DROPPED_MM2"] for r in SCHEDULE + SHAPE_SCHEDULE)),
            "small_sections_under_40mm": sum(1 for r in SCHEDULE + SHAPE_SCHEDULE
                                             if max(r["X_MM"], r["Y_MM"], r["Z_MM"]) < 40)}
    with open(os.path.join(REPO, "03_PRINT", "handoff.json"), "w", encoding="utf-8") as f:
        _json.dump(hand, f, indent=1)
    if SHAPE_SCHEDULE:
        sh = os.path.join(REPO, "04_ENGINEERING", "reports", "shape_only_schedule.csv")
        with open(sh, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(SHAPE_SCHEDULE[0]))
            w.writeheader()
            w.writerows(SHAPE_SCHEDULE)
        with open(os.path.join(SHAPE_OUT, "placement.json"), "w", encoding="utf-8") as f:
            _json.dump({"note": "as production/placement.json, for the SHAPE ONLY tier",
                        "parts": SHAPE_PLACEMENT}, f, indent=1)
        print(f"\nSHAPE ONLY — outer form ours, interface still to come from the car")
        print(f"   {len({r['PANEL'] for r in SHAPE_SCHEDULE})} panels, "
              f"{len(SHAPE_SCHEDULE)} sections -> 03_PRINT/shape_only/")
        print( "   these are shape masters for fitting, NOT parts ready to bond, and they are not")
        print( "   in the supplier package. Each row carries what is still missing.")
        print(f"wrote {sh}")
    return rows


main()
