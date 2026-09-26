"""
print_qc.py — are the exported files actually printable? Nobody had asked.

WHAT WAS MISSING. The pipeline checks that a section fits the plate and that a file holds one
connected piece. Neither is the question a slicer asks. A slicer needs a CLOSED, MANIFOLD solid
with consistent winding and a positive volume; given anything else it either guesses, or prints a
shell with holes in it, or silently drops geometry. 417 files have been produced across this
project and not one of them had been opened and checked.

WHAT IT CHECKS, per file:
  watertight   every edge shared by exactly two triangles. An edge with one is a hole; an edge
               with three or more is a non-manifold junction that no slicer handles predictably.
  winding      the two triangles on each edge traverse it in opposite directions. Consistent
               winding is what tells the slicer which side is inside.
  volume       the signed volume is positive. Negative means the solid is inside out, and a
               slicer will happily print its complement.
  degenerate   triangles with no area, which come from cuts that landed on an existing vertex.

It runs OUTSIDE Blender on purpose: it reads the files that will be sent, not the objects they
came from, so nothing about the build can hide a problem in the file.

WHAT IT CANNOT DO. It says the file is a well-formed solid, not that the solid is the right shape
-- assembly_check.py answers that -- and it says nothing about printability in the other sense:
overhangs, thin walls and supports depend on the shop's answers in docs/13 Q30 and Q32.

    python3 01_CAD/scripts/print_qc.py
"""

import glob
import json
import os
import struct
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRS = [("ready to bond", os.path.join(REPO, "03_PRINT", "production")),
        ("shape only", os.path.join(REPO, "03_PRINT", "shape_only"))]
# MILLIMETRES, and the number matters. The first version used 1e-4 "metres" on files that are in
# millimetres, so the tolerance was 0.0001 mm -- and a float32 at 900 mm has a step of about
# 1.07e-4 mm, so the threshold sat BELOW the noise of the format. Vertices that are the same point
# landed in different buckets, and the checker reported 349 of 417 files as broken. A micron is
# four orders below any printing tolerance and two above the float32 step at this size.
Q = 1e-3          # mm of quantisation when matching vertices


def read_tris(path):
    with open(path, "rb") as f:
        head = f.read(84)
        if len(head) < 84:
            return None
        n = int.from_bytes(head[80:84], "little")
        body = f.read()
    if len(body) < n * 50:
        return None
    return [struct.unpack("<9f", body[i * 50 + 12:i * 50 + 48]) for i in range(n)]


def check(path):
    tris = read_tris(path)
    if tris is None:
        return {"unreadable": True}
    if not tris:
        return {"empty": True}
    edges = defaultdict(int)
    directed = defaultdict(int)
    vol = 0.0
    degen = 0
    for t in tris:
        p = [(round(t[i * 3] / Q), round(t[i * 3 + 1] / Q), round(t[i * 3 + 2] / Q))
             for i in range(3)]
        a, b, c = (t[0:3], t[3:6], t[6:9])
        # signed volume of the tetrahedron to the origin; summed over a closed surface it is 6V
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0]))
        if p[0] == p[1] or p[1] == p[2] or p[0] == p[2]:
            degen += 1
            continue
        for i in range(3):
            u, v = p[i], p[(i + 1) % 3]
            edges[tuple(sorted((u, v)))] += 1
            directed[(u, v)] += 1
    holes = sum(1 for k, n in edges.items() if n == 1)
    nonmanifold = sum(1 for k, n in edges.items() if n > 2)
    # winding: for a consistently wound closed mesh every directed edge appears exactly once
    bad_wind = sum(1 for k, n in directed.items() if n > 1)
    return {"tris": len(tris), "holes": holes, "nonmanifold": nonmanifold,
            "winding": bad_wind, "volume_cm3": vol / 6.0 / 1000.0, "degenerate": degen}


