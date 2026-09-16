"""
donor_exposure.py — which donor values actually bound which panel. A binary question, answered
binary, because the magnitude version of it is not measurable on a blockout mesh.

WHY THIS FILE REPLACES AN EARLIER ANSWER. boundary_sensitivity.py moved each approximate donor value
by 25 mm and reported how far a panel's spec-X extent changed: 28.0 mm for the hood, 42.5 for the
front fender. Those numbers were wrong, in the way this project has been wrong four times before --
a number produced by the discretisation was read as a fact about the surface. The sweep was the
disproof, and it read:

    panel  value                 2        5       10       25       40      <- perturbation, mm
    P02    cowl_x             28.0     28.0     28.0     28.0     71.2
    P15    door_rear_x        60.1     60.1     60.1     60.1     60.1

A 2 mm move cannot push an edge 60 mm. What moved was which mesh station happened to be the panel's
outermost, because the map assigned whole faces by where their centre fell and the blockout's
stations near those lines sit 36 to 75 mm apart.

That cause is now gone. panel_map.split_on_boundaries cuts the body on every plane panel_of switches
on before anything is assigned, so no face straddles a boundary and the panels begin and end exactly
on their boundary values. The sweep, rerun below on every call, now tracks the perturbation instead
of sitting on stations -- the hood reads about 5, 12, 26 and 38 mm for moves of 5, 10, 25 and 40 --
which is what a real boundary does. Two rows still read flat, and the reason is the same class of
thing scaled down: the cut planes are the UNPERTURBED ones, so a boundary moved off its own cut no
longer has a face edge to land on.

So the magnitudes here are now indicative rather than meaningless, and the statement that does not
need a mesh at all is still the one to quote. Where a donor value bounds a panel, the seam IS that
value's plane, so it travels exactly as far as the estimate is out -- 15 to 30 mm by the band
cage_986 records -- against a 15 mm provisional trim allowance.

What was always worth measuring is the binary the audit had been guessing: does this value bound
this panel? manufacturing_audit answers that by overlapping spec-X spans, which asks "could it be
near" and then treats the answer as "does it move". The rockers overlap both shut-line zones and are
moved by neither, because panel_of returns P07 below the rocker line in every X branch.

Two further facts, from a code trace rather than a measurement, both checkable by grep:

  1. The body geometry reads exactly FOUR donor values -- cowl_x, hoop_x, track_front, track_rear.
     The tracks are PUBLISHED, so the entire donor exposure of the SHAPE is two numbers.
  2. The wheel-arch cut's vertical centre is NOT the donor tyre. It is ARCHES tod, 647 and 675:
     19*25.4 + 2*235*0.35 = 647.1 and 19*25.4 + 2*275*0.35 = 675.1, arithmetic on the 235/35R19 and
     275/35R19 sizes we chose. Neither statev_master_volumes.py nor statev_skeleton.py nor
     panel_map.py reads DIMS["tire_od"] at all. manufacturing_audit's INFLUENCE table calls that
     centre approx. It is not, and every panel sent to CONDITIONAL by an arch overlap alone was sent
     there by a value the geometry never reads.

Still NOT measured, and the distinction is the whole caveat:

  BOUNDARY  answered below, as a binary. The donor value moves the line between two panels.
  SHAPE     not answered. cowl_x and hoop_x also place the cabin cutter, so if they move, the body
            changes rather than the line across it, and no trim allowance covers that. It needs one
            body rebuild per perturbation.

    import bpy; exec(open(".../donor_exposure.py").read())
"""

import bmesh
import bpy
import csv
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "reports", "donor_exposure.csv")
TRIM = 15.0           # PROVISIONAL trim allowance from pilot_P21.PROVISIONAL
BAND = (15.0, 30.0)   # the uncertainty cage_986.py records for values labelled approx
# The probe has to be the recorded uncertainty itself, not something small. A 2 mm probe misses
# real participation: if no mesh station happens to lie within 2 mm of the line, no face changes
# panel and the value looks innocent. P03 and P09 both read clean at 2 mm and both react at 25.
# So the question asked is the one that matters -- if the estimate is out by as much as cage_986
# says it may be out by, does this panel change? -- and the probe is the top of that band.
PROBE = BAND[1]
SWEEP = (2, 5, 10, 25, 40)

_pm_src = open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8").read()

# Which boundary in panel_map.B each APPROX donor value drives. Published values are absent on
# purpose: the scan cannot move them, so perturbing them would measure nothing real.
DRIVEN_BY = {
    "cowl_x":       ["cowl"],
    "door_front_x": ["door_front"],
    "door_rear_x":  ["door_rear"],
    "hoop_x":       ["hoop"],
}


def load_map(overrides=None):
    ns = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_map.py"), "__name__": "_pm"}
    exec(_pm_src.split("\ndef main(")[0], ns)
    if overrides:
        ns["B"].update(overrides)
    return ns


