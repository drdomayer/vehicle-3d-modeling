"""
check_lighting.py — does every lamp cavity actually fit inside the body, and is it still legal?

Runs inside Blender against the BUILT master volumes. That distinction is the whole point. The
projector's packaging note used to say the half-width at its station was 680 mm, which is what the
section CONTROL DATA says; the surface those sections produce gives 652 there. Checking a part
against the input to a loft rather than against its output is how a headlamp came to protrude
41.5 mm through the top of the nose without anything complaining.

Two checks per lamp:

    ENCLOSURE   the body, sampled only inside the lamp's own Y band, must reach at least the top
                of the cavity at the lamp's station. A lamp whose top is above the bodywork is not
                recessed, it is sticking out.
    LEGAL       CLAUDE.md hard constraint 5: a headlamp's lit surface sits at least 500 mm above
                the ground. The lit lower edge is taken as the cavity's lower edge.

    import bpy; exec(open(".../check_lighting.py").read())
"""

import ast
import bpy
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
LEGAL_MIN_MM = 500.0          # CLAUDE.md hard constraint 5, headlamp lit surface above ground

with open(os.path.join(REPO, "01_CAD/scripts/statev_skeleton.py"), encoding="utf-8") as f:
    _src = f.read()
_i = _src.index("BOXES = [")
BOXES = ast.literal_eval(_src[_i + len("BOXES = "):_src.index("\n]", _i) + 2])

LAMPS = [b for b in BOXES if any(k in b[0] for k in ("PROJECTOR", "DRL", "TAIL", "REFLECT"))]


def body_points():
    master = bpy.data.collections.get("STATEV_MASTER")
    if master is None:
        return None
    out = []
    for o in master.all_objects:
        if o.type == "MESH" and "VOLUME" in o.name:
            for v in o.data.vertices:
                p = o.matrix_world @ v.co
                out.append((-p.x * 1000, p.y * 1000, p.z * 1000))
    return out


def main():
    V = body_points()
    if not V:
        print("no STATEV_MASTER volumes in the scene — build them first")
        return
    print("=" * 96)
    print("LIGHTING PACKAGING CHECK, against the BUILT body rather than the section data")
    print("=" * 96)
    print(f"\n{'LAMP':<14}{'specX':>7}{'cavity Z':>12}{'body top in its Y band':>24}"
          f"{'ENCLOSURE':>11}{'LEGAL':>8}")
    bad = 0
    for name, coll, x, y, z, sx, sy, sz, status, note in LAMPS:
        z_lo, z_hi = z - sz / 2.0, z + sz / 2.0
        y_lo, y_hi = abs(y) - sy / 2.0, abs(y) + sy / 2.0
        near = [p for p in V if abs(p[0] - x) < max(60.0, sx / 2.0)
                and y_lo <= abs(p[1]) <= y_hi]
        top = max((p[2] for p in near), default=None)
        enc = "n/a" if top is None else ("OK" if top >= z_hi else f"OUT {z_hi - top:.0f}mm")
        legal = "n/a" if "PROJECTOR" not in name and "DRL" not in name else (
            "OK" if z_lo >= LEGAL_MIN_MM else f"LOW {LEGAL_MIN_MM - z_lo:.0f}mm")
        if enc.startswith("OUT") or legal.startswith("LOW"):
            bad += 1
        print(f"{name:<14}{x:>7}{f'{z_lo:.0f}..{z_hi:.0f}':>12}"
              f"{('--' if top is None else f'{top:.1f}'):>24}{enc:>11}{legal:>8}")
    print(f"\n{bad} problem(s).")
    if bad:
        print("A lamp that reads OUT is not recessed into the body; it protrudes by that much.")
        print("Moving it rearward along specX is usually the cheapest fix, because the body rises")
        print("toward the cowl. Dropping it is usually not: the legal floor leaves little margin.")
    return bad


main()
