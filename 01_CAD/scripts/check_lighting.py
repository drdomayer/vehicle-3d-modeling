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
    WIDTH       the lamp must not be wider than the car is at that station. TAIL_BAR was 1560 wide
                where the body is 1498, so it overhung by 31 mm a side on top of standing proud,
                and only the height was being looked at.
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
    print(f"\n{'LAMP':<14}{'specX':>7}{'cavity Z':>12}{'body top in band':>18}"
          f"{'half-width':>12}{'ENCLOSURE':>11}{'WIDTH':>10}{'LEGAL':>8}")
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
        station = [p for p in V if abs(p[0] - x) < max(60.0, sx / 2.0)]
        hw = max((abs(p[1]) for p in station), default=None)
        wid = "n/a" if hw is None else ("OK" if y_hi <= hw else f"OVER {y_hi - hw:.0f}mm")
        if enc.startswith("OUT") or legal.startswith("LOW") or wid.startswith("OVER"):
            bad += 1
        print(f"{name:<14}{x:>7}{f'{z_lo:.0f}..{z_hi:.0f}':>12}"
              f"{('--' if top is None else f'{top:.1f}'):>18}"
              f"{('--' if hw is None else f'{hw:.1f}'):>12}{enc:>11}{wid:>10}{legal:>8}")
    bad += visibility()
    bad += legal_geometry()
    print(f"\n{bad} problem(s).")
    if bad:
        print("A lamp that reads OUT is not recessed into the body; it protrudes by that much.")
        print("A lamp that reads OVER is wider than the car is at its own station.")
        print("Moving it rearward along specX is usually the cheapest fix, because the body rises")
        print("toward the cowl. Dropping it is usually not: the legal floor leaves little margin.")
    return bad


# R48 GEOMETRIC VISIBILITY of the dipped beam, added 2026-10-05 (v066) with the eye bezels. The
# angles are the regulation's: 45 deg outward, 10 inward, 15 up, 10 down from the lamp's axis. What
# is measured is the FRACTION OF THE LENS a ray leaving it at that angle clears everything built --
# body, Stage 03 elements, the bezels. Rays from 0.9 of the lens radius, 13 x 13 grid.
# What it does NOT decide: how much hidden apparent surface the technical service accepts. That is
# their call on the real lamp (hard constraint 6). What it guards: a styling part may never take a
# lens away silently. A direction at 0 % is a problem; anything else is printed for the engineer.
LENS = dict(sx=-675.0, y=645.0, z=560.0, r=45.0)    # PROJECTOR face, Hella 90 mm bi-LED
R48_DIRS = [("axis", 0.0, 0.0), ("45 out", 45.0, 0.0), ("10 in", -10.0, 0.0),
            ("15 up", 0.0, 15.0), ("10 down", 0.0, -10.0)]


def visibility():
    import math
    import bmesh
    import mathutils
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for cn in ("STATEV_MASTER", "STATEV_STAGE03"):
        c = bpy.data.collections.get(cn)
        if c is None:
            continue
        for o in c.all_objects:
            if o.type != "MESH" or o.name.startswith(("CUT_", "_")):
                continue
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            me.transform(o.matrix_world)
            bm.from_mesh(me)
            ev.to_mesh_clear()
    tree = BVHTree.FromBMesh(bm)
    print(f"\nR48 GEOMETRIC VISIBILITY, dipped beam -- fraction of the {2 * LENS['r']:.0f} mm lens a ray clears")
    print(f"{'side':<6}" + "".join(f"{d[0]:>10}" for d in R48_DIRS))
    bad = 0
    for sgn, side in ((1, "L"), (-1, "R")):
        row = []
        for _n, h, v in R48_DIRS:
            th, ph = math.radians(h), math.radians(v)
            d = mathutils.Vector((math.cos(th) * math.cos(ph), sgn * math.sin(th) * math.cos(ph), math.sin(ph)))
            ok = n = 0
            for i in range(-6, 7):
                for j in range(-6, 7):
                    y, z = LENS["y"] + 0.9 * LENS["r"] * i / 6, LENS["z"] + 0.9 * LENS["r"] * j / 6
                    if (y - LENS["y"]) ** 2 + (z - LENS["z"]) ** 2 > (0.9 * LENS["r"]) ** 2:
                        continue
                    o = mathutils.Vector((-LENS["sx"] / 1000.0 + 0.0015, sgn * y / 1000.0, z / 1000.0))
                    n += 1
                    ok += tree.ray_cast(o, d, 3.0)[0] is None
            row.append(100.0 * ok / n)
            bad += ok == 0
        print(f"{side:<6}" + "".join(f"{r:>9.0f}%" for r in row))
    bm.free()
    print("  0 % in any direction is a problem; how much obstruction the technical service accepts is")
    print("  theirs to judge on the real lamp. The eye bezels are cut by this cone, so they add none.")
    return bad


