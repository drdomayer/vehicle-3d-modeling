"""
fit_test.py — the one printed panel that decides whether to print the other five hundred.

CLAUDE.md, hard constraint 6: "Do not let the owner skip a fit-test on a single printed panel
before printing the rest." Nothing in this project had produced one, and more to the point nothing
had said what the test MEASURES or what counts as passing it. A fit test whose result is "looks
about right" does not protect anything.

WHAT THE TEST IS FOR. Between the design surface and a finished panel sit six things this project
has assumed rather than measured: that a 3 mm printed wall survives lamination without distorting;
that the tab joint holds two sections in alignment while they are bonded; that a section prints at
the orientation lay_flat chose; that filler and paint do not bury the character lines; that the
core's own shrinkage is small enough to ignore; and that the printed part is actually the size the
file says. Every one of them is a docs/13 question with no answer, and a single small panel answers
all six for the price of one print.

WHY THIS PANEL. Chosen from the data, not from preference. It must be entirely ours (so a bad
result blames the process, not a missing scan), small enough to be cheap, carry real curvature in
two directions (a flat test panel proves nothing about a car), come in more than one section (or
the tab joint goes untested), and sit somewhere cosmetically forgiving if it comes out wrong.

WHAT THE OWNER CAN ACTUALLY MEASURE, and this is the part that makes the test real: a caliper and a
steel rule, no scanner. So the sheet gives point-to-point distances between features that can be
found by eye on the part -- extremes and corners -- and those distances are what the printed,
laminated and filled part is checked against at each stage. A number that drifts tells you WHICH
stage moved it.

    python3 01_CAD/scripts/fit_test.py [PANEL]
"""

import csv
import json
import math
import os
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(REPO, "03_PRINT", "production")
OUT = os.path.join(REPO, "04_ENGINEERING", "reports")
DEFAULT = "P39"

# What one printed panel is being asked to answer. Each is an assumption the whole run rests on.
QUESTIONS = [
    ("does a 3 mm printed wall survive lamination without distorting",
     "docs/13 Q30 — the wall is a DESIGN ASSUMPTION, never tested"),
    ("does the tab joint hold two sections in line while they are bonded",
     "the tab is 20 mm, dropped inward by a wall plus a 1 mm bond line — decided, not proven"),
    ("does the section print at the orientation the pipeline chose",
     "docs/13 Q32/Q33 — orientation is 'lay flattest', not chosen against an overhang limit"),
    ("do filler and paint bury the character lines",
     "the side lip turns 67 degrees and the crest 55; nobody has seen either under paint"),
    ("is the printed part the size the file says",
     "shrinkage is assumed zero; PLA and PETG are not zero"),
    ("does the finished panel still match the design surface",
     "assembly_check says the FILES do, to a median of 0.00 mm. The PART is a different claim."),
]


def read_stl(path):
    with open(path, "rb") as f:
        head = f.read(84)
        n = int.from_bytes(head[80:84], "little")
        body = f.read()
    return [struct.unpack("<9f", body[i * 50 + 12:i * 50 + 48]) for i in range(n)]


def panel_points(pid, placement):
    """Every vertex of the panel, back in car coordinates, in millimetres of spec X / Y / Z."""
    pts = []
    for name, mat in placement.items():
        if not name.startswith(pid + "_"):
            continue
        p = os.path.join(PROD, name)
        if not os.path.exists(p):
            continue
        M = mat
        for t in read_stl(p):
            for k in range(3):
                x, y, z = t[k * 3] / 1000.0, t[k * 3 + 1] / 1000.0, t[k * 3 + 2] / 1000.0
                wx = M[0][0] * x + M[0][1] * y + M[0][2] * z + M[0][3]
                wy = M[1][0] * x + M[1][1] * y + M[1][2] * z + M[1][3]
                wz = M[2][0] * x + M[2][1] * y + M[2][2] * z + M[2][3]
                pts.append((-wx * 1000.0, wy * 1000.0, wz * 1000.0))
    return pts


def landmarks(pts):
    """Six points a person can find on the part without a scanner: the extreme of each axis.

    An extreme is a corner or a tip -- something you can put a caliper jaw on. A point in the middle
    of a curved face is not measurable by hand and is not offered."""
    names = ("front-most", "rear-most", "left-most", "right-most", "lowest", "highest")
    idx = []
    for axis, want_max in ((0, False), (0, True), (1, True), (1, False), (2, False), (2, True)):
        best = None
        for p in pts:
            if best is None or (p[axis] > best[axis]) == want_max:
                best = p
        idx.append(best)
    return list(zip(names, idx))


