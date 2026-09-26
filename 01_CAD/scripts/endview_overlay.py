"""
endview_overlay.py — the car from AHEAD and from BEHIND, against ref-09, as shapes.

WHY. On 2026-09-26 a full visual review put the model beside the reference from six angles. From
the side and from above they agree, and the goal check said so for a week. From ahead they do not
agree at all: the model is a rounded body -- domed hood, round fenders, an oval mouth -- and the
reference is flat and angular: wide near-planar surfaces meeting at crisp edges, a full-width light
bar, a trapezoidal mouth, a flat top line. Every metric passed because no metric looked from the
front. The side silhouette is the crown line, the plan is the width; neither says HOW the surface
gets from the width up to the crown, and that is the whole difference between a soap bar and the
reference.

WHAT IT COMPARES, and why normalised. ref-09's front and rear views are shot from slightly above
and disqualified for calibration on 2026-09-17: they show the cockpit, so heights are
foreshortened and the wheels are in the outline. But SHAPE survives that. The top outline of the
body -- height as a function of position across the car -- is taken from both pictures, each
normalised by its own overall width and by its own height from the widest point to the crown, and
compared as a curve. Two cars of different size with the same section shape give the same curve;
a domed one and a flat-topped one do not.

WHAT IS LEFT OUT. The middle of the reference's top outline is the windscreen frame and the roll
hoops, which the model does not carry, so the comparison runs over the OUTER part of each side --
from the widest point in to 60% of the half-width -- which is the fender and the outer hood, the
surfaces that decide whether the front reads as a dome or as a wedge.

    python3 01_CAD/scripts/endview_overlay.py
"""

import os
from collections import deque

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(REPO, "07_PRESENTATION/references/ref-09-statev-001-four-view-CURRENT-TARGET.png")
OUT = os.path.join(REPO, "04_ENGINEERING/statev_v01/front")
MODEL = {"front": os.path.join(OUT, "model_front.png"), "rear": os.path.join(OUT, "model_rear.png")}
# the two panels in the collage, as fractions of the image: (x0, y0, x1, y1)
PANEL = {"front": (0.0, 0.36, 0.495, 0.68), "rear": (0.505, 0.36, 1.0, 0.68)}
# OUTER 25% ONLY, changed from 60% on 2026-09-26. Two reasons, both measured. The reference's end
# views are shot from above, so everything behind the nearest surface is pushed DOWN in the image
# by perspective; only the nearest surface -- the fender, at the outer edge -- is compared fairly.
# And on the model side the whole-car envelope was owned by the rear structures over the entire
# 25..60% band (buttress 1026 mm at |Y| 600, haunch 932 at 700), so the number said nothing about
# the front. The model mask is now the front zone alone, and the band is the fender's.
INNER = 0.25          # fraction of the half-width from the outside, compared
SAMPLES = 25


def car_mask_ref(img):
    """Backdrop flood-filled from the frame; what is not backdrop is the car (plus its shadow)."""
    a = img.astype(np.int16)
    h, w = a.shape[:2]
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            seen[y, x] = True
            q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            seen[y, x] = True
            q.append((y, x))
    while q:
        y, x = q.popleft()
        v = a[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]:
                if int(np.abs(a[ny, nx] - v).max()) <= 10:
                    seen[ny, nx] = True
                    q.append((ny, nx))
    return ~seen


def top_outline(mask):
    """For each column, the topmost car pixel; None where there is no car."""
    h, w = mask.shape
    out = []
    for x in range(w):
        col = np.where(mask[:, x])[0]
        out.append(int(col.min()) if len(col) else None)
    return out


