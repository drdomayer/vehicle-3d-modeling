"""
check_reports.py — is what is written down still about the car that is built?

WHY IT EXISTS. On 2026-09-21 the rocker's spec-X extent in manufacturing_audit.csv read 292..2122.
Re-run on the same scene with the same scripts it comes out 292..2069. The committed value dated
from v026 and had survived v027, v028, v029 and v030 untouched, while the audit was RUN in those
sessions and its summary reported to the owner. Fifty-three millimetres of a panel boundary, in a
file that feeds the supplier package, four versions out of date, and nothing in the repo could tell.

That is the same hole that was closed for the goal check on 2026-09-18 — the ortho silhouettes and
the curvature file are now refused when older than the build — except it was closed for two files
and left open for every other generated file in the project. A stale report does not fail: it
answers confidently about a car that no longer exists.

WHAT IT CHECKS, in two steps, because one number cannot answer both questions. The first version of
this file compared every report against the newest build script's MTIME and immediately proved
itself too blunt: a `git checkout` of a script touches it without changing it, and every report in
the project went red. The reverse fails too — edit a script and do not rebuild, and the SCENE is
stale while every report looks current.

  1. is the BUILD current with the scripts?  a sha of the three build scripts' bytes, stamped into
     data/last_build.json by statev_master_volumes.build(), against the same sha now.
  2. is each REPORT current with the build?  its mtime against the build's own timestamp.

Files with a version in the name -- v014_report.txt and its kind -- are skipped. CLAUDE.md is
explicit that a report with a version in its name is historical and NOT current, so flagging it is
noise, and noise is how a check stops being read.

What it still cannot do: tell a report that was re-run and came out identical from one that was
never re-run, and see a change that came from a data file rather than a script.

    python3 01_CAD/scripts/check_reports.py
"""

import hashlib
import json
import os
import re
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = ["statev_skeleton.py", "statev_master_volumes.py", "stage03_elements.py"]
WATCH = [("04_ENGINEERING/reports", (".csv", ".txt")),
         ("04_ENGINEERING/statev_v01/overlay", (".png",)),
         ("04_ENGINEERING/statev_v01/plan", (".png",)),
         ("01_CAD/scripts/data", ("last_curvature.json", "last_surface.json",
                                 "goal_baseline.json")),
         ("03_PRINT", ("README.md", "handoff.json"))]


def scripts_sha():
    h = hashlib.sha256()
    for n in BUILD:
        with open(os.path.join(REPO, "01_CAD/scripts", n), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


# v019_report.txt and _v015 both count. The first version of this regex required the underscore and
# flagged five historical reports as stale, which is exactly the noise that stops a check being read.
HISTORICAL = re.compile(r"(^|_)v0\d\d")

# Files in these directories that are not reports about the current car. Listed with the reason
# rather than silently skipped, so the list can be argued with.
# Who writes what. Saying "re-run the scripts that write these" and not saying WHICH is how the
# three orphans survived a week: nobody could tell that no script wrote them. A file here with no
# entry is reported as an ORPHAN, which is a harder thing to ignore than "stale".
# (B) = needs Blender, (P) = plain python3.
WRITER = {
    "manufacturing_audit.csv": "(B) manufacturing_audit.py",
    "panel_measured.csv": "(B) panel_extract.py",
    "print_schedule.csv": "(B) panel_production.py",
    "supplier_package.csv": "(B) supplier_package.py",
    "exploded_assembly.csv": "(B) exploded_assembly.py",
    "donor_exposure.csv": "(B) donor_exposure.py",
    "edge_test.txt": "(B) edge_test.py",
    "scan_dependency.txt": "(P) scan_dependency_report.py",
    "panel_register.txt": "(P) panel_registry.py",
    "panel_bom.csv": "(P) panel_registry.py --csv",
    "donor_conflicts.txt": "(P) check_statev_vs_donor.py",
    "panel_architecture.csv": "(P) panel_architecture.py --csv",
    "panel_definition.csv": "(P) panel_definition.py --csv",
    "model_side.png": "(B) ortho_views.py",
    "model_plan.png": "(B) ortho_views.py",
    "overlay_ref05_side.png": "(P) silhouette_overlay.py",
    "plan_profile_compare.png": "(P) plan_overlay.py",
    "last_curvature.json": "(B) highlight_test.py",
    "last_surface.json": "(B) surface_probe.py",
    "handoff.json": "(B) panel_production.py",
    "README.md": "(P) print_qc.py",
    "fit_test_P39.txt": "(P) fit_test.py P39",
    "overhang.csv": "(P) overhang_report.py",
}

NOT_A_REPORT = {
    "goal_baseline.json": "a baseline is SUPPOSED to predate the build — that is what makes it one",
    "checkpoint01.txt": "a record of a decision taken on a date, not a measurement of the car now",
}


def main():
    stamp_p = os.path.join(REPO, "01_CAD/scripts/data/last_build.json")
    print("=" * 84)
    print("REPORT FRESHNESS — is what is written down still about the car that is built?")
    print("=" * 84)
    if not os.path.exists(stamp_p):
        print("\n  no data/last_build.json — run statev_master_volumes.py in Blender first.")
        print("  Without it nothing here can be answered, and guessing is what this file exists")
        print("  to stop.")
        return 1
    with open(stamp_p, encoding="utf-8") as f:
        stamp = json.load(f)
    now_sha, built_sha = scripts_sha(), stamp.get("scripts_sha")
    bt = stamp.get("when", 0)
    print(f"\n  scene built  {time.strftime('%Y-%m-%d %H:%M', time.localtime(bt))}  "
          f"from scripts {built_sha}")
    if now_sha != built_sha:
        print(f"  scripts now  {now_sha}  — THE BUILD IS STALE. Re-run the three build scripts in")
        print("  Blender; every report below describes a car the scripts no longer make.")
    else:
        print("  the build matches the scripts on disk")
    print()
    stale, ok, skipped = [], 0, 0
    for rel, exts in WATCH:
        d = os.path.join(REPO, rel)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if not any(n.endswith(e) or n == e for e in exts):
                continue
            if HISTORICAL.search(n) or n in NOT_A_REPORT:
                skipped += 1
                continue
            p = os.path.join(d, n)
            age = bt - os.path.getmtime(p)
            if age > 1.0:
                stale.append((os.path.join(rel, n), age / 3600.0))
            else:
                ok += 1
    for f, h in sorted(stale, key=lambda t: -t[1]):
        w = WRITER.get(os.path.basename(f))
        tag = "STALE " if w else "ORPHAN"
        print(f"  {tag} {f:52s} {h:7.1f} h old   {w or 'NO SCRIPT WRITES THIS'}")
    print(f"\n  {ok} current, {len(stale)} stale, {skipped} not checked (historical, or listed in "
          f"NOT_A_REPORT with a reason)")
    orphan = [f for f, _ in stale if os.path.basename(f) not in WRITER]
    if stale:
        print("\n  A stale report does not fail — it answers confidently about a car that no longer")
        print("  exists. (B) runs inside Blender, (P) as python3 01_CAD/scripts/<name>.")
    if orphan:
        print(f"\n  {len(orphan)} ORPHAN(S): no script writes them, so they can never be refreshed")
        print("  and will sit there looking like live data. That is how three of them survived a")
        print("  week. Give the writer the file, or delete the file.")
    print("\n  It cannot tell a report re-run to an identical result from one never re-run, and")
    print("  it cannot see a change that came from a data file rather than a script.")
    return 1 if (stale or now_sha != built_sha) else 0


sys.exit(main())
