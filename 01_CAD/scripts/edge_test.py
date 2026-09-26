"""
edge_test.py — docs/16's CONTINUITY map, measured. The one measurement this project never had.

WHAT WAS MISSING. Three things about the shape have numbers: the silhouette against ref-05, the plan
against ref-09, and the principal-curvature ratio. None of them can see an edge.

  - the silhouette compares OUTLINES and says so itself;
  - the plan is the outline seen from above;
  - highlight_test.py takes the MEDIAN curvature ratio over ~6000 vertices, and a crease is two rows
    of vertices out of sixty. Closing the door channel's upper edge on 2026-09-18 turned a 12-degree
    roll into a 74-degree crease and moved that median by 0.01. Its own closing note admits the gap:
    "it cannot see whether the light BREAKS at the three voids."

So the character of the car — which is its edges — was unmeasured, while three numbers said the
shape was right. docs/16 wrote the specification for it on 2026-09-14 and it has been sitting in
`CONTINUITY` as a table nothing reads:

    G0  a deliberate structural break      -> a large angle IS the design
    G1  a transition of character          -> visible but modest
    G2  the main body surfaces             -> must stay soft; a crease here is the defect

THE TEST IS TWO-SIDED, and that is the point. "Sharper is better" is how a car ends up looking
faceted. A G2 line that measures 40 degrees fails exactly as loudly as a G0 line that measures 4.
docs/16's own words: "G2 не се гони навсякъде. Точно това прави CAD моделите сапунени."

HOW IT MEASURES. On the BUILT mesh, after the booleans, not on ring() — the rings are smoothed along
X before they are lofted, and a measurement taken on the input cannot see what that does. For each
named line and each station along it, the nearest mesh edge running lengthwise is found and its
dihedral angle taken: the angle between the two faces sharing it. That is literally the angle the
light turns through when it crosses the line.

WHAT IT CANNOT DO. It measures the lines it is TOLD about, so a crease somewhere nobody named is
invisible to it, and it says nothing about whether a line is in the right PLACE — only about how
hard it breaks.

    import bpy; exec(open(".../edge_test.py").read())
"""

import math
import os

import bmesh
import bpy
import mathutils

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "reports")
BODY = ["STATEV_FRONT_VOLUME", "STATEV_SIDE_VOLUME", "STATEV_REAR_VOLUME"]
SRC = os.path.join(REPO, "01_CAD/scripts/statev_master_volumes.py")

# What each class is allowed to measure, in degrees of dihedral. These are not measurements, they
# are the reading of docs/16's three words turned into bands, and they are the thing to argue with
# if a verdict looks wrong.
BAND = {"G0": (40.0, 110.0),    # a structural break. Below 40 it is a blend, not a break.
        "G1": (8.0, 40.0),      # visible but modest
        "G2": (0.0, 9.0)}       # the main surfaces: soft, or it is the soap-bar defect inverted

# RECORDED EXCEPTIONS. A line may sit outside its band on purpose, and then the reason is written
# here rather than the band being widened until nothing fails. Same pattern as the freeze rule: the
# machinery does not argue, it names what is outside and who decided it. A line NOT in this list that
# goes out of band is a defect and says so.
EXCEPTIONS = {
    "FRONT_FENDER_TOP -> FRONT_FENDER_SIDE (crest)":
        "the DESIGN turns 55.5 degrees here and always has; the mesh was rendering 44.2 until the "
        "crest was anchored on 2026-09-21, and 38.6 before that. So this is not a line that got "
        "sharper, it is a line that became visible. docs/16 classes it G1 and this file's G1 band "
        "tops out at 40 -- a number this file invented, not one docs/16 gives. "
        "OWNER'S CALL, and it is the SAME call as the rocker below: two of docs/16's G1 lines are "
        "designed at about 50 degrees, so either the band is too tight for a car with this "
        "language, or both lines are harder than the spec intends.",
    "DOOR_UPPER -> ROCKER (sill line)":
        "sharpened on purpose, 55 -> 18 -> 10 mm of transition on 2026-09-15/16, because the sill "
        "read as a soft hollow with no line at all. docs/16 classes it G1 and it measures ~47, so it "
        "is 7 degrees past a band this file invented -- docs/16 gives the CLASS, not the number. "
        "The honest reading is that a sill line on this kind of car is at the hard end of G1. "
        "OWNER'S CALL, not settled: either the band is too tight here or the tuck transition goes "
        "back to ~18 mm.",
}


