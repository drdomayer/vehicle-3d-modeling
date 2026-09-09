"""
extract_blueprint_986.py — pull plan-view half-width and cross-section templates out of the
CC-BY 4-view blueprint (04_ENGINEERING/reference/getoutlines_986_1996_4view_ccby.gif).

Runs OUTSIDE Blender (needs Pillow + numpy):  python3 01_CAD/scripts/extract_blueprint_986.py
Writes 01_CAD/scripts/data/986_plan_section.json, consumed by block_986.py.

Drawing facts (measured 2026-09-09):
  side view  y 4..139,  car nose at LEFT; tyre contact centres px 125 (front) / 395.5 (rear)
  top view   y 155..355, centreline row 255, nose at left, same x scale as side view
  front view x 27..238,  rear view x 284..495, rows 369..504
Scale ≈ 8.9 mm/px (wheelbase → 8.93, body width → 8.85). Accuracy ±20–30 mm. Not engineering data.
"""

import json
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "04_ENGINEERING/reference/getoutlines_986_1996_4view_ccby.gif")
OUT = os.path.join(ROOT, "01_CAD/scripts/data/986_plan_section.json")

WHEELBASE = 2415.0
BODY_HALF_W = 890.0
SIDE = (4, 139); TOP = (155, 355); VIEWS_Y = (369, 504)
FRONT_X = (27, 238); REAR_X = (284, 495)
PX_FRONT_WC, PX_REAR_WC = 125.0, 395.5      # side & top view share x
TOP_CENTRE_ROW = 255.0


def smooth(a, k=7):
    ker = np.ones(k) / k
    return np.convolve(np.pad(a, (k // 2, k // 2), mode="edge"), ker, mode="valid")


def main():
    a = np.array(Image.open(SRC).convert("L")) < 128
    s_x = WHEELBASE / (PX_REAR_WC - PX_FRONT_WC)          # mm/px along the car

    # ---------------- plan-view half-width vs x
    top = a[TOP[0]:TOP[1] + 1, :]
    cols = np.where(top.any(axis=0))[0]
    ymin = np.array([np.where(top[:, c])[0].min() for c in cols]) + TOP[0]
    ymax = np.array([np.where(top[:, c])[0].max() for c in cols]) + TOP[0]
    hw_px = (ymax - ymin) / 2.0
    # remove one-column dropouts (mirror gaps etc.) then smooth
    hw_px = np.maximum(hw_px, np.minimum(np.roll(hw_px, 1), np.roll(hw_px, -1)))
    hw_px = smooth(hw_px, 5)
    s_y = BODY_HALF_W / hw_px.max()                         # calibrate width on 1780 published
    plan = [(round(float((PX_FRONT_WC - c) * s_x), 1), round(float(h * s_y), 1)) for c, h in zip(cols, hw_px)]
    # x from front axle (forward positive); drop the last/first 2 px (bumper tips are 1-px spikes)
    plan = plan[2:-2]

    # ---------------- cross-section template from front and rear views
    def section(x0, x1):
        v = a[VIEWS_Y[0]:VIEWS_Y[1] + 1, x0:x1 + 1]
        rows = np.where(v.any(axis=1))[0]
        xmin = np.array([np.where(v[r])[0].min() for r in rows]); xmax = np.array([np.where(v[r])[0].max() for r in rows])
        w = (xmax - xmin).astype(float)
        # ground = last row; body max width excluding mirrors: take the 60th percentile of the lower half
        ground = rows.max()
        body_rows = rows[rows > rows.min() + 40]              # below windshield/mirrors
        wmax = np.percentile(w[rows > rows.min() + 40], 95)
        s = (2 * BODY_HALF_W) / wmax
        prof = []
        for r, ww in zip(rows, w):
            z = (ground - r) * s
            if ww > wmax * 1.02:                              # mirrors
                continue
            prof.append((round(float(z), 1), round(float(min(ww, wmax) / 2.0 * s), 1)))
        return prof, round(float(s), 3)

    front, s_f = section(*FRONT_X)
    rear, s_r = section(*REAR_X)

    # ---------------- hoops / seats from the plan view (informational)
    # P21 soft-top positioning points show as two black dots on the windshield header
    band = a[190:321, 185:205]                             # cabin rows only, header columns
    dots = np.where(band.sum(axis=1) >= 12)[0] + 190
    p21 = [int(dots.min()), int(dots.max())] if dots.size else None

    data = {
        "source": os.path.relpath(SRC, ROOT),
        "license": "CC BY 4.0 (getoutlines.com)",
        "accuracy_mm": 30,
        "scale_mm_per_px": {"x": round(s_x, 3), "y_plan": round(s_y, 3), "front": s_f, "rear": s_r},
        "plan_half_width": plan,                # [[x_mm from front axle, half_width_mm], ...] nose → tail
        "section_front": front,                 # [[z_mm, half_width_mm], ...] top → ground, mirrors removed
        "section_rear": rear,
        "p21_rows_px": p21,
        "notes": "x forward positive; sections are outer silhouettes incl. tyres at the bottom rows",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print("scale:", data["scale_mm_per_px"])
    print("plan x range:", plan[0][0], "→", plan[-1][0], "| half-width max", max(h for _, h in plan))
    print("front section top z:", front[0][0], "| rear section top z:", rear[0][0])
    if p21:
        print("P21 dots rows:", p21, "→ ±", round((p21[1] - p21[0]) / 2 * s_y), "mm (manual: ±477)")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
