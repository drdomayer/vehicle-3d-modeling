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
    splitter_top    = 194,    # the splitter LIP and its recess (CUT_LIP_RECESS, Z 150..194).
                              # 300 until 2026-10-02 (v056): with the mouth's floor now at 220
                              # the whole nose under Z 300 printed as carbon -- a 180 mm grey band
                              # across the front where ref-09 has a thin black lip. At 194 --
                              # ON the recess's ceiling -- the part is the lip and the recess's
                              # floor and back wall, an L profile, with the seam hidden in the
                              # recess's shadow. (200 was tried first: the 6 mm strip above the
                              # ceiling joined the lip only through the recess walls, which the
                              # skin accounting rejects, and the part extracted as two pieces.)
    # v057: the DIFFUSER's top edge behind the fascia station. ref-09's rear view puts the black
    # lower valance at ~37% of the hoop height (lamps ~57%, deck ~68%): on ours, with the lamps at
    # ~610, that is ~400 -- the painted wall was coming down to Z 330 and read as a pear. Stepped
    # up around the exhausts (EXHAUST envelope, two pipes at Z 378..482) so they sit inside the
    # black box, as in the render, instead of straddling a seam. Outboard of diffuser_half the
    # corner legs stay painted down to the rocker line, as the render's do.
    diffuser_top    = 410,
    diffuser_half   = 660,
    exhaust_box_top = 500,
    exhaust_box_half= 190,
    rocker_end      = 2415,   # rear axle, PUBLISHED. The rear arch removes everything below the
                              # rocker line between 2050 and 2780, so anything below that line aft
                              # of the axle is the severed corner P39/P40, never the sill.
)


# Faces that are not exterior skin at all. The blockout is a closed solid, so its mesh includes
# the floor pan and the inward-facing walls the cabin cut and the arch cuts left behind. Those are
# not panels and counting them as panels inflates every area figure — the first run of this script
# reported 22.6 m2 of "panel", which is roughly twice a car's exterior.
NOT_PANEL = {
    "X_FLOOR":       "underside; the body floor at Z 120, not a body panel",
    "X_CABIN":       "inward wall left by the cabin cut; interior, not skin",
    "X_ARCH":        "inward wall of a wheel arch; a liner at most, not a panel",
    # The boolean caps, added 2026-09-16. They are listed here as well as rejected in not_panel()
    # because the report's accounting is only honest if every rejected face appears in it. Before
    # this, four reasons existed in the code and not in the table, so 267 faces left the count
    # without a row explaining where they went.
    "X_CABIN_FLOOR": "flat floor of the cabin cut at Z 640; it looks up into the cabin",
    "X_CABIN_END":   "front or rear wall of the cabin cut; normal along X, not skin",
    "X_ARCH_WALL":   "the arch cylinder itself; the wheel well, not the body",
    "X_ARCH_END":    "the disc closing the arch cylinder inboard; inside the removed volume",
    # Stage 03 openings, added 2026-09-17. A pocket has walls, and a wall that looks into a duct is
    # not exterior skin any more than the cabin's wall is.
    "X_INTAKE":      "wall of the side-intake mouth; it looks into the duct, not at the road",
    "X_FENDER_SLOT": "wall of the fender vent slot; it looks into the wheel well",
    "X_MOUTH":       "wall of the central mouth; it looks into the duct behind the mask",
    "X_ROCKER_CHANNEL": "wall or floor of the sill undercut; it looks at the road, not the side",
    "X_CORNER":      "wall of the corner intake box; it looks into the brake duct",
    "X_LIP":         "the recess above the splitter lip; a shadow line, not skin",
    "X_TAIL_CORNER": "wall of the tail corner pocket under the light bar's L end",
    "X_LOUVRE":      "wall or floor of the engine-cover louvre aperture; it looks into the engine bay",
    "X_BADGE":       "wall or floor of the badge band between the tail lamps; a dark recess, printed with P21",
    "X_EYE":         "wall or floor of the headlamp eye recess; black, printed with the fascia / fender",
}

DIFFUSER_FRONT = 2870.0   # DIFFUSER_FLOOR's first station in statev_master_volumes: the tunnel's start


