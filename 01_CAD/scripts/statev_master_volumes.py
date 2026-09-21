"""
statev_master_volumes.py — STAGE 01: the master exterior volumes.

Supersedes statev_preview_loft.py. That one was a single global loft through every section, which
is the thing the surface specification forbids; it existed only to judge proportion and it failed
its own highlight test because the car's three negative-space regions did not exist in it.

This builds the DESIGN MASTER: the large volumes, with the voids cut as real geometry, split into
per-zone objects that can be adjusted independently. It is NOT production geometry — no seams, no
thickness, no flanges, no fasteners. Class-A surfacing remains manual work on top of this.

What it does:
  1. skin lofted from the master sections, crowned by HOOD_SPINE at the front and DECK_SPINE behind
  2. per-zone shaping so the front, the door and the haunch do not share one character
  3. FIVE void families cut as booleans — the whole point of this stage:
       cabin aperture, wheel arches, fender channels, door channel into the side intake,
       rear lower undercut
  4. buttresses as separate masses around the roof envelope
  5. split into STATEV_FRONT / STATEV_SIDE / STATEV_REAR

Donor hardpoints are read, never written. Nothing here moves a wheel, the screen or a shut line.
"""

import bpy
import mathutils
import bmesh
import math
import os
import time

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "01_CAD", "scripts") \
    if "__file__" in globals() else "/Users/miroslavstatev/vehicle-3d-modeling/01_CAD/scripts"
REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else os.path.join(REPO, "01_CAD/scripts")
_sk = {}
with open(os.path.join(_here, "statev_skeleton.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("\ndef build():")[0], _sk)
SECTIONS, PFX = _sk["SECTIONS"], _sk["PFX"]
PANEL_SEAMS = _sk["PANEL_SEAMS"]
HOOD_SPINE, DECK_SPINE, ARCHES = _sk["HOOD_SPINE"], _sk["DECK_SPINE"], _sk["ARCHES"]
widening, sx, mm, half_width_at = _sk["widening"], _sk["sx"], _sk["mm"], _sk["half_width_at"]
D = _sk["donor_dims"]()

ROOT = "STATEV_MASTER"
ZONES = {"STATEV_FRONT": (-1000, 340), "STATEV_SIDE": (340, 1900), "STATEV_REAR": (1900, 3500)}

MAX_HALF_WIDTH = 925.0    # 1850 overall. A soft cap: only the widest band near the rear axle is
                          # touched, so the shoulder line everywhere else is left alone.
PROFILE_STEP = 6.0   # mm between Z samples of the section BEFORE the character fields are applied
N_HALF = 60
SUBDIV = 6        # sub-stations between master sections; 6 gives ~85 rings over the car
CROWN_FACTOR = 0.10

# ---- negative spaces as CONTINUOUS FIELDS, not boolean station cuts.
#
# Every one of these used to be a lofted cutter driven through a boolean. That produced a hard edge
# wherever the cutter met the skin, a depth that jumped from station to station, and — four times
# running on the door — no depth at all through the middle while the boolean reported success.
# They are now part of the section profile, the same way the rear buttress was fixed: the surface
# is built with the void already in it, so there is nothing to subtract and nothing to fail.
#
# Each field is a super-gaussian in Z riding on a centre line, times a longitudinal envelope that
# runs in from x0, peaks at xp and releases to x1. The exponent n > 2 gives a flat-bottomed channel
# with defined shoulders rather than a round dent, and the whole thing stays C1 continuous in both
# directions: smoothstep has zero slope at each end, so there is no station-to-station step anywhere.
# w and n together decide whether it reads as a channel or a dent. At w 84 / n 2.4 the skirt of the
# gaussian was still 50 mm deep 70 mm out from the centre, so the channel ate its own shoulders and
# measured half its designed depth. w 64 / n 3.0 holds full depth to +-30 and is down to a quarter
# of it by +-70: about 180 mm of visible channel with an edge at each side.
VOID_FIELDS = {
    # ONE line from behind the front wheel to the intake mouth, not two channels that meet.
    # Measured as two separate fields they left an 18 mm slack water at specX 550 where the front
    # one was releasing and the door one had not built. A side line that dies and restarts halfway
    # along the door is worse than no side line, so it is a single field with a depth that varies
    # along its length: shallow as it leaves the arch, deepest right behind it, easing through the
    # door, gathering again into the intake.
    # It starts at the TRAILING EDGE OF THE FRONT ARCH, not over the wheel. The front arch is a
    # 350 mm cylinder on the axle, so at specX 330 it has already removed everything below Z 440 —
    # the channel's own lower shoulder. Asking for depth there produced a number the surface could
    # not show: the line simply merged into the arch opening. It now emerges from behind it.
    "SIDE_CHANNEL": dict(depth=[(340, 70), (520, 132), (800, 116), (1200, 108),
                                (1600, 108), (1900, 114), (2240, 120)],
                         x0=340.0, xa=480.0, xb=1900.0, x1=2240.0, w=64.0, n=3.0,
                         centre=[(340, 500), (620, 512), (800, 524),
                                 (1200, 536), (1600, 548), (2240, 560)]),
    # the intake mouth the side line runs into. Ahead of the rear wheel, as the donor requires.
    "SIDE_INTAKE": dict(depth=124.0, x0=1780.0, xa=1940.0, xb=2110.0, x1=2300.0, w=72.0, n=2.8,
                        centre=[(1780, 554), (2070, 536), (2300, 518)]),
}
# STAGE 02 FINDING, 2026-09-15. docs/16 CONTINUITY lists REAR_FASCIA -> DIFFUSER as one of only
# two G0 transitions on the car, meaning a crease rather than a blend. The built edge turns 2.6 to
# 3.4 degrees, which is no crease at all. Narrowing `trans` from 72 to 18 was tried and produced
# geometry IDENTICAL to 72, to the vertex: at 60 points per half-section the resample cannot
# resolve a transition that narrow, so this parameter is inert at the current resolution. A G0
# crease here needs explicit control points, the way the buttress crest needed them — which is
# Stage 03 work on a surface that does not exist yet, not a number change.
# trans 72 -> 24 on 2026-09-18. The note above is still true of v029: at 60 arc-length samples
# the resample could not resolve this transition and 18 gave geometry identical to 72, so the
# parameter was inert. feature_anchors() now pins a sample on edge and on edge-trans at every
# station, which is the "explicit control points" the note asked for, so it is live again.
REAR_UNDERCUT_FIELD = dict(depth=108.0, x0=2260.0, xa=2560.0, xb=2950.0, x1=3400.0, trans=24.0,
                           edge=[(2260, 322), (2960, 336), (3400, 300)])

NOSE_MOUTH = [(-965, 0, 200, 330), (-930, 155, 185, 345), (-850, 215, 180, 350),
              (-770, 195, 185, 342), (-700, 95, 200, 325), (-655, 0, 215, 310)]

# The blade itself: thin the nose above the mouth so the upper line reads sharp, not blunt.
NOSE_BLADE_X0, NOSE_BLADE_X1 = -965.0, -640.0
NOSE_BLADE_Z = 350.0        # everything above this at the nose is drawn in
NOSE_BLADE_THIN = 46.0      # mm taken off the half-width at the top of the blade

CABIN_Y, CABIN_Z = 700, 640

# Beltline. The A-pillar measured 217 mm below the screen base while the rear of the cabin was at
# 139 — the line was not just low, it wandered. The cause was visible in the section: at specX 440
# the body tucked in at Z 732 and from there ran as one long straight cone to the crown at 970, so
# there was no door top at all. BELT_LIFT added a point inboard of the cabin cut, which the cut then
# removed. Lifting the whole cabin would have hidden that rather than fixed it.
#
# What is built now is the door top itself: through the cabin the flank is held near vertical up to
# a DESIGNED height, and the section turns in only there. BELT_Z is that height — one continuous
# line from the A-pillar, dipping gently through the door, rising to meet DECK_SPINE at the hoop
# plane, so cowl -> A-pillar -> door -> deck is a single move.
#
# The gap to the 970 screen base lands at 86 at the A-pillar and around 118 in the middle of the
# door. 115 mm was a guide, not a target: a gap that VARIES smoothly is what reads as designed,
# and forcing one number everywhere would have flattened the cabin.
# The belt shelf starts well AHEAD of the screen base and ramps in over 155 mm. Two reasons, and
# the second is the design one. Mechanically, the rings are smoothed along X over roughly +-100 mm
# before the mesh is built, so a shelf that appears abruptly at the screen base is averaged away
# with the cowl in front of it — at 420 the door top came out 40 mm low however high BELT_Z asked
# for. Architecturally, the top of the front fender and the top of the door are the same line: it
# should arrive at the A-pillar already at belt height, not step up to it. The cabin APERTURE is
# untouched at specX 420 — this moves our surface, not the donor opening.
CABIN_X0, CABIN_X1 = 340.0, 1780.0
CABIN_RAMP = 110.0
# The first two entries are the A-pillar foot, not the door. v017 let table_z clamp forward of
# specX 420, so the shelf asked for 880 all the way back to where it started and carried the front
# fender top up with it — 678 to 839 at specX 350, a 161 mm rise nobody approved. Giving the line an
# explicit, low value at 345 lets the shelf ramp in without lifting the fender: measured over five
# parameter tests, X0 340 / ramp 110 with these two entries puts the fender top at 764 instead of
# 839 while the door top only falls 15 mm. Below about 755 at 345 the value stops doing anything —
# the shelf drops under the section's own profile and cabin_flank has nothing left to pull.
BELT_Z = [(345, 755), (420, 912), (560, 838), (800, 859), (1000, 853), (1200, 850),
          (1400, 853), (1600, 861), (1780, 872)]
CABIN_FLANK_LO = 470.0      # from just above the rocker up to BELT_Z the door side is near vertical
CABIN_FLANK_PULL = 0.92

# Lowered from z_hi 1090 to 985 and widened 210 -> 300, starting 160 mm further forward. At 1090
# they read as two towers competing with the roll hoops. The hoops themselves are donor structure at
# Z 1235 and cannot move — making them read lighter means lowering OUR volume around them, not theirs.
# The blade now RIDES on the deck spine instead of having its own floor and ceiling. Its base is
# the deck line at that station and its height is a gaussian on the rear axle, so it grows out of
# the haunch, peaks over the wheel and releases into the deck with nothing left to step off.
# Ending it at 2640 with a fixed z_lo is what produced the 201 mm crown step at specX 2800.
# 6. The front fender crest. Added 2026-09-16 from the overlay against ref-05, which measured the
# body 17 to 147 mm below the render across the whole front, worst at spec X -300 to 0.
#
# It is a FIELD and not a section point, and the failed attempt is worth keeping: raising the top of
# S03 to S06 in statev_skeleton does not reach the surface, because section_profile blends two
# sections on the union of their Z levels and keeps only levels BOTH define, so a crest at Z 874 in
# S04 is discarded against S03, which stops at 774. Measured 68 mm short at its own station.
#
# `z` is read straight off the reference's own silhouette at the overlay's calibration -- 2.8753
# mm/px from the wheelbase, independently confirmed by the render's windscreen base landing on 969
# against the donor's published cowl at 970. `y` is a design call: the crest sits outboard so the
# hood can stay sunk between the fenders, which is what "layered panels, floating fenders" means.
# `out` and `drop` give the crest a steep approach instead of a single point, the same fix the deck
# edge needed on 2026-09-15 -- one control point gets averaged away by resample.
FRONT_CREST = dict(
    z=[(-950, 530), (-850, 584), (-700, 650), (-500, 774), (-350, 849), (-250, 874),
       (-150, 892), (0, 903), (150, 906), (300, 909), (430, 935)],
    y=[(-950, 170), (-850, 330), (-700, 470), (-500, 560), (-250, 590), (0, 600),
       (300, 585), (430, 560)],
    out=26.0, drop=30.0)

BUTTRESS = dict(x0=1740, x1=3200, y=620, w=300, height=152)   # starts at the hoop plane,
                                                              # outboard of the cabin cut


def section_profile(spec_x):
    items = sorted(((v[0], v[2]) for v in SECTIONS.values()), key=lambda t: t[0])
    xs = [i[0] for i in items]
    if spec_x <= xs[0]:
        base = items[0][1]
    elif spec_x >= xs[-1]:
        base = items[-1][1]
    else:
        base = None
        for i in range(len(xs) - 1):
            if xs[i] <= spec_x <= xs[i + 1]:
                t = (spec_x - xs[i]) / (xs[i + 1] - xs[i])
                a, b = items[i][1], items[i + 1][1]
                zs = sorted({z for z, _ in a} | {z for z, _ in b})
                base = []
                for z in zs:
                    ya, yb = half_width_at(a, z), half_width_at(b, z)
                    if ya is not None and yb is not None:
                        base.append((z, ya + t * (yb - ya)))
                break
    return [(z, y + widening(spec_x, z)) for z, y in base]


def spine_z(table, spec_x):
    xs = [t[0] for t in table]
    if not (xs[0] <= spec_x <= xs[-1]):
        return None
    for i in range(len(table) - 1):
        (x0, z0), (x1, z1) = table[i], table[i + 1]
        if x0 <= spec_x <= x1:
            f = 0.0 if x1 == x0 else (spec_x - x0) / (x1 - x0)
            return z0 + f * (z1 - z0)
    return table[-1][1]


def resample(poly, n):
    d = [0.0]
    for i in range(1, len(poly)):
        d.append(d[-1] + math.dist(poly[i - 1], poly[i]))
    total, out = d[-1], []
    for i in range(n):
        t = total * i / (n - 1)
        for j in range(len(d) - 1):
            if d[j] <= t <= d[j + 1]:
                f = 0.0 if d[j + 1] == d[j] else (t - d[j]) / (d[j + 1] - d[j])
                out.append((poly[j][0] + f * (poly[j + 1][0] - poly[j][0]),
                            poly[j][1] + f * (poly[j + 1][1] - poly[j][1])))
                break
        else:
            out.append(poly[-1])

    # Keep the corners. resample places n points by arc length, so a vertex that is a crest gets
    # straddled by two samples and the crest itself is never in the output -- the front fender
    # crests added on 2026-09-16 arrived 68 mm short at their own station because of this, and the
    # deck edge needed two control points a day earlier for the same reason. Any input vertex that
    # is a strict local maximum in z is snapped onto the nearest output sample, so a crest survives
    # sampling instead of being averaged away.
    for i in range(1, len(poly) - 1):
        if poly[i][1] > poly[i - 1][1] and poly[i][1] > poly[i + 1][1]:
            j = min(range(len(out)), key=lambda k: math.dist(out[k], poly[i]))
            out[j] = poly[i]
    return out


# ---------------------------------------------------------------- feature anchors (v030)
# WHY. Measured at specX 1200 on v029, the section carries 794 degrees of total turning and the
# 60-point resample delivers 524 of it -- a third of the character is thrown away by the sampling,
# and the largest single corner falls from 86.8 to 46.4 degrees. Worse, of the turning that does
# survive only two places are corners (the floor at Z 120 and the rocker edge at Z 315); the door
# channel, its upper edge and the shoulder above it are rolls of 4 to 13 degrees per step spread
# over 70 to 90 mm. docs/16 lists DOOR_UPPER -> DOOR_CHANNEL and REAR_FASCIA -> DIFFUSER as G0,
# meaning a crease. A 12-degree roll is not a crease.
#
# The note left in VOID_FIELDS on 2026-09-15 had the diagnosis right -- "a G0 crease here needs
# explicit control points ... at 60 points per half-section the resample cannot resolve a
# transition that narrow" -- and deferred it to a surface that did not exist yet. It exists now.
#
# So every station pins a sample exactly on each named longitudinal line. The count is FIXED (ten)
# and every level comes from table_z of a table that is continuous in X, so an anchor never appears
# or disappears between neighbouring stations. That is the constraint the buttress inner edge broke
# on 2026-09-15: a guard that switches on and off between stations destroys the point
# correspondence build() relies on when it smooths along X.
LIP_TRANS = 18.0     # mm of height over which the channel's upper edge closes. At specX 1200 the
                     # super-gaussian still carries 63 mm of depth 12 mm below the lip, so closing
                     # it over 18 gives a 74-degree face: a crease that a 3 mm laminate can still
                     # follow. 12 was tried and reads as an undercut rather than an edge.


def feature_anchors(spec_x):
    """Z levels that MUST carry a sample. Fixed count, every one from a table continuous in X."""
    ch = VOID_FIELDS["SIDE_CHANNEL"]
    c = table_z(ch["centre"], spec_x)
    lip = side_lip(spec_x)
    u = REAR_UNDERCUT_FIELD
    ez = table_z(u["edge"], spec_x)
    return [c - ch["w"],            # channel lower shoulder
            c,                      # channel floor
            lip - LIP_TRANS,        # steep approach to the lip
            lip,                    # THE LIP -- docs/16 G0
            ROCKER_EDGE_Z - 10.0,   # rocker approach
            ROCKER_EDGE_Z,          # rocker edge
            ez - u["trans"],        # undercut approach
            ez,                     # undercut edge -- docs/16 G0
            table_z(SHOULDER_TRAJECTORY, spec_x),   # the one main side line
            FLANK_Z_HI]             # top of the near-vertical rear flank


def resample_anchored(poly, n, anch):
    """resample(), but with samples pinned on the feature lines.

    The anchors are placed exactly and the remaining budget is spread over the intervals between
    them by arc length. Anchors outside the section's own Z range are clamped onto it rather than
    dropped, because dropping one would change the point count from station to station."""
    zs = [p[1] for p in poly]
    lo, hi = min(zs) + 2.0, max(zs) - 2.0
    if hi <= lo:
        return resample(poly, n)
    d = [0.0]
    for i in range(1, len(poly)):
        d.append(d[-1] + math.dist(poly[i - 1], poly[i]))
    total = d[-1]
    if total <= 0.0:
        return resample(poly, n)

    def at_s(t):
        for j in range(len(d) - 1):
            if d[j] <= t <= d[j + 1]:
                f = 0.0 if d[j + 1] == d[j] else (t - d[j]) / (d[j + 1] - d[j])
                return (poly[j][0] + f * (poly[j + 1][0] - poly[j][0]),
                        poly[j][1] + f * (poly[j + 1][1] - poly[j][1]))
        return poly[-1]

    def s_of_z(z):
        """arc position of the FIRST crossing of this height, walking up from the floor"""
        for j in range(len(poly) - 1):
            z0, z1 = poly[j][1], poly[j + 1][1]
            if (z0 - z) * (z1 - z) <= 0.0 and z0 != z1:
                f = (z - z0) / (z1 - z0)
                return d[j] + f * (d[j + 1] - d[j])
        return None

    ss = []
    for z in anch:
        s = s_of_z(min(hi, max(lo, z)))
        if s is not None:
            ss.append(s)
    ss.sort()
    # keep them apart, so two anchors never collapse onto one sample and change the count
    for i in range(1, len(ss)):
        if ss[i] - ss[i - 1] < 1.0:
            ss[i] = ss[i - 1] + 1.0
    ss = [s for s in ss if 1.0 < s < total - 1.0]
    k = len(ss)
    free = n - k - 2
    if free < k + 1:
        return resample(poly, n)
    bounds = [0.0] + ss + [total]
    seg = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
    L = sum(seg)
    # largest-remainder allocation: deterministic, and stable between neighbouring stations
    raw = [free * x / L for x in seg]
    take = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda j: raw[j] - take[j], reverse=True)[:free - sum(take)]:
        take[i] += 1
    out = [poly[0]]
    for i in range(len(seg)):
        for j in range(1, take[i] + 1):
            out.append(at_s(bounds[i] + seg[i] * j / (take[i] + 1)))
        if i < k:
            out.append(at_s(bounds[i + 1]))
    out.append(poly[-1])
    while len(out) > n:
        # drop the sample that is closest to its neighbour and is NOT an anchor
        best, bi = None, None
        for i in range(1, len(out) - 1):
            if any(abs(out[i][1] - min(hi, max(lo, z))) < 0.5 for z in anch):
                continue
            g = math.dist(out[i - 1], out[i]) + math.dist(out[i], out[i + 1])
            if best is None or g < best:
                best, bi = g, i
        if bi is None:
            break
        out.pop(bi)
    while len(out) < n:
        gi = max(range(1, len(out)), key=lambda i: math.dist(out[i - 1], out[i]))
        out.insert(gi, ((out[gi - 1][0] + out[gi][0]) / 2, (out[gi - 1][1] + out[gi][1]) / 2))
    return out


def smoothstep(a, b, x):
    if a == b:
        return 0.0 if x < a else 1.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)



