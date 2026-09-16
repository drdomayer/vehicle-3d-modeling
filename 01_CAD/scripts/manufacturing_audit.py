"""
manufacturing_audit.py — prove, panel by panel, what the scan can and cannot change.

The earlier readiness column was an assertion: one field said OURS or DONOR and everything followed
from it. This derives the answer instead, from what actually generates the surface.

WHAT SHAPES THE BODY. ring() builds every section from our own data — SECTIONS, the character
fields, HOOD_SPINE and DECK_SPINE, the void fields. Three donor-derived things then touch it:

    AXLE_WIDENING   keyed on specX 0 and 2415, i.e. on the WHEELBASE, which is PUBLISHED.
    the arch cuts   cylinders whose X comes from the wheelbase and whose Y comes from TRACK, both
                    PUBLISHED; whose radius is ours; and whose vertical centre comes from tyre OD,
                    which is APPROX.
    the cabin cut   spans cowl_x to hoop_x, |Y| < 700, above Z 640. Both of those X values are
                    APPROX, from a 4.153 mm/px blueprint.

and two boundaries are donor-derived rather than shape-derived:

    door shut lines 440 and 1635, APPROX. They bound panels; they do not curve them.

So a panel's real exposure is: which of those five reach into its own extents. That is measurable,
and it is what this script measures rather than restating.

    1  FULLY NOW      only our data and PUBLISHED donor values touch its shape. The scan cannot
                      reshape it; it can only move the car's datum, which moves every panel alike.
    2  NOW, PARAMETRIC INTERFACE
                      an APPROX donor value positions a cut through it or bounds it. The surface
                      between those bounds is still ours, so the shape survives and the boundary
                      is a parameter. Model it; keep the boundary symbolic.
    3  WAIT FOR SCAN  the panel is an overlay on a donor surface whose form we do not have, or its
                      opening is a donor feature nobody has measured. Here the scan changes the
                      SHAPE, and building early means rebuilding.

    import bpy; exec(open(".../manufacturing_audit.py").read())
"""

import bmesh
import bpy
import csv
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "reports", "manufacturing_audit.csv")

_pd = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_definition.py"), "__name__": "_pd"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_definition.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(argv):")[0], _pd)
DEFROWS = {r["PANEL_ID"]: r for r in _pd["rows"]()}
COMMON = _pd["COMMON"]
ROOF_BLOCKED = _pd["ROOF_BLOCKED"]

# Zones of influence, in spec X. This table is a SCREEN, not a measurement: overlapping a zone
# means a donor value could be near the panel, which is a different question from whether it moves
# the panel. Where donor_exposure.csv exists it is measured per panel and this table is only used
# for parts that have no geometry to measure. The distinction cost the rockers a wrong
# classification: they overlap both shut-line zones and both arch zones and are moved by none.
#   name: (x_lo, x_hi, provenance, what it does to the panel)
INFLUENCE = {
    "cabin cut":      (420.0, 1760.0, "APPROX",
                       "cowl_x and hoop_x place the aperture that cuts this panel's top"),
    # CORRECTED 2026-09-16. Both arch entries said PUBLISHED+APPROX, on the grounds that the cut's
    # vertical centre came from tyre OD. It does not. The centre is ARCHES tod in statev_skeleton,
    # 647 and 675, which is 19*25.4 + 2*235*0.35 and 19*25.4 + 2*275*0.35 -- arithmetic on the tyre
    # sizes we chose, exact to 0.1 mm. DIMS["tire_od"] is never read by statev_master_volumes.py,
    # statev_skeleton.py or panel_map.py; the whole body reads four donor values and that is not
    # one of them. Because classify() matched the substring APPROX, every panel an arch reached was
    # pushed to CONDITIONAL by a number the geometry does not use.
    "front arch cut": (-350.0, 350.0, "PUBLISHED",
                       "X from wheelbase and Y from track, both published; radius ours; vertical "
                       "centre is our own 235/35R19 arithmetic, not a donor value"),
    "rear arch cut":  (2050.0, 2780.0, "PUBLISHED",
                       "X from wheelbase and Y from track, both published; radius ours; vertical "
                       "centre is our own 275/35R19 arithmetic, not a donor value"),
    "front shut line": (430.0, 450.0, "APPROX", "door_front_x bounds this panel"),
    "rear shut line":  (1625.0, 1645.0, "APPROX", "door_rear_x bounds this panel"),
}

