"""
panel_extract.py — turn the panel map into actual separate panel objects, and measure them.

panel_map.py proved the 38 registered parts tile the body with nothing left over. This takes the
next step: it cuts the body along those boundaries into one object per panel, measures each, and
fills in the columns panel_bom.csv has been carrying as NEEDS_GEOMETRY since the register was
written — length, width, height, surface area, solid volume with the print core wall, and an
estimated mass.

WHAT THIS IS NOT, and it matters. v020 is a Stage 01 blockout and docs/16 says the blockout is
discarded once real surfacing begins, so these are not the panels that will be printed. They are
the right SHAPE OF ANSWER at the wrong STAGE: the numbers tell you how big each panel is, how many
printer beds it needs and roughly what it weighs, which is what the supplier questionnaire and the
split strategy need long before the final surfaces exist. Every figure is recomputed from whatever
geometry is current, so none of it has to be maintained by hand.

Mass rests on an assumed density and a design-assumption wall thickness, both flagged in
panel_pipeline.py. They are order-of-magnitude figures, not quotes.

    import bpy; exec(open(".../panel_extract.py").read())
"""

import bmesh
import bpy
import csv
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
OUT_CSV = os.path.join(REPO, "04_ENGINEERING", "reports", "panel_measured.csv")

# One dict as BOTH globals and locals. With two dicts the functions defined in there capture the
# globals one and their module-level data lands in the locals one, so panel_of() cannot see B.
_pm = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_map.py"), "__name__": "_pm"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_map.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pm)
panel_of = _pm["panel_of"]
not_panel = _pm["not_panel"]
NAME_OF = _pm["NAME_OF"]
PALETTE_ORDER = _pm["PALETTE_ORDER"]

_pp = {"__file__": os.path.join(REPO, "01_CAD/scripts/panel_pipeline.py"), "__name__": "_pp"}
with open(os.path.join(REPO, "01_CAD/scripts/panel_pipeline.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(")[0], _pp)
WORKING = _pp["WORKING"]
PRINTER = _pp["PRINTER"]


def extract_panels(coll_name="STATEV_PANELS"):
    """One mesh object per panel id, cut out of the master volumes along the mapped boundaries."""
    old = bpy.data.collections.get(coll_name)
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(coll_name)
    bpy.context.scene.collection.children.link(coll)

    master = bpy.data.collections["STATEV_MASTER"]
    bodies = [o for o in master.all_objects if o.type == "MESH" and "VOLUME" in o.name]
    made = {}
    for pid in PALETTE_ORDER:
        verts, faces = [], []
        for src in bodies:
            bm = bmesh.new()
            bm.from_mesh(src.data)
            bm.faces.ensure_lookup_table()
            for f in bm.faces:
                c = src.matrix_world @ f.calc_center_median()
                n = (src.matrix_world.to_3x3() @ f.normal).normalized()
                sx, ay, z = -c.x * 1000, abs(c.y * 1000), c.z * 1000
                ny = -n.y if c.y > 0 else n.y
                if not_panel(sx, ay, z, n.z, ny):
                    continue
                if panel_of(sx, ay, z) != pid:
                    continue
                base = len(verts)
                for v in f.verts:
                    verts.append(tuple(src.matrix_world @ v.co))
                faces.append(tuple(range(base, base + len(f.verts))))
            bm.free()
        if not faces:
            continue
        me = bpy.data.meshes.new(f"PANEL_{pid}")
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new(f"{pid}_{NAME_OF.get(pid, 'PANEL')}", me)
        ob["panel_id"] = pid
        ob["stage"] = "01 blockout region — not a production panel"
        coll.objects.link(ob)
        made[pid] = ob
    return made


# panel_map keys on |Y|, so these regions answer for both sides at once and come out of extraction
# as a mirrored pair. Their piece count has to be read per side or every one of them looks split.
MIRRORED = {"P03", "P04", "P07", "P08", "P09", "P10", "P11", "P12", "P15", "P16",
            "P17", "P18", "P28", "P41", "P39", "P40", "P19", "P42"}


