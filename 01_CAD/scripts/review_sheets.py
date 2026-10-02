"""
review_sheets.py — ref-09's seven panels beside the model from the same side, one sheet each.

    python3 01_CAD/scripts/review_sheets.py [files|clean]

Reads rv_glossy_<mode>_<view>.png (glossy_renders.py) and crops ref-09 into its seven panels
(side, top, front, rear, side-intake detail, front-mask detail, rear detail). Writes one sheet
per panel plus an index sheet into 04_ENGINEERING/statev_v01/review/sheets/<mode>/. Pictures, not
measurements: the numbers are check_goal.py.
"""
import os
import sys

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(REPO, "07_PRESENTATION/references/ref-09-statev-001-four-view-CURRENT-TARGET.png")
R = os.path.join(REPO, "04_ENGINEERING/statev_v01/review")
OUT = os.path.join(R, "sheets")
# ref-09 panels as fractions of the collage (x0, y0, x1, y1) -> model view tag
PANELS = [("side", (0.000, 0.000, 0.520, 0.350), "side"),
          ("top", (0.525, 0.000, 1.000, 0.350), "top"),
          ("front", (0.000, 0.360, 0.495, 0.680), "front"),
          ("rear", (0.505, 0.360, 1.000, 0.680), "rear"),
          ("intake", (0.000, 0.690, 0.312, 0.975), "intake"),
          ("mask", (0.315, 0.690, 0.680, 0.975), "mask"),
          ("taildetail", (0.683, 0.690, 1.000, 0.975), "taildetail")]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "files"
    out = os.path.join(OUT, mode)
    os.makedirs(out, exist_ok=True)
    ref = Image.open(REF).convert("RGB")
    W, H = ref.size
    rows = []
    for name, (x0, y0, x1, y1), tag in PANELS:
        r = ref.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        p = os.path.join(R, f"rv_glossy_{mode}_{tag}.png")
        if not os.path.exists(p):
            print(f"  missing {p}")
            continue
        m = Image.open(p).convert("RGB")
        h = 420
        r = r.resize((int(r.width * h / r.height), h))
        m = m.resize((int(m.width * h / m.height), h))
        sheet = Image.new("RGB", (r.width + m.width + 30, h + 34), (255, 255, 255))
        sheet.paste(r, (0, 34))
        sheet.paste(m, (r.width + 30, 34))
        d = ImageDraw.Draw(sheet)
        d.text((6, 8), f"ref-09  {name}", fill=(0, 0, 0))
        d.text((r.width + 36, 8), f"model ({mode})  {tag}", fill=(0, 0, 0))
        fn = os.path.join(out, f"sheet_{name}.png")
        sheet.save(fn)
        rows.append(sheet)
        print(f"  wrote {fn}")
    if rows:
        w = max(s.width for s in rows)
        idx = Image.new("RGB", (w, sum(s.height for s in rows) + 10 * len(rows)), (255, 255, 255))
        y = 0
        for s in rows:
            idx.paste(s, (0, y))
            y += s.height + 10
        idx.save(os.path.join(out, "sheet_all.png"))
        print(f"  wrote {os.path.join(out, 'sheet_all.png')}")


if __name__ == "__main__":
    main()