def load():
    """master_volumes' namespace, plus the skeleton's own tables it re-exports.

    CONTINUITY, SURFACE and PANEL_SEAMS live in statev_skeleton and master_volumes reaches them
    through its `_sk` dict, so they are lifted here rather than read from a second copy."""
    src = open(SRC).read().split("\ndef build():")[0]
    M = {"__name__": "mv"}
    exec(compile(src, SRC, "exec"), M)
    for k in ("CONTINUITY", "SURFACE", "PANEL_SEAMS"):
        M.setdefault(k, M["_sk"][k])
    return M


def lines(M):
    """(name, continuity class, z(spec_x), spec_x range) for every line the build actually defines.

    Only lines whose height comes from a table in the build are here. A transition in CONTINUITY
    with no geometric definition — NOSE -> HOOD, ENGINE_COVER -> REAR_FASCIA — is listed at the end
    as unmeasured rather than quietly dropped."""
    tz, ch, U = M["table_z"], M["VOID_FIELDS"]["SIDE_CHANNEL"], M["REAR_UNDERCUT_FIELD"]
    IN = M["VOID_FIELDS"]["SIDE_INTAKE"]
    return [
        ("DOOR_UPPER -> DOOR_CHANNEL (the side lip)", "G0",
         lambda x: M["side_lip"](x), (ch["x0"] + 140, IN["x1"] - 120)),
        ("REAR_FASCIA -> DIFFUSER (undercut edge)", "G0",
         lambda x: tz(U["edge"], x), (U["xa"], U["xb"])),
        ("DOOR_CHANNEL lower shoulder", "G1",
         lambda x: tz(ch["centre"], x) - ch["w"], (ch["xa"], ch["xb"])),
        ("DOOR_UPPER -> ROCKER (sill line)", "G1",
         lambda x: M["ROCKER_EDGE_Z"], (M["ROCKER_X0"] + 260, M["ROCKER_X1"] - 260)),
        ("the one main side line (shoulder)", "G1",
         lambda x: tz(M["SHOULDER_TRAJECTORY"], x), (-300.0, 3100.0)),
        ("REAR_HAUNCH_TOP -> REAR_HAUNCH_SIDE", "G1",
         lambda x: tz(M["FLANK_TOP"], x), (M["FLANK_X0"] + 300, M["FLANK_X1"] - 300)),
        # FRONT_CREST is the OUTER top line of the front fender, so its class is
        # FRONT_FENDER_TOP -> FRONT_FENDER_SIDE (G1), not HOOD -> FRONT_FENDER_TOP (G2). The first
        # run of this test had it as G2 and called 38.6 degrees a defect. It is not: the crest was
        # given a deliberate two-point corner on 2026-09-16 because ref-05 has a defined fender top
        # line, and 38.6 sits at the top of the G1 band. docs/16's G2 "hood to fender" is the
        # handover across the TOP of the car between two surfaces, which has no height table here
        # and is in the unmeasured list below.
        ("FRONT_FENDER_TOP -> FRONT_FENDER_SIDE (crest)", "G1",
         lambda x: tz(M["FRONT_CREST"]["z"], x), (-700.0, 300.0)),
    ]


