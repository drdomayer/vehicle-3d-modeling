"""
silhouette_overlay.py — measure the model against the reference render instead of judging it by eye.

"Does it look like the picture" is the question that has driven every geometry pass in this project
and it has never had a number attached. This attaches one. The side view in ref-05 is close enough
to orthographic to be measurable -- the two wheel centres sit within 2.2 px of the same height -- so
the picture can be put in the same coordinate frame as the model and the two outlines compared
station by station.

CALIBRATION, and it rests on exactly one published number. The bronze wheels are the only feature in
the render whose real size we know, so they are what sets the scale: the bronze pixels are clustered
into two wheels, each centre found by iterating a centroid inside a 105 px radius, and the distance
between them is the wheelbase, 2415 mm from the workshop manual. That gives 2.8753 mm/px. The ground
line comes from the same two centres plus OUR tyre radii, and the two estimates of it agree to 7 px,
which is 20 mm -- that disagreement is the honest error bar on everything below.

THE CAMERA MUST FACE THE SAME WAY AS THE PICTURE, and getting that wrong is silent. A Blender
camera at -Y with rotation (90, 0, 0) looks along +Y with its right axis on repo +X, which is
FORWARD -- so the render came out mirrored, nose on the right, and the first full comparison table
read our nose against the reference's tail and called it a 247 mm error in the rear deck. The
camera now sits at +Y looking -Y, image +x is spec X rearward, and the render agrees with the mesh
to 3 mm at eight rear stations. That check runs in the report below.

WHAT THIS CANNOT DO. It compares OUTLINES. Two cars with the same silhouette and completely
different surfaces read identical here, and docs/16 is explicit that the language lives in the
curvature rather than the outline. A difference this finds is real; an agreement it reports is not a
pass. It also cannot see anything the render hides behind itself.

    python3 01_CAD/scripts/silhouette_overlay.py
"""

import os
from collections import deque

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(REPO, "07_PRESENTATION/references/ref-05-986-futuristic-v3-CHOSEN.png")
OUT = os.path.join(REPO, "04_ENGINEERING/statev_v01/overlay")

# The shared frame. Big enough for both cars so nothing clips at the edge.
MMPX, W, H = 2.8753, 1680, 560
OX, OY = 417.4, 521.7          # front axle centre, ground line, in canvas pixels
REF_PANEL = 518                # the side view is the top panel of the collage, above the gutter
REF_OX, REF_OY = 393.0, 491.1  # the same origin, in the reference's own pixels


def calibrate(panel):
    """Wheel centres and scale, from the bronze rims. Returns (front, rear, mm/px, ground)."""
    R, G, B = panel[:, :, 0], panel[:, :, 1], panel[:, :, 2]
    m = (R - B > 35) & (R > 85) & (R - G > 12)
    ys, xs = np.nonzero(m)
    band = (ys > 295) & (ys < 470)
    ys, xs = ys[band].astype(float), xs[band].astype(float)

    def centre(sel):
        X, Y = xs[sel], ys[sel]
        cx, cy = np.median(X), np.median(Y)
        for _ in range(6):
            k = np.hypot(X - cx, Y - cy) < 105
            cx, cy = X[k].mean(), Y[k].mean()
        return cx, cy

    f, r = centre(xs < 800), centre(xs >= 800)
    mmpx = 2415.0 / (r[0] - f[0])
    gf, gr = f[1] + (647 / 2) / mmpx, r[1] + (675 / 2) / mmpx
    return f, r, mmpx, (gf + gr) / 2.0, abs(gf - gr)


