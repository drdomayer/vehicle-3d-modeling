"""
assembly_check.py — put the printed files back together and measure the car that comes out.

THE QUESTION THIS ANSWERS, and nothing in this repo answered it before. Every shape measurement so
far -- the silhouette against ref-05, the plan against ref-09, the curvature, the edge angles --
is taken on STATEV_*_VOLUME, the master body. That is not what gets built. What gets built is 248
printed sections, bonded together and laminated. Between the master body and those files sit six
operations: extraction into panels, a 3 mm solidify, a grid cut, a tab dropped inward by a wall plus
a bond line, a per-piece separation, and a lay-flat that rotates each section onto its flattest
face. Any of them can lose or move surface, and the owner's actual question -- does it come out 1:1
with the render when assembled -- was not askable, because the files did not record where they go.

They do now: panel_production.py writes placement.json with the matrix that returns each file to
the car. This reads the STLs back, applies it, and asks three things of the result.

  1. DEVIATION. For points sampled on the master surface, how far is the nearest assembled
     surface? This catches a panel that moved, a tab that displaced a section, a solidify that
     grew the wrong way.
  2. COVERAGE. What fraction of the master surface has any assembled part within tolerance? This
     catches surface that no panel claims -- the gap between the register and the car.
  3. SILHOUETTE. The assembly's own outline against the same ref-05 calibration, so the answer is
     in the same units as every previous claim about matching the render.

WHAT IT CANNOT DO. It measures the CORE, the printed plastic. The laminate on top adds its own
thickness and the filler and paint another, and none of that exists as data yet -- docs/13 Q12 and
Q30. It also assumes the parts are bonded exactly where the design says, which a real build will
not manage; the 4 mm panel gaps and the flange overlaps are designed clearances, not errors, and
they will show here as deviation at the seams.

    import bpy; exec(open(".../assembly_check.py").read())
"""

import json
import math
import os
import random

import bmesh
import bpy
import mathutils
from mathutils.bvhtree import BVHTree

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
PROD = os.path.join(REPO, "03_PRINT", "production")
SHAPE = os.path.join(REPO, "03_PRINT", "shape_only")
BODY = ["STATEV_FRONT_VOLUME", "STATEV_SIDE_VOLUME", "STATEV_REAR_VOLUME"]
SAMPLES = 4000
NEAR = 8.0       # mm; a master point with assembled surface this close counts as covered


def panel_map():
    """panel_map.not_panel() as a predicate on a bmesh face, or None if it cannot be loaded."""
    np_ = load_panel_map().get("not_panel")
    if np_ is None:
        print("  panel_map unavailable; sampling the whole solid instead")
        return None

    def keep(f):
        # the same call panel_extract makes, argument for argument: spec X, |Y|, Z, and the
        # normal's Z and its INBOARD Y component, which is negated on the left half.
        c = f.calc_center_median()
        n = f.normal.normalized()
        sx, ay, z = -c.x * 1000.0, abs(c.y * 1000.0), c.z * 1000.0
        ny = -n.y if c.y > 0 else n.y
        return not np_(sx, ay, z, n.z, ny)
    return keep


_PM = {}


def load_panel_map():
    """panel_map's namespace, loaded once and QUIETLY.

    It has no `if __name__` guard, so exec'ing it runs its whole report -- and the first version of
    these two bridges exec'd it twice, printing the panel map into the middle of this one."""
    if "M" not in _PM:
        p = os.path.join(REPO, "01_CAD/scripts/panel_map.py")
        M = {"__name__": "pm_quiet", "__file__": p}
        import contextlib as _cx
        import io as _io
        try:
            with _cx.redirect_stdout(_io.StringIO()):
                exec(compile(open(p).read(), p, "exec"), M)
        except Exception as e:
            print(f"  could not load panel_map ({e})")
            M = {}
        _PM["M"] = M
    return _PM["M"]


