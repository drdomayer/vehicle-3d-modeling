"""
check_goal.py — the two measurements that ARE the goal, run together, against a recorded baseline.

Everything else in this repo checks that the car is consistent: the map closes, the locked values
have not moved, the lamps fit, nothing is over the print plate. All necessary, none of it the point.
The point is stated in CLAUDE.md and judged by eye: does it look like the render.

Two numbers stand for that, and both already exist.

    SILHOUETTE   silhouette_overlay.py, the profile against ref-05 at the wheelbase calibration.
    SURFACE      highlight_test.py, the ratio of principal curvatures -- docs/16's own criterion,
                 0 being the long controlled highlight and 1 the balloon.

Neither was run on v024, v025 or v026. Three versions were committed on the strength of the
bookkeeping checks alone, and the front silhouette had regressed from 3 mm to 21 the whole time --
a vent liner standing 100 mm proud of the bonnet it was supposed to line. The overlay found it in
one run. It was never run.

So this runs both, compares them with the last recorded pass, and says REGRESSED out loud. A number
that got worse without a reason recorded beside it is a bug, not a design decision.

    python3 01_CAD/scripts/check_goal.py --record     store the current values as the baseline
    python3 01_CAD/scripts/check_goal.py              compare against it

The Blender half (rendering the model into the overlay frame) must be done first, from Blender;
this reads what those scripts print. It refuses to guess if a number is missing.
"""

import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(REPO, "01_CAD/scripts/data/goal_baseline.json")
TOL = {"front_mm": 3.0, "rear_mm": 5.0, "mean_mm": 5.0, "curvature": 0.02}


def run(script):
    r = subprocess.run([sys.executable, os.path.join(REPO, "01_CAD/scripts", script)],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


def parse_silhouette(txt):
    out = {}
    m = re.search(r"mean \|difference\| (\d+) mm", txt)
    if m:
        out["mean_mm"] = float(m.group(1))
    m = re.search(r"FRONT, spec X below 500: (\d+) mm mean", txt)
    if m:
        out["front_mm"] = float(m.group(1))
    m = re.search(r"the model sits (\d+) mm", txt)
    if m:
        out["rear_mm"] = float(m.group(1))
    return out


def parse_curvature(txt):
    m = re.search(r"median principal-curvature ratio ([\d.]+)", txt)
    return {"curvature": float(m.group(1))} if m else {}


def main():
    got = {}
    got.update(parse_silhouette(run("silhouette_overlay.py")))
    # The curvature half needs the mesh, which lives in Blender, so highlight_test.py writes its
    # result out and this reads it. The age is checked: a value older than the scripts that build
    # the car is a value from a different car, and reporting it as current would be the same class
    # of mistake this whole check exists to stop.
    cp = os.path.join(REPO, "01_CAD/scripts/data/last_curvature.json")
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as f:
            c = json.load(f)
        newest = max(os.path.getmtime(os.path.join(REPO, "01_CAD/scripts", n))
                     for n in ("statev_master_volumes.py", "stage03_elements.py",
                               "statev_skeleton.py"))
        if c.get("when", 0) < newest:
            print("  STALE: the curvature was measured before the last change to the build scripts.")
            print("  Run highlight_test.py in Blender again; it is not reported here.")
        else:
            got["curvature"] = c["curvature"]
    else:
        print("  no curvature on file — run highlight_test.py inside Blender first")
    missing = [k for k in TOL if k not in got]
    print("=" * 84)
    print("GOAL CHECK — the silhouette against ref-05, and the surface against docs/16")
    print("=" * 84)
    if missing:
        print(f"\n  MISSING: {', '.join(missing)}. Not reporting a pass on a partial measurement.")
    record = "--record" in sys.argv
    old = {}
    if os.path.exists(BASE):
        with open(BASE, encoding="utf-8") as f:
            old = json.load(f)
    print(f"\n  {'metric':<14}{'now':>9}{'baseline':>11}{'change':>9}   verdict")
    bad = 0
    for k in ("front_mm", "rear_mm", "mean_mm", "curvature"):
        if k not in got:
            continue
        n = got[k]
        o = old.get(k)
        if o is None:
            print(f"  {k:<14}{n:>9.2f}{'--':>11}{'--':>9}   no baseline yet")
            continue
        d = n - o
        worse = d > TOL[k]
        bad += 1 if worse else 0
        print(f"  {k:<14}{n:>9.2f}{o:>11.2f}{d:>+9.2f}   "
              f"{'REGRESSED' if worse else ('better' if d < -TOL[k] else 'unchanged')}")
    if record and not missing:
        os.makedirs(os.path.dirname(BASE), exist_ok=True)
        with open(BASE, "w", encoding="utf-8") as f:
            json.dump(got, f, indent=2)
        print(f"\n  recorded as the baseline: {BASE}")
    elif bad:
        print(f"\n  {bad} metric(s) regressed. A number that got worse with no reason written beside")
        print("  it is a bug. Find it before committing, or record the reason and re-baseline.")
    else:
        print("\n  nothing regressed")
    return got


main()
