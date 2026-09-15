"""
split_sensitivity.py — how many printed sections the car becomes, as a function of the one number
nobody has given us yet.

docs/13 Q26 asks the printer for its usable build volume. Until it is answered no split can be
computed, and panel_pipeline.py refuses to guess one. That is correct, and it is also unhelpful in
a conversation with a supplier, because "we cannot proceed without your answer" carries less weight
than "your answer is the difference between 30 pieces and 300".

So this computes the split count across a range of plausible machines instead of picking one. Every
row is a HYPOTHESIS about a machine, not a measurement of ours. The panel sizes are real, measured
by panel_extract.py on the current geometry; only the bed sizes are invented, and they are invented
openly so the shape of the answer can be seen before the real number arrives.

Mirrored panels are counted per side, because a left fender and a right fender are two prints.

    python3 01_CAD/scripts/split_sensitivity.py
"""

import csv
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(REPO, "04_ENGINEERING", "reports", "panel_measured.csv")

# Panels the map covers as one region spanning both sides. Each is two physical prints, and each
# print is half the measured width.
MIRRORED = {"P03", "P07", "P09", "P11", "P15", "P17"}

# Hypothetical machines. None of these is a quote or a measurement; they bracket what a print farm
# might actually have. The last is the Modix BIG-180X class CLAUDE.md names as a possible purchase.
BEDS = [
    ("desktop 300",      300, 300, 300),
    ("mid 400",          400, 400, 450),
    ("large 500",        500, 500, 500),
    ("XL 600",           600, 600, 600),
    ("BIG-180X class", 1800, 600, 600),
]


def sections(L, W, H, bx, by, bz):
    """Axis-aligned section count. A real split follows seams and voids and will usually do better
    than this; it is a ceiling, not a plan."""
    return (math.ceil(L / bx) or 1) * (math.ceil(W / by) or 1) * (math.ceil(H / bz) or 1)


def main():
    if not os.path.exists(CSV):
        print(f"no {CSV} — run panel_extract.py inside Blender first")
        return
    with open(CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    pieces = []
    for r in rows:
        L, W, H = float(r["LENGTH"]), float(r["WIDTH"]), float(r["HEIGHT"])
        n = 2 if r["ID"] in MIRRORED else 1
        pieces.append((r["ID"], r["PART"], L, W / n if n == 2 else W, H, n))

    print("=" * 100)
    print("SPLIT SENSITIVITY — panel sizes are measured, bed sizes are hypotheses")
    print("=" * 100)
    print(f"\n{'ID':<6}{'PART':<22}{'L':>7}{'W':>7}{'H':>7}{'off':>5}" +
          "".join(f"{b[0]:>17}" for b in BEDS))
    totals = {b[0]: 0 for b in BEDS}
    for pid, part, L, W, H, n in pieces:
        line = f"{pid:<6}{part:<22}{L:>7.0f}{W:>7.0f}{H:>7.0f}{n:>5}"
        for name, bx, by, bz in BEDS:
            s = sections(L, W, H, bx, by, bz) * n
            totals[name] += s
            line += f"{s:>17}"
        print(line)
    print(f"\n{'':<47}" + "".join(f"{totals[b[0]]:>17}" for b in BEDS))
    print(f"{'TOTAL PRINTED SECTIONS FOR THE WHOLE CAR':<47}")
    print("\n  'off' is how many of that panel the car carries: 2 for a mirrored pair, 1 otherwise.")
    print("  W for a mirrored pair is per side, because a left and a right fender are two prints.")
    print("\n  Read it as the SHAPE of the answer, not the answer. A real split follows the seams and")
    print("  the voids rather than a grid, so it will beat these counts — but the ratio between the")
    print("  columns is the point, and the ratio is what docs/13 Q26 decides.")
    best, worst = min(totals.values()), max(totals.values())
    print(f"\n  Across these machines the car is between {best} and {worst} printed sections.")
    print("  That factor is why Q26 is the first question on the printer's list and why no split")
    print("  strategy is written until it comes back.")


if __name__ == "__main__":
    main()
