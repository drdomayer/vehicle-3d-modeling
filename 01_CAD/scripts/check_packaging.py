"""
check_packaging.py — every envelope box against the body the sections actually produce.

check_lighting.py did this for the four lamps and found three of them placed wrongly. The mistake
behind all three was the same, and it has now cost this project four times counting the void
cutters before v016: a number taken from the INPUT to a loft is not a fact about its OUTPUT. The
section control data says one thing; the surface those sections generate says another, and parts
were being placed against the first.

So the check is generalised. For every box in statev_skeleton.BOXES it measures, at that box's own
station and inside that box's own Y band:

    ABOVE    how far the box's top stands above the body. Positive means it protrudes.
    OUTBOARD how far the box's outer edge stands beyond the body's half-width. Positive means it
             is wider than the car is there.

What counts as a fault depends on what the box is for, and the collection says which:

    04_LIGHTING     a cavity. Must be enclosed. Protruding is a fault.
    05_MECHANICAL   under the skin. Must be enclosed. Protruding is a fault.
    03_AERO         a surface feature. It sits ON the body, so a few mm either way is expected;
                    a large protrusion is still a fault.
    02_BODY         the body itself, or a design-group envelope around it. Reaching the surface is
                    the point, and these are reported for information only.

    import bpy; exec(open(".../check_packaging.py").read())
"""

import ast
import bpy
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
AERO_TOLERANCE_MM = 25.0      # a surface feature may stand this proud before it is called a fault

with open(os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), encoding="utf-8") as f:
    _src = f.read()
_i = _src.index("BOXES = [")
BOXES = ast.literal_eval(_src[_i + len("BOXES = "):_src.index("\n]", _i) + 2])

MUST_ENCLOSE = {"04_LIGHTING", "05_MECHANICAL"}
INFORMATIONAL = {"02_BODY"}

# Boxes whose mismatch is understood and waiting on something that is not modelling. They still
# print their numbers — a blocked item should stay visible — but they are not counted as faults,
# because a check that raises the same known thing every run stops being read.
KNOWN_BLOCKED = {
    "BUTTRESS": "the box carries the reference's intent, a blade to Z 1090. The built body has a "
                "10 mm lip on the crown instead, because a real blade needs the deck between the "
                "blades to drop and DECK_SPINE is marked BLOCKED in docs/14: its heights sit in "
                "the volume the soft top folds into. Waits on scan session S2, not on modelling.",
}


def body_points():
    master = bpy.data.collections.get("STATEV_MASTER")
    if master is None:
        return []
    return [(-(o.matrix_world @ v.co).x * 1000,
             (o.matrix_world @ v.co).y * 1000,
             (o.matrix_world @ v.co).z * 1000)
            for o in master.all_objects
            if o.type == "MESH" and "VOLUME" in o.name
            for v in o.data.vertices]


def main():
    V = body_points()
    if not V:
        print("no STATEV_MASTER volumes in the scene — build them first")
        return
    print("=" * 104)
    print("PACKAGING CHECK — 31 envelope boxes against the BUILT body, not the section data")
    print("=" * 104)
    rows, faults = [], 0
    for name, coll, x, y, z, sx, sy, sz, status, note in BOXES:
        z_hi = z + sz / 2.0
        y_lo, y_hi = max(0.0, abs(y) - sy / 2.0), abs(y) + sy / 2.0
        tol = max(60.0, sx / 2.0)
        station = [p for p in V if abs(p[0] - x) < tol]
        band = [p for p in station if y_lo <= abs(p[1]) <= y_hi]
        top = max((p[2] for p in band), default=None)
        hw = max((abs(p[1]) for p in station), default=None)
        above = None if top is None else z_hi - top
        out = None if hw is None else y_hi - hw
        limit = 0.0 if coll in MUST_ENCLOSE else AERO_TOLERANCE_MM
        fault = (coll not in INFORMATIONAL and name not in KNOWN_BLOCKED
                 and ((above is not None and above > limit)
                      or (out is not None and out > limit)))
        if fault:
            faults += 1
        rows.append((name, coll, x, above, out, fault, coll in INFORMATIONAL))

    print(f"\n{'BOX':<22}{'COLLECTION':<16}{'specX':>7}{'ABOVE body':>12}{'OUTBOARD':>11}  VERDICT")
    for name, coll, x, above, out, fault, info in rows:
        f = lambda v: "   --  " if v is None else f"{v:7.1f}"
        verdict = ("BLOCKED" if name in KNOWN_BLOCKED
                   else "info" if info else "FAULT" if fault else "ok")
        print(f"{name:<22}{coll:<16}{x:>7}{f(above)}{f(out)}  {verdict}")
    print(f"\n{faults} fault(s) outside 02_BODY.")
    for k, why in KNOWN_BLOCKED.items():
        print(f"\nBLOCKED  {k}: {why}")
    print("ABOVE and OUTBOARD are in millimetres; positive means the box sticks out of the car.")
    print("02_BODY rows are informational: those boxes ARE the body, so reaching the surface is")
    print("the point. Everything else is either a cavity that must be enclosed or a surface")
    print(f"feature allowed {AERO_TOLERANCE_MM:.0f} mm of stand-off.")
    return faults


main()
