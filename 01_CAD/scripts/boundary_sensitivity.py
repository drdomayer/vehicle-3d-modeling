"""
boundary_sensitivity.py — how conditional is CONDITIONAL, in millimetres.

Five panels are classified CONDITIONAL: their surface is ours but an approximate donor value places
a cut through them or bounds them. The label is correct and useless on its own, because it does not
say whether the uncertainty is something a trim allowance absorbs or something that rebuilds the
panel. That is a measurable question and this measures it.

Two different effects, and they are not the same size:

    BOUNDARY SHIFT  the donor value moves where one panel ends and the next begins. The surface
                    does not change; the cut line across it does. If the shift is inside the trim
                    allowance the panel can be built now with material left on and trimmed at the
                    fit test.
    SHAPE SHIFT     cowl_x and hoop_x also place the cabin cutter, which removes material from the
                    body. If those move, the body itself changes, not just the panel's boundary.
                    No trim allowance covers that.

The perturbation is +-25 mm, the middle of the +-15 to 30 mm band cage_986.py records for values
labelled approx. It is not a worst case; it is the stated uncertainty.

    import bpy; exec(open(".../boundary_sensitivity.py").read())
"""

import bmesh
import bpy
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
DELTA = 25.0
TRIM = 15.0     # PROVISIONAL trim allowance from pilot_P21.PROVISIONAL

_pm_src = open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8").read()
CONDITIONAL = ["P02", "P03", "P07"]          # P04 and P08 mirror P03 and P07
NAMES = {"P02": "HOOD", "P03": "FRONT_FENDER", "P07": "ROCKER"}

# Which boundary in panel_map.B each approximate donor value drives.
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
        for k, v in overrides.items():
            ns["B"][k] = v
    return ns


def measure(ns, body_pts):
    """Area and spec-X extent per panel, under one set of boundary values."""
    out = {}
    for pid, ay, z, sx, area in body_pts:
        p = ns["panel_of"](pid, ay, z)     # pid here is actually spec X; see caller
        if p is None:
            continue
        a, lo, hi = out.get(p, (0.0, 1e9, -1e9))
        out[p] = (a + area, min(lo, sx), max(hi, sx))
    return out


def gather():
    """Every exterior face once: (specX, |Y|, Z, specX again, area). Cheap to re-bin."""
    ns = load_map()
    master = bpy.data.collections["STATEV_MASTER"]
    pts = []
    for src in [o for o in master.all_objects if o.type == "MESH" and "VOLUME" in o.name]:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        for f in bm.faces:
            c = src.matrix_world @ f.calc_center_median()
            n = (src.matrix_world.to_3x3() @ f.normal).normalized()
            sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
            ny = -n.y if c.y > 0 else n.y
            if ns["not_panel"](sx, ay, z, n.z, ny):
                continue
            pts.append((sx, ay, z, sx, f.calc_area()))
        bm.free()
    return pts


def main():
    pts = gather()
    base_ns = load_map()
    base = measure(base_ns, pts)

    print("=" * 100)
    print("BOUNDARY SENSITIVITY — how far a CONDITIONAL panel's edge moves if the donor estimate is")
    print(f"out by {DELTA:.0f} mm, which is the middle of the +-15 to 30 mm band recorded for approx values")
    print("=" * 100)
    print(f"\n{'donor value':<14}{'moves':<14}{'panel':<8}{'area m2':>10}{'d area':>9}"
          f"{'d edge mm':>11}  verdict against the {TRIM:.0f} mm trim allowance")

    worst = 0.0
    for dval, keys in DRIVEN_BY.items():
        for sign in (+1, -1):
            ov = {k: base_ns["B"][k] + sign * DELTA for k in keys}
            ns = load_map(ov)
            got = measure(ns, pts)
            for pid in CONDITIONAL:
                if pid not in base or pid not in got:
                    continue
                a0, lo0, hi0 = base[pid]
                a1, lo1, hi1 = got[pid]
                d_area = a1 - a0
                d_edge = max(abs(lo1 - lo0), abs(hi1 - hi0))
                if abs(d_area) < 1e-6 and d_edge < 0.5:
                    continue
                worst = max(worst, d_edge)
                verdict = "trim absorbs it" if d_edge <= TRIM else "EXCEEDS the trim allowance"
                print(f"{dval:<14}{f'{sign:+.0f}{DELTA:.0f} mm':<14}{pid:<8}{a1:>10.3f}"
                      f"{d_area:>+9.3f}{d_edge:>11.1f}  {verdict}")

    print(f"\n  largest boundary movement across all four values and both directions: {worst:.1f} mm")
    print(f"  provisional trim allowance: {TRIM:.0f} mm")
    print("\n  SHAPE SHIFT is the other half and is NOT measured here. cowl_x and hoop_x also place")
    print("  the cabin cutter, so if they move the body itself changes and no trim covers that.")
    print("  Measuring it needs a rebuild per perturbation, which is the next step if this half")
    print("  comes out favourable.")
    return worst


main()