# The Stage 03 pockets, as stage03_elements.py cuts them. Named here so the rejection can be read
# against its source instead of against four bare numbers.
POCKETS = [("X_INTAKE", 1910.0, 2180.0, 420.0, 1000.0, 440.0, 710.0),
           ("X_FENDER_SLOT", -250.0, 180.0, 375.0, 560.0, 690.0, 1000.0),
           # v056: the TRAPEZOID (stage03 MOUTH: hw 320 at Z 220, 380 at Z 430), not its box. The
           # box claimed the fascia's own skin beside the lower corners as mouth wall -- in the
           # render, as black triangles at both bottom corners of the mouth.
           ("X_MOUTH", -1000.0, -815.0, 0.0, 390.0, 215.0, 435.0,
            [(0.0, 220.0), (320.0, 220.0), (380.0, 430.0), (0.0, 430.0)]),
           ("X_ROCKER_CHANNEL", 470.0, 1610.0, 840.0, 1000.0, 195.0, 285.0),
           # v056: the corner intake is a QUAD in Y-Z, not a box (stage03 CORNER_POLY): its inner
           # edge leans out from Y 450 at the top to 590 at the bottom. The box test would throw
           # away the painted wedge between it and the mouth, so the polygon decides.
           ("X_CORNER", -1000.0, -745.0, 445.0, 750.0, 235.0, 485.0,
            [(450.0, 480.0), (745.0, 480.0), (745.0, 240.0), (590.0, 240.0)]),
           # v056: the engine-cover louvre field (stage03 LOUVRE), read off ref-09's top view
           ("X_LOUVRE", 2207.0, 2893.0, 0.0, 388.0, 700.0, 1100.0),
           # v065: the headlamp eye (stage03 EYE), in THREE convex parts because the outline is not
           # convex. in_poly is a convex test; the first run had two parts, and the second was
           # concave at (820, 592) -- the lower edge's slope falls 0.733 -> 0.667 there -- so the
           # extended edge 820..850 rejected the eye's own floor at Y 708 and left it in P01 as a
           # loose face. Measured, then split. And 8 mm of slack, not POLY_TOL: where the lower edge
           # crosses the nose's corner crease (Y 750..775) the boolean leaves a 1-2 mm lip of facets
           # with their normals pointing down, ~6 mm outside the outline -- 4 cm2 a side, which made
           # P01 three pieces. They are black and printed with the panel either way.
           ("X_EYE", -1000.0, -500.0, 515.0, 705.0, 500.0, 632.0,
            [(520.0, 548.0), (560.0, 522.0), (600.0, 505.0), (700.0, 505.0), (700.0, 627.0),
             (600.0, 625.0), (560.0, 608.0), (520.0, 576.0)], 8.0),
           ("X_EYE", -1000.0, -450.0, 695.0, 825.0, 500.0, 642.0,
            [(700.0, 505.0), (760.0, 548.0), (820.0, 592.0), (820.0, 637.0), (760.0, 632.0),
             (700.0, 627.0)], 8.0),
           ("X_EYE", -1000.0, -450.0, 815.0, 855.0, 585.0, 645.0,
            [(820.0, 592.0), (850.0, 612.0), (850.0, 640.0), (820.0, 637.0)], 8.0),
           # v060: the badge band, a 20 mm recess in the tail face between the lamps (stage03 BAND)
           ("X_BADGE", 3180.0, 3500.0, 0.0, 431.0, 584.0, 646.0),
           ("X_LIP", -1000.0, -905.0, 0.0, 625.0, 148.0, 196.0),
           ("X_TAIL_CORNER", 3175.0, 3500.0, 685.0, 765.0, 347.0, 580.0)]


# The cabin cutter and the arch cutters, as statev_master_volumes actually builds them. Named here
# so the cap rules below can be read against their source instead of against bare numbers.
CABIN = dict(x0=420.0, x1=1760.0, y=700.0, z=640.0)      # cowl_x .. hoop_x, |Y| < 700, Z 640 up
ARCH_CUTS = ((0.0, 350.0, 323.5), (2415.0, 365.0, 337.5))  # spec X, radius, centre Z (tod/2)
CAP_TOL = 12.0   # a boolean leaves its cap ON the cut plane; this is slack, not a search radius


POLY_TOL = 5.0   # a wall face lies ON the polygon's edge; this is slack, not a search radius


def in_poly(u, v, poly, tol):
    """Inside the convex polygon (u, v), or within tol of one of its edges."""
    inside, n = True, len(poly)
    sgn = None
    for i in range(n):
        (a, b), (c, d) = poly[i], poly[(i + 1) % n]
        cr = (c - a) * (v - b) - (d - b) * (u - a)
        L = ((c - a) ** 2 + (d - b) ** 2) ** 0.5
        if abs(cr) / L <= tol:
            continue          # on this edge, within the slack
        s = cr > 0
        if sgn is None:
            sgn = s
        elif s != sgn:
            inside = False
            break
    return inside