# Which CONTINUITY transition each registered panel seam belongs to. A seam and a continuity class
# are DIFFERENT facts and the report keeps them apart: the class is about the surface, the seam is
# about panels. On a real car a G0 break is often a 4 mm gap between two tangent panels rather than
# a crease, so a seam is evidence that the light breaks there even when the surface does not turn —
# but it does not make a G1 "satisfied", because a gap is a break, not a transition.
SEAM_OF = {
    ("HOOD", "FRONT_FENDER_TOP"): "HOOD_to_FRONT_BODY",
    ("FRONT_FENDER_SIDE", "DOOR_UPPER"): "FRONT_FENDER_to_DOOR",
    ("DOOR_UPPER", "ROCKER"): "ROCKER_to_UPPER_BODY",
    ("DOOR_UPPER", "REAR_HAUNCH_TOP"): "DOOR_SHUT_REAR",
    ("REAR_DECK", "ENGINE_COVER"): "ENGINE_COVER_to_DECK",
    ("ENGINE_COVER", "REAR_FASCIA"): "REAR_FASCIA_to_DECK",
    ("REAR_FASCIA", "DIFFUSER"): "DIFFUSER_to_FASCIA",
    ("REAR_HAUNCH_SIDE", "DIFFUSER"): "DIFFUSER_to_FASCIA",
}

# Which transition each measured line answers, so the coverage table can say so.
LINE_OF = {
    "DOOR_UPPER -> DOOR_CHANNEL (the side lip)": ("DOOR_UPPER", "DOOR_CHANNEL"),
    "REAR_FASCIA -> DIFFUSER (undercut edge)": ("REAR_FASCIA", "DIFFUSER"),
    "DOOR_UPPER -> ROCKER (sill line)": ("DOOR_UPPER", "ROCKER"),
    "REAR_HAUNCH_TOP -> REAR_HAUNCH_SIDE": ("REAR_HAUNCH_TOP", "REAR_HAUNCH_SIDE"),
    "FRONT_FENDER_TOP -> FRONT_FENDER_SIDE (crest)": ("FRONT_FENDER_TOP", "FRONT_FENDER_SIDE"),
}

# Transitions whose break is a HOLE. An opening is a physical break in the surface and the light
# stops at it, so it is evidence of the same standing as a panel gap -- and saying "no line defined"
# about the mouth of an intake would be reporting a missing feature that is not missing. Each entry
# names the object or table in the build that makes the hole, so the claim can be checked.
OPENING_OF = {
    ("NOSE", "FRONT_LOWER_INTAKE"): ("NOSE_MOUTH", "boolean in statev_master_volumes"),
    ("HOOD", "HEADLIGHT_SURROUND"): ("HEADLIGHT_SURROUND_L", "slot cut by stage03_elements"),
    ("DOOR_CHANNEL", "SIDE_INTAKE_MOUTH"): ("INTAKE_BLADE_L", "mouth cut by stage03_elements"),
}

UNMEASURED = ["NOSE -> HOOD", "HOOD -> HEADLIGHT_SURROUND", "NOSE -> FRONT_LOWER_INTAKE",
              "DOOR_CHANNEL -> SIDE_INTAKE_MOUTH", "REAR_HAUNCH_TOP -> BUTTRESS",
              "BUTTRESS -> REAR_DECK", "REAR_DECK -> ENGINE_COVER",
              "ENGINE_COVER -> REAR_FASCIA", "REAR_HAUNCH_SIDE -> DIFFUSER",
              "FRONT_FENDER_SIDE -> DOOR_UPPER", "DOOR_UPPER -> REAR_HAUNCH_TOP"]


def seam_offsets():
    """How far each registered panel seam sits off the built skin, in mm.

    Until 2026-09-21 these were nine hand-typed polylines from 2026-09-14 and nothing had ever
    compared them with the car: they were off it by 25 to 152 mm on average, 210 at worst. They are
    now generated from their plane and snapped onto the built surface, so this should read 0 — and
    the point of measuring it anyway is that if it ever stops reading 0, the generator broke.
    """
    from mathutils.bvhtree import BVHTree
    bm = body_bm()
    tree = BVHTree.FromBMesh(bm)
    out = {}
    for ob in bpy.data.objects:
        if not ob.name.startswith("SEAM_") or ob.type != "CURVE":
            continue
        nm = ob.name[5:].rsplit("_", 1)[0]
        for spl in ob.data.splines:
            for p in spl.points:
                co = ob.matrix_world @ mathutils.Vector(p.co[:3])
                h = tree.find_nearest(co)
                if h[0] is not None:
                    d = (h[0] - co).length * 1000.0
                    out[nm] = max(out.get(nm, 0.0), d)
    bm.free()
    return out