def measure(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    area = sum(f.calc_area() for f in bm.faces)
    bm.to_mesh(ob.data)
    # How many disconnected pieces the region is in, per side. A region in two pieces is not one
    # part, however tidy its area figure looks, and the area figure is what hid it: P07 and P28
    # both measured plausibly and both print in two. Mirrored regions answer for both sides of the
    # car, so their count is halved -- the mirror is not a second piece.
    bm.verts.ensure_lookup_table()
    seen, n = set(), 0
    for v in bm.verts:
        if v in seen:
            continue
        n += 1
        stack = [v]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(e.other_vert(u) for e in u.link_edges)
    mirrored = ob.get("panel_id") in MIRRORED
    pieces = n // 2 if mirrored and n % 2 == 0 else n
    bm.free()
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    sx = [-v.x * 1000 for v in vs]
    y = [v.y * 1000 for v in vs]
    z = [v.z * 1000 for v in vs]
    wall = WORKING["core_wall_mm"]
    vol_mm3 = area * 1e6 * wall                      # area m2 -> mm2, times the wall
    mass_g = vol_mm3 / 1000.0 * WORKING["density_g_cm3"]
    return dict(PIECES=pieces, LENGTH=round(max(sx) - min(sx), 1), WIDTH=round(max(y) - min(y), 1),
                HEIGHT=round(max(z) - min(z), 1), AREA_M2=round(area, 3),
                CORE_VOLUME_CM3=round(vol_mm3 / 1000.0, 1), EST_MASS_KG=round(mass_g / 1000.0, 2),
                FACES=len(ob.data.polygons))


def main():
    print("=" * 100)
    print("PANEL EXTRACT — the mapped regions cut out and measured")
    print("v020 is a Stage 01 blockout; these are regions at blockout stage, not production panels.")
    print("=" * 100)
    made = extract_panels()
    rows = []
    print(f"\n{'ID':<6}{'PART':<22}{'L':>8}{'W':>8}{'H':>8}{'AREA m2':>10}"
          f"{'core cm3':>11}{'mass kg':>9}{'pieces':>8}")
    for pid, ob in made.items():
        m = measure(ob)
        rows.append(dict(ID=pid, PART=NAME_OF.get(pid, "?"), **m))
        print(f"{pid:<6}{NAME_OF.get(pid,'?'):<22}{m['LENGTH']:>8.0f}{m['WIDTH']:>8.0f}"
              f"{m['HEIGHT']:>8.0f}{m['AREA_M2']:>10.3f}{m['CORE_VOLUME_CM3']:>11.0f}"
              f"{m['EST_MASS_KG']:>9.2f}{m['PIECES']:>8}"
              + ("" if m["PIECES"] == 1 else "   <-- not one part"))
    split = [r["ID"] for r in rows if r["PIECES"] != 1]
    if split:
        print(f"\n  {len(split)} region(s) are NOT one connected part: {' '.join(split)}")
        print("  The register carries each as one part. Whether to split the entry, absorb the")
        print("  loose piece into a neighbour, or bridge over the opening is a register decision.")
        print("  pilot_panel.py refuses to export an STL for any of them until it is taken.")
    tot_a = sum(r["AREA_M2"] for r in rows)
    tot_m = sum(r["EST_MASS_KG"] for r in rows)
    print(f"\n  {len(rows)} panel regions   total skin {tot_a:.3f} m2   "
          f"total core mass ~{tot_m:.1f} kg")
    print(f"  wall {WORKING['core_wall_mm']} mm is a DESIGN ASSUMPTION; density "
          f"{WORKING['density_g_cm3']} g/cm3 is an ENGINEERING ASSUMPTION. Neither is a quote.")
    if PRINTER["build_x_mm"] is None:
        print("  bed count per panel is not computed: the printer's usable build volume is still")
        print("  unknown (docs/13 Q26), and nothing here guesses it.")
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT_CSV}")
    return rows


main()