# Measured exposure, written by donor_exposure.py: panel -> list of approx donor values that were
# shown to move its boundary when perturbed by the recorded uncertainty. Absent means not measured,
# which is not the same as measured clean, so the screen is used instead and the PROOF column says
# which of the two answered.
EXPOSURE_CSV = os.path.join(REPO, "04_ENGINEERING", "reports", "donor_exposure.csv")


def measured_exposure():
    if not os.path.exists(EXPOSURE_CSV):
        return {}
    with open(EXPOSURE_CSV, encoding="utf-8") as f:
        return {r["PANEL"]: [v for v in r["BOUNDED_BY"].split(";") if v]
                for r in csv.DictReader(f)}

# Panels whose SHAPE, not merely whose boundary, is a donor feature. These cannot be derived from
# the influence zones because the dependency is on a surface or an opening, not on a coordinate.
SHAPE_IS_DONOR = {
    "P09": "overlay on the OEM door skin; its inner form is that skin",
    "P10": "overlay on the OEM door skin; its inner form is that skin",
    "P15": "overlay bonded to the welded quarter; its inner form is that quarter",
    "P16": "overlay bonded to the welded quarter; its inner form is that quarter",
    "P11": "frames the real intake opening, whose shape nobody has measured",
    "P12": "frames the real intake opening, whose shape nobody has measured",
    "P31": "sits inside that same unmeasured opening",
    "P32": "sits inside that same unmeasured opening",
    "P37": "clips onto the OEM mirror body; its inner form is that body",
    "P38": "clips onto the OEM mirror body; its inner form is that body",
}


def panel_extents():
    """spec-X span of every extracted panel object."""
    coll = bpy.data.collections.get("STATEV_PANELS")
    if coll is None:
        return None
    out = {}
    for ob in coll.objects:
        pid = ob.get("panel_id")
        if not pid:
            continue
        xs = [-(ob.matrix_world @ v.co).x * 1000 for v in ob.data.vertices]
        out[pid] = (min(xs), max(xs))
    return out


def exposure(pid, span):
    """Which influence zones reach into this panel."""
    if span is None:
        return []
    lo, hi = span
    hit = []
    for name, (a, b, prov, what) in INFLUENCE.items():
        if hi >= a and lo <= b:
            hit.append((name, prov, what))
    return hit


def classify(pid, hits, span, measured=None):
    # A panel with no extents cannot be proven anything. These are the Stage 03 detail parts —
    # inserts, blades, housings, louvres, masks — which the register carries as parts but which do
    # not yet exist as geometry, so nothing can be measured about them. Defaulting them into
    # category 1 because no influence zone happened to hit them would be the silent kind of wrong.
    if span is None:
        return 0, "no geometry yet; a Stage 03 detail part, so nothing can be measured about it"
    if pid in ROOF_BLOCKED:
        return 3, "roof fold envelope, which exists nowhere as data"
    if pid in SHAPE_IS_DONOR:
        return 3, SHAPE_IS_DONOR[pid]
    # Measured beats screened. donor_exposure.py perturbs each approx donor value by the band
    # cage_986 records for it and reports which panels actually changed; where that answer exists
    # for this panel it is the answer, because the screen can only say "nearby".
    if measured is not None and pid in measured:
        by = measured[pid]
        if by:
            return 2, "measured: boundary moves with " + ", ".join(by)
        return 1, ("measured: no approx donor value moves its boundary, and the cabin cut -- the "
                   "only thing cowl_x and hoop_x reshape -- does not reach it")
    approx = [h for h in hits if "APPROX" in h[1]]
    if approx:
        return 2, "screened only: " + "; ".join(f"{n}: {w}" for n, _, w in approx)
    return 1, "only our own data and published donor values reach it"