def not_panel(sx, ay, z, nz, ny):
    # v066: the floor never faces FORWARD. Ahead of the fascia line (spec X < -655) the lower edge of
    # the nose chamfer rolls under at Z 120..132 with normals like (-0.63, 0.39, -0.67): the rule
    # below took that strip for floor, and it was the only skin joining the splitter's front lip
    # (Y 0..530) to its chamfer band (Y 470..790) -- so P28 was two surfaces touching at ONE vertex,
    # hidden for months by a piece count that walked vertices. A face there with |nx| over 0.25 is
    # the splitter's own surface. The flat floor reads |nx| ~0.
    nxa = max(0.0, 1.0 - nz * nz - ny * ny) ** 0.5
    nose_edge = sx < -655.0 and nxa > 0.25
    if z < 130 and nz < -0.4 and not nose_edge:
        return "X_FLOOR"
    # v061: the underside roll-under. Faces facing the road (nz < -0.85) just above Z 130 were
    # skin while their neighbours below 130 were floor, so the strip broke into islands that the
    # print chain then dropped -- assembly_check's worst point, a 24 mm gap under P03 at spec X
    # -309, Z 120..135, present since at least v059. Kept off the diffuser, whose tunnel ceiling
    # faces down at Z 150..330 and IS a panel.
    if z < 145 and nz < -0.85 and sx < DIFFUSER_FRONT and not nose_edge:
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
    for nm, x0, x1, y0, y1, z0, z1, *poly in POCKETS:
        # EVERY face inside a pocket box is a pocket wall: the outer skin there is what the cut
        # removed. Until 2026-09-26 the test asked for a Y or Z normal, so the two END walls of
        # the fender slot (normal along X, 21 745 and 16 585 mm2) passed as skin and reached P03
        # as two lone faces connected to nothing -- and the same walls were then missing from
        # the panel's print file, because panel_production drops what this rejects. The walls
        # are not exterior skin (this table), but they ARE the panel's geometry to print; the
        # production gather keeps a pocket's walls with the panel whose region the pocket is in.
        if x0 <= sx <= x1 and y0 <= ay <= y1 and z0 <= z <= z1:
            # an entry may carry its own slack after the polygon (the eye, v065); the rest use POLY_TOL
            if poly and not in_poly(ay, z, poly[0], poly[1] if len(poly) > 1 else POLY_TOL):
                continue
            return nm
    for ax, r, cz in ARCH_CUTS:
        d = ((sx - ax) ** 2 + (z - cz) ** 2) ** 0.5
        # "abs(nz) < 0.9" spared the near-horizontal facets at the TOP of the cylinder, meant to
        # protect the skin over the arch lip. Measured 2026-09-26: the spared faces were the wheel
        # well's ceiling -- 14 162 mm2 facets at Z 675..701 with their normals pointing DOWN
        # (nz -0.92..-1.0), which no exterior face does -- and they reached P15 as a detached
        # 273 x 346 mm shelf. Skin over the lip faces UP; only that is spared.
        # 2 mm, not CAP_TOL. Measured 2026-09-26: every wall face sits within 0.6 mm of the
        # cylinder, while 39 (rear) and 46 (front) SKIN faces at the arch lip sat 1.3..10.8 mm
        # off it and were being thrown away with the wall -- which is what made the arch edge of
        # every printed fender and haunch a staircase. The wall is ON the cylinder; skin is not.
        if abs(d - r) < 2.0 and nz < 0.9:
            return "X_ARCH_WALL"            # on the cylinder itself: the wheel well, not the skin
        # and the disc that closes the cylinder's inboard end. The arch cutter is a cylinder of
        # finite depth, so it leaves a flat wall at the inner end of the wheel well as well as the
        # curved one. It is inside the removed circle with its normal along Y, which no exterior
        # face can be: skin cannot live inside the volume the cut took away.
        if d < r - CAP_TOL and abs(ny) > 0.9:
            return "X_ARCH_END"
    return None


