"""
highlight_test.py — docs/16's own criterion, measured instead of eyeballed.

docs/16 gives the test that decides whether a surface reads as a car or as a balloon: long controlled
highlight bands PASS, round soft ones are "ballooned", scattered ones mean the surface is over-worked
and dead-straight ones mean it is not worked at all. It was run once, on 2026-09-14, against the
preview loft, and the verdict was FAIL, ballooned -- correctly, because none of the three negative
spaces existed in that model. It has not been run since, and everything since v016 has been about
building those voids into the profile rather than cutting them.

The 2026 run was a judgement on two matcap screenshots. This measures.

WHAT A HIGHLIGHT IS, on a mesh. A studio strip light overhead reflects where the surface normal
bisects the eye and the light, so for a fixed direction L the highlight is the set of faces whose
n.L sits in a narrow band. That set is an ISOPHOTE, and its shape is the thing docs/16 is describing:
a long thin isophote is a long controlled highlight, a round isophote is a balloon.

THE FIRST ATTEMPT MEASURED THE MESH, NOT THE SURFACE, and it is left written down because it is the
fifth time this project has made that mistake. It took iso-bands of n.L, found their connected
components and reported ELONGATION, length over width. On a lofted body the faces are arranged in
rings, an iso-band follows one ring, and a band one face wide has a width of zero. The median
elongation came out at 34,211:1 and the verdict was PASS. That is the topology answering, not the
shape.

WHAT ACTUALLY DISTINGUISHES A BALLOON, and it is in docs/16's own words even if not in its numbers:
a balloon curves the same amount in every direction and a controlled surface does not. That is the
ratio of the two principal curvatures. Near 1 the surface is spherical, which is the balloon; near 0
it is cylindrical, which is the long highlight, because light sweeps along the direction that is not
curving. Both near zero is flat -- unsculpted, the other failure docs/16 names.

So this measures principal curvature per vertex, from the variation of the normal across the
one-ring, and reports the distribution. It is self-tested on a sphere, a cylinder and a plane on
every run, because a curvature estimator that has not been shown to return 1, 0 and nothing on those
three is not evidence of anything.

WHAT IT CANNOT DO. It says the surface holds a direction. It does not say the direction is the RIGHT
one, and it cannot see whether the light BREAKS where docs/16 wants it to break.

    import bpy; exec(open(".../highlight_test.py").read())
"""

import math
import os

import bmesh
import bpy
import mathutils

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT = os.path.join(REPO, "04_ENGINEERING", "statev_v01", "surface_test")


SAMPLE = 6000        # vertices sampled; the estimate is a distribution, not a per-vertex report
FLAT = 2e-4          # 1/mm below which both curvatures count as flat rather than shaped


def principal(co, nrm, ring):
    """k1, k2 at a vertex, from the normal curvature along each one-ring direction.

    For a neighbour w the normal curvature in that direction is 2*(n . (w-v)) / |w-v|^2. Fitting
    those against the second fundamental form in the tangent plane gives the two principal values.
    """
    n = nrm.normalized()
    u = mathutils.Vector((1, 0, 0))
    if abs(n.dot(u)) > 0.9:
        u = mathutils.Vector((0, 1, 0))
    e1 = (u - n * n.dot(u)).normalized()
    e2 = n.cross(e1).normalized()
    A, b = [], []
    for w in ring:
        d = w - co
        L2 = d.length_squared
        if L2 < 1e-12:
            continue
        k = 2.0 * n.dot(d) / L2
        t = (d - n * n.dot(d))
        if t.length < 1e-9:
            continue
        t.normalize()
        a, c = t.dot(e1), t.dot(e2)
        A.append((a * a, 2 * a * c, c * c))
        b.append(k)
    if len(A) < 3:
        return None
    # normal equations for the 3 unknowns of the shape operator
    M = [[0.0] * 3 for _ in range(3)]
    r = [0.0] * 3
    for row, bb in zip(A, b):
        for i in range(3):
            r[i] += row[i] * bb
            for j in range(3):
                M[i][j] += row[i] * row[j]
    for i in range(3):
        M[i][i] += 1e-12
    try:
        m = mathutils.Matrix(M).inverted()
    except ValueError:
        return None
    x = m @ mathutils.Vector(r)
    E, F, G = x[0], x[1], x[2]
    tr, det = E + G, E * G - F * F
    disc = max(tr * tr / 4.0 - det, 0.0) ** 0.5
    return tr / 2.0 + disc, tr / 2.0 - disc