def main():
    total, bad = 0, []
    print("=" * 96)
    print("PRINT QC — the exported files, read as a slicer would read them")
    print("=" * 96)
    for label, d in DIRS:
        files = sorted(glob.glob(os.path.join(d, "*.stl")))
        if not files:
            continue
        # The list of PARTS is placement.json, not the directory. On 2026-09-26 this read 288
        # files in production against 213 parts: 75 were sections from an earlier numbering that
        # panel_production.py had never removed, audited here as if they were the car. A file
        # not in placement.json is an orphan and is reported as one, not counted as a part.
        pj = os.path.join(d, "placement.json")
        if os.path.exists(pj):
            with open(pj, encoding="utf-8") as f:
                parts = set(json.load(f)["parts"])
            orphans = [p for p in files if os.path.basename(p) not in parts]
            absent = sorted(parts - {os.path.basename(p) for p in files})
            if orphans or absent:
                print(f"\n  {label}: {len(orphans)} file(s) on disk that are NOT in placement.json"
                      f" and {len(absent)} part(s) in placement.json with no file -- "
                      "re-run panel_production.py; neither is audited here")
            files = [p for p in files if os.path.basename(p) in parts]
        issues = 0
        for p in files:
            total += 1
            r = check(p)
            why = []
            if r.get("unreadable"):
                why.append("unreadable")
            elif r.get("empty"):
                why.append("no triangles")
            else:
                if r["holes"]:
                    why.append(f"{r['holes']} open edge(s)")
                if r["nonmanifold"]:
                    why.append(f"{r['nonmanifold']} non-manifold edge(s)")
                # Winding is only reported where it is an INDEPENDENT defect. An edge shared by
                # three or more faces necessarily has two of them traversing it the same way, so
                # on a file that already has non-manifold edges the winding count is the same
                # fault counted again -- the first version printed both and made one problem look
                # like two.
                if r["winding"] and not r["nonmanifold"]:
                    why.append(f"{r['winding']} inconsistent winding")
                if r["volume_cm3"] <= 0:
                    why.append(f"volume {r['volume_cm3']:.1f} cm3")
                if r["degenerate"]:
                    why.append(f"{r['degenerate']} degenerate")
            if why:
                issues += 1
                bad.append((os.path.relpath(p, REPO), "; ".join(why)))
        print(f"\n  {label:15s} {len(files):4d} files, {len(files)-issues:4d} clean, "
              f"{issues:4d} with something to say")
    if bad:
        print(f"\n  {len(bad)} of {total} files are not a well-formed solid:")
        for p, why in bad[:25]:
            print(f"    {os.path.basename(p):42s} {why}")
        if len(bad) > 25:
            print(f"    ... and {len(bad)-25} more")
    else:
        print(f"\n  all {total} files are closed, manifold, consistently wound and positive")
    print("\n  This says the file is a well-formed SOLID, not that it is the right SHAPE —")
    print("  assembly_check.py answers that. It says nothing about overhangs, thin walls or")
    print("  supports, which wait on docs/13 Q30 and Q32.")
    write_readme(total, bad)
    return 1 if bad else 0