# ---------------------------------------------------------------- character fields
# Five design elements, each a tunable field rather than hand-sculpted geometry, so a note like
# "the shoulder should rise 200 mm later" is a number change and not a remodel.

# 1. The one main side line: front fender -> door -> rear haunch. (spec_x, z) of its trajectory.
SHOULDER_TRAJECTORY = [(-950, 470), (-700, 505), (-250, 545), (0, 565), (350, 578),
                       (800, 592), (1200, 612), (1600, 648), (2000, 700), (2415, 735),
                       (2800, 712), (3200, 648), (3420, 600)]
SHOULDER_GAIN = 13.0      # mm of local width gained at the line
SHOULDER_W_BELOW = 42.0   # tight below: this is what makes it read as a crease, not a bulge
SHOULDER_W_ABOVE = 95.0   # soft release above

# 2. Tension over the front wheel: a shoulder that starts low ahead of it, peaks above it, releases
FENDER_GAIN = 52.0        # was 34: at the axle we read 745 half-width against the donor's 850
FENDER_X, FENDER_XW = -30.0, 380.0    # tighter, so it is a fender and not a general swelling
FENDER_Z, FENDER_ZW = 600.0, 180.0    # higher and taller, so there is body above the arch crown

# 3. The rocker as its own element: the body tucks in below a defined sill line between the arches
ROCKER_TUCK = 34.0        # mm the sill draws in
ROCKER_EDGE_Z = 315.0     # the sill line itself
ROCKER_X0, ROCKER_X1 = 330.0, 1820.0

# 2b. Rear flank. Every section was a smooth arc from floor to crown, so the haunch read as a bulge.
# In the reference the flank is near vertical between the shoulder and the undercut.
FLANK_X0, FLANK_X1 = 1900.0, 3050.0
FLANK_Z_LO, FLANK_Z_HI = 300.0, 660.0      # the band held near constant width
# 0.88 -> 0.95 on 2026-09-16. check_donor_fit measured the rear quarter with ONE millimetre of air
# over the donor's own skin at spec X 2107 -- our 883 against the donor's 882 -- and that panel is an
# OVERLAY, so it has to sit outside the OEM skin by the 15 to 20 mm CLAUDE.md requires, plus its own
# laminate. Pulling the flank harder onto the station maximum is width the locked 1850 already
# allows: the rear is +-925 at its widest and this band was sitting 42 mm inside that.
FLANK_PULL = 0.95                          # how strongly it is pulled to the station maximum
FLANK_EASE_TOP = 34.0                      # short: a crisp shoulder edge, not a roll
FLANK_SHOULDER = 16.0                      # extra mass in the shoulder just above the flank

# 2c. FRONT flank. The rear got this treatment on 2026-09-14 and the front never did, and the
# curvature measurement says so: by Z band, the front fender reads 0.47 / 0.49 / 0.40 / 0.54 / 0.23
# where the rear haunch reads 0.36 / 0.30 / 0.22 / 0.47 / 0.37 and the door channel gets down to
# 0.12. Worst is Z 660-800 at 0.54 -- the shoulder between the flank and the new crest, curving the
# same amount in every direction, which is the definition of the balloon docs/16 warns about.
# Same mechanism as the rear: hold the section near its station maximum through a Z band so the side
# runs flat along X and the curvature collects at the crest above and the tuck below.
FRONT_FLANK_X0, FRONT_FLANK_X1 = -700.0, 500.0
FRONT_FLANK_Z_LO, FRONT_FLANK_Z_HI = 480.0, 800.0
# Z_LO was tried at 380 as well and made the band below WORSE, 0.46 -> 0.56: the lower ramp then
# lands inside Z 330-500 and a ramp is itself curvature in two directions. Left at 480, where the
# ramp falls in a band that is already being held.
FRONT_FLANK_PULL = 0.82
FRONT_FLANK_EASE_TOP = 60.0

# 2d. HAUNCH SAIL — ATTEMPTED AND REVERTED 2026-09-21. Kept as a note so it is not tried again.
#
# The haunch is the worst zone on the car for curvature and the blame is in one band: Z 800-879
# reads 0.61 on 70 vertices, with 880-959 at 0.43 on 138, against 0.21 at the nose. That is the
# ramp between the top of the near-vertical flank at FLANK_Z_HI 660 and the deck edge, about 140 mm
# tall, with nothing holding a direction in it -- the same shape of defect the front fender had
# before front_flank().
#
# flank()'s cure does not apply: it pulls the section OUT toward the station maximum, and out is
# the wrong way here. The width is locked at 925, the section already carries 862 at Z 800, and the
# reference tucks this area IN above the shoulder toward the deck.
#
# So the band was made a RULED surface instead: the section straightened between the flank top and
# its own crown, which costs no width and should drive one principal curvature to zero. Measured
# A/B on the same base, strength the only difference:
#
#   strength   zone 1900-3050   Z 800-879   Z 880-959
#      0.0          0.29           0.61        0.43
#      0.5          0.31           0.73        0.36
#      0.8          0.33           0.77        0.19
#      1.0          0.28           0.70        0.31
#
# It moves the problem rather than solving it: the deck edge above improves sharply, the band itself
# gets WORSE, and the zone is a wash. Straightening a curve pins its ends and moves its middle, and
# the middle is not where the trouble is.
#
# The finding is the negative result. This band is not reachable by a field that acts on whole
# sections, which is what every character field in this file is. CLAUDE.md says it: the free-form
# surfaces are the owner's manual work in Blender and my job is to check and correct, not to
# pretend to sculpt class-A surfaces with primitives. The band is named precisely so the sculpting
# has a target: spec X 1900 to 3050, Z 800 to 880, on both sides.

# 7. PLAN WAIST. The first measurement of the plan puts us 57 to 73 mm of half-width too wide from
# 43 to 57% of the length -- spec X 930 to 1540, the middle of the door. The render has a waist
# there and we run straight. It is a plan correction only: it takes width out and leaves every Z
# alone, which is why the side silhouette is unchanged by it.
WAIST_X, WAIST_XW = 1235.0, 330.0
WAIST_DEPTH = 66.0

# 1b. Belt dip. Between the wheels the 986 reads visually compressed; my sections were flat there,
# which is the "flat platform" in the side view. This lowers the top of the body through the door.
# Dip moved back and made shallower. Starting it at 430 put it right under the cowl and turned the
# scuttle-to-door handover into a 208 mm cliff. It now starts at 940, well clear of the screen.
BELT_DIP_X0, BELT_DIP_PEAK, BELT_DIP_X1 = 940.0, 1280.0, 1740.0
BELT_DIP = 26.0

