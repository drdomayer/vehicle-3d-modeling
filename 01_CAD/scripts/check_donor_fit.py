"""
check_donor_fit.py — the BUILT body against the donor, not the spec table against the donor.

check_statev_vs_donor.py reads SECTIONS and PACKAGE out of statev_skeleton and compares those
numbers with the 986. That was right when there was nothing but a skeleton. It is wrong now, and it
is wrong in the way this project has been wrong before: a number taken from the INPUT to the loft is
not a fact about its OUTPUT. Five of the character features -- the side line, the fender crest, the
rocker, the flank, the buttress -- exist only as fields applied after the sections, so the spec-side
check cannot see them at all. It still reports that the fender does not crown over the front wheel;
the built body has crowned over it since v021.

This measures the surface that exists. Everything it prints is read off STATEV_MASTER and compared
with cage_986.DIMS or with the measured 986 plan, and every donor value carries its provenance,
because a conflict against a published number and a conflict against a blueprint estimate are not
the same conflict.

    import bpy; exec(open(".../check_donor_fit.py").read())
"""

import json
import os

import bmesh
import bpy

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
HERE = os.path.join(REPO, "01_CAD/scripts")

_cg = {}
with open(os.path.join(HERE, "cage_986.py"), encoding="utf-8") as f:
    exec(f.read().split("# ---------------------------------------------------------------- helpers")[0]
         .replace("import bpy", ""), _cg)
DIMS = _cg["DIMS"]
_sk = {}
with open(os.path.join(HERE, "statev_skeleton.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef build(")[0].replace("import bpy", ""), _sk)
ARCHES, SPEC = _sk["ARCHES"], _sk["PACKAGE"]
with open(os.path.join(HERE, "data", "986_plan_section.json"), encoding="utf-8") as f:
    PLAN = json.load(f)

CLEAR_MIN = 15.0      # CLAUDE.md hard constraint 3: 15-20 mm air to anything OEM until the scan


def body_points():
    out = []
    for o in bpy.data.collections["STATEV_MASTER"].all_objects:
        if o.type != "MESH" or "VOLUME" not in o.name:
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            out.append((-w.x * 1000, w.y * 1000, w.z * 1000))
    return out


def band(P, sx, tol=25.0, z_lo=None, z_hi=None):
    return [(y, z) for x, y, z in P
            if abs(x - sx) < tol and (z_lo is None or z >= z_lo) and (z_hi is None or z <= z_hi)]