def normalised_curve(mask):
    """Height above the widest-row level, as a function of position across, both normalised.

    The 'widest row' is the row where the mask is widest -- the fender line in a front view, which
    is the natural zero for 'how far the surface climbs to the crown'. Returns samples over the
    OUTER 60% of each half, averaged left/right, as (fraction in from the edge, height fraction)."""
    h, w = mask.shape
    widths = [(np.where(mask[y])[0].max() - np.where(mask[y])[0].min()) if mask[y].any() else 0
              for y in range(h)]
    yw = int(np.argmax(widths))
    row = np.where(mask[yw])[0]
    x0, x1 = int(row.min()), int(row.max())
    W = x1 - x0
    top = top_outline(mask)
    # NORMALISE BY A BODY POINT, NOT THE GLOBAL CROWN. The first version divided by the height to
    # the highest pixel of the whole outline, and that is the windscreen header on the reference
    # and the cowl on the model -- two different things, so the model's fractions came out
    # inflated and the comparison was not like with like. The innermost compared sample, 60% of
    # the half-width in from the edge, is outer hood on both pictures; both curves end at 1.0 there
    # and the SHAPE between the edge and that point is what is compared.
    def h_at(f):
        hs = []
        for xx in (x0 + f * W / 2.0, x1 - f * W / 2.0):
            t = top[int(round(xx))]
            if t is not None:
                hs.append(yw - t)
        return sum(hs) / len(hs) if hs else None
    H = h_at(INNER)
    if not H or H <= 0 or W <= 0:
        return None
    curve = []
    for i in range(SAMPLES):
        f = INNER * i / (SAMPLES - 1)                 # 0 at the outer edge, INNER toward centre
        hh = h_at(f)
        if hh is not None:
            curve.append((f, hh / H))
    crown = min(t for t in top if t is not None)
    return curve, (x0, x1, yw, crown)


def main():
    ref_full = np.asarray(Image.open(REF).convert("RGB"))
    H, W = ref_full.shape[:2]
    print("=" * 96)
    print("END VIEWS — front and rear, the model against ref-09, as normalised top outlines")
    print("=" * 96)
    print("\n  0 = the widest point, 1 = the height 25% of the half-width in. The outer quarter only:")
    print("  the fender shoulder, nearest the camera, the one part an elevated view shows fairly.")
    print("  Model mask = front zone (spec X < 440) or rear zone (> 1760) alone.")
    results = {}
    for view in ("front", "rear"):
        if not os.path.exists(MODEL[view]):
            print(f"\n  {view}: no model silhouette — run ortho_views.py in Blender first")
            continue
        x0, y0, x1, y1 = PANEL[view]
        ref = ref_full[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
        rc = normalised_curve(car_mask_ref(ref))
        mod = np.asarray(Image.open(MODEL[view]).convert("RGB")).mean(axis=2) > 128
        mc = normalised_curve(mod)
        if rc is None or mc is None:
            print(f"\n  {view}: could not find an outline")
            continue
        (rcurve, rbox), (mcurve, mbox) = rc, mc
        print(f"\n  {view.upper()}")
        print(f"    {'in from edge':>12s} {'ref':>7s} {'model':>7s} {'diff':>7s}")
        diffs = []
        for (f, r), (_, m) in zip(rcurve, mcurve):
            diffs.append(m - r)
            if True:
                print(f"    {f*100:11.0f}% {r:7.2f} {m:7.2f} {m-r:+7.2f}")
        mean = float(np.mean(np.abs(diffs)))
        bias = float(np.mean(diffs))
        results[view] = (mean, bias)
        print(f"    mean |diff| {mean:.3f} of the climb over the outer quarter, bias {bias:+.3f} "
              f"({'model climbs HIGHER, rounder' if bias > 0 else 'model climbs lower, flatter'})")
        # the picture
        canvas = np.full((300, 700, 3), 30, np.uint8)
        for curve, col in ((rcurve, (90, 140, 255)), (mcurve, (255, 150, 60))):
            pts = [(int(40 + f / INNER * 620), int(260 - hh * 220)) for f, hh in curve]
            for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
                n = max(abs(bx - ax), abs(by - ay), 1)
                for k in range(n + 1):
                    px, py = ax + (bx - ax) * k // n, ay + (by - ay) * k // n
                    canvas[max(0, py - 1):py + 2, max(0, px - 1):px + 2] = col
        Image.fromarray(canvas).save(os.path.join(OUT, f"endview_{view}_compare.png"))
    print("\n  A curve that rises steeply near the edge and flattens is a WEDGE with a crisp fender")
    print("  line; one that rises gently and keeps rising is a DOME. Blue = reference, orange =")
    print(f"  model, in {OUT}/endview_*_compare.png")
    return results


if __name__ == "__main__":
    main()
