"""
exploded_assembly.py — the other half of the manufacturing prompt, which has been recorded as
unexecuted since 2026-09-14 because it needed real surfaces. The parts now exist, so it runs.

panel_registry.py listed what it could not do without geometry: mass, centre of mass, the exploded
view itself, and whether the assembly order actually works. Three of those four are exact arithmetic
on the extracted parts and are done here. The fourth is not exact and is not pretended to be.

    EXPLODED VIEW      each part moved along its own install vector, by a distance that grows with
                       its assembly step, so the order is readable in the picture rather than only
                       in the table. Exact: it is a translation, nothing is reshaped.
    MASS AND BALANCE   volume and centroid of each part's core, and the assembly's centre of mass.
                       Exact given the wall and the density, and BOTH of those are assumptions --
                       3.0 mm and 1.24 g/cm3 -- so the mass is provisional and the BALANCE is the
                       useful part, because a ratio survives a wrong density.
    REMOVAL SCREEN     the register claims every part comes off without removing another. That is a
                       swept-volume question and this is NOT a swept-volume test. It is a screen:
                       the part's footprint perpendicular to its install vector, against the
                       footprint of every part fitted earlier, plus their order along that vector.
                       It can raise a false alarm where panels nest without touching, and it cannot
                       see a part that fouls only after rotating. It says "look here", never "this
                       is fine".

    import bpy; exec(open(".../exploded_assembly.py").read())
"""

import bmesh
import bpy
import colorsys
import csv
import math
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT_CSV = os.path.join(REPO, "04_ENGINEERING", "reports", "exploded_assembly.csv")
SHOTS = os.path.join(REPO, "04_ENGINEERING", "statev_v01", "exploded")
COLL = "STATEV_EXPLODED"
GAP = 110.0          # mm of separation per assembly step, for the picture only

_pr = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_registry.py"), "__name__": "_pr"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_registry.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(argv):")[0], _pr)
PARTS = {p[0]: p for p in _pr["PARTS"]}

_pp = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_pipeline.py"), "__name__": "_pp"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_pipeline.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pp)
WALL = _pp["WORKING"]["core_wall_mm"]
DENSITY = _pp["WORKING"]["density_g_cm3"]

# Install vector -> unit direction in REPO axes (X forward, Y left, Z up). Spec X is +rearward, so
# a part installed "+X" travels forward in repo terms; the register's vectors are read in spec.
VEC = {"+X": (-1, 0, 0), "-X": (1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0),
       "+Z": (0, 0, 1), "-Z": (0, 0, -1)}


def solid(ob, wall_mm):
    """A copy of the panel given its core wall, so mass and centroid mean something."""
    cp = ob.copy()
    cp.data = ob.data.copy()
    bpy.context.scene.collection.objects.link(cp)
    m = cp.modifiers.new("core", "SOLIDIFY")
    m.thickness, m.offset, m.use_even_offset = wall_mm / 1000.0, -1.0, False
    bpy.context.view_layer.objects.active = cp
    bpy.ops.object.modifier_apply(modifier=m.name)
    return cp


def volume_and_centroid(ob):
    """Signed-tetrahedron volume and centroid about the origin. Exact for a closed mesh."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    vol = 0.0
    cx = cy = cz = 0.0
    for f in bm.faces:
        a, b, c = (ob.matrix_world @ v.co for v in f.verts)
        d = a.dot(b.cross(c)) / 6.0
        vol += d
        cx += d * (a.x + b.x + c.x) / 4.0
        cy += d * (a.y + b.y + c.y) / 4.0
        cz += d * (a.z + b.z + c.z) / 4.0
    bm.free()
    if abs(vol) < 1e-12:
        return 0.0, (0.0, 0.0, 0.0)
    return abs(vol), (cx / vol, cy / vol, cz / vol)


def footprint(ob, axis):
    """The part's extent in the two axes perpendicular to `axis`, plus its span along it."""
    w = [ob.matrix_world @ v.co for v in ob.data.vertices]
    ax = [abs(a) for a in axis].index(1)
    per = [i for i in (0, 1, 2) if i != ax]
    g = lambda i: [(p.x, p.y, p.z)[i] * 1000 for p in w]
    return ((min(g(per[0])), max(g(per[0]))), (min(g(per[1])), max(g(per[1]))),
            (min(g(ax)), max(g(ax))))


def overlap(a, b, slack=0.0):
    return a[0] - slack < b[1] and b[0] - slack < a[1]


