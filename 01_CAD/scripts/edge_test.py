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
    "DOOR_UPPER -> ROCKER (sill line)":
        "sharpened on purpose, 55 -> 18 -> 10 mm of transition on 2026-09-15/16, because the sill "
        "read as a soft hollow with no line at all. docs/16 classes it G1 and it measures ~47, so it "
        "is 7 degrees past a band this file invented -- docs/16 gives the CLASS, not the number. "
        "The honest reading is that a sill line on this kind of car is at the hard end of G1. "
        "OWNER'S CALL, not settled: either the band is too tight here or the tuck transition goes "
        "back to ~18 mm.",
}


def load():
    src = open(SRC).read().split("\ndef build():")[0]
    M = {"__name__": "mv"}
    exec(compile(src, SRC, "exec"), M)
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
         lambda x: M["FLANK_Z_HI"], (M["FLANK_X0"] + 300, M["FLANK_X1"] - 300)),
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


UNMEASURED = ["NOSE -> HOOD", "HOOD -> FRONT_FENDER_TOP (G2, across the top)",
              "HOOD -> HEADLIGHT_SURROUND", "NOSE -> FRONT_LOWER_INTAKE",
              "DOOR_CHANNEL -> SIDE_INTAKE_MOUTH", "REAR_HAUNCH_TOP -> BUTTRESS",
              "BUTTRESS -> REAR_DECK", "REAR_DECK -> ENGINE_COVER",
              "ENGINE_COVER -> REAR_FASCIA", "REAR_HAUNCH_SIDE -> DIFFUSER",
              "FRONT_FENDER_SIDE -> DOOR_UPPER", "DOOR_UPPER -> REAR_HAUNCH_TOP"]


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
        if min(f.normal.normalized().dot(r) for f in e.link_faces) < 0.20:
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
    txt.append(f"  {'line':44s} {'cls':4s} {'n':>3s} {'median':>7s} {'min':>6s} {'max':>6s}  verdict")
    worst = []
    for name, cls, zfn, (x0, x1) in lines(M):
        vals = []
        n = max(6, int((x1 - x0) / 120.0))
        for i in range(n + 1):
            sx = x0 + (x1 - x0) * i / n
            a = at(idx, sx, zfn(sx))
            if a is not None:
                vals.append(a)
        if not vals:
            txt.append(f"  {name:44s} {cls:4s}   -       -      -      -  NO EDGE FOUND")
            worst.append((name, cls, None))
            continue
        vals.sort()
        med = vals[len(vals) // 2]
        if len(vals) < 4:
            # A median of two or three samples is not a measurement. The first version of this file
            # reported one and it was wrong; saying so is the only correct output here.
            txt.append(f"  {name:44s} {cls:4s} {len(vals):3d} {med:7.1f} {vals[0]:6.1f} "
                       f"{vals[-1]:6.1f}  TOO FEW SAMPLES — no verdict")
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
        txt.append(f"  {name:44s} {cls:4s} {len(vals):3d} {med:7.1f} {vals[0]:6.1f} {vals[-1]:6.1f}"
                   f"  {v}")
        rows.append((name, cls, med, v))
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
    txt.append("")
    txt.append("  NOT MEASURED — in CONTINUITY but with no line the build defines a height for:")
    for u in UNMEASURED:
        txt.append(f"    {u}")
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
