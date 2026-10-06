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
import math
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

    # ---- 0. THE SIDE, against the donor block, 2026-09-26. Added after the sill band measured
    # inside the donor at 146 of 150 samples (worst -189 mm) and the door band at 101 of 140
    # (worst -125) without any row here saying so. Body vertices in each band against
    # data/donor_side_986.json (the block, +-30..50); vertices inside a stage-03 pocket box are
    # skipped, because a pocket floor is a hole, not skin.
    try:
        with open(os.path.join(HERE, "data", "donor_side_986.json"), encoding="utf-8") as f:
            ds = json.load(f)
        _pm = {"__name__": "_pm"}
        with open(os.path.join(HERE, "panel_map.py"), encoding="utf-8") as f:
            exec(f.read().split("\ndef main(")[0], _pm)
        pockets = _pm["POCKETS"]

        def dhw(sx, z):
            X, Z, H = ds["spec_x"], ds["z"], ds["half_width"]
            if not (X[0] <= sx <= X[-1] and Z[0] <= z <= Z[-1]):
                return None
            i = min(int((sx - X[0]) / 50.0), len(X) - 2)
            j = min(int((z - Z[0]) / 25.0), len(Z) - 2)
            fx, fz = (sx - X[i]) / 50.0, (z - Z[j]) / 25.0
            c = [H[str(X[i + a])][str(Z[j + b])] for a in (0, 1) for b in (0, 1)]
            if any(v is None for v in c):
                return None
            return (c[0] * (1 - fz) + c[1] * fz) * (1 - fx) + (c[2] * (1 - fz) + c[3] * fz) * fx

        for what, x0, x1, z0, z1 in (("sill band air, Z 150..320", 360, 1820, 150, 320),
                                     ("door band air, Z 400..700", 460, 1620, 400, 700),
                                     ("rear quarter air, Z 400..700", 1700, 2300, 400, 700)):
            worst, n, n_in = None, 0, 0
            n_cut = [0]
            for x, y, z in P:
                if not (x0 <= x <= x1 and z0 <= z <= z1):
                    continue
                if any(px0 <= x <= px1 and py0 <= abs(y) <= py1 and pz0 <= z <= pz1
                       for _, px0, px1, py0, py1, pz0, pz1, *_poly in pockets):
                    continue
                # v069: nor the side scoop. It cuts the OEM quarter ON PURPOSE (owner's decision,
                # docs/14 Z): its floor is inside the donor skin by design, and the cut itself is what
                # the bodyshop does. Excluded by name and counted, not silently.
                if any(py0 <= abs(y) <= py1 and _pm["in_poly"](x, z, ppoly, ptol)
                       for _, py0, py1, ppoly, ptol in _pm.get("POCKETS_XZ", [])):
                    n_cut[0] += 1
                    continue
                # nor the arch cylinders' own walls and end caps: the first run reported -303 mm
                # at spec X 2294 / Z 682 from a vertex ON the rear arch cylinder (d = 365) at the
                # cutter's inboard end, Y 579 -- the wheel well, not the quarter's skin.
                if any(math.hypot(x - ax, z - tod / 2.0) < radius + 6.0
                       for ax, radius, open_w, tod, twid in ARCHES.values()):
                    continue
                # nor the cabin cutter's own walls: -162 mm at spec X 1760 / Z 640 was the corner
                # of the aperture's rear wall at Y 700, inside the cut, not skin.
                cb = _pm["CABIN"]
                if cb["x0"] - 12 <= x <= cb["x1"] + 12 and abs(y) <= cb["y"] + 12 and z >= cb["z"] - 12:
                    continue
                d = dhw(x, z)
                if d is None:
                    continue
                n += 1
                air = abs(y) - d
                if air < 15.0:
                    n_in += 1
                if worst is None or air < worst[0]:
                    worst = (air, x, z, abs(y), d)
            if worst:
                add("CHECK" if worst[0] < 15.0 else "OK", what, f"{worst[0]:+.0f}", ">= 15",
                    "donor block approx +-30..50 mm",
                    f"{n_in} of {n} skin vertices under +15 mm; worst at spec X {worst[1]:.0f} "
                    f"Z {worst[2]:.0f}: ours {worst[3]:.0f}, donor {worst[4]:.0f}. Hard constraint 3." +
                    (f" {n_cut[0]} vertices in the side scoop not counted: it cuts the OEM quarter by "
                     f"decision (docs/14 Z)." if n_cut[0] else ""))
    except (OSError, KeyError) as e:
        add("CHECK", "side vs donor", "--", "table", "data/donor_side_986.json", f"not measured: {e}")

    # ---- 1. the nose against the donor's own front face
    nose = min(X)
    donor_nose = -DIMS["front_overhang"][0]
    add("CHECK" if nose > donor_nose else "OK",
        "nose vs donor bumper face", f"{nose:.0f}", f"{donor_nose:.0f}",
        DIMS["front_overhang"][1],
        f"the STATEV nose sits {nose - donor_nose:+.0f} mm relative to the donor's front face; "
        f"positive means INSIDE the donor's own overhang, where the crash beam and its brackets are")

    # ---- 1b. how far our FRONT OPENINGS go back past the crash structure's rear mounts (2026-10-06).
    # P1 (impact absorber rear mount): Y published (800 L-R), X scaled off the set-up drawing.
    try:
        p8 = -((DIMS["door_front_x"][0] + DIMS["door_rear_x"][0]) / 2.0 + DIMS["jack_front_to_rear_x"][0] / 2.0)
        p1 = p8 - DIMS["jack_front_to_impact_absorber_x"][0]
        _pm2 = {"__name__": "_pm2"}
        with open(os.path.join(HERE, "panel_map.py"), encoding="utf-8") as f:
            exec(f.read().split("\ndef main(")[0], _pm2)
        deep = {nm: x1 for nm, x0, x1, *_r in _pm2["POCKETS"] if nm in ("X_MOUTH", "X_CORNER")}
        worst = max(deep.values())
        add("CHECK" if worst > p1 + 40.0 else "SCAN", "front openings vs crash structure",
            f"{worst:.0f}", f"<= {p1:.0f}", "P1 Y published, X approx +-40",
            "the impact absorbers' rear mounts P1 sit at spec X " + f"{p1:.0f} (|Y| "
            f"{DIMS['impact_absorber_y_total'][0] / 2:.0f}); our openings go back to " +
            ", ".join(f"{k[2:].lower()} {v:.0f}" for k, v in deep.items()) +
            " -- behind them even at the +40 end of the band. The bumper beam lies between P1 and the "
            "986's face at a height nobody has measured; at mouth height (Z 220..430) the mouth cuts "
            "through it. Hard constraint 4: it stays. P01 / P43 / the corner grilles wait on it.")
    except (KeyError, OSError) as e:
        add("CHECK", "front openings vs crash structure", "--", "--", "cage_986", f"not measured: {e}")
    # ---- 1c. the same at the rear. P20 (rear absorbers' mounts) and the 986's rear face bound the
    # span; our openings there sit BETWEEN them, not past the absorbers, so whether they meet the beam
    # is its height -- SCAN, not CHECK.
    try:
        p11 = -((DIMS["door_front_x"][0] + DIMS["door_rear_x"][0]) / 2.0 - DIMS["jack_front_to_rear_x"][0] / 2.0)
        p20 = p11 + DIMS["jack_rear_to_impact_absorber_rear_x"][0]
        add("SCAN", "rear openings vs crash structure", f"{p20:.0f}..3420", "beam height", "P20 Y published, X approx +-40",
            f"the rear absorbers' mounts P20 sit at spec X {p20:.0f} (|Y| "
            f"{DIMS['impact_absorber_rear_y_total'][0] / 2:.0f}); the 986's rear face is at ~{2415 + DIMS['rear_overhang'][0]:.0f} (blueprint, approx). "
            "Our tail slot (to 3178, Z 593..631), the lamp housings, the plate recess, the exhausts and the "
            "diffuser tunnel (Z <= 410) all lie in that span. Whether they meet the beam is its height, "
            "which nobody has measured.")
    except (KeyError, OSError) as e:
        add("SCAN", "rear openings vs crash structure", "--", "--", "cage_986", f"not measured: {e}")

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

    # ---- 3. the arch aperture. REWRITTEN 2026-09-18, because the previous version reported the
    # DESIRABLE condition as a problem and did it for two sessions.
    #
    # It compared the designed aperture (track/2 + open_w/2) against the body half-width measured
    # just outside the arch's X range, and flagged CHECK whenever the aperture was wider -- 26.2 mm
    # on the front, 24.8 on the rear. But a wheel-arch cutter MUST reach outboard of the skin, or a
    # web of material is left spanning the opening. So `open_w` beyond the skin is cutter margin,
    # not an error, and the outer boundary of what you actually SEE is the body's own silhouette,
    # never open_w. The old test could only be satisfied by narrowing the cutter until it stopped
    # cutting through, which is the real defect it would have caused.
    #
    # The condition with a consequence is whether the arch is open. Measured on the BUILT mesh:
    # inside the arch cylinder, is there any skin left outboard of the aperture's inner edge? At the
    # front axle the body carries nothing at all below Z 600 and at the rear nothing below Z 680, so
    # both are through-cut. The margin is reported as the number it is.
    for key, (ax, radius, open_w, tod, twid) in ARCHES.items():
        track = DIMS["track_front"][0] if key == "FRONT" else DIMS["track_rear"][0]
        aperture = track / 2.0 + open_w / 2.0
        y_in = track / 2.0 - open_w / 2.0
        zc = tod / 2.0
        web = []
        for x, y, z in P:
            if math.hypot(x - ax, z - zc) < radius - 6.0 and abs(y) > y_in + 10.0:
                web.append((x, y, z))
        outside = 0.0
        for off in (-radius - 60, radius + 60):
            b = band(P, ax + off, 30.0)
            if b:
                outside = max(outside, max(abs(y) for y, _ in b))
        margin = aperture - outside
        add("OK" if not web else "CHECK",
            f"{key} arch is cut through", "0 web" if not web else f"{len(web)} verts",
            "0 web", "opening ours, track published",
            (f"no skin left inside the opening; the cutter reaches Y {aperture:.1f} against a body "
             f"{outside:.1f} wide beside the arch, so {margin:+.1f} mm of cutter margin — which is "
             f"what a through-cut needs. The visible opening edge is the body's own silhouette, "
             f"never open_w.") if not web else
            (f"{len(web)} vertices of skin remain inside the arch cylinder outboard of Y "
             f"{y_in + 10:.0f}: a web spanning the wheel opening. The cutter is too narrow."))

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