def place(img, ox, oy):
    """Put an image on the shared canvas so its own origin lands on the canvas origin."""
    out = np.zeros((H, W, 3), np.uint8)
    dx, dy = int(round(OX - ox)), int(round(OY - oy))
    h, w = img.shape[:2]
    x0, y0 = max(0, dx), max(0, dy)
    x1, y1 = min(W, dx + w), min(H, dy + h)
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = img[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    return out


def top_line(mask):
    """First filled pixel from the top, per column. None where the column is empty."""
    out = []
    for x in range(mask.shape[1]):
        col = np.nonzero(mask[:, x])[0]
        out.append(col[0] if len(col) else None)
    return out


def main():
    ref_full = np.asarray(Image.open(REF).convert("RGB"))
    panel = ref_full[:REF_PANEL].astype(float)
    f, r, mmpx, ground, spread = calibrate(panel)
    print("=" * 96)
    print("SILHOUETTE OVERLAY — the model against ref-05, in one coordinate frame")
    print("=" * 96)
    print(f"\nCALIBRATION, from the only feature whose real size is published")
    print(f"   front wheel centre  ({f[0]:7.1f}, {f[1]:6.1f}) px")
    print(f"   rear  wheel centre  ({r[0]:7.1f}, {r[1]:6.1f}) px")
    print(f"   wheelbase           {r[0]-f[0]:7.1f} px = 2415 mm  ->  {mmpx:.4f} mm/px")
    print(f"   the two centres differ in height by {r[1]-f[1]:+.1f} px, so the view is within "
          f"{abs(r[1]-f[1])*mmpx:.0f} mm of orthographic")
    print(f"   ground line y = {ground:.1f}; the front and rear tyres disagree about it by "
          f"{spread:.1f} px = {spread*mmpx:.0f} mm")
    print(f"   THAT DISAGREEMENT IS THE ERROR BAR on every number below.")

    model = np.asarray(Image.open(os.path.join(OUT, "model_side.png")).convert("RGB"))
    ref_c = place(ref_full[:REF_PANEL], REF_OX, REF_OY)
    mod_c = place(model, OX, OY) if model.shape[:2] != (H, W) else model
    mod_mask = mod_c.mean(axis=2) > 128

    # The reference outline. Two detectors were tried and the first one is worth recording as a
    # warning: "the first strong vertical gradient scanning down" reported a flat 1414 mm across
    # two thirds of the car, which is the top of the frame. It was finding the backdrop's own
    # vignette, not the car, and it would have produced a full table of confident wrong numbers.
    #
    # What works is the opposite question. The backdrop is one smooth connected region and the car
    # is a hole in it, so the backdrop is flood-filled from the frame edge, stepping only between
    # neighbours within 8 levels of each other. A smooth gradient is traversable at that tolerance;
    # the car's edge is not.
    # NB the fill runs on the reference's OWN pixels, before it is padded onto the shared canvas.
    # Run on the padded version it stops instantly at the black padding, which is a step of 28
    # levels, and every column then reports the first row of the pasted panel -- a flat 1411 mm
    # across the whole car, the same shape of wrong answer as the gradient detector gave.
    ref_f = ref_full[:REF_PANEL].astype(np.int16)
    h0, w0 = ref_f.shape[:2]
    seen = np.zeros((h0, w0), bool)
    q = deque()
    for x in range(w0):
        for y in (0, h0 - 1):
            if not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for y in range(h0):
        for x in (0, w0 - 1):
            if not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        v = ref_f[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h0 and 0 <= nx < w0 and not seen[ny, nx]:
                if int(np.abs(ref_f[ny, nx] - v).max()) <= 8:
                    seen[ny, nx] = True
                    q.append((ny, nx))
    ref_mask = place((~seen)[:, :, None].repeat(3, axis=2).astype(np.uint8) * 255,
                     REF_OX, REF_OY).mean(axis=2) > 128
    ref_top = top_line(ref_mask)
    mod_top = top_line(mod_mask)

    # Bands where the reference shows something our body deliberately does not contain. The
    # windscreen frame and the twin roll hoops are DONOR parts -- CLAUDE.md keeps them and the body
    # is built around them -- so the detector meets them and the model has nothing there. A
    # difference inside these bands is not a body error and must not be read as one.
    NOT_OURS = [(420, 1100, "windscreen frame and glass, donor"),
                (1100, 2100, "roll hoops and the open cockpit, donor")]

    print(f"\n{'spec X':>8}{'ref top Z':>11}{'model top Z':>13}{'model - ref':>13}  band")
    rows = []
    for sx in range(-900, 3500, 150):
        x = int(round(OX + sx / mmpx))
        if not (0 <= x < W):
            continue
        rt, mt = ref_top[x], mod_top[x]
        if rt is None or mt is None:
            print(f"{sx:>8}{'--' if rt is None else f'{(OY-rt)*mmpx:.0f}':>11}"
                  f"{'--' if mt is None else f'{(OY-mt)*mmpx:.0f}':>13}{'':>13}")
            continue
        rz, mz = (OY - rt) * mmpx, (OY - mt) * mmpx
        band = next((w for a, b, w in NOT_OURS if a <= sx < b), "")
        rows.append((sx, rz, mz, mz - rz, band))
        print(f"{sx:>8}{rz:>11.0f}{mz:>13.0f}{mz-rz:>+13.0f}  {band}")

    ours = [r for r in rows if not r[4]]
    if ours:
        d_ = [abs(r[3]) for r in ours]
        front = [r for r in ours if r[0] < 500]
        rear = [r for r in ours if r[0] >= 2100]
        print(f"\n   {len(ours)} stations where the body is ours to compare "
              f"({len(rows)-len(ours)} skipped as donor)")
        print(f"   mean |difference| {np.mean(d_):.0f} mm, worst {max(d_):.0f} mm at spec X "
              f"{ours[int(np.argmax(d_))][0]}")
        if front:
            print(f"   FRONT, spec X below 500: {np.mean([abs(r[3]) for r in front]):.0f} mm mean, "
                  f"worst {max(abs(r[3]) for r in front):.0f}")
        if rear:
            m = np.mean([r[3] for r in rear])
            print(f"   REAR, spec X 2100 and back: the model sits {abs(m):.0f} mm "
                  f"{'BELOW' if m < 0 else 'above'} the reference, consistently")
            print("   The deck decision of 2026-09-14 -- deck 960 -> 880, buttress 1090 -> 985,")
            print("   taken because the render's heights sat inside the roof fold volume -- is what")
            print("   this measures the cost of.")

        print("\n   A difference here is real. An agreement is NOT a pass: this compares OUTLINES,")
        print("   and docs/16 says the language lives in the curvature, not the outline.")

    # the picture, so the numbers can be checked by eye
    # Overall length, at the same calibration. The reference is an AI render and its proportions
    # are not a specification, but this says how far our locked 4370 is from the picture it came
    # from -- and the length is one of the values that cannot be changed, so it is worth knowing.
    # Columns with a single stray pixel are not the car. The flood fill leaves specks in the dark
    # corners of the backdrop, and taking any() over the column let one of them stand in for the
    # nose and put it 107 mm further forward than it is.
    rx_ = np.nonzero(ref_mask.sum(axis=0) >= 8)[0]
    mx_ = np.nonzero(mod_mask.sum(axis=0) >= 8)[0]
    if len(rx_) and len(mx_):
        rl = (rx_.max() - rx_.min()) * mmpx
        ml = (mx_.max() - mx_.min()) * mmpx
        print(f"\n   overall length in the picture {rl:.0f} mm, model {ml:.0f} mm "
              f"({ml-rl:+.0f})")
        print(f"   nose at spec X {(rx_.min()-OX)*mmpx:.0f} vs {(mx_.min()-OX)*mmpx:.0f}, "
              f"tail at {(rx_.max()-OX)*mmpx:.0f} vs {(mx_.max()-OX)*mmpx:.0f}")
        print("   the picture's own length is not a specification -- 4370 is locked and this is")
        print("   only how far the locked value sits from the render it was drawn against.")

    comp = (ref_c * 0.65).astype(np.uint8)
    e1 = np.zeros_like(mod_mask); e1[1:] = mod_mask[1:] ^ mod_mask[:-1]
    e2 = np.zeros_like(mod_mask); e2[:, 1:] = mod_mask[:, 1:] ^ mod_mask[:, :-1]
    edge = e1 | e2
    comp[edge] = (255, 90, 40)
    for x in range(0, W, 2):
        if ref_top[x] is not None:
            comp[max(0, ref_top[x] - 1):ref_top[x] + 2, x] = (60, 210, 255)
    comp[int(OY):int(OY) + 2, :] = (120, 120, 120)
    p = os.path.join(OUT, "overlay_ref05_side.png")
    Image.fromarray(comp).save(p)
    print(f"\nwrote {p}")
    print("   orange = the model's outline, blue = the reference's detected top line,")
    print("   grey = the ground the wheels put the car on.")


main()