def main():
    pid = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).upper()
    pl_path = os.path.join(PROD, "placement.json")
    if not os.path.exists(pl_path):
        print("  no placement.json — run panel_production.py in Blender first")
        return 1
    with open(pl_path, encoding="utf-8") as f:
        placement = json.load(f)["parts"]
    sched = [r for r in csv.DictReader(open(os.path.join(OUT, "print_schedule.csv")))
             if r["PANEL"] == pid]
    if not sched:
        print(f"  {pid} has no sections in print_schedule.csv")
        return 1
    name = sched[0]["NAME"]
    pts = panel_points(pid, placement)
    if not pts:
        print(f"  {pid} has no readable files")
        return 1

    txt = []
    txt.append("=" * 96)
    txt.append(f"FIT TEST — {pid} {name}")
    txt.append("=" * 96)
    txt.append("")
    txt.append("  CLAUDE.md hard constraint 6: one panel is printed, laminated and checked BEFORE")
    txt.append("  the rest. This is that panel, and this sheet is what the check consists of.")
    txt.append("")
    txt.append("  WHAT ONE PRINT ANSWERS")
    for q, why in QUESTIONS:
        txt.append(f"    - {q}")
        txt.append(f"        {why}")
    txt.append("")
    txt.append(f"  THE FILES — {len(sched)} section(s), print all of them")
    txt.append(f"    {'file':44s} {'L':>7s} {'W':>7s} {'H':>7s}  one piece")
    for r in sched:
        txt.append(f"    {os.path.basename(r['FILE']):44s} {float(r['X_MM']):7.1f} "
                   f"{float(r['Y_MM']):7.1f} {float(r['Z_MM']):7.1f}  "
                   f"{'yes' if int(r['PIECES_IN_FILE']) == 1 else 'NO'}")
    txt.append("")
    txt.append("    Each file is already laid on its flattest face and sitting on Z = 0. Print it as")
    txt.append("    it comes; do not re-orient it, because the schedule's placement puts it back on")
    txt.append("    the car in that orientation and nothing else records which way up it went.")
    txt.append("")

    lm = landmarks(pts)
    txt.append("  THE MEASUREMENTS — a caliper and a steel rule, no scanner")
    txt.append("    Six landmarks, each an extreme of the part, so each is a corner or a tip you can")
    txt.append("    put a jaw on. Measure every pair at every stage and write the number down.")
    txt.append("")
    txt.append(f"    {'landmark':14s} {'spec X':>9s} {'Y':>9s} {'Z':>9s}")
    for nm, p in lm:
        txt.append(f"    {nm:14s} {p[0]:9.1f} {p[1]:9.1f} {p[2]:9.1f}")
    txt.append("")
    txt.append("    DESIGN DISTANCES, in millimetres. These are what the part is checked against.")
    for i in range(len(lm)):
        for j in range(i + 1, len(lm)):
            d = math.dist(lm[i][1], lm[j][1])
            if d < 40:
                continue
            txt.append(f"      {lm[i][0]:14s} -> {lm[j][0]:14s} {d:9.1f}")
    txt.append("")
    txt.append("  WHEN TO MEASURE, and what a change at each stage means")
    txt.append("    1. straight off the printer, per section   -> shrinkage, and whether the")
    txt.append("       printer built the file it was given")
    txt.append("    2. sections bonded, before laminate        -> whether the tab joint held them")
    txt.append("       in line; this is the number most likely to move")
    txt.append("    3. after laminate, before filler           -> whether the wall distorted under")
    txt.append("       the resin's heat and shrinkage")
    txt.append("    4. after filler and paint                  -> the finished panel, and whether")
    txt.append("       the character lines are still readable")
    txt.append("")
    txt.append("  WHAT PASSING MEANS, and it is a decision, not a measurement")
    txt.append("    This project has no tolerance from anybody yet — docs/13 Q16 is unanswered — so")
    txt.append("    no number here can be called a limit without inventing one. What the sheet can")
    txt.append("    say honestly is the SCALE the rest of the work assumes:")
    txt.append("      - the panel gaps are designed at 4 mm, so a joint that moves more than about")
    txt.append("        2 mm eats half the gap and will show;")
    txt.append("      - the flange is 30 mm with a 1 mm bond line, so a face out of plane by more")
    txt.append("        than 1 mm has nothing left to bond into;")
    txt.append("      - the whole car is built to a locked width of 1850 mm; a panel 1 % off is")
    txt.append("        18 mm, which is four gaps.")
    txt.append("    Write the measured numbers down, then decide with the composite shop. The point")
    txt.append("    of this panel is to have real numbers in that conversation instead of a plan.")
    txt.append("")
    txt.append("  WHAT THIS TEST CANNOT TELL YOU")
    txt.append("    It says nothing about anything that touches the donor — this panel was chosen")
    txt.append("    because it does not. Fit to the car is a separate test, after the scan, and it")
    txt.append("    is the only one of the two that the scan can change.")
    out = "\n".join(txt)
    print(out)
    with open(os.path.join(OUT, f"fit_test_{pid}.txt"), "w", encoding="utf-8") as f:
        f.write(out + "\n")
    print(f"\n  wrote {os.path.join(OUT, f'fit_test_{pid}.txt')}")
    return 0


sys.exit(main())