def main():
    src = bpy.data.collections.get("STATEV_PANELS")
    if src is None:
        print("no STATEV_PANELS — run panel_extract.py first")
        return
    old = bpy.data.collections.get(COLL)
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(coll)

    have = {o.get("panel_id"): o for o in src.objects if o.get("panel_id")}
    order = sorted(have, key=lambda p: (int(PARTS[p][4]), p))

    print("=" * 108)
    print("EXPLODED ASSEMBLY — mass, balance, and a screen on the removal rule")
    print("=" * 108)
    print(f"\n{'step':>5} {'part':<7}{'name':<22}{'vec':<5}{'mass kg':>9}{'centroid specX,Y,Z':>26}")

    rows, solids, total_m, mx, my, mz = [], {}, 0.0, 0.0, 0.0, 0.0
    for i, pid in enumerate(order):
        pr = PARTS[pid]
        step, vec = int(pr[4]), pr[5]
        sol = solid(have[pid], WALL)
        vol, c = volume_and_centroid(sol)
        mass = vol * 1e9 / 1000.0 * DENSITY / 1000.0          # m3 -> cm3 -> g -> kg
        solids[pid] = sol
        total_m += mass
        mx += mass * -c[0] * 1000
        my += mass * c[1] * 1000
        mz += mass * c[2] * 1000
        print(f"{step:>5} {pid:<7}{pr[1]:<22}{vec:<5}{mass:>9.2f}"
              f"{f'{-c[0]*1000:.0f}, {c[1]*1000:.0f}, {c[2]*1000:.0f}':>26}")
        rows.append(dict(PART=pid, NAME=pr[1], SIDE=pr[2], STEP=step, INSTALL_VECTOR=vec,
                         MASS_KG=round(mass, 3), CORE_VOLUME_CM3=round(vol * 1e9 / 1000.0, 1),
                         CENTROID_SPECX=round(-c[0] * 1000, 1), CENTROID_Y=round(c[1] * 1000, 1),
                         CENTROID_Z=round(c[2] * 1000, 1)))

        # exploded copy, for the picture
        ep = have[pid].copy()
        ep.data = have[pid].data.copy()
        ep.name = f"X_{pid}_{pr[1]}"
        # An exploded view separates parts along the direction they come OFF, which is the reverse
        # of the install vector, so each part floats away from the car rather than into it.
        d = VEC.get(vec, (0, 0, 1))
        k = -GAP * (step - 2) / 1000.0
        ep.location = (d[0] * k, d[1] * k, d[2] * k)
        mat = bpy.data.materials.new(f"MX_{pid}")
        mat.use_nodes = False
        r, g, b = colorsys.hsv_to_rgb(i / max(1, len(order)), 0.62, 0.92)
        mat.diffuse_color = (r, g, b, 1.0)
        ep.data.materials.append(mat)
        coll.objects.link(ep)

    print(f"\n  {len(rows)} parts with geometry   total core {total_m:.1f} kg")
    print(f"  centre of mass of the bodywork alone: specX {mx/total_m:.0f}, "
          f"Y {my/total_m:.1f}, Z {mz/total_m:.0f}")
    print(f"  wheelbase 0..2415, so the shell's mass sits "
          f"{(mx/total_m)/2415*100:.0f}% of the way back between the axles.")
    print(f"  Y {my/total_m:.1f} mm off centre is the symmetry check: it should be zero and this is")
    print("  how far from zero the parts actually are.")
    print(f"  MASS IS PROVISIONAL: {WALL} mm wall x {DENSITY} g/cm3, both assumptions. The BALANCE")
    print("  survives a wrong density; the kilograms do not.")

    # ---- removal screen
    print("\nREMOVAL SCREEN — a screen, not a swept-volume test. It asks whether a part fitted")
    print("EARLIER sits in the corridor this part travels through on its way OFF the car, which is")
    print("the reverse of its install vector.")
    flags = 0
    for i, pid in enumerate(order):
        vec = PARTS[pid][5]
        # REMOVAL travels the reverse of the install vector -- the register says so in as many
        # words. The first run of this screen tested the install direction instead and raised 36
        # pairs, most of them a rear part "passing" every panel ahead of it while actually moving
        # away from the car.
        iv = VEC.get(vec, (0, 0, 1))
        d = (-iv[0], -iv[1], -iv[2])
        ax = [abs(a) for a in d].index(1)
        sgn = d[ax]
        pa, pb, span = footprint(have[pid], d)
        for earlier in order[:i]:
            if PARTS[earlier][4] == PARTS[pid][4]:
                continue                     # same step: they go on together, order undefined
            qa, qb, qspan = footprint(have[earlier], d)
            if not (overlap(pa, qa) and overlap(pb, qb)):
                continue
            # is the earlier part beyond this one along the travel direction?
            ahead = (qspan[1] > span[1]) if sgn > 0 else (qspan[0] < span[0])
            if ahead:
                flags += 1
                back = {"+X": "-X", "-X": "+X", "+Y": "-Y", "-Y": "+Y",
                        "+Z": "-Z", "-Z": "+Z"}[vec]
                print(f"   {pid} ({PARTS[pid][1]}, step {PARTS[pid][4]}, comes off {back}) passes the "
                      f"footprint of {earlier} ({PARTS[earlier][1]}, step {PARTS[earlier][4]})")
    print(f"   {flags} pair(s) raised. Each needs a look at the real surfaces before it means")
    print("   anything: nesting panels overlap in footprint without touching.")

    for s in solids.values():
        bpy.data.objects.remove(s, do_unlink=True)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT_CSV}")
    print(f"built collection {COLL}: {len(coll.objects)} parts, coloured, offset along their own")
    print(f"install vectors by {GAP:.0f} mm per assembly step.")
    return rows


main()