# R48 MOUNTING GEOMETRY per function, added 2026-10-06 with the envelopes for the rest of the
# legal lighting (hard constraint 5). VALUES FROM MEMORY OF UN R48 -- every number below is to be
# confirmed by the technical service before anything is cut (hard constraint 6). The vehicle's
# extreme outer edge is the locked half-width, 925; heights are the lit envelope's own edges.
# h: (min, max) for both edges; outer: max distance from the vehicle's outer edge to the lamp's
# outer edge; sep: min distance between the inner edges of the pair; front: max distance from the
# front of the vehicle (nose, spec X -950); low: minimum height of the lower edge.
HALF_W, NOSE_X = 925.0, -950.0
R48 = [
    ("PROJECTOR",      "dipped beam",            dict(h=(500, 1200), outer=400)),
    ("IND_FRONT",      "front indicator",        dict(h=(350, 1500), outer=400, sep=600)),
    ("IND_SIDE",       "side indicator cat 5",   dict(h=(350, 1500), front=1800)),
    ("TAIL_END",       "rear position/stop/ind.", dict(h=(350, 1500), outer=400, sep=600)),
    ("CHMSL",          "third stop lamp",        dict(low=850)),
    ("REVERSE",        "reversing lamp",         dict(h=(250, 1200))),
    ("FOG_REAR",       "rear fog lamp",          dict(h=(250, 1000), stop_gap=100)),
    ("REFLECTOR_REAR", "rear retro-reflector",   dict(h=(250, 900), outer=400, sep=600)),
    ("PLATE_LAMP",     "plate lamp",             dict()),
]


def legal_geometry():
    box = {b[0]: b for b in BOXES}
    tb = box.get("TAIL_BAR")
    stop_low = tb[4] - tb[7] / 2.0 if tb else None
    print("\nR48 MOUNTING GEOMETRY -- every function the law asks for, against its envelope")
    print("  (R48 values from memory; the technical service confirms them -- hard constraint 6)")
    print(f"  {'function':26s}{'envelope':16s}{'height':>14s}  checks")
    bad = 0
    for nm, what, r in R48:
        b = box.get(nm)
        if b is None:
            print(f"  {what:26s}{nm:16s}{'--':>14s}  MISSING -- no envelope")
            bad += 1
            continue
        _n, _c, x, y, z, sx, sy, sz, _st, _note = b
        lo, hi = z - sz / 2.0, z + sz / 2.0
        y_in, y_out = abs(y) - sy / 2.0, abs(y) + sy / 2.0
        notes = []
        if "h" in r:
            ok = r["h"][0] <= lo and hi <= r["h"][1]
            notes.append(f"height {r['h'][0]}..{r['h'][1]} {'ok' if ok else 'FAIL'}")
            bad += not ok
        if "low" in r:
            ok = lo >= r["low"]
            notes.append(f"lower edge >= {r['low']}: {lo:.0f} {'ok' if ok else 'FAIL'}")
            bad += not ok
        if "outer" in r and y:
            d = HALF_W - y_out
            ok = d <= r["outer"]
            notes.append(f"outer edge {d:.0f} from the side (<= {r['outer']}) {'ok' if ok else 'FAIL'}")
            bad += not ok
        if "sep" in r and y:
            d = 2.0 * y_in
            ok = d >= r["sep"]
            notes.append(f"pair {d:.0f} apart (>= {r['sep']}) {'ok' if ok else 'FAIL'}")
            bad += not ok
        if "front" in r:
            d = x - NOSE_X
            ok = d <= r["front"]
            notes.append(f"{d:.0f} from the front (<= {r['front']}) {'ok' if ok else 'FAIL'}")
            bad += not ok
        if "stop_gap" in r and stop_low is not None:
            d = stop_low - hi
            ok = d >= r["stop_gap"]
            notes.append(f"{d:.0f} below the stop lamps (>= {r['stop_gap']}) {'ok' if ok else 'FAIL'}")
            bad += not ok
        print(f"  {what:26s}{nm:16s}{f'{lo:.0f}..{hi:.0f}':>14s}  " + "; ".join(notes or ["present"]))
    print("  Envelopes only: the apertures, the modules' E-marks and their photometry are not checked here.")
    return bad


main()