# Every plane panel_of can switch on. A face whose centre decides its panel is a face that gets
# assigned by where its middle happens to fall, and on a mesh whose tessellation is not itself
# mirror-symmetric that produces panels that are not mirror-symmetric either: P28 and P41 came out
# 0.142 and 0.099 m2, and P01's area-weighted centroid sat 65 mm off the centreline, on a body whose
# VOLUME is symmetric to 0.2 litres. The shape was never asymmetric; the assignment was.
#
# So the body is cut on these planes before anything is assigned. Then no face straddles a boundary,
# every face lies wholly inside one panel, and the answer stops depending on tessellation.
def boundary_planes():
    """(normal, point, spec_x_from): a plane cuts only faces reaching spec X >= spec_x_from. The
    v057 diffuser planes are LOCAL to the tail: cut across the whole car they split faces inside
    the side-intake and nose pockets, and the halves that fell outside a pocket box became loose
    islands (P01 two pieces, P11/P12 three)."""
    X = [B["nose_end"], B["cowl"], B["door_front"], B["door_rear"], B["hoop"], B["intake_front"],
         B["intake_rear"], B["cover_front"], B["rocker_end"], B["fascia_front"]]
    Z = [B["rocker_top"], B["splitter_top"], 700.0, 900.0]
    Y = [0.0, B["hood_half_width"], B["cover_half_width"], 715.0, CABIN["y"]]
    ALL = -1.0e9
    out = [((-1.0, 0.0, 0.0), (-v / 1000.0, 0.0, 0.0), ALL) for v in X]     # spec X -> repo x
    out += [((0.0, 0.0, 1.0), (0.0, 0.0, v / 1000.0), ALL) for v in Z]
    out += [((0.0, 1.0, 0.0), (0.0, v / 1000.0, 0.0), ALL) for v in Y]
    out += [((0.0, 1.0, 0.0), (0.0, -v / 1000.0, 0.0), ALL) for v in Y if v > 0]
    tail = B["fascia_front"] - 10.0
    out += [((0.0, 0.0, 1.0), (0.0, 0.0, v / 1000.0), tail)
            for v in (B["diffuser_top"], B["exhaust_box_top"])]
    for v in (B["exhaust_box_half"], B["diffuser_half"]):
        out += [((0.0, 1.0, 0.0), (0.0, v / 1000.0, 0.0), tail),
                ((0.0, 1.0, 0.0), (0.0, -v / 1000.0, 0.0), tail)]
    return out


def split_on_boundaries(bm):
    """Cut the mesh on every plane panel_of switches on. Splits only; removes nothing."""
    for no, co, x_from in boundary_planes():
        if x_from > -1.0e8:
            fs = [f for f in bm.faces if max(-v.co.x * 1000.0 for v in f.verts) >= x_from]
            es = list({e for f in fs for e in f.edges})
            vs = list({v for f in fs for v in f.verts})
            geom = vs + es + fs
        else:
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        if not geom:
            continue
        bmesh.ops.bisect_plane(bm, geom=geom, plane_no=no, plane_co=co,
                               clear_outer=False, clear_inner=False)
    return bm


def diffuser_top_at(ay):
    """The P21/P22 seam height at this half-width, behind the fascia station (v057)."""
    if ay < B["exhaust_box_half"]:
        return B["exhaust_box_top"]
    if ay < B["diffuser_half"]:
        return B["diffuser_top"]
    return B["rocker_top"]


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
        if sx >= B["hoop"] and ay < B["cover_half_width"] and z > 700:
            return "P19"                       # v056: the deck behind the hoops, not the haunch
        return "P15"                           # haunch begins at the rear shut line
    # ---- REAR
    if sx < B["intake_rear"] and B["rocker_top"] <= z < 700:
        return "P11"                           # side intake surround
    if sx >= B["fascia_front"] and z < diffuser_top_at(ay):
        return "P22"                           # v057: the black lower valance and exhaust box
    if z < B["rocker_top"]:
        # v055: the diffuser starts where its tunnel starts (DIFFUSER_FLOOR, 2870), so the tunnel
        # ceiling and the legs are one moulding; with the boundary at 3000 the ceiling between
        # 2870 and 3000 was a loose 134 x 506 mm piece of P39/P40
        if sx > DIFFUSER_FRONT:
            return "P22"
        return "P39" if sx > B["rocker_end"] else "P07"
    if sx >= B["fascia_front"]:
        return "P21"                           # rear fascia
    if sx >= B["cover_front"] and ay < B["cover_half_width"]:
        return "P20"                           # engine cover
    if sx >= B["cover_front"] and z > 900:
        return "P19"                           # rear deck, outboard of the cover
    if sx < B["cover_front"] and (z > 900 or (ay < B["cover_half_width"] and z > 700)):
        # v056: the DECK between the hoop plane and the cover. Called P17 until today, but P17
        # became the stage-03 buttress blade on 2026-09-29 and extraction let the blade replace
        # this region -- so the strip of deck behind the hoops was in no file at all.
        return "P19"
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
    print("\n  Mirrored parts share one region, because this map keys on |Y| and cannot tell the")
    print("  sides apart: P03 stands for P03+P04, P07 for P07+P08, P39 for P39+P40, P09 for")
    print("  P09+P10, P11 for P11+P12, P15 for P15+P16, P17 for P17+P18, P28 for P28+P41,")
    print("  P19 for P19+P42. The extraction splits them on the sign of Y, which is a fact about")
    print("  the car and not a choice: +Y is left by this repo's own convention.")
    print("  Parts that are inserts, housings or details inside another panel do not appear as")
    print("  regions and will not until Stage 03: channels, blades, ducts, louvres, surrounds,")
    print("  the mask, the plate recess, the mirror caps and every light housing.")
    if unassigned:
        print(f"\n  WARNING {unassigned} faces belong to no panel. The map has holes.")
    return tally, area


main()