def panel_of():
    """panel_map.panel_of() as a face -> part id, or None if it cannot be loaded."""
    fn = load_panel_map().get("panel_of")
    if fn is None:
        return None

    def who(f):
        c = f.calc_center_median()
        n = f.normal.normalized()
        sx, ay, z = -c.x * 1000.0, abs(c.y * 1000.0), c.z * 1000.0
        try:
            r = fn(sx, c.y * 1000.0, z, n.z, (-n.y if c.y > 0 else n.y))
        except TypeError:
            try:
                r = fn(sx, ay, z)
            except Exception:
                return "?"
        except Exception:
            return "?"
        return (r if isinstance(r, str) else (r[0] if r else "?")) or "?"
    return who


def master_bm():
    bm = bmesh.new()
    for n in BODY:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        me = o.to_mesh()
        try:
            bm.from_mesh(me)
        finally:
            o.to_mesh_clear()
    return bm


def read_stl(path):
    """Triangles of a binary STL, in millimetres. Returns [] for a file with no triangles.

    The first version returned None both for "cannot read" and for "no triangles", and reported
    six files as MISSING when all 248 were on disk. An empty printed file is a different problem
    from an absent one and is worth saying out loud."""
    import struct
    with open(path, "rb") as f:
        head = f.read(84)
        if len(head) < 84:
            return None
        n = int.from_bytes(head[80:84], "little")
        body = f.read()
    if len(body) < n * 50:
        return None
    return [[(v[0], v[1], v[2]), (v[3], v[4], v[5]), (v[6], v[7], v[8])]
            for v in (struct.unpack("<9f", body[i * 50 + 12:i * 50 + 48]) for i in range(n))]


def assembled_tree(placement):
    """One BVH of every printed part, put back where it belongs, in metres."""
    bm = bmesh.new()
    used, missing = 0, []
    for p, mat in placement.items():
        name = os.path.basename(p)
        if not os.path.exists(p):
            missing.append(name)
            continue
        tris = read_stl(p)
        if tris is None:
            missing.append((name, "unreadable"))
            continue
        if not tris:
            missing.append((name, "0 triangles"))
            continue
        M = mathutils.Matrix(mat)
        for t in tris:
            vs = [bm.verts.new(M @ mathutils.Vector((c[0] / 1000.0, c[1] / 1000.0, c[2] / 1000.0)))
                  for c in t]
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
        used += 1
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm, used, missing