# 4. The tail drawn out instead of ending in a wall
TAIL_START, TAIL_END_X = 2800.0, 3420.0
TAIL_NARROW = 0.86        # half-width multiplier reached at the very tail
TAIL_DROP = 140.0         # mm the crown falls over the same run; the tail sits lower

# 5. Buttress crest (used in the blade loft): top width as a fraction of base
BUTTRESS_TOP_FRAC = 0.20

# 5b. Deck edge. The crest was ONE control point, so the 60-point resample rounded it and the deck
# read as a pillow: below it sat 200 mm of dead straight 45 degree ramp with nothing on it, and the
# corner itself measured only 26 degrees at specX 2000 and 2900. Two points make it a corner the
# resample cannot smooth away — a short steep approach, then the crest — which is what gives the
# top of the rear quarter a line for light to break on. Geometry, not a boolean, and it does not
# touch the crown: the centreline still closes at max(crown, b_top - 40) exactly as before.
DECK_EDGE_OUT = 12.0     # mm outboard of the crest where the approach starts
DECK_EDGE_DROP = 34.0    # mm below the crest at that point -> a 70 degree final approach

# STAGE 02, ATTEMPTED AND REVERTED 2026-09-15. docs/16 asks the buttress for TWO clear edges.
# Adding an inner one cost 13.9 mm of crown against a 1.2 mm tolerance, and raising the section
# resolution to 72, 84 and 96 points did not recover it, so it was not a sampling artefact.
#
# The measurement that explains it: b_top stands only 2 to 14 mm above the section's own top
# through the whole buttress range, and it oscillates station to station — 4.6, 11.7, 3.8, 13.6,
# 2.0, 10.8, 6.4. Any guard written on that headroom switches on and off between neighbouring
# stations, which breaks the point correspondence build() relies on when it smooths along X.
#
# The real finding is underneath that. What is built is not a buttress standing on a sunken deck;
# it is a 10 mm lip on the crown. It cannot be given two edges until the deck between the blades
# can drop, and DECK_SPINE is marked BLOCKED in docs/14 because its heights sit in the volume the
# soft top folds into. This waits for scan session S2, not for more modelling.


def table_z(table, spec_x):
    xs = [t[0] for t in table]
    if spec_x <= xs[0]:
        return table[0][1]
    if spec_x >= xs[-1]:
        return table[-1][1]
    for i in range(len(table) - 1):
        (x0, z0), (x1, z1) = table[i], table[i + 1]
        if x0 <= spec_x <= x1:
            f = (spec_x - x0) / (x1 - x0)
            return z0 + f * (z1 - z0)
    return table[-1][1]


def flank(spec_x, z, hw, hw_max):
    """Pull the profile toward the station's widest value across a Z band, which turns a rolling
    arc into a near-vertical flank. Returns the corrected half-width."""
    if not (FLANK_X0 <= spec_x <= FLANK_X1) or not (FLANK_Z_LO <= z <= FLANK_Z_HI):
        return hw
    ends = min(smoothstep(FLANK_X0, FLANK_X0 + 300, spec_x),
               1.0 - smoothstep(FLANK_X1 - 300, FLANK_X1, spec_x))
    inb = min(smoothstep(FLANK_Z_LO, FLANK_Z_LO + 70, z),
              1.0 - smoothstep(FLANK_Z_HI - FLANK_EASE_TOP, FLANK_Z_HI, z))
    k = FLANK_PULL * ends * inb
    return hw + (hw_max - hw) * k


def front_flank(spec_x, z, hw, hw_max):
    """The same pull as flank(), on the front. Kept as its own function rather than a second band
    inside flank() because FLANK_SHOULDER and the door-channel note both key off the rear band's
    own constants, and folding them together would change the rear while trying to fix the front."""
    if not (FRONT_FLANK_X0 <= spec_x <= FRONT_FLANK_X1):
        return hw
    if not (FRONT_FLANK_Z_LO <= z <= FRONT_FLANK_Z_HI):
        return hw
    ends = min(smoothstep(FRONT_FLANK_X0, FRONT_FLANK_X0 + 260, spec_x),
               1.0 - smoothstep(FRONT_FLANK_X1 - 260, FRONT_FLANK_X1, spec_x))
    inb = min(smoothstep(FRONT_FLANK_Z_LO, FRONT_FLANK_Z_LO + 70, z),
              1.0 - smoothstep(FRONT_FLANK_Z_HI - FRONT_FLANK_EASE_TOP, FRONT_FLANK_Z_HI, z))
    return hw + (hw_max - hw) * (FRONT_FLANK_PULL * ends * inb)


def character(spec_x, z):
    """Millimetres added to (or taken off) the half-width at this station and height."""
    add = 0.0
    # main side line
    zs = table_z(SHOULDER_TRAJECTORY, spec_x)
    w = SHOULDER_W_BELOW if z < zs else SHOULDER_W_ABOVE
    add += SHOULDER_GAIN * math.exp(-((z - zs) / w) ** 2)
    # front fender tension
    add += (FENDER_GAIN * math.exp(-((spec_x - FENDER_X) / FENDER_XW) ** 2)
            * math.exp(-((z - FENDER_Z) / FENDER_ZW) ** 2))
    # rear shoulder mass, sitting just above the vertical flank
    if FLANK_X0 <= spec_x <= FLANK_X1:
        ends = min(smoothstep(FLANK_X0, FLANK_X0 + 300, spec_x),
                   1.0 - smoothstep(FLANK_X1 - 300, FLANK_X1, spec_x))
        add += FLANK_SHOULDER * ends * math.exp(-((z - (FLANK_Z_HI + 40)) / 85.0) ** 2)
    # waist between the nose and the front fender, so the fender reads as a separate volume
    add -= 16.0 * math.exp(-((spec_x - (-560)) / 190.0) ** 2) * math.exp(-((z - 430) / 190.0) ** 2)
    # plan waist through the door, measured off ref-09's top view. No Z term: it is the plan that
    # is wrong, not the section, and adding one would move a silhouette that already matches.
    add -= WAIST_DEPTH * math.exp(-((spec_x - WAIST_X) / WAIST_XW) ** 2)
    # nose blade: thin the section above the mouth so the upper line is sharp
    if NOSE_BLADE_X0 <= spec_x <= NOSE_BLADE_X1 and z > NOSE_BLADE_Z:
        run = min(smoothstep(NOSE_BLADE_X1, NOSE_BLADE_X1 - 140, spec_x), 1.0)
        add -= NOSE_BLADE_THIN * run * smoothstep(NOSE_BLADE_Z, NOSE_BLADE_Z + 90, z)
    # rocker tuck, with a defined edge at ROCKER_EDGE_Z
    if ROCKER_X0 <= spec_x <= ROCKER_X1 and z < ROCKER_EDGE_Z:
        ends = min(smoothstep(ROCKER_X0, ROCKER_X0 + 260, spec_x),
                   1.0 - smoothstep(ROCKER_X1 - 260, ROCKER_X1, spec_x))
        # 10 mm of transition: crisper still. Depth unchanged — the edge is what was missing.
        add -= ROCKER_TUCK * ends * (1.0 - smoothstep(ROCKER_EDGE_Z - 10, ROCKER_EDGE_Z, z))
    return add


def tail_factor(spec_x):
    t = smoothstep(TAIL_START, TAIL_END_X, spec_x)
    return 1.0 - (1.0 - TAIL_NARROW) * t, TAIL_DROP * t


ZONE_BLEND = 420      # mm over which one zone's character hands over to the next


def zone_shape(spec_x, z, hw, z_top):
    """Per-zone character, BLENDED. The first version switched character with if/elif at specX 340
    and 1900, which put a step in the surface exactly where the shoulder line crosses — that is
    where the kinks in the stage-01 side view came from. All three characters are now evaluated
    and mixed with smoothstep weights, so nothing changes abruptly at a zone boundary."""
    t = 0.0 if z_top <= 130 else (z - 120) / (z_top - 120)
    f_front = 1.0 + 0.020 * math.sin(math.pi * t) - 0.030 * t ** 3          # tense, flat-topped
    f_side = 1.0 - 0.045 * max(0.0, t - 0.55) / 0.45                        # upper half draws in
    # muscular over the wheel, then released toward the tail rather than ending in a vertical wall
    peak = math.exp(-((spec_x - 2415) / 700.0) ** 2)                        # centred on the rear axle
    f_rear = 1.0 + (0.030 + 0.038 * peak) * math.sin(math.pi * min(1.0, t * 1.15))
    w_side = smoothstep(340 - ZONE_BLEND, 340 + ZONE_BLEND, spec_x)
    w_rear = smoothstep(1900 - ZONE_BLEND, 1900 + ZONE_BLEND, spec_x)
    f = f_front * (1 - w_side) + f_side * (w_side - w_rear) + f_rear * w_rear
    return hw * f