def main():
    ext = panel_extents()
    meas = measured_exposure()
    # Mirrored panels share one extracted region and one measurement with their partner.
    for a, b in (("P04", "P03"), ("P08", "P07"), ("P10", "P09"), ("P12", "P11"),
                 ("P16", "P15"), ("P18", "P17")):
        if b in meas and a not in meas:
            meas[a] = meas[b]
    if ext is None:
        print("no STATEV_PANELS collection — run panel_extract.py first")
        return
    print("=" * 112)
    print("MANUFACTURING AUDIT — what the scan can change, derived rather than asserted")
    print("=" * 112)
    rows, buckets = [], {0: [], 1: [], 2: [], 3: []}
    for pid, d in DEFROWS.items():
        # mirrored parts share one extracted region; P04 reads P03's span and so on
        span = ext.get(pid) or ext.get({"P04": "P03", "P08": "P07", "P10": "P09", "P12": "P11",
                                        "P16": "P15", "P18": "P17"}.get(pid, ""))
        hits = exposure(pid, span)
        cat, why = classify(pid, hits, span, meas)
        buckets[cat].append(pid)
        rows.append(dict(
            PANEL=pid, NAME=d["NAME"],
            SHAPE_STATUS={0: "UNPROVEN, no geometry", 1: "ours, provable",
                          2: "ours between donor bounds", 3: "donor-governed"}[cat],
            SCAN_DEPENDENCY={0: "unknown until it exists", 1: "datum only",
                             2: "boundary position only", 3: "SHAPE"}[cat],
            DONOR_INTERFACE=d["DONOR_INTERFACE"],
            PANEL_BOUNDARY=d["BOUNDARY_REASON"],
            THICKNESS="PROVISIONAL — " + COMMON["THICKNESS"].split(". ")[1],
            SPLIT=d["SPLIT_STRATEGY"], FLANGE=COMMON["FLANGE"],
            FASTENING=d["MOUNTING"], PRINT_ORIENTATION=COMMON["ORIENTATION"],
            SUPPORT_STRATEGY=COMMON["SUPPORT"],
            FIT_TEST_REQUIRED="not yet" if cat == 0 else ("yes" if cat > 1
                              else "yes, but only the interface"),
            BLOCKER={0: "Stage 03 geometry does not exist yet", 1: "none",
                     2: "docs/13 supplier answers only", 3: "scan"}[cat],
            VERDICT={0: "BLOCKED", 1: "PROCEED", 2: "CONDITIONAL", 3: "SCAN REQUIRED"}[cat],
            CATEGORY=cat, PROOF=why, X_SPAN=("--" if span is None
                                             else f"{span[0]:.0f}..{span[1]:.0f}")))
    # The four-level verdict. BLOCKED covers two different situations and the reason column keeps
    # them apart: a panel behind the roof envelope is waiting on a measurement nobody can take yet,
    # a Stage 03 detail part is waiting on geometry that has not been built. Neither can proceed,
    # but they are not blocked by the same thing and they will not unblock at the same time.
    labels = {1: "PROCEED        — shape provable, only our data and published donor values",
              2: "CONDITIONAL    — model now, donor-derived boundary kept parametric",
              3: "SCAN REQUIRED  — the scan changes the SHAPE, not just the position",
              0: "BLOCKED        — no geometry exists yet; a Stage 03 detail part"}
    for cat in (1, 2, 3, 0):
        sel = [r for r in rows if r["CATEGORY"] == cat]
        print(f"\n{labels[cat]}   ({len(sel)})")
        for r in sel:
            print(f"  {r['PANEL']:<6}{r['NAME']:<24}{r['X_SPAN']:>16}   {r['PROOF']}")
    roof = [p for p in buckets[3] if p in ROOF_BLOCKED]
    print(f"\n  PROCEED {len(buckets[1])}   CONDITIONAL {len(buckets[2])}   "
          f"SCAN REQUIRED {len(buckets[3])}   BLOCKED {len(buckets[0])}")
    print(f"  of the {len(buckets[3])} SCAN REQUIRED, {len(roof)} are behind the roof envelope and")
    print("  the rest are donor-surface overlays or unmeasured openings. Different waits.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")
    return rows


main()