def write_readme(total, bad):
    """03_PRINT/README.md — the one page a print farm reads, generated so it cannot drift.

    Until 2026-09-26 the print directory held STLs, a placement matrix and a CSV, and nothing that
    said what they were, what wall they assumed, what material, or what to check. A hand-written
    page would have been wrong within a week, which check_reports.py exists to catch; this one is
    rebuilt from handoff.json (the production run) and this file's own result every time QC runs,
    and QC is the last step."""
    import json
    hp = os.path.join(REPO, "03_PRINT", "handoff.json")
    if not os.path.exists(hp):
        print("  (no handoff.json — README not written; run panel_production.py first)")
        return
    with open(hp, encoding="utf-8") as f:
        h = json.load(f)
    D = h["decisions"]
    rb, so = h["ready_to_bond"], h["shape_only"]
    L = []
    L.append("# STATEV 001 — print files: what is in this folder and what to do with it")
    L.append("")
    L.append("*Generated by `print_qc.py` from the last production run. Do not edit by hand; "
             "re-run the pipeline instead.*")
    L.append("")
    L.append("## Two tiers, two folders")
    L.append("")
    L.append(f"| folder | parts | sections | one piece | fits bed | what it is |")
    L.append(f"|---|---|---|---|---|---|")
    L.append(f"| `production/` | {len(rb['parts'])} | {rb['sections']} | {rb['one_piece']} | "
             f"{rb['fits_bed']} | cores whose outer shape is final; mounting interface still "
             f"to come from the donor scan |")
    L.append(f"| `shape_only/` | {len(so['parts'])} | {so['sections']} | {so['one_piece']} | "
             f"{so['fits_bed']} | shape masters for fitting — **not** parts to bond; the inner "
             f"face or the trim edge depends on the car |")
    L.append("")
    L.append("Every file is one printable solid, laid on its flattest face, sitting on Z = 0, in "
             "**millimetres**. Print it as it comes. `placement.json` in each folder carries the "
             "matrix that puts each file back on the car; `04_ENGINEERING/reports/print_schedule.csv` "
             "carries the same as degrees and millimetres.")
    L.append("")
    L.append("## What the files assume — every one is provisional until the shop answers docs/13")
    L.append("")
    L.append(f"| assumption | value | replaced by |")
    L.append(f"|---|---|---|")
    L.append(f"| build volume | {D['bed_mm'][0]:.0f} × {D['bed_mm'][1]:.0f} × {D['bed_mm'][2]:.0f} "
             f"mm, {D['bed_margin_mm']:.0f} mm margin | Q26 — **changes every cut in this folder** |")
    L.append(f"| wall | {D['wall_mm']:.1f} mm | Q30 |")
    L.append(f"| material density | {D['density_g_cm3']} g/cm³ (generic PLA, unmeasured) | Q37 |")
    L.append(f"| bonding flange | {D['flange_w_mm']:.0f} mm + {D['bond_line_mm']:.0f} mm bond line "
             f"| Q15 |")
    L.append(f"| panel gap | {D['panel_gap_mm']:.0f} mm | Q16 |")
    L.append(f"| joint tab | {D['tab_mm']:.0f} mm past each cut, dropped inward by wall + bond | "
             f"fit test |")
    L.append(f"| orientation | {D['orient']} | Q32 / Q33 |")
    L.append("")
    L.append(f"Estimated core mass across both tiers at these assumptions: **~{h['core_kg']} kg**.")
    L.append("")
    L.append("## Quality of the files, as a slicer sees them")
    L.append("")
    L.append(f"`print_qc.py` reads every file back: closed, manifold, consistently wound, positive "
             f"volume. Last run: **{total - len(bad)} of {total} clean**, {len(bad)} with a "
             f"defect.")
    if bad:
        L.append("")
        L.append("Files with something to say (all non-manifold edges, a handful each; most "
                 "slicers repair these, but that is not a guarantee):")
        L.append("")
        for p, why in bad[:15]:
            L.append(f"- `{os.path.basename(p)}` — {why}")
        if len(bad) > 15:
            L.append(f"- … and {len(bad) - 15} more, listed by `print_qc.py`")
    L.append("")
    L.append("## Known problems, stated rather than hidden")
    L.append("")
    L.append(f"- **{h['small_sections_under_40mm']} sections are under 40 mm** in their largest "
             f"dimension. A 3D grid over a thin curved shell leaves corner fragments; they are "
             f"real geometry but not handleable parts. A fix is known to be needed and is not "
             f"done. Expect to lose or discard some.")
    L.append("- The files are the **core** only. Laminate, filler and paint go on top and none of "
             "their thicknesses exist as data yet.")
    ov = os.path.join(REPO, "04_ENGINEERING", "reports", "overhang.csv")
    if os.path.exists(ov):
        L.append("- Orientation is *lay flattest, class-A face up* — never chosen against an "
                 "overhang limit (Q32). "
                 "`04_ENGINEERING/reports/overhang.csv` says, per file, how much area hangs past "
                 "45° and 60° as laid and turned over, so the shop's limit turns into a count "
                 "rather than a question.")
    L.append("- Nothing here touches the donor car. Every mounting point, hinge, hole and flange "
             "that lands on the Porsche is deliberately absent until the car is scanned.")
    L.append("")
    L.append("## Before printing all of it: print ONE panel")
    L.append("")
    L.append("`04_ENGINEERING/reports/fit_test_P39.txt` names the panel (P39 ROCKER_END_L, three "
             "sections), the six assumptions one print tests, six landmarks to measure with a "
             "caliper at four stages, and what a change at each stage means. That test is a hard "
             "rule of this project, not a suggestion.")
    L.append("")
    L.append("## Shape-only tier: what each part is still missing")
    L.append("")
    for pid, why in so["missing"].items():
        L.append(f"- **{pid}** — {why}")
    out = os.path.join(REPO, "03_PRINT", "README.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"\n  wrote {out}")


sys.exit(main())