def envelope(V, spec_x):
    """Longitudinal shape of a void: run in from x0, HOLD full depth from xa to xb, release to x1.
    A single peak instead of a plateau meant the channel was at its designed depth at exactly one
    station and tapering everywhere else, and it left a 9 mm gap at specX 1860 where the door
    channel had released and the intake had not yet built. smoothstep has zero slope at both knees,
    so the plateau joins the ramps without a break in curvature."""
    if not (V["x0"] <= spec_x <= V["x1"]):
        return 0.0
    return min(smoothstep(V["x0"], V["xa"], spec_x),
               1.0 - smoothstep(V["xb"], V["x1"], spec_x))


def side_lip(spec_x):
    """The single upper edge of the side line: channel behind the front wheel through to the mouth."""
    ch = VOID_FIELDS["SIDE_CHANNEL"]
    return table_z(ch["centre"], spec_x) + ch["w"]


def void_field(spec_x, z):
    """Millimetres to take OFF the half-width here. The deepest of the overlapping channels wins
    rather than their sum, so where the door channel runs into the intake the two read as one
    continuous opening that deepens, not as two dents added together."""
    worst = 0.0
    for V in VOID_FIELDS.values():
        e = envelope(V, spec_x)
        if e <= 0.0:
            continue
        zc = table_z(V["centre"], spec_x)
        dep = V["depth"] if isinstance(V["depth"], float) else table_z(V["depth"], spec_x)
        v = dep * e * math.exp(-abs((z - zc) / V["w"]) ** V["n"])
        # The upper edge is CLOSED, not faded out. The super-gaussian skirt carried the channel
        # 70 to 90 mm above its own centre, so the body above it was a roll instead of a shoulder
        # and there was no line for light to break on -- docs/16 asks G0 here. Clipping the field
        # at centre + w over LIP_TRANS takes nothing off the width above the lip and leaves a real
        # face below it. Nothing is ADDED anywhere, so the locked 1850 cannot be touched by it.
        # ONE lip line for the whole side, not one per field. Measured at specX 2107 the two lips
        # sat 14 mm apart -- the channel's at 622, the intake's at 608 -- and the edge angle fell
        # to 0 right where the side line runs into the mouth. VOID_FIELDS already states this
        # principle for the DEPTH ("ONE line ... not two channels that meet"); the edge is the same
        # line and gets the same treatment. docs/16 has DOOR_CHANNEL -> SIDE_INTAKE_MOUTH as G1, so
        # the line carries through the handover instead of dying and restarting.
        lip = side_lip(spec_x)
        v *= 1.0 - smoothstep(lip - LIP_TRANS, lip, z)
        worst = max(worst, v)
    U = REAR_UNDERCUT_FIELD
    e = envelope(U, spec_x)
    if e > 0.0:
        ez = table_z(U["edge"], spec_x)
        worst = max(worst, U["depth"] * e * (1.0 - smoothstep(ez - U["trans"], ez, z)))
    return worst


def cabin_flank(spec_x, z, hw, hw_max):
    """Hold the door side near vertical from just above the rocker up to the belt line, so the top
    of the door is a real shelf at a designed height instead of a point on a cone to the crown.
    This is what connects the beltline to the A-pillar; nothing here touches the donor screen."""
    if not (CABIN_X0 <= spec_x <= CABIN_X1 + 140):
        return hw
    bz = table_z(BELT_Z, spec_x)
    if z < CABIN_FLANK_LO or z > bz:
        return hw
    ends = min(smoothstep(CABIN_X0, CABIN_X0 + CABIN_RAMP, spec_x),
               1.0 - smoothstep(CABIN_X1 - 60, CABIN_X1 + 140, spec_x))
    inb = min(smoothstep(CABIN_FLANK_LO, CABIN_FLANK_LO + 90, z),
              1.0 - smoothstep(bz - 58, bz, z))
    return hw + (hw_max - hw) * CABIN_FLANK_PULL * ends * inb


