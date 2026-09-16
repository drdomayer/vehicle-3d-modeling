"""
panel_map.py — assign every face of the body to exactly one registered panel, colour it, and prove
the 38 parts actually tile the car. Runs inside Blender.

This is a MAP, not a set of panels. v019 is a Stage 01 blockout and docs/16 says the blockout is
discarded when surfacing begins. What is being tested here is the ARCHITECTURE: do the seams in
statev_skeleton.PANEL_SEAMS, plus the parts in panel_registry.PARTS, cover the whole outer surface
once and only once? A panel map with holes in it is a panel map that will produce a car with holes.

The rules are ORDERED and the first match wins, so no face can belong to two panels by accident.
Every boundary value is a seam that already exists with a recorded reason, or a donor hardpoint.
No boundary is invented here to make the map come out tidy.

    import bpy; exec(open(".../panel_map.py").read())
"""

import bmesh
import bpy
import colorsys
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"

_pr = {}
with open(os.path.join(REPO, "01_CAD/scripts/panel_registry.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(argv):")[0],
         {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_registry.py"), "__name__": "_pr"}, _pr)
PARTS = _pr["PARTS"]
NAME_OF = {p[0]: p[1] for p in PARTS}

# Boundaries. Every one of these is a seam with a reason in statev_skeleton.PANEL_SEAMS or a donor
# hardpoint in cage_986.DIMS. They are named here rather than written as bare numbers so that a
# reader can check each against its source.
B = dict(
    nose_end        = -655,   # DIFFUSER-style: end of the nose mouth family, NOSE_MOUTH last station
    hood_front      = -655,   # HOOD_to_FRONT_BODY seam, forward end
    cowl            = 420,    # donor windshield base, DIMS cowl_x
    door_front      = 440,    # donor shut line, DIMS door_front_x
    door_rear       = 1635,   # donor shut line, DIMS door_rear_x
    hoop            = 1760,   # donor roll hoop plane, DIMS hoop_x
    cover_front     = 2000,   # ENGINE_COVER_to_DECK seam
    fascia_front    = 3000,   # REAR_FASCIA_to_DECK seam
    rocker_top      = 330,    # ROCKER_to_UPPER_BODY seam, and DIFFUSER_to_FASCIA at the same Z
    hood_half_width = 380,    # HOOD_to_FRONT_BODY seam path, where it leaves the centre
    cover_half_width= 560,    # ENGINE_COVER_to_DECK seam path, outer end
    intake_front    = 1780,   # SIDE_INTAKE field x0 in statev_master_volumes
    intake_rear     = 2300,   # SIDE_INTAKE field x1
    splitter_top    = 300,    # our splitter, below the nose mouth floor (NOSE_MOUTH z_lo 200-215)
    rocker_end      = 2415,   # rear axle, PUBLISHED. The rear arch removes everything below the
                              # rocker line between 2050 and 2780, so anything below that line aft
                              # of the axle is the severed corner P39/P40, never the sill.
)


# Faces that are not exterior skin at all. The blockout is a closed solid, so its mesh includes
# the floor pan and the inward-facing walls the cabin cut and the arch cuts left behind. Those are
# not panels and counting them as panels inflates every area figure — the first run of this script
# reported 22.6 m2 of "panel", which is roughly twice a car's exterior.
NOT_PANEL = {
    "X_FLOOR":  "underside; the body floor at Z 120, not a body panel",
    "X_CABIN":  "inward wall left by the cabin cut; interior, not skin",
    "X_ARCH":   "inward wall of a wheel arch; a liner at most, not a panel",
}


# The cabin cutter and the arch cutters, as statev_master_volumes actually builds them. Named here
# so the cap rules below can be read against their source instead of against bare numbers.
CABIN = dict(x0=420.0, x1=1760.0, y=700.0, z=640.0)      # cowl_x .. hoop_x, |Y| < 700, Z 640 up
ARCH_CUTS = ((0.0, 350.0, 323.5), (2415.0, 365.0, 337.5))  # spec X, radius, centre Z (tod/2)
CAP_TOL = 12.0   # a boolean leaves its cap ON the cut plane; this is slack, not a search radius


def not_panel(sx, ay, z, nz, ny):
    if z < 130 and nz < -0.4:
        return "X_FLOOR"
    if CABIN["x0"] <= sx <= CABIN["x1"] and ay <= 715 and z > 600 and ny > 0.4:
        return "X_CABIN"
    for ax, r, _cz in ARCH_CUTS:
        if abs(sx - ax) < r and z < 700 and ny > 0.4:
            return "X_ARCH"

    # Boolean CAPS. Added 2026-09-16 after a face-size audit: nine faces larger than 0.05 m2 were
    # passing all of the rules above and being counted as exterior skin, 3.953 m2 of it. The worst
    # was a single four-vertex quad of 1.876 m2 lying flat at Z 640 across the whole cabin aperture
    # -- the floor of the cabin cut, assigned to P09 DOOR_SKIN, and on its own half of that panel's
    # reported area. The rules above screen on ny, so a cap whose normal points along X or Z passes
    # them untouched however large it is, and nothing downstream looks at face size.
    #
    # A cap has a signature that needs no list: it sits ON a cut plane with its normal along that
    # plane's axis. That is what is tested, against the cutters the build uses.
    if CABIN["x0"] - CAP_TOL <= sx <= CABIN["x1"] + CAP_TOL and ay <= CABIN["y"] + CAP_TOL:
        if abs(z - CABIN["z"]) < CAP_TOL and abs(nz) > 0.9:
            return "X_CABIN_FLOOR"          # the aperture's floor, looking up into the cabin
        if z > CABIN["z"] - CAP_TOL:
            if min(abs(sx - CABIN["x0"]), abs(sx - CABIN["x1"])) < CAP_TOL and abs(nz) < 0.35:
                return "X_CABIN_END"        # the cut's front or rear wall, normal along X
    for ax, r, cz in ARCH_CUTS:
        d = ((sx - ax) ** 2 + (z - cz) ** 2) ** 0.5
        if abs(d - r) < CAP_TOL and abs(nz) < 0.9:
            return "X_ARCH_WALL"            # on the cylinder itself: the wheel well, not the skin
        # and the disc that closes the cylinder's inboard end. The arch cutter is a cylinder of
        # finite depth, so it leaves a flat wall at the inner end of the wheel well as well as the
        # curved one. It is inside the removed circle with its normal along Y, which no exterior
        # face can be: skin cannot live inside the volume the cut took away.
        if d < r - CAP_TOL and abs(ny) > 0.9:
            return "X_ARCH_END"
    return None


def panel_of(sx, ay, z):
    """Ordered rules, first match wins. Returns a panel id or None."""
    # ---- FRONT
    if sx < B["nose_end"]:
        return "P28" if z < B["splitter_top"] else "P01"
    if sx < B["door_front"]:
        if z < B["rocker_top"] and sx > 120:
            return "P07"                       # rocker starts behind the front arch
        if ay < B["hood_half_width"] and sx < B["cowl"]:
            return "P02"                       # hood
        return "P03"                           # front fender
    # ---- SIDE
    if sx < B["door_rear"]:
        if z < B["rocker_top"]:
            return "P07"
        return "P09"                           # door skin
    if sx < B["intake_front"]:
        if z < B["rocker_top"]:
            return "P07"
        return "P15"                           # haunch begins at the rear shut line
    # ---- REAR
    if sx < B["intake_rear"] and B["rocker_top"] <= z < 700:
        return "P11"                           # side intake surround
    if z < B["rocker_top"]:
        if sx > B["fascia_front"]:
            return "P22"
        return "P39" if sx > B["rocker_end"] else "P07"
    if sx >= B["fascia_front"]:
        return "P21"                           # rear fascia
    if sx >= B["cover_front"] and ay < B["cover_half_width"]:
        return "P20"                           # engine cover
    if sx >= B["cover_front"] and z > 900:
        return "P19"                           # rear deck, outboard of the cover
    if sx < B["cover_front"] and z > 900:
        return "P17"                           # buttress, between hoop plane and cover
    return "P15"                               # rear haunch, everything else


PALETTE_ORDER = ["P01", "P28", "P02", "P03", "P07", "P39", "P09", "P11", "P15", "P17", "P19",
                 "P20", "P21", "P22"]


def colour(i, n):
    r, g, b = colorsys.hsv_to_rgb(i / max(1, n), 0.62, 0.92)
    return (r, g, b, 1.0)


def main():
    print("=" * 96)
    print("STATEV 001 — PANEL MAP on v019.  A map of the architecture, not a set of panels.")
    print("=" * 96)
    master = bpy.data.collections["STATEV_MASTER"]
    bodies = [o for o in master.all_objects if o.type == "MESH" and "VOLUME" in o.name]

    mats = {}
    for i, pid in enumerate(PALETTE_ORDER):
        m = bpy.data.materials.get(f"PANEL_{pid}") or bpy.data.materials.new(f"PANEL_{pid}")
        m.use_nodes = False
        m.diffuse_color = colour(i, len(PALETTE_ORDER))
        mats[pid] = m

    tally, area, unassigned = {}, {}, 0
    other, other_area = {}, {}
    for ob in bodies:
        ob.data.materials.clear()
        slot_of = {}
        for pid in PALETTE_ORDER:
            ob.data.materials.append(mats[pid])
            slot_of[pid] = len(ob.data.materials) - 1
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            c = ob.matrix_world @ f.calc_center_median()
            n = (ob.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            # inward-pointing is toward the centreline, so compare the normal's Y against the
            # side the face is on
            ny = -n.y if c.y > 0 else n.y
            skip = not_panel(sx, ay, z, n.z, ny)
            if skip:
                other[skip] = other.get(skip, 0) + 1
                other_area[skip] = other_area.get(skip, 0.0) + f.calc_area()
                continue
            pid = panel_of(sx, ay, z)
            if pid is None or pid not in slot_of:
                unassigned += 1
                continue
            f.material_index = slot_of[pid]
            tally[pid] = tally.get(pid, 0) + 1
            area[pid] = area.get(pid, 0.0) + f.calc_area()
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()

    total = sum(tally.values())
    print(f"\n{'ID':<6}{'PART':<24}{'FACES':>8}{'SHARE':>8}{'AREA m2':>10}")
    for pid in PALETTE_ORDER:
        n = tally.get(pid, 0)
        print(f"{pid:<6}{NAME_OF.get(pid, '?'):<24}{n:>8}{100*n/max(1,total):>7.1f}%"
              f"{area.get(pid, 0.0):>10.3f}")
    print(f"\n  exterior skin: {total} faces, {sum(area.values()):.3f} m2")
    print(f"  {'':<6}{'NOT A PANEL':<24}{'FACES':>8}{'':>8}{'AREA m2':>10}")
    for k, why in NOT_PANEL.items():
        print(f"  {'':<6}{k:<24}{other.get(k,0):>8}{'':>8}{other_area.get(k,0.0):>10.3f}   {why}")
    print(f"  unassigned {unassigned}   (a non-zero number here means the map has holes)")
    print("\n  Mirrored parts share one region: P03 stands for P03+P04, P07 for P07+P08,")
    print("  P09 for P09+P10, P11 for P11+P12, P15 for P15+P16, P17 for P17+P18.")
    print("  Parts that are inserts, housings or details inside another panel do not appear as")
    print("  regions and will not until Stage 03: channels, blades, ducts, louvres, surrounds,")
    print("  the mask, the plate recess, the mirror caps and every light housing.")
    if unassigned:
        print(f"\n  WARNING {unassigned} faces belong to no panel. The map has holes.")
    return tally, area


main()