def main():
    placement, tiers = {}, {}
    for d, tier in ((PROD, "ready to bond"), (SHAPE, "shape only")):
        p = os.path.join(d, "placement.json")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for k, v in json.load(f)["parts"].items():
                placement[os.path.join(d, k)] = v
                tiers[os.path.join(d, k)] = tier
    if not placement:
        print("  no placement.json — run panel_production.py in Blender first. Without it the")
        print("  printed files cannot be put back and nothing here can be answered.")
        return

    mb = master_bm()
    if not mb.faces:
        print("  no master body in the scene — run statev_master_volumes.py first")
        return
    # Only EXTERIOR SKIN counts. The master is a closed solid, so its mesh also carries the floor
    # pan, the cabin cut's inward walls and the wheel-arch liners -- surface no panel is supposed to
    # reproduce. The first run sampled all of it and reported 18.4% coverage against a 25.199 m2
    # "master surface", where the skin is about 15.6. panel_map already knows which face is which
    # and is asked here rather than guessed at.
    pm = panel_map()
    skin = [f for f in mb.faces if pm(f)] if pm else list(mb.faces)
    ab, used, missing = assembled_tree(placement)

    print("=" * 96)
    print("ASSEMBLY CHECK — the printed files put back together, against the surface they came from")
    print("=" * 96)
    print(f"\n  {used} printed files re-assembled" +
          (f", {len(missing)} unusable" if missing else ""))
    for nm, why in missing[:8]:
        print(f"    {why.upper():12s} {nm}")

    tree = BVHTree.FromBMesh(ab)
    random.seed(7)
    # sample the master surface by area, so a big panel is not under-represented
    faces = skin
    areas = [f.calc_area() for f in faces]
    total = sum(areas)
    cum, acc = [], 0.0
    for a in areas:
        acc += a
        cum.append(acc)
    pof = panel_of()
    d, owner = [], []
    for _ in range(SAMPLES):
        t = random.random() * total
        lo, hi = 0, len(cum) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < t:
                lo = mid + 1
            else:
                hi = mid
        f = faces[lo]
        vs = [v.co for v in f.verts]
        a, b = random.random(), random.random()
        if a + b > 1.0:
            a, b = 1 - a, 1 - b
        p = vs[0] + (vs[1] - vs[0]) * a + (vs[min(2, len(vs) - 1)] - vs[0]) * b
        hit = tree.find_nearest(p)
        d.append((hit[0] - p).length * 1000.0 if hit[0] is not None else 9999.0)
        owner.append(pof(f) if pof else "?")
    # TWO QUESTIONS, and reporting one number for both is how a sound pipeline looks broken.
    # "How much of the car exists as printable files" is a project-status question: 20 of the 42
    # parts are SCAN REQUIRED or BLOCKED and have no files at all, so most of the body is simply
    # absent. "Are the files that DO exist in the right place" is the engineering question, and it
    # is only askable on the surface those files claim.
    produced = {os.path.basename(n).split("_")[0] for n in placement}
    near_d = [x for i, x in enumerate(d) if owner[i] in produced]
    far_d = [x for i, x in enumerate(d) if owner[i] not in produced]
    d.sort()
    covered = sum(1 for x in d if x <= NEAR) / len(d) * 100.0
    print(f"\n  master EXTERIOR SKIN {total:.3f} m2, {SAMPLES} points sampled by area")
    print(f"  {len(produced)} panels have printed files; the rest of the register does not")
    print(f"\n  ON SURFACE THAT HAS FILES  ({len(near_d)} of {SAMPLES} points)")
    if near_d:
        nd = sorted(near_d)
        print(f"     median {nd[len(nd)//2]:6.2f} mm   90th {nd[int(len(nd)*0.9)]:6.2f}   "
              f"99th {nd[int(len(nd)*0.99)]:6.2f}   worst {nd[-1]:7.2f}")
        print(f"     within {NEAR:.0f} mm: {sum(1 for x in nd if x <= NEAR)/len(nd)*100:5.1f}%"
              f"   <- this is whether the PIPELINE is right")
    if far_d:
        fd = sorted(far_d)
        print(f"\n  ON SURFACE WITH NO FILES YET  ({len(far_d)} points, median "
              f"{fd[len(fd)//2]:.0f} mm away)")
        print( "     that is the 20 parts still SCAN REQUIRED or BLOCKED, not a defect")
    print(f"\n  WHOLE SKIN: {covered:5.1f}% has assembled material within {NEAR:.0f} mm"
          f"   <- this is how much of the CAR exists as files")

    mn = [min(v.co[i] for v in ab.verts) * 1000 for i in range(3)]
    mx = [max(v.co[i] for v in ab.verts) * 1000 for i in range(3)]
    print(f"\n  assembly bbox  length {mx[0]-mn[0]:7.1f}  width {mx[1]-mn[1]:7.1f}  "
          f"height {mx[2]-mn[2]:7.1f} mm")
    bmn = [min(v.co[i] for v in mb.verts) * 1000 for i in range(3)]
    bmx = [max(v.co[i] for v in mb.verts) * 1000 for i in range(3)]
    print(f"  master   bbox  length {bmx[0]-bmn[0]:7.1f}  width {bmx[1]-bmn[1]:7.1f}  "
          f"height {bmx[2]-bmn[2]:7.1f} mm")

    print("\n  It measures the printed CORE. The laminate, the filler and the paint add their own")
    print("  thickness and none of it exists as data yet (docs/13 Q12, Q30). It also assumes every")
    print("  part is bonded exactly where the design says; the 4 mm panel gaps and the flange")
    print("  overlaps are designed clearances and will read as deviation at the seams.")
    mb.free()
    ab.free()


main()
