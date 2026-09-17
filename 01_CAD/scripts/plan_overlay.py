"""
plan_overlay.py — the plan shape, which is the axis the side view says nothing about.

The silhouette overlay has the profile matching ref-05 to 3 mm across the front, and the owner's
answer to that was that the dimensions are fine and the shapes are not. He is right, and the reason
the measurements could not see it is that every one of them was in ONE projection. A car whose side
elevation is perfect can still be the wrong shape in plan, and nothing in this repo has ever looked
at the plan.

ref-09 supplies a top view. Its wheels are hidden under the bodywork, so it cannot be calibrated on
the wheelbase the way the side view is -- and it does not need to be, for this question. Comparing
SHAPE rather than SIZE removes the calibration entirely:

    each station is a fraction of the car's own length, nose 0 to tail 1
    each half-width is a fraction of that car's own maximum half-width

Two cars of different sizes with the same plan shape give identical curves. Two cars of the same size
with different plan shapes do not. That is exactly the question being asked.

CONSISTENCY, MEASURED FIRST. The four views of ref-09 are cross-checked before anything is read off
them: the side view is calibrated on its own wheelbase, that fixes the length, the length calibrates
the top view, and the height calibrates the front and rear. Three views then have to agree on one
width. They do not -- top 1890, front 2019, rear 2205, a 315 mm spread -- and the reason is visible
in the images: the front and rear views show the inside of the cockpit, so the camera is above the
car and their heights are foreshortened. Only the SIDE and TOP views are used here. The front and
rear are shape references for the eye, not measurements.

    python3 01_CAD/scripts/plan_overlay.py
"""

import os
from collections import deque

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(REPO, "07_PRESENTATION/references/ref-09-statev-001-four-view-CURRENT-TARGET.png")
MODEL = os.path.join(REPO, "04_ENGINEERING/statev_v01/plan/model_plan.png")
OUT = os.path.join(REPO, "04_ENGINEERING/statev_v01/plan")

TOP_PANEL = (28, 361, 825, 1518)      # the top view inside the collage
OUR_LENGTH, OUR_WIDTH = 4370.0, 1850.0
N = 24                                # stations along the car


def flood_mask(p, tol=8):
    """The car, as everything the smooth backdrop cannot reach from the frame edge."""
    h, w, _ = p.shape
    P = p.astype(np.int16)
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        v = P[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]:
                if int(np.abs(P[ny, nx] - v).max()) <= tol:
                    seen[ny, nx] = True
                    q.append((ny, nx))
    return ~seen


def profile(mask, n):
    """Half-width at n stations, as a fraction of the car's own max half-width, nose to tail.
    The centreline is taken as the mask's own mid-row so a crooked crop cannot skew it."""
    cols = np.nonzero(mask.sum(axis=0) >= 6)[0]
    if not len(cols):
        return None, None
    x0, x1 = cols.min(), cols.max()
    rows = np.nonzero(mask.sum(axis=1) >= 6)[0]
    cy = (rows.min() + rows.max()) / 2.0
    hw = []
    for i in range(n):
        x = int(round(x0 + (x1 - x0) * i / (n - 1)))
        col = np.nonzero(mask[:, x])[0]
        hw.append(max(abs(col.max() - cy), abs(cy - col.min())) if len(col) else 0.0)
    hw = np.array(hw, float)
    return hw / hw.max(), (x1 - x0)


def main():
    ref = np.asarray(Image.open(REF).convert("RGB"))
    y0, y1, x0, x1 = TOP_PANEL
    ref_top = ref[y0:y1, x0:x1]
    ref_hw, ref_len = profile(flood_mask(ref_top), N)

    mod = np.asarray(Image.open(MODEL).convert("RGB"))
    mod_mask = mod.mean(axis=2) > 128
    mod_hw, mod_len = profile(mod_mask, N)

    if ref_hw is None or mod_hw is None:
        print("one of the two plans came out empty — not reporting a comparison on that")
        return

    print("=" * 92)
    print("PLAN SHAPE — the model against ref-09's top view, normalised so size cannot hide shape")
    print("=" * 92)
    print("\n  Each station is a fraction of that car's OWN length; each half-width a fraction of")
    print("  its OWN maximum. Calibration is therefore irrelevant and cannot be got wrong.")
    print(f"\n{'along the car':>14}{'render':>9}{'model':>9}{'difference':>12}   as mm on our 1850 wide")
    diffs = []
    for i in range(N):
        t = i / (N - 1)
        d = mod_hw[i] - ref_hw[i]
        diffs.append(abs(d))
        print(f"{t*100:>13.0f}%{ref_hw[i]:>9.3f}{mod_hw[i]:>9.3f}{d:>+12.3f}"
              f"{d*OUR_WIDTH/2:>+22.0f}")
    d = np.array(diffs)
    print(f"\n  mean difference {d.mean()*100:.1f}% of max half-width "
          f"({d.mean()*OUR_WIDTH/2:.0f} mm on our car)")
    print(f"  worst {d.max()*100:.1f}% at {np.argmax(d)/(N-1)*100:.0f}% along "
          f"({d.max()*OUR_WIDTH/2:.0f} mm)")
    print("\n  A car whose side elevation matches to 3 mm can still be the wrong shape in plan.")
    print("  This is the first time this project has looked.")

    # the picture
    h = 420
    comp = np.zeros((h, 900, 3), np.uint8)
    for i in range(N - 1):
        for arr, col in ((ref_hw, (60, 210, 255)), (mod_hw, (255, 110, 40))):
            xa, xb = int(40 + i * 820 / (N - 1)), int(40 + (i + 1) * 820 / (N - 1))
            ya = int(h / 2 - arr[i] * 170)
            yb = int(h / 2 - arr[i + 1] * 170)
            for k in range(max(abs(xb - xa), 1)):
                x = xa + k
                y = int(ya + (yb - ya) * k / max(abs(xb - xa), 1))
                comp[max(0, y - 1):y + 2, x] = col
                comp[h - min(h - 1, y) - 2:h - min(h - 1, y) + 1, x] = col
    comp[h // 2, 40:860] = (90, 90, 90)
    p = os.path.join(OUT, "plan_profile_compare.png")
    Image.fromarray(comp).save(p)
    print(f"\nwrote {p}   blue = the render's plan, orange = ours, mirrored about the centreline")


main()