def main():
    P = body_points()
    if not P:
        print("no STATEV_MASTER — build the body first")
        return
    X = [p[0] for p in P]
    rows = []

    def add(sev, what, got, want, prov, note):
        rows.append((sev, what, got, want, prov, note))

    # ---- 1. the nose against the donor's own front face
    nose = min(X)
    donor_nose = -DIMS["front_overhang"][0]
    add("CHECK" if nose > donor_nose else "OK",
        "nose vs donor bumper face", f"{nose:.0f}", f"{donor_nose:.0f}",
        DIMS["front_overhang"][1],
        f"the STATEV nose sits {nose - donor_nose:+.0f} mm relative to the donor's front face; "
        f"positive means INSIDE the donor's own overhang, where the crash beam and its brackets are")

    # ---- 2. does the fender crown over the tyre, at the arch crown, on the BUILT surface
    for key, (ax, radius, open_w, tod, twid) in ARCHES.items():
        track = DIMS["track_front"][0] if key == "FRONT" else DIMS["track_rear"][0]
        tyre_out = track / 2.0 + twid / 2.0
        crown_z = tod / 2.0 + radius
        # the body just outboard of the arch, at the crown height, measured either side of the axle
        got = 0.0
        for off in (-radius - 60, radius + 60):
            b = band(P, ax + off, 30.0, crown_z - 40, crown_z + 40)
            if b:
                got = max(got, max(abs(y) for y, _ in b))
        add("OK" if got >= tyre_out else "CHECK",
            f"{key} fender crowns the tyre", f"{got:.1f}", f"{tyre_out:.1f}",
            f"track {DIMS['track_front'][1]}, tyre ours",
            f"body half-width at the arch crown height against the tyre's outer face: "
            f"{got - tyre_out:+.1f} mm")

    # ---- 3. the arch aperture against the surface it is cut into.
    # Measured just OUTSIDE the arch's own X range, where the cut does not reach, because inside it
    # the body has already had the material removed and its remaining width is not the width the
    # opening was cut into. The first version measured at the axle and reported the front opening as
    # 130 mm wider than the surface, which is the hole talking, not the panel.
    for key, (ax, radius, open_w, tod, twid) in ARCHES.items():
        track = DIMS["track_front"][0] if key == "FRONT" else DIMS["track_rear"][0]
        aperture = track / 2.0 + open_w / 2.0
        surface = 0.0
        for off in (-radius - 60, radius + 60):
            b = band(P, ax + off, 30.0)
            if b:
                surface = max(surface, max(abs(y) for y, _ in b))
        add("OK" if surface >= aperture - 1 else "CHECK",
            f"{key} arch opening vs surface", f"{aperture:.1f}", f"{surface:.1f}",
            "opening ours, track published",
            f"the opening reaches Y {aperture:.1f} and the body is {surface:.1f} wide there: "
            f"{aperture - surface:+.1f} mm of opening with no surface to cut")

    # ---- 4. air to the OEM skin where the OEM skin stays: the rear quarters are overlays
    # plan_half_width is ALREADY in millimetres, in repo X with forward positive -- the note in the
    # file says so and block_986.py reads it that way. Scaling it again by mm/px turned the donor's
    # half-width into 6341 mm and the clearance into -5416, which is the kind of number that should
    # stop a report rather than appear in one.
    hw = PLAN["plan_half_width"]
    worst = None
    for px, py in hw:
        sx = -px
        if not (1635 <= sx <= 2780):          # door shut line back to the rear arch: welded quarter
            continue
        donor_y = py
        # Z 400 to 630 only: above that the cabin cut's own wall stands at |Y| 700 and reading it
        # as our skin made the quarter look 163 mm INSIDE the donor at spec X 1768, which is the
        # aperture talking again.
        # ... and the SIDE INTAKE MOUTH has to be excluded the same way. Stage 03 cuts a real mouth
        # at spec X 1955..2165, Z 448..700, inward to Y 430, so inside that range the widest surface
        # in this Z band is the POCKET FLOOR. Unexcluded it reported our skin at 579 against the
        # donor's 883 at spec X 2116 and called it a 304 mm shortfall; on 2026-09-16, before the
        # mouth existed, the same measurement read 883 against 882. Fifth time in this project that
        # a measurement found a hole and reported it as the panel: the opening is not the quarter.
        if 1930 <= sx <= 2190:
            continue
        b = band(P, sx, 30.0, 400, 630)
        if not b:
            continue
        ours = max(abs(y) for y, _ in b)
        gap = ours - donor_y
        if worst is None or gap < worst[0]:
            worst = (gap, sx, ours, donor_y)
    if worst:
        # The donor half-width here is a blueprint estimate carrying +-30 mm, and the whole margin
        # available inside the locked 1850 at that station is about 43 mm. A gap smaller than the
        # donor number's own error band is not a result, and tuning the flank against it would be
        # fitting our surface to a measurement that cannot support the precision.
        band_mm = PLAN["accuracy_mm"]
        undecidable = abs(worst[0] - CLEAR_MIN) < band_mm
        add("SCAN" if undecidable else ("CHECK" if worst[0] < CLEAR_MIN else "OK"),
            "air over the welded quarter", f"{worst[0]:.0f}", f">= {CLEAR_MIN:.0f}",
            f"donor plan approx +-{band_mm} mm",
            f"tightest at spec X {worst[1]:.0f}: our skin {worst[2]:.0f}, donor {worst[3]:.0f}. "
            f"The new quarter is an OVERLAY and must sit OUTSIDE the OEM skin. "
            + (f"The shortfall is {CLEAR_MIN - worst[0]:.0f} mm against a donor figure that is "
               f"itself +-{band_mm}, so this is NOT decidable before the scan -- and the room the "
               f"locked 1850 leaves at that station is only about {925 - worst[3]:.0f} mm."
               if undecidable else ""))

    # ---- 5. the door aperture the skin has to cover
    b1 = band(P, DIMS["door_front_x"][0] * -1, 25.0, 330, 900)
    b2 = band(P, DIMS["door_rear_x"][0] * -1, 25.0, 330, 900)
    if b1 and b2:
        add("OK", "door aperture covered",
            f"{-DIMS['door_rear_x'][0] + DIMS['door_front_x'][0]:.0f}", "1195",
            DIMS["door_front_x"][1],
            "the body carries surface at both shut lines, so the skin spans the aperture")

    # ---- 6. ride height
    add("OK" if min(p[2] for p in P) >= SPEC["ground_clearance"] - 1 else "CHECK",
        "ground clearance", f"{min(p[2] for p in P):.0f}", f"{SPEC['ground_clearance']}",
        "ours, road legal target",
        f"lowest point of the body; the donor's published clearance is {DIMS['clearance'][0]} mm "
        f"({DIMS['clearance'][1]})" if "clearance" in DIMS else "lowest point of the body")

    print("=" * 104)
    print("DONOR FIT — the BUILT body against the 986, with every donor value's provenance")
    print("=" * 104)
    print(f"\n{'':<6}{'what':<34}{'built':>10}{'donor':>10}   provenance")
    for sev, what, got, want, prov, note in rows:
        print(f"{sev:<6}{what:<34}{got:>10}{want:>10}   {prov}")
        print(f"      {note}")
    n = sum(1 for r in rows if r[0] == "CHECK")
    ns_ = sum(1 for r in rows if r[0] == "SCAN")
    print(f"\n  {len(rows)} measurements: {n} needing attention, {ns_} not decidable before the scan.")
    print("  PUBLISHED values are from the workshop manual and cannot move. APPROX values are from a")
    print("  4.153 mm/px CC-BY blueprint and carry +-15 to 30 mm, so a conflict inside that band is")
    print("  not yet a conflict. Nothing here is a substitute for the scan; it is what can be")
    print("  checked before there is a car.")
    return rows


main()