# Behind the hoops the deck height is the spine, not whatever the section's last control point says.
# The old code did crown = max(crown, z_top + 10), so a section point at Z 900 forced the crown to
# 910 while the spine asked for 880 — a flat plate across the top. That is the "separate plate" read.
def ring(spec_x):
    prof = sorted(section_profile(spec_x), key=lambda p: p[0])
    deck = spine_z(DECK_SPINE, spec_x)
    if deck is not None:
        keep = [(z, y) for z, y in prof if z <= deck - 40]
        if len(keep) >= 3:
            prof = keep
    z_floor = prof[0][0]
    z_top, hw_top = prof[-1]
    # Crown handover. HOOD_SPINE ends at the cowl (specX 420, Z 970) and DECK_SPINE starts at the
    # hoop plane (1760, Z 960). Between them is the cabin, where the top of the body is the beltline.
    # The first version fell straight from 970 to the beltline in one millimetre — a step exactly
    # where the shoulder line crosses, and the single biggest kink in the stage-01 side view.
    crown = spine_z(HOOD_SPINE, spec_x)
    if crown is None:
        crown = spine_z(DECK_SPINE, spec_x)
    if crown is None:
        x0, z0 = HOOD_SPINE[-1]
        x1, z1 = DECK_SPINE[0]
        belt = z_top + hw_top * CROWN_FACTOR
        a = smoothstep(x0, x0 + 700, spec_x)          # long release out of the cowl, was 320
        b = smoothstep(x1 - 320, x1, spec_x)          # gather into the deck
        crown = z0 * (1 - a) + belt * (a - b) + z1 * b
    if BELT_DIP_X0 <= spec_x <= BELT_DIP_X1:
        f = (smoothstep(BELT_DIP_X0, BELT_DIP_PEAK, spec_x)
             * (1.0 - smoothstep(BELT_DIP_PEAK, BELT_DIP_X1, spec_x)) * 4.0)
        crown -= BELT_DIP * min(1.0, f)
    narrow, drop = tail_factor(spec_x)
    # NOTE, 2026-09-15. This guard stops the crown falling below the section's own top, and through
    # the NOSE that is not a guard, it is the author. Measured at six stations from specX -950 to
    # -450, the section wins at four of them: S00 to S03 carry top points at Z 450, 550, 650 and
    # 700, a staircase that overrides whatever HOOD_SPINE asks for. HOOD_SPINE only becomes
    # authoritative from about specX -250 rearward.
    #
    # Consequence: docs/16 asks the nose to be "longitudinally almost flat" and says "do not lift
    # the centre", and it is not — it climbs 100 mm in the first 200. Three different HOOD_SPINE
    # tables were tried and all three produced the same nose to within 4 mm, because none of them
    # is what sets it. The lever is SECTIONS S00-S03 in statev_skeleton.py, and moving it changes
    # the nose silhouette that CHECKPOINT 01 looked at, so it is a design decision and not a fix.
    # The guard used to be `max(crown - drop, z_top + 10)` against the section's GLOBAL top, and
    # that is what made the section the author of the nose. It is now measured against the section's
    # top WHERE THE SECTION IS STILL BROAD: a crest carried by less than 80 % of the station's
    # half-width is a fender crest, not the hood, and the centreline is entitled to sit below it.
    # 55 % was tried first and was too loose -- the new crests sit at 65-67 % of the half-width, so
    # they still counted as broad, the hood came up with them and the body measured highest on the
    # centreline at every front station, which is the opposite of the fender it was meant to build.
    # Without this the fender crests added to SECTIONS on 2026-09-16 would have dragged the hood up
    # with them and closed the very gap between hood and fender they were added to open.
    hw_max = max(h for _, h in prof) if prof else 1.0
    z_broad = max((z for z, h in prof if h >= 0.80 * hw_max), default=prof[0][0])
    crown = max(crown - drop, z_broad + 10)
    # Inside the cabin the crown is cut away entirely, so it costs nothing to hold it above the
    # door top — and it has to be held, or BELT_DIP drags the centreline below the shelf and the
    # section turns back DOWN after it. That was the whole of the 14 mm the door top was losing
    # through the middle of the door.
    if CABIN_X0 <= spec_x <= CABIN_X1:
        crown = max(crown, table_z(BELT_Z, spec_x) + 12)
    # Buttress as PROFILE, not as a boolean union. Two sequential unions and then a single
    # two-shell union both collapsed the skin; and a shape that belongs to the body should come
    # from the loft, not be glued on. The section simply stays wide up to the blade top at Y +-620,
    # then falls to the centreline crown, which lofts into a ridge each side of a sunken deck.
    b = BUTTRESS
    b_top = None
    if b["x0"] <= spec_x <= b["x1"]:
        deck = spine_z(DECK_SPINE, spec_x)
        if deck is None:
            deck = DECK_SPINE[0][1] if spec_x < DECK_SPINE[0][0] else DECK_SPINE[-1][1]
        rise = math.exp(-((spec_x - 2415.0) / 620.0) ** 2)
        b_top = deck + b["height"] * rise

    # Carry the section up to the belt line through the cabin. The old code added ONE point at
    # 94% of the top half-width, which is inboard of the cabin cut at Y 700 — the cut then removed
    # exactly the thing that was supposed to become the door top.
    if CABIN_X0 <= spec_x <= CABIN_X1 and table_z(BELT_Z, spec_x) > z_top + 20:
        bz = table_z(BELT_Z, spec_x)
        for i in range(1, 6):
            prof = prof + [(z_top + (bz - z_top) * i / 5.0, hw_top)]
        z_top, hw_top = prof[-1]
    # Densify the profile in Z BEFORE shaping. This is the fix for a fault that had been quietly
    # halving every character field in the script since the fields were written.
    #
    # section_profile() returns the section's own control points and there are only about six of
    # them, 130 to 150 mm apart. character() was evaluated at those points and nowhere else, so a
    # field with a 10 mm transition — the rocker edge — was sampled at Z 250 and again at Z 400 and
    # the loft drew a straight line between them. The 34 mm tuck came out as a 150 mm ramp with no
    # edge at all, and measured as a 0.0 mm step.
    #
    # It explains a run of things that looked unrelated: why REAR_UNDERCUT_FIELD's `trans` was inert
    # at 18 mm and at 72, why the channel's w and n made no difference, and why raising N_HALF never
    # helped. N_HALF resamples the finished polyline; it cannot recover detail the polyline never
    # carried. The sampling has to be dense where the FIELDS are evaluated, not where the result is
    # resampled.
    #
    # Measured effect at specX 1200, with every locked dimension unchanged: the rocker step goes
    # from unreadable to 30.2 mm against the 34 asked for, the channel entry from unreadable to
    # 115 degrees, and the channel's chord depth from 69.9 mm to 99.0. 6 mm is used because 12, 6
    # and 3 give the same answer to within half a degree, so 6 is inside the plateau.
    _zs = [p[0] for p in prof]
    _fine, _z = [], _zs[0]
    while _z <= _zs[-1] + 1e-6:
        _hw = prof[-1][1]
        for _i in range(len(prof) - 1):
            (_z0, _y0), (_z1, _y1) = prof[_i], prof[_i + 1]
            if _z0 <= _z <= _z1:
                _f = 0.0 if _z1 == _z0 else (_z - _z0) / (_z1 - _z0)
                _hw = _y0 + _f * (_y1 - _y0)
                break
        _fine.append((_z, _hw))
        _z += PROFILE_STEP
    if _fine[-1][0] < _zs[-1] - 1e-6:
        _fine.append(prof[-1])
    prof = _fine
    shaped = [(z, zone_shape(spec_x, z, hw, z_top) + character(spec_x, z)) for z, hw in prof]
    hw_max = max(y for _, y in shaped)
    pts = []
    for z, y in shaped:
        y = flank(spec_x, z, y, hw_max)
        y = front_flank(spec_x, z, y, hw_max)
        y = cabin_flank(spec_x, z, y, hw_max) * narrow
        # The voids come LAST, after every field that pulls the surface outward. Applied earlier
        # they were pulled straight back out again by flank(), which is a second reason the door
        # channel measured nothing through the middle.
        y -= void_field(spec_x, z)
        pts.append((min(MAX_HALF_WIDTH, max(20.0, y)), z))
    half = [(0.0, z_floor)] + pts
    # The door top, carried inboard past the cabin cut. Without this the shelf stopped around
    # Y 810 and the aperture edge at Y 700 sat on the ramp up to the crown, so what you measured
    # as the beltline was not the door top at all.
    if CABIN_X0 <= spec_x <= CABIN_X1:
        bz = table_z(BELT_Z, spec_x)
        ends = min(smoothstep(CABIN_X0, CABIN_X0 + CABIN_RAMP, spec_x),
                   1.0 - smoothstep(CABIN_X1 - 60, CABIN_X1 + 140, spec_x))
        if ends > 0.35:
            # Hold the door side out to the aperture edge for the whole belt band. Appending a
            # single shelf point was not enough: above the flank the section still tucked in, so
            # the cut at Y 700 landed on the tuck and the door top measured 14 mm low.
            pts = [((max(y, CABIN_Y + 14) if CABIN_FLANK_LO + 120 <= z <= bz - 8 else y), z)
                   for y, z in pts]
            if pts[-1][0] > CABIN_Y - 40:
                half = [(0.0, z_floor)] + pts + [(CABIN_Y - 40, bz)]
            else:
                half = [(0.0, z_floor)] + pts
    # the front fender crest, the same mechanism as the buttress crest at the rear
    fc = FRONT_CREST
    fz = table_z(fc["z"], spec_x) if fc["z"][0][0] <= spec_x <= fc["z"][-1][0] else None
    if fz is not None and fz > pts[-1][1] + 8:
        fy = table_z(fc["y"], spec_x)
        fdrop = min(fc["drop"], 0.6 * (fz - pts[-1][1]))
        if fdrop > 6:
            half.append((fy + fc["out"], fz - fdrop))
        half.append((fy, fz))
    if b_top is not None and b_top > pts[-1][1] + 8:
        y_crest = b["y"] + b["w"] * BUTTRESS_TOP_FRAC / 2
        # The drop is capped at 60 % of the height actually available above the section top. A
        # fixed 34 mm was simply skipped wherever the buttress is low — at specX 2200 and again
        # out at 3100 — which left the edge strong over the wheel and absent at both ends of it.
        drop = min(DECK_EDGE_DROP, 0.60 * (b_top - pts[-1][1]))
        if drop > 6:
            half.append((y_crest + DECK_EDGE_OUT, b_top - drop))   # steep approach into the crest
        half.append((y_crest, b_top))                              # the blade crest
    half.append((0.0, max(crown, (b_top - 40) if b_top else crown)))
    half = resample_anchored(half, N_HALF, feature_anchors(spec_x))
    return list(half) + [(-y, z) for y, z in reversed(half[1:-1])]