def self_test():
    """A sphere must give a ratio near 1, a cylinder near 0, a plane nothing at all."""
    print("\nSELF-TEST of the curvature estimator")
    out = []
    for name, make, want in (("sphere r=500", "sphere", 1.0),
                             ("cylinder r=500", "cyl", 0.0),
                             ("plane", "plane", None)):
        bm = bmesh.new()
        if make == "sphere":
            bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.5)
        elif make == "cyl":
            # Built by hand. bmesh.ops.create_cone makes ONE ring along the axis, so every vertex
            # has three edges, the one-ring filter drops all of them and the test came back with no
            # vertices at all -- which is a failing test that says nothing about the estimator.
            import math as _m
            NS, NZ, R = 48, 12, 0.5
            vs = [[bm.verts.new((R * _m.cos(2 * _m.pi * i / NS), R * _m.sin(2 * _m.pi * i / NS),
                                 -1.0 + 2.0 * j / NZ)) for i in range(NS)] for j in range(NZ + 1)]
            for j in range(NZ):
                for i in range(NS):
                    i2 = (i + 1) % NS
                    bm.faces.new((vs[j][i], vs[j][i2], vs[j + 1][i2], vs[j + 1][i]))
        else:
            bmesh.ops.create_grid(bm, x_segments=24, y_segments=24, size=1.0)
        bm.verts.ensure_lookup_table()
        bm.normal_update()
        rs = []
        for v in bm.verts:
            if len(v.link_edges) < 4:
                continue
            p = principal(v.co, v.normal, [e.other_vert(v).co for e in v.link_edges])
            if p is None:
                continue
            k1, k2 = (abs(p[0]) / 1000.0, abs(p[1]) / 1000.0)   # per mm
            if max(k1, k2) < FLAT:
                rs.append(("flat", 0.0))
            else:
                rs.append(("shaped", min(k1, k2) / max(k1, k2)))
        shaped = [r for t, r in rs if t == "shaped"]
        flat = sum(1 for t, _ in rs if t == "flat")
        med = sorted(shaped)[len(shaped) // 2] if shaped else None
        ok = (want is None and flat > 0.8 * len(rs)) or \
             (want is not None and med is not None and abs(med - want) < 0.22)
        print(f"   {name:<16}{'ratio ' + f'{med:.2f}' if med is not None else 'no shaped verts':<22}"
              f"{'flat ' + str(flat):<10}{'PASS' if ok else 'FAIL'}")
        out.append(ok)
        bm.free()
    return all(out)

# Light directions. A car is judged on a strip light running along it and on the sky above, which is
# what a studio render and a showroom both give it, so the bank is tilted overhead sweeping across.
LIGHTS = [("overhead", (0.0, 0.0, 1.0)),
          ("high 3/4 left", (0.30, 0.55, 0.78)),
          ("high 3/4 right", (0.30, -0.55, 0.78)),
          ("low raking", (0.15, 0.92, 0.36))]
BANDS = [(0.92, 0.98), (0.84, 0.90), (0.74, 0.80), (0.62, 0.68)]
LONG = 4.0          # elongation at which a band counts as a controlled highlight rather than a blob
MIN_FACES = 12      # below this a component is noise, not a highlight


def main():
    if not self_test():
        print("\n   the estimator itself failed its own test — nothing below would mean anything")
        return
    P = []
    for o in bpy.data.collections["STATEV_MASTER"].all_objects:
        if o.type != "MESH" or "VOLUME" not in o.name:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        bm.normal_update()
        M = o.matrix_world
        N = M.to_3x3()
        for v in bm.verts:
            if len(v.link_edges) < 4:
                continue
            p = principal(v.co, v.normal, [e.other_vert(v).co for e in v.link_edges])
            if p is None:
                continue
            w = M @ v.co
            P.append((-w.x * 1000, abs(w.y * 1000), w.z * 1000,
                      abs(p[0]) / 1000.0, abs(p[1]) / 1000.0))
        bm.free()
    if not P:
        print("no STATEV_MASTER — build the body first")
        return

    def classify(k1, k2):
        hi, lo = max(k1, k2), min(k1, k2)
        if hi < FLAT:
            return "flat", 0.0
        return "shaped", lo / hi

    print("=" * 100)
    print("HIGHLIGHT TEST — docs/16's criterion as curvature, not as a look at a screenshot")
    print("=" * 100)
    ZONES = [("nose", -950, -640), ("front fender", -640, 350), ("door and channel", 350, 1635),
             ("haunch and intake", 1635, 2415), ("deck and buttress", 2415, 3000),
             ("tail", 3000, 3420)]
    print(f"\n{'zone':<20}{'verts':>7}{'flat %':>8}{'median ratio':>14}{'cylindrical %':>15}  reading")
    allr = []
    for name, a, b in ZONES:
        sel = [classify(p[3], p[4]) for p in P if a <= p[0] < b]
        if not sel:
            continue
        shaped = [r for t, r in sel if t == "shaped"]
        flat = sum(1 for t, _ in sel if t == "flat") / len(sel) * 100
        if not shaped:
            print(f"{name:<20}{len(sel):>7}{flat:>8.0f}{'--':>14}{'--':>15}  nothing but flat")
            continue
        med = sorted(shaped)[len(shaped) // 2]
        cyl = sum(1 for r in shaped if r < 0.25) / len(shaped) * 100
        allr += shaped
        reading = ("controlled — light runs" if med < 0.25 else
                   "BALLOONED — curves alike in every direction" if med > 0.55 else
                   "mixed")
        print(f"{name:<20}{len(sel):>7}{flat:>8.0f}{med:>14.2f}{cyl:>15.0f}  {reading}")
    med = sorted(allr)[len(allr) // 2]
    cyl = sum(1 for r in allr if r < 0.25) / len(allr) * 100
    print(f"\n  whole body: median principal-curvature ratio {med:.2f}, "
          f"{cyl:.0f}% of shaped vertices cylindrical (ratio under 0.25)")
    print("  0 is a cylinder and the long highlight docs/16 asks for; 1 is a sphere, the balloon.")
    verdict = ("PASS — the surface holds a direction" if med < 0.25 else
               "BALLOONED" if med > 0.55 else "MIXED — parts of the car hold a highlight, parts do not")
    print(f"\n  {verdict}")
    # Written out so check_goal.py can read it. It cannot run this itself -- the curvature needs the
    # mesh, and the mesh lives in Blender -- and a check that silently skips half of itself is worse
    # than no check.
    import json as _json
    import time as _time
    _p = os.path.join(REPO, "01_CAD/scripts/data/last_curvature.json")
    os.makedirs(os.path.dirname(_p), exist_ok=True)
    with open(_p, "w", encoding="utf-8") as _f:
        _json.dump({"curvature": round(med, 4), "cylindrical_pct": round(cyl, 1),
                    "when": _time.time(),
                    "blend": bpy.data.filepath}, _f, indent=2)
    print(f"\n  wrote {_p}")
    print("  It says the surface holds a DIRECTION, not that the direction is the right one, and it")
    print("  cannot see whether the light BREAKS at the three voids. That stays a separate question.")
    return P


main()