def gather(ns):
    """Every exterior face once as (specX, |Y|, Z, area). Binned repeatedly, read once."""
    pts = []
    for src in [o for o in bpy.data.collections["STATEV_MASTER"].all_objects
                if o.type == "MESH" and "VOLUME" in o.name]:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        # Cut on the boundary planes first, as the extractors do, so a face is not assigned by
        # where its centre happens to fall. The planes are the UNPERTURBED ones: a perturbation
        # then moves faces cleanly across a boundary they already align with, which is exactly the
        # change this is trying to detect.
        ns["split_on_boundaries"](bm)
        for f in bm.faces:
            if f.calc_area() < 1e-9:
                continue
            c = src.matrix_world @ f.calc_center_median()
            n = (src.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            if ns["not_panel"](sx, ay, z, n.z, -n.y if c.y > 0 else n.y):
                continue
            pts.append((sx, ay, z, f.calc_area()))
        bm.free()
    return pts


def bin_panels(ns, pts):
    """Area and spec-X extent per panel under one set of boundary values."""
    out = {}
    for sx, ay, z, area in pts:
        p = ns["panel_of"](sx, ay, z)
        if p is None:
            continue
        a, lo, hi = out.get(p, (0.0, 1e9, -1e9))
        out[p] = (a + area, min(lo, sx), max(hi, sx))
    return out


def changed(base, got, pid):
    """Did this panel react at all? Area and extent together, so a pure reassignment still shows."""
    if pid not in got:
        return True
    a0, lo0, hi0 = base[pid]
    a1, lo1, hi1 = got[pid]
    return abs(a1 - a0) > 1e-6 or abs(lo1 - lo0) > 0.4 or abs(hi1 - hi0) > 0.4


def quantisation_evidence(base_ns, base, pts, watch):
    """Run the disproof in the docstring rather than asking the reader to trust it."""
    print("\nWHY THE MAGNITUDE IS NOT REPORTED — extent change against perturbation size")
    print("  a value that really travelled would grow with the perturbation; these do not\n")
    print(f"  {'panel':<6}{'donor value':<14}" + "".join(f"{d:>8}" for d in SWEEP))
    for dval, keys in DRIVEN_BY.items():
        for pid in watch:
            row = []
            for d in SWEEP:
                w = 0.0
                for sgn in (1, -1):
                    got = bin_panels(load_map({k: base_ns["B"][k] + sgn * d for k in keys}), pts)
                    if pid in got:
                        w = max(w, abs(got[pid][1] - base[pid][1]), abs(got[pid][2] - base[pid][2]))
                row.append(w)
            if max(row) > 0.4:
                print(f"  {pid:<6}{dval:<14}" + "".join(f"{v:>8.1f}" for v in row))
    print("\n  Rows that track the perturbation are real boundary travel; rows that sit flat are")
    print("  a boundary that has moved off its own cut plane, since the cuts are the unperturbed")
    print("  ones. Either way the figure to quote needs no mesh: where a donor value bounds a")
    print(f"  panel the seam IS that plane, so it travels the estimate's own error, {BAND[0]:.0f} to "
          f"{BAND[1]:.0f} mm,")
    print(f"  against a {TRIM:.0f} mm trim allowance.")


def main():
    base_ns = load_map()
    pts = gather(base_ns)
    base = bin_panels(base_ns, pts)
    NAME_OF = base_ns["NAME_OF"]

    bound = {pid: [] for pid in base}
    for dval, keys in DRIVEN_BY.items():
        for sgn in (1, -1):
            got = bin_panels(load_map({k: base_ns["B"][k] + sgn * PROBE for k in keys}), pts)
            for pid in base:
                if changed(base, got, pid) and dval not in bound[pid]:
                    bound[pid].append(dval)

    print("=" * 104)
    print("DONOR EXPOSURE — does an APPROX donor value bound this panel? Measured, not inferred from")
    print("spec-X overlap. The answer reported is the binary; the sweep below shows the magnitude")
    print("and how far it can be trusted.")
    print("=" * 104)
    print(f"\n{'panel':<7}{'name':<22}{'area m2':>9}  {'bounded by':<40}verdict")

    rows = []
    for pid in sorted(base):
        a0, lo0, hi0 = base[pid]
        by = bound[pid]
        if not by:
            v = "boundary INDEPENDENT of every approx donor value"
        else:
            v = f"boundary travels with the estimate: {BAND[0]:.0f}-{BAND[1]:.0f} mm vs {TRIM:.0f} mm trim"
        print(f"{pid:<7}{NAME_OF.get(pid,''):<22}{a0:>9.3f}  "
              f"{(', '.join(b.replace('_x','') for b in by) or '-'):<40}{v}")
        rows.append(dict(PANEL=pid, NAME=NAME_OF.get(pid, ""), AREA_M2=round(a0, 4),
                         X_MIN=round(lo0), X_MAX=round(hi0),
                         BOUNDED_BY=";".join(by) or "",
                         BOUNDARY_DONOR_DEPENDENT="no" if not by else "yes",
                         TRAVEL_MM="0" if not by else f"{BAND[0]:.0f}-{BAND[1]:.0f}",
                         TRIM_MM=TRIM, VERDICT=v))

    ind = [r["PANEL"] for r in rows if not r["BOUNDED_BY"]]
    dep = [r["PANEL"] for r in rows if r["BOUNDED_BY"]]
    print(f"\n  boundary independent of every approx donor value : {len(ind):>2}   {' '.join(ind)}")
    print(f"  boundary set by an approx donor value            : {len(dep):>2}   {' '.join(dep)}")

    quantisation_evidence(base_ns, base, pts, dep)

    print("\n  INDEPENDENT here means the BOUNDARY does not move. cowl_x and hoop_x also place the")
    print("  cabin cutter, so their SHAPE half is unmeasured and a panel the cabin cut reaches is")
    print("  not cleared by this alone. Panels entirely below the cabin cut are.")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")
    return rows


main()