def built_hw(spec_x, z_lo, z_hi):
    """Half-width of the ACTUAL BUILT body at this station across a height band.
    The cutters used to be sized from section_profile(), which is the raw input. The body is built
    by ring(), which adds the zone shaping, the character fields, the flank pull and the tail
    taper, and comes out wider. A cutter sized to the raw profile ended up entirely INSIDE the
    body, hollowing it instead of opening it — which is why three of the four voids measured 0.0
    mm of depth while every boolean reported success."""
    # Sample at the CENTRE of the band, not the maximum across band+-60. Using the max pulled in the
    # shoulder above the channel, so subtracting the depth from it still left the cutter outside the
    # local surface — which is why the door channel measured 0-10 mm through the middle of the door.
    zc = (z_lo + z_hi) / 2.0
    r = ring(spec_x)
    near = [(abs(z - zc), abs(y)) for y, z in r]
    near.sort()
    k = max(3, len(near) // 14)
    return sum(v for _, v in near[:k]) / k


# Cutter resolution. The nose mouth is the only boolean left on the body, and the faceting under it
# was never the body's fault: the body carries sections every 17-33 mm through the nose. The CUTTER
# was a box — a four-corner rectangle lofted through six stations up to 80 mm apart — so the hole it
# left had flat panels along its length and a 90 degree knife edge where it met the skin. Neither of
# these changes the mouth: same position, same depth, same height. It is sampling and a fillet.
CUTTER_STEP = 12.0      # mm between lofted stations after resampling
CUTTER_ARC = 5          # points per rounded inner corner
CUTTER_FILLET = 26.0    # mm radius on the two inner corners, capped by the opening's own size


def _catmull(ts, vs, t):
    """Catmull-Rom through the control values, so resampling a coarse table does not just replace
    long flat facets with short ones joined at the same kinks."""
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    p1, p2 = vs[i], vs[i + 1]
    p0 = vs[i - 1] if i > 0 else p1
    p3 = vs[i + 2] if i + 2 < len(vs) else p2
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    return 0.5 * ((2 * p1) + (-p0 + p2) * u
                  + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def _cutter_section(hw, depth, z_lo, z_hi):
    """(y, z) ring for one station: outboard corners square, the two INNER corners filleted.
    Only the inner face and the two lips ever become visible surface; the outer face is buried."""
    y_out, y_in = hw + 150, hw - depth
    r = max(0.0, min(CUTTER_FILLET, (z_hi - z_lo) / 3.0, depth / 2.0))
    if r < 1.0:
        return [(y_out, z_lo), (y_in, z_lo), (y_in, z_hi), (y_out, z_hi)]
    pts = [(y_out, z_lo)]
    cy, cz = y_in + r, z_lo + r
    for k in range(CUTTER_ARC):                     # bottom inner corner, 270 deg -> 180 deg
        a = math.radians(270 - 90 * k / (CUTTER_ARC - 1))
        pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    cz = z_hi - r
    for k in range(CUTTER_ARC):                     # top inner corner, 180 deg -> 90 deg
        a = math.radians(180 - 90 * k / (CUTTER_ARC - 1))
        pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    pts.append((y_out, z_hi))
    return pts


def make_cutter(name, stations, coll, mirror=True):
    """Loft a cutter from (spec_x, depth, z_lo, z_hi). It sits outboard of the body and eats in."""
    xs = [t[0] for t in stations]
    fine = []
    x = xs[0]
    while x < xs[-1]:
        fine.append(x)
        x += CUTTER_STEP
    fine.append(xs[-1])
    sampled = [(t,
                _catmull(xs, [q[1] for q in stations], t),
                _catmull(xs, [q[2] for q in stations], t),
                _catmull(xs, [q[3] for q in stations], t)) for t in fine]
    objs = []
    for sgn in ((1, -1) if mirror else (1,)):
        verts, faces, rings = [], [], []
        for spec_x, depth, z_lo, z_hi in sampled:
            hw = built_hw(spec_x, z_lo, z_hi)
            sec = _cutter_section(hw, depth, z_lo, z_hi)
            if sgn < 0:
                sec = list(reversed(sec))   # mirroring by negating Y reverses the winding; undo it
                                            # here, by construction, instead of hoping recalc fixes it
            idx = []
            for y, z in sec:
                idx.append(len(verts))
                verts.append((mm(sx(spec_x)), mm(sgn * y), mm(z)))
            rings.append(idx)
        n = len(rings[0])
        for a, b in zip(rings[:-1], rings[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append((a[i], a[j], b[j], b[i]))
        faces.append(tuple(reversed(rings[0])))
        faces.append(tuple(rings[-1]))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new(f"_cut_{name}_{'L' if sgn > 0 else 'R'}", me)
        coll.objects.link(ob)
        objs.append(ob)   # NOT hidden: a hidden operand is dropped from the depsgraph and the
                          # boolean then differences against nothing, which corrupts the result
    return objs


def fix_normals(ob, label=""):
    """Loft winding comes out inside-out, which makes a boolean DIFFERENCE eat the body instead of
    the void. Recalculate outward and verify by signed volume."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # clean before judging: a chain of booleans leaves slivers and doubled verts, and the next
    # EXACT operation chokes on them. This is what made the 15th cut collapse the whole body.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    vol = bm.calc_volume(signed=True)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    if label and (vol <= 0 or nonman):
        print(f"    ! {label}: volume {vol:.4f}, non-manifold edges {nonman}")
    return vol


def boolean(target, cutters):
    """One cutter at a time, with normals re-fixed between each. A chain of booleans applied in one
    go flips the output winding partway through and the next difference then eats the body instead
    of the void — that is how this first came out as 52 faces."""
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    for c in cutters:
        m = target.modifiers.new(c.name, "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", c, "EXACT"
        n_before = len(target.data.polygons)
        bpy.ops.object.modifier_apply(modifier=m.name)
        fix_normals(target)
        n_after = len(target.data.polygons)
        if n_after < 200:
            raise RuntimeError(f"boolean with {c.name} collapsed the body: "
                               f"{n_before} -> {n_after} faces")
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)



# ---------------------------------------------------------------- panel seams, ON the surface
def contour_half(spec_x):
    """The +Y half of the section, ordered by Z. The uncut skin -- which is what a panel seam lies
    on: the opening is cut OUT of the panel afterwards, so the seam belongs on the panel."""
    return sorted([(y, z) for y, z in ring(spec_x) if y >= 0.0], key=lambda p: p[1])


def seam_y_at(spec_x, z):
    c = contour_half(spec_x)
    for i in range(len(c) - 1):
        (y0, z0), (y1, z1) = c[i], c[i + 1]
        if (z0 - z) * (z1 - z) <= 0.0 and z1 != z0:
            f = (z - z0) / (z1 - z0)
            return y0 + f * (y1 - y0)
    return None


def seam_z_at(spec_x, y, branch):
    """Height where the section carries this half-width, on the chosen branch.

    A seam that sweeps in plan -- the hood's rear cut, the engine cover, the fascia -- states which
    Y it passes through and the height is the surface's business, not a typed number."""
    c = contour_half(spec_x)
    if not c:
        return None
    top = max(range(len(c)), key=lambda i: c[i][0])     # the widest point splits the two branches
    seg = c[top:] if branch == "upper" else list(reversed(c[:top + 1]))
    for i in range(len(seg) - 1):
        (y0, z0), (y1, z1) = seg[i], seg[i + 1]
        if (y0 - y) * (y1 - y) <= 0.0 and y1 != y0:
            f = (y - y0) / (y1 - y0)
            return z0 + f * (z1 - z0)
    return seg[-1][1] if seg else None


def seam_points(spec):
    """(spec_x, y, z) on the skin, from the seam's intent alone."""
    k = spec["kind"]
    if k == "station":
        z0, z1 = spec["z"]
        c = [(spec["x"], y, z) for y, z in contour_half(spec["x"]) if z0 <= z <= z1]
        return c
    if k == "rail":
        x0, x1 = spec["x"]
        out = []
        for i in range(13):
            x = x0 + (x1 - x0) * i / 12.0
            y = seam_y_at(x, spec["z"])
            if y is not None:
                out.append((x, y, spec["z"]))
        return out
    if k == "profile":
        # The listed y values are the EXTENT of the seam, not the whole curve. Three points make a
        # panel cut that is two straight segments; sampling between them reads the surface rather
        # than inventing anything, and the hood cut is a curve on a real car.
        ys, out = spec["ys"], []
        fine = []
        for i in range(len(ys) - 1):
            for k2 in range(4):
                fine.append(ys[i] + (ys[i + 1] - ys[i]) * k2 / 4.0)
        fine.append(ys[-1])
        for y in fine:
            z = seam_z_at(spec["x"], y, spec["branch"])
            if z is not None:
                out.append((spec["x"], y, z))
        return out
    raise ValueError(f"unknown seam kind {k!r}")


def _body_tree(subs):
    import bmesh as _bm
    from mathutils.bvhtree import BVHTree
    bm = _bm.new()
    for c in ZONES:
        for o in subs[c].objects:
            me = o.to_mesh()
            try:
                bm.from_mesh(me)
            finally:
                o.to_mesh_clear()
    if not bm.faces:
        bm.free()
        return None, None
    return BVHTree.FromBMesh(bm), bm


def snap_to_body(tree, spec, x, y, z, sgn=1):
    """Move the point onto the BUILT surface along the axis that preserves the seam's intent.

    Generating from ring() alone leaves the seam 10 mm off on average and 56 at worst, and the
    reason is the one this file already warns about beside built_hw(): a number taken from the
    INPUT of a loft is not a fact about its OUTPUT. The rings are smoothed along X over +-2 stations
    before they are lofted and then five void families are cut out of the result, so ring() is the
    seam's intent, not its position. A station or rail seam keeps its X and Z and finds the flank by
    a ray coming in from outboard; a profile seam keeps its X and Y and finds the skin from above or
    below. Rays come from OUTSIDE inward so they land on the outer skin and not on the cabin wall.
    """
    # Each side is snapped to ITS OWN half. Mirroring the +Y curve leaves the -Y one up to 2.5 mm
    # off, because the body is symmetric by construction but its TESSELLATION is not -- the same
    # asymmetry that made P28/P41 differ by 30% on 2026-09-16.
    V = mathutils.Vector
    if spec["kind"] in ("station", "rail"):
        hit = tree.ray_cast(V((mm(sx(x)), sgn * 2.0, mm(z))), V((0.0, -sgn * 1.0, 0.0)), 4.0)
        return (x, sgn * hit[0].y * 1000.0, z) if hit[0] is not None else None
    up = spec.get("branch", "upper") == "upper"
    o = V((mm(sx(x)), mm(sgn * y), 2.5 if up else -1.5))
    hit = tree.ray_cast(o, V((0.0, 0.0, -1.0 if up else 1.0)), 4.5)
    return (x, y, hit[0].z * 1000.0) if hit[0] is not None else None


def build_seams(coll, subs):
    """Draw every seam as its plane intersected with the BUILT skin."""
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    tree, bm = _body_tree(subs)
    if tree is None:
        print("  panel seams: no body to lie on")
        return 0
    n, missed = 0, 0
    for nm, (reason, spec) in PANEL_SEAMS.items():
        raw = seam_points(spec)
        for suffix, sgn in (("_L", 1), ("_R", -1)):
            pts = []
            for x, y, z in raw:
                p = snap_to_body(tree, spec, x, y, z, sgn)
                if p is None:
                    missed += 1
                else:
                    pts.append((p[0], sgn * abs(p[1]) if spec["kind"] != "profile" else sgn * p[1],
                                p[2]))
            if len(pts) < 2:
                print(f"  SEAM {nm}{suffix}: refused — {len(pts)} point(s) landed on the skin")
                continue
            cu = bpy.data.curves.new(f"SEAM_{nm}{suffix}", "CURVE")
            cu.dimensions = "3D"
            sp = cu.splines.new("POLY")
            sp.points.add(len(pts) - 1)
            for i, (x, y, z) in enumerate(pts):
                sp.points[i].co = (mm(sx(x)), mm(y), mm(z), 1.0)
            ob = bpy.data.objects.new(f"SEAM_{nm}{suffix}", cu)
            coll.objects.link(ob)
            ob["status"] = "DECIDED"
            ob["reason"] = reason
            ob["kind"] = spec["kind"]
            ob["locked_by_donor"] = "donor shut line" in reason or "locked" in reason
            ob["note"] = ("panel boundary, GENERATED from the section. A seam exists only for a "
                          "reason - donor line, access, removal, manufacture or mounting. "
                          "Decorative seams are forbidden.")
            n += 1
    bm.free()
    print(f"  panel seams: {n} curves generated ON the skin from {len(PANEL_SEAMS)} intents"
          + (f", {missed} intent point(s) missed the body and were dropped" if missed else ""))
    return n

def build():
    scene = bpy.context.scene
    root = bpy.data.collections.get(ROOT)
    if root:
        for c in list(root.children):
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
        for o in list(root.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        root = bpy.data.collections.new(ROOT)
        scene.collection.children.link(root)
    subs = {}
    for n in list(ZONES) + ["STATEV_ROOF", "STATEV_DETAILS", "_WORK"]:
        c = bpy.data.collections.new(n)
        root.children.link(c)
        subs[n] = c

    # ---- 1. skin
    order = sorted(v[0] for v in SECTIONS.values())
    stations = []
    for i in range(len(order) - 1):
        stations += [order[i] + (order[i + 1] - order[i]) * k / SUBDIV for k in range(SUBDIV)]
    stations.append(order[-1])

    # Faceting comes from the control data, not from shading. Smooth each ring point ALONG X
    # before building, so the fix is in the geometry rather than a smooth modifier over a bad shape.
    raw = [ring(x) for x in stations]
    npts = len(raw[0])
    smooth_rings = []
    for i, r in enumerate(raw):
        row = []
        for k in range(npts):
            # SMOOTHING BY NEAREST POINT: TRIED 2026-09-21, MEASURED, REVERTED. The note stays
            # because the reasoning was sound and the result still says no.
            #
            # The concern was real. v030 gives every station ten anchored samples and spreads the
            # rest by arc length, and the allocation is recomputed per station: it CHANGES between
            # neighbours at 60 of 90 steps, shuffling up to 38 samples in one step. So index k is
            # not the same place on the section from one ring to the next, and this loop averages
            # by index. Averaging unrelated points is wrong on its face.
            #
            # Two measurements said it was costing something, and BOTH were artefacts of the
            # vertex arrangement, which is the mistake this project keeps making:
            #   - second difference along X taken PER INDEX: 15.85 mm against 9.27 for the plain
            #     resample. Per-index. An anchored resample legitimately puts points elsewhere, so
            #     of course the per-index differences grow.
            #   - the principal-curvature ratio: 0.279 -> 0.242 when smoothing by nearest point.
            #     That estimator reads the one-ring, and aligning the one-ring with the surface's
            #     flow lowers it without the shape changing.
            #
            # The test that cannot be gamed is the surface as a FUNCTION: y(x, z) sampled on a
            # fixed grid, where moving vertices along the same curve changes nothing. On that
            # measure the two are the same car -- |d2y/dx2| 17.37 against 17.25 mm, |d2y/dz2| 28.17
            # against 28.74. The index mixing is conceptually wrong and quantitatively nil, because
            # the window is +-2 stations at about 48 mm and the section barely changes across it.
            #
            # Nearest-point smoothing also cost real things: 2 degenerate faces where there were
            # none, and the worst face-to-face normal jump went from 120.6 to 154.6 degrees. So the
            # simple version stays. surface_probe.py now measures the ungameable number on every
            # run, so the next claim of this kind fails immediately.
            acc_y = acc_z = wsum = 0.0
            for d, wgt in ((-2, 1), (-1, 4), (0, 6), (1, 4), (2, 1)):
                j = min(len(raw) - 1, max(0, i + d))
                acc_y += raw[j][k][0] * wgt
                acc_z += raw[j][k][1] * wgt
                wsum += wgt
            row.append((acc_y / wsum, acc_z / wsum))
        smooth_rings.append(row)

    verts, faces, rings = [], [], []
    for spec_x, r in zip(stations, smooth_rings):
        idx = []
        for y, z in r:
            idx.append(len(verts))
            verts.append((mm(sx(spec_x)), mm(y), mm(z)))
        rings.append(idx)
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))

    me = bpy.data.meshes.new("MASTER_SKIN")
    me.from_pydata(verts, [], faces)
    me.update()
    skin = bpy.data.objects.new(PFX + "MASTER_SKIN", me)
    subs["_WORK"].objects.link(skin)
    for p in me.polygons:
        p.use_smooth = True
    print(f"  skin volume before booleans: {fix_normals(skin):.3f} m3")

    # ---- 2. the five void families
    cuts = []
    # cabin
    bpy.ops.mesh.primitive_cube_add(size=1.0,
                                    location=(mm((D["cowl_x"] + D["hoop_x"]) / 2.0), 0, mm(CABIN_Z + 400)))
    cab = bpy.context.active_object
    cab.name = "_cut_cabin"
    cab.scale = (mm(abs(D["cowl_x"] - D["hoop_x"])), mm(2 * CABIN_Y), mm(800))
    for c in cab.users_collection:
        c.objects.unlink(cab)
    subs["_WORK"].objects.link(cab)
    cuts.append(cab)
    # wheel arches
    for key, (ax, radius, open_w, tod, _tw) in ARCHES.items():
        ht = (D["track_front"] if key == "FRONT" else D["track_rear"]) / 2.0
        for sgn in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(radius=mm(radius), depth=mm(open_w + 400),
                                                vertices=56,
                                                location=(mm(sx(ax)), mm(sgn * (ht + 200)), mm(tod / 2)))
            cyl = bpy.context.active_object
            cyl.name = f"_cut_arch_{key}_{'L' if sgn > 0 else 'R'}"
            cyl.rotation_euler = (math.radians(90), 0, 0)
            for c in cyl.users_collection:
                c.objects.unlink(cyl)
            subs["_WORK"].objects.link(cyl)
            cuts.append(cyl)
    # Only the nose mouth is still cut. A mouth is an opening in the FRONT face of the car and
    # cannot come out of a section profile; the four side voids now can, and do. That takes the
    # boolean count from fifteen to six and removes the whole class of failure with it.
    cuts = make_cutter("nose_mouth", NOSE_MOUTH, subs["_WORK"]) + cuts
    for c in cuts:
        fix_normals(c, c.name)
    boolean(skin, cuts)
    print(f"  skin volume after booleans:  {fix_normals(skin):.3f} m3, "
          f"{len(skin.data.polygons)} faces")

    # ---- 3. buttresses, lofted as blades rather than boxes.
    # The first version was literally a cube. A buttress reads as: rising -> tightening -> blade ->
    # merging into the deck, so it is built from stations along X with a varying height and width.


    # ---- 4. split the skin into zones
    bpy.ops.object.select_all(action="DESELECT")
    skin.select_set(True)
    bpy.context.view_layer.objects.active = skin
    made = []
    for zname, (x0, x1) in ZONES.items():
        cp = skin.copy()
        cp.data = skin.data.copy()
        cp.name = PFX + zname.replace("STATEV_", "") + "_VOLUME"
        subs[zname].objects.link(cp)
        bm = bmesh.new()
        bm.from_mesh(cp.data)
        kill = [f for f in bm.faces if not (x0 <= -f.calc_center_median().x * 1000 <= x1)]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(cp.data)
        bm.free()
        cp["status"] = "MASTER_VOLUME"
        cp["stage"] = "01 — design master, not production geometry"
        mat = bpy.data.materials.get("STATEV_BODY")
        if mat:
            cp.data.materials.clear()
            cp.data.materials.append(mat)
        cp.color = (0.045, 0.115, 0.075, 1.0)
        made.append((cp.name, len(cp.data.polygons)))
    bpy.data.objects.remove(skin, do_unlink=True)
    for o in list(subs["_WORK"].objects):
        bpy.data.objects.remove(o, do_unlink=True)

    seam_coll = None
    for c in bpy.data.collections:
        if c.name == "08_PANEL_SEAMS":
            seam_coll = c
            break
    if seam_coll is not None:
        build_seams(seam_coll, subs)
    else:
        print("  08_PANEL_SEAMS not in the scene — run statev_skeleton.py first; seams not drawn")

    # Stamp what this scene was built from. check_reports.py needs two different facts and mtime
    # cannot give either: whether the BUILD matches the scripts on disk, and whether each REPORT
    # matches the build. A `git checkout` touches a script without changing it and makes every
    # report look stale; editing a script without rebuilding makes the scene stale while every
    # report looks fine. A content hash plus a build time separates the two.
    try:
        import hashlib as _hl
        import json as _js
        h = _hl.sha256()
        for _n in ("statev_skeleton.py", "statev_master_volumes.py", "stage03_elements.py"):
            with open(os.path.join(SCRIPTS, _n), "rb") as _f:
                h.update(_f.read())
        os.makedirs(os.path.join(SCRIPTS, "data"), exist_ok=True)
        with open(os.path.join(SCRIPTS, "data", "last_build.json"), "w") as _f:
            _js.dump({"when": time.time(), "scripts_sha": h.hexdigest()[:16]}, _f, indent=2)
    except Exception as _e:
        print(f"  could not stamp the build: {_e}")

    print(f"{ROOT}: " + " | ".join(f"{n} {f}f" for n, f in made))
    print("cut: cabin, 4 wheel arches, nose mouth. Built into the loft: front channel, "
          "door channel, side intake, rear undercut, buttress.")
    return root


build()
