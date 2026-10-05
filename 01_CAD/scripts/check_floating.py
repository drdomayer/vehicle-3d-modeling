"""
check_floating.py — does any separate element stand proud of the body where it should sit inside?

    Blender:  import bpy; exec(open(".../check_floating.py").read())

WHY. The owner's review twice in two days: "flying elements". Every time it was found by eye on a
render. This is the measurement: for every Stage-03 element (STATEV_STAGE03) the distance its
vertices stand OUTSIDE the body skin, by ray parity against the closed body volumes. A housing,
duct, mask frame or blade is meant to sit inside the skin or inside a pocket; a vertex outside the
skin by more than PROUD_MM is a part the car would show. Elements whose job is to stand proud
(the buttress sails, the diffuser fins under a rising floor) are listed with what they are.

Run after stage03_elements.py on the same build.
"""
import bpy
import mathutils

PROUD_MM = 3.0
EXPECTED_PROUD = {"BUTTRESS": "sail standing on the haunch (shape-only, scan S2)",
                  "DIFFUSER_FIN": "fin under the rising diffuser floor",
                  "SPLITTER_END": "end fence standing ahead of the chamfered corner (v060)"}


def body():
    """The skin BEFORE the Stage-03 openings (stage03_elements keeps a hidden copy): a blade in a
    pocket is outside the cut body by design and only the uncut skin says if it is proud."""
    c = bpy.data.collections.get("_STAGE03_UNCUT") or bpy.data.collections.get("STATEV_MASTER")
    return [o for o in c.all_objects if o.type == "MESH"] if c else []


def tree_of(objs):
    """One BVH over the body volumes in world space. Hidden objects have no evaluated mesh, so
    Object.ray_cast refuses them; a tree from the mesh data does not care."""
    from mathutils.bvhtree import BVHTree
    vs, fs = [], []
    for o in objs:
        M, b = o.matrix_world, len(vs)
        vs += [M @ v.co for v in o.data.vertices]
        fs += [[b + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(vs, fs)


def inside(tree, p):
    """Ray parity along two directions; both must agree, so a grazing ray cannot lie."""
    votes = []
    for d in (mathutils.Vector((0, 0, 1)), mathutils.Vector((0.013, -1, 0.017)).normalized()):
        n, org = 0, p.copy()
        for _ in range(64):
            loc, nor, idx, dist = tree.ray_cast(org, d)
            if loc is None:
                break
            n += 1
            org = loc + d * 1e-5
        votes.append(n % 2 == 1)
    return all(votes)


def outside_by(tree, p):
    """Distance from p to the nearest skin point, if p is outside the body; 0 if inside."""
    if inside(tree, p):
        return 0.0
    loc, nor, idx, dist = tree.find_nearest(p)
    return (dist or 0.0) * 1000.0


def main():
    objs = body()
    s3 = bpy.data.collections.get("STATEV_STAGE03")
    tree = tree_of(objs) if objs else None
    if not objs or not s3:
        print("  build the body and run stage03_elements.py first")
        return
    print("=" * 92)
    print("FLOATING CHECK — Stage-03 elements against the body skin, by ray parity")
    print("=" * 92)
    bad = 0
    rows = []
    for ob in sorted(s3.all_objects, key=lambda o: o.name):
        if ob.type != "MESH":
            continue
        M = ob.matrix_world
        vs = [M @ v.co for v in ob.data.vertices]
        step = max(1, len(vs) // 400)
        out = [outside_by(tree, p) for p in vs[::step]]
        worst = max(out) if out else 0.0
        share = sum(1 for d in out if d > PROUD_MM) / max(1, len(out)) * 100.0
        why = next((t for k, t in EXPECTED_PROUD.items() if k in ob.name), "")
        verdict = "ok" if worst <= PROUD_MM else ("expected" if why else "FLOATING")
        bad += verdict == "FLOATING"
        rows.append((ob.name, ob.get("panel_id", "-"), worst, share, verdict, why))
    print(f"\n  {'element':<26}{'part':<6}{'worst mm':>10}{'% proud':>9}   verdict")
    for n, pid, w, sh, v, why in rows:
        print(f"  {n:<26}{pid:<6}{w:>10.1f}{sh:>9.0f}   {v}{('  -- ' + why) if why else ''}")
    print(f"\n  {bad} element(s) stand proud of the skin where they should sit inside it.")
    print(f"  PROUD_MM {PROUD_MM}: a vertex closer than that to the skin is within the laminate.")
    return rows


main()