def body_bm():
    bm = bmesh.new()
    for n in BODY:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        me = o.to_mesh()
        try:
            bm.from_mesh(me)
        finally:
            o.to_mesh_clear()
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    return bm


def edges_index(bm):
    """Lengthwise edges on the left side, as (spec_x, z, dihedral_deg), bucketed by spec_x."""
    buckets = {}
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        a, b = e.verts[0].co, e.verts[1].co
        d = b - a
        if d.length < 1e-9:
            continue
        # lengthwise: the edge runs mostly along the car, so the light crosses it top-to-bottom
        if abs(d.x) < 0.55 * d.length:
            continue
        m = (a + b) / 2.0
        if m.y <= 0.0:
            continue
        # BOTH faces must belong to the OUTER SKIN. The first run reported
        # REAR_HAUNCH_TOP -> REAR_HAUNCH_SIDE at a median of 90 degrees and a maximum of 124 on five
        # samples, and the reason was not the haunch: FLANK_Z_HI is 660 and the rear arch cut, a
        # 350 mm cylinder on the axle, crowns at about the same height, so what was measured was the
        # vertical wall of the wheel opening.
        #
        # The obvious filter -- require both faces to carry Y in their normal -- was tried and is
        # WRONG: at the front fender crest the surface is turning over the top, both faces point
        # mostly up, and it threw away seven of nine samples, then reported a median of 7.3 degrees
        # off the two that survived and called the crest too soft. A two-sample median is not a
        # measurement.
        # The test that separates the two cases is RADIAL: skin faces point away from the body's own
        # axis, and a cut wall points along the cut. r is the outward direction at the edge, taken
        # from the axis at mid-height.
        r = mathutils.Vector((0.0, m.y, m.z - 0.570))
        if r.length < 1e-6:
            continue
        r.normalize()
        # Two faces that BOTH face up cannot be a cut wall -- cut walls are near vertical -- so a
        # crest between them is skin whatever the radial test says. Added 2026-09-26, when the
        # front crest gained a valley inboard of it: the valley-side face points up and slightly
        # inboard, its radial dot came out at 0.05, and the whole crest vanished from this test
        # (0.5 degrees measured against 67.8 in the profile). A filter built for arch walls was
        # rejecting the hood.
        both_up = all(f.normal.normalized().z > 0.30 for f in e.link_faces)
        if not both_up and min(f.normal.normalized().dot(r) for f in e.link_faces) < 0.20:
            continue

        sx, z = -m.x * 1000.0, m.z * 1000.0
        try:
            ang = math.degrees(e.calc_face_angle())
        except ValueError:
            continue
        buckets.setdefault(int(sx // 50), []).append((sx, z, ang, m.y * 1000.0))
    return buckets


def at(buckets, sx, z):
    """The hardest lengthwise edge within 16 mm of this height at this station."""
    cand = []
    for k in (int(sx // 50) - 1, int(sx // 50), int(sx // 50) + 1):
        for s, zz, ang, y in buckets.get(k, []):
            if abs(s - sx) <= 45.0 and abs(zz - z) <= 16.0:
                cand.append((ang, y))
    if not cand:
        return None
    return max(a for a, _ in cand)


def design_angle(M, sx, z):
    """The turn the DESIGN puts on this line, read before the section is resampled.

    WHY THIS COLUMN EXISTS. Everything else in this file is a dihedral on the built mesh, and on
    2026-09-21 a 2x2 showed what that is worth on its own: the rocker line reads 12.2 degrees with
    an arc-length resample and 47.7 with feature anchors, for the SAME design. Its field is a 34 mm
    tuck over a 10 mm transition, and a sample every 38 mm cannot show a 10 mm transition. The mesh
    number was not wrong, it was answering a different question -- what the surface SHOWS, not what
    it HAS -- and I read it as the second for two days.

    Both matter, and they matter for different reasons. The design angle is the intent. The mesh
    angle is what gets printed, because the core is the mesh: a crease the mesh cannot render is a
    crease the laminated panel will not have. The gap between them is representation loss, and it is
    a number worth seeing rather than discovering later on a part.

    Measured on the profile as it stands BEFORE resample(), which runs at PROFILE_STEP -- 6 mm
    against the mesh's 38 -- so it sees transitions the mesh cannot.
    """
    captured = {}
    orig = M["resample_anchored"]

    def spy(poly, n, anch):
        captured["poly"] = list(poly)
        return orig(poly, n, anch)

    M["resample_anchored"] = spy
    try:
        M["ring"](sx)
    finally:
        M["resample_anchored"] = orig
    poly = captured.get("poly")
    if not poly:
        return None
    best = 0.0
    for i in range(1, len(poly) - 1):
        if abs(poly[i][1] - z) > 16.0:
            continue
        p0, p1, p2 = poly[i - 1], poly[i], poly[i + 1]
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        n1 = math.hypot(*v1)
        n2 = math.hypot(*v2)
        if n1 < 1e-9 or n2 < 1e-9:
            continue
        c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        best = max(best, math.degrees(math.acos(c)))
    return best


def main():
    M = load()
    bm = body_bm()
    idx = edges_index(bm)
    rows, txt = [], []
    txt.append("=" * 100)
    txt.append("EDGE TEST — docs/16's CONTINUITY classes, as dihedral angles on the built mesh")
    txt.append("=" * 100)
    txt.append("")
    txt.append("  G0 wants 40-110 deg (a break), G1 wants 8-40 (a transition), G2 wants under 9")
    txt.append("  (the main surfaces stay soft -- chasing G2 everywhere is what makes CAD soap,")
    txt.append("  and a crease where the map says G2 is the same defect inverted).")
    txt.append("")
    txt.append(f"  {'line':44s} {'cls':4s} {'n':>3s} {'mesh':>7s} {'design':>8s} {'lost':>7s}  verdict")
    worst = []
    for name, cls, zfn, (x0, x1) in lines(M):
        vals, dvals = [], []
        n = max(6, int((x1 - x0) / 120.0))
        for i in range(n + 1):
            sx = x0 + (x1 - x0) * i / n
            a = at(idx, sx, zfn(sx))
            if a is not None:
                vals.append(a)
            d = design_angle(M, sx, zfn(sx))
            if d is not None:
                dvals.append(d)
        if not vals:
            txt.append(f"  {name:44s} {cls:4s}   -       -      -      -  NO EDGE FOUND")
            worst.append((name, cls, None))
            continue
        vals.sort()
        med = vals[len(vals) // 2]
        if len(vals) < 4:
            # A median of two or three samples is not a measurement. The first version of this file
            # reported one and it was wrong; saying so is the only correct output here.
            txt.append(f"  {name:44s} {cls:4s} {len(vals):3d} {med:7.1f} {'--':>8s} {'--':>7s}"
                       f"  TOO FEW SAMPLES — no verdict")
            worst.append((name, cls, None))
            continue
        lo, hi = BAND[cls]
        if lo <= med <= hi:
            v = "ok"
        elif name in EXCEPTIONS:
            v = "out of band — RECORDED exception"
        elif med < lo:
            v = "TOO SOFT — the light does not break here"
        else:
            v = "TOO SHARP — a crease where the map wants a surface"
        dvals.sort()
        dmed = dvals[len(dvals) // 2] if dvals else 0.0
        loss = dmed - med
        txt.append(f"  {name:44s} {cls:4s} {len(vals):3d} {med:7.1f} {dmed:8.1f} {loss:7.1f}  {v}")
        rows.append((name, cls, med, v, dmed))
        if v != "ok":
            worst.append((name, cls, med))
    txt.append("")
    ok = sum(1 for r in rows if r[3] == "ok")
    exc = sum(1 for r in rows if r[3].startswith("out of band"))
    bad = sum(1 for r in rows if r[3].startswith("TOO"))
    txt.append(f"  LINES IN BAND {ok} / RECORDED EXCEPTION {exc} / DEFECT {bad}"
               f"  (of {len(lines(M))} measured)")
    if exc:
        txt.append("")
        for r in rows:
            if r[3].startswith("out of band"):
                txt.append(f"  {r[0]} — {EXCEPTIONS[r[0]]}")
    # ---- coverage of the whole map, so no transition leaves the report without a row
    txt.append("")
    txt.append("  " + "-" * 96)
    txt.append("  COVERAGE — every transition in CONTINUITY, and what evidence exists for it")
    txt.append("  " + "-" * 96)
    txt.append("")
    seam_off = seam_offsets()
    by_line = {LINE_OF[r[0]]: r for r in rows if r[0] in LINE_OF}
    txt.append(f"  {'transition':38s} {'cls':4s} {'crease':>17s}  {'break made by':44s}")
    cov = 0
    for (a, b), cls in sorted(M["CONTINUITY"].items()):
        r = by_line.get((a, b))
        crease = f"{r[2]:.1f} deg {('ok' if r[3] == 'ok' else '!')}" if r else "no line defined"
        sm = SEAM_OF.get((a, b))
        op = OPENING_OF.get((a, b))
        if sm is None and op is None:
            ev = "nothing"
        elif sm is not None:
            ev = (f"seam {sm} ({seam_off[sm]:.2f} mm off skin)" if sm in seam_off
                  else f"seam {sm} (NOT IN SCENE)")
        else:
            ev = (f"opening {op[0]}" if bpy.data.objects.get(op[0]) or op[1].startswith("boolean")
                  else f"opening {op[0]} (NOT IN SCENE)")
        if r or sm or op:
            cov += 1
        txt.append(f"  {a + ' -> ' + b:38s} {cls:4s} {crease:>17s}  {ev:44s}")
    txt.append("")
    txt.append(f"  {cov} of {len(M['CONTINUITY'])} transitions have evidence: a measured crease, a "
               f"registered panel seam, or a real opening.")
    txt.append("  A seam is not a substitute for a class. The class is about the SURFACE; the seam is")
    txt.append("  about PANELS. On a real car a G0 break is often a 4 mm gap between two tangent")
    txt.append("  panels rather than a crease, so a seam is evidence that the light breaks — but it")
    txt.append("  never makes a G1 'satisfied', because a gap is a break and not a transition.")
    txt.append("")
    txt.append("  NO CREASE LINE — the build defines no height table for these, so the angle is")
    txt.append("  not measurable. The coverage table above says whether anything else breaks the")
    txt.append("  light there; several are satisfied by a panel gap or a real opening instead.")
    for u in UNMEASURED:
        txt.append(f"    {u}")
    txt.append("")
    txt.append("  'lost' is design minus mesh: how much of the designed turn the built mesh fails to")
    txt.append("  show. A NEGATIVE value is not a bonus -- it is faceting. A gentle line sampled every")
    txt.append("  38 mm becomes a few flat panels, and the dihedral between two of them can exceed the")
    txt.append("  smooth turn it is approximating. The main side line reads 15.9 on the mesh against")
    txt.append("  6.5 in the design for exactly that reason.")
    txt.append("")
    txt.append("  It measures only the lines it is told about, and it says nothing about whether a")
    txt.append("  line is in the right PLACE — only how hard it breaks.")
    out = "\n".join(txt)
    print(out)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "edge_test.txt"), "w") as f:
        f.write(out + "\n")
    print(f"\n  wrote {os.path.join(OUT, 'edge_test.txt')}")
    bm.free()
    return ok, len(rows)


main()
