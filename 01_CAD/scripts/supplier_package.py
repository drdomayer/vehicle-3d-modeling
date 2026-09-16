"""
supplier_package.py — one file for the printer and the composite shop, instead of six.

Everything a supplier needs about a part is already recorded, but it is spread across the register,
the architecture, the manufacturing definition, the audit, the measurements and the donor-exposure
measurement. Six CSVs is not a package; it is a request that the supplier do the joining. This joins
them, per part, and says plainly which cells are answers and which are questions.

Three kinds of cell, and the difference is the point:

    a value        measured off v020 or recorded in the register. It is what it says.
    PROVISIONAL    our working assumption, stated so it can be argued with. The 3 mm wall and the
                   1.24 g/cm3 density are assumptions, not quotes, and the mass follows from them.
    UNKNOWN Qnn    a question for the supplier, with its number in docs/13. Nothing is guessed to
                   fill one of these, and a part is not ready while any that blocks it is open.

Runs outside Blender: it reads the CSVs the Blender scripts already wrote. Regenerate those first if
the geometry has moved.

    python3 01_CAD/scripts/supplier_package.py
"""

import csv
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS = os.path.join(REPO, "04_ENGINEERING", "reports")
OUT = os.path.join(REPORTS, "supplier_package.csv")
PRINT_DIR = os.path.join(REPO, "03_PRINT")

# Questions in docs/13 that gate a cell. Kept here as one list so the covering letter can be
# generated from the same source the table uses.
Q = {
    "wall":        (30, "minimum printed wall for a laminating core"),
    "build":       (26, "usable build volume, not the catalogue figure"),
    "orientation": (32, "maximum unsupported overhang"),
    "flange":      (15, "bonding flange width"),
    "infill":      (37, "infill pattern and density for a core that will be laminated"),
    "exotherm":    (28, "resin exotherm against the print's heat deflection temperature"),
    "material":    (29, "print material the shop will accept under its resin"),
    "gap":         (16, "panel gap the shop works to"),
}


def read(name):
    p = os.path.join(REPORTS, name)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    key = "PANEL" if rows and "PANEL" in rows[0] else "ID"
    return {r[key]: r for r in rows}


def pilot_file(pid):
    d = os.path.join(PRINT_DIR, f"pilot_{pid}")
    if not os.path.isdir(d):
        return ""
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".stl"):
            return os.path.relpath(os.path.join(d, fn), REPO)
    return ""


# Every part is now measured on its own side by panel_extract, so nothing here reads a partner's
# row. The map is kept only for the donor-exposure table, which is still per region because the
# question it answers -- does this donor value bound this panel -- has one answer for both sides.
TWIN = {"P04": "P03", "P08": "P07", "P10": "P09", "P12": "P11", "P16": "P15",
        "P18": "P17", "P40": "P39", "P41": "P28", "P42": "P19"}


def main():
    bom = read("panel_bom.csv")
    audit = read("manufacturing_audit.csv")
    meas = read("panel_measured.csv")
    expo = read("donor_exposure.csv")
    if not bom or not audit:
        print("missing panel_bom.csv or manufacturing_audit.csv — run the Blender scripts first")
        return

    rows = []
    for pid, b in bom.items():
        a = audit.get(pid, {})
        m = meas.get(pid, {})
        e = expo.get(pid) or expo.get(TWIN.get(pid, ""), {})
        stl = pilot_file(pid)
        verdict = a.get("VERDICT", "?")
        # A part is only offered for quotation when its shape is proven AND a file exists. Every
        # other row is in the table so the supplier can quote the whole car, marked for what it is.
        offer = ("quote this now" if verdict == "PROCEED" and stl else
                 "proven, no file yet" if verdict == "PROCEED" else
                 "do not quote yet: " + a.get("BLOCKER", "?"))
        rows.append(dict(
            PART=pid, NAME=b.get("NAME", ""), SIDE=b.get("SIDE", ""),
            GROUP=b.get("DESIGN_GROUP", ""), ASSEMBLY_STEP=b.get("ASSEMBLY_STEP", ""),
            INSTALL_VECTOR=b.get("INSTALL_VECTOR", ""),
            METHOD=b.get("MANUFACTURING_METHOD", ""),
            STATUS=verdict, OFFER=offer,
            # geometry, measured
            LENGTH_MM=m.get("LENGTH", ""), WIDTH_MM=m.get("WIDTH", ""), HEIGHT_MM=m.get("HEIGHT", ""),
            SKIN_AREA_M2=m.get("AREA_M2", ""), PIECES=m.get("PIECES", ""),
            # core, provisional
            CORE_WALL_MM="PROVISIONAL 3.0 — " + f"Q{Q['wall'][0]}: {Q['wall'][1]}",
            CORE_VOLUME_CM3=m.get("CORE_VOLUME_CM3", ""),
            CORE_MASS_KG=m.get("EST_MASS_KG", ""),
            CORE_MASS_BASIS="PROVISIONAL: 3.0 mm wall x 1.24 g/cm3. Neither is a quote.",
            INFILL=f"UNKNOWN Q{Q['infill'][0]}: {Q['infill'][1]}",
            PRINT_MATERIAL=f"UNKNOWN Q{Q['material'][0]}: {Q['material'][1]}",
            # what the supplier must answer before this part can be made
            SPLIT=f"UNKNOWN Q{Q['build'][0]}: {Q['build'][1]}",
            SPLIT_INTENT=a.get("SPLIT", ""),
            PRINT_ORIENTATION=f"UNKNOWN Q{Q['orientation'][0]}: {Q['orientation'][1]}",
            FLANGE_WIDTH=f"UNKNOWN Q{Q['flange'][0]}: {Q['flange'][1]}",
            PANEL_GAP=f"UNKNOWN Q{Q['gap'][0]}: {Q['gap'][1]}",
            EXOTHERM=f"UNKNOWN Q{Q['exotherm'][0]}: {Q['exotherm'][1]}",
            # what the car must answer
            DONOR_INTERFACE=a.get("DONOR_INTERFACE", ""),
            SCAN_DEPENDENCY=a.get("SCAN_DEPENDENCY", ""),
            BOUNDARY_DONOR_DEPENDENT=e.get("BOUNDARY_DONOR_DEPENDENT", ""),
            BOUNDED_BY=e.get("BOUNDED_BY", ""),
            TRIM_ALLOWANCE=("PROVISIONAL 15 mm, and measured insufficient where BOUNDED_BY is set: "
                            "the seam travels 15-30 mm with the estimate"
                            if e.get("BOUNDED_BY") else "PROVISIONAL 15 mm"),
            PROOF=a.get("PROOF", ""), STL=stl or "none yet"))

    order = {"PROCEED": 0, "CONDITIONAL": 1, "SCAN REQUIRED": 2, "BLOCKED": 3}
    rows.sort(key=lambda r: (order.get(r["STATUS"], 9), r["PART"]))

    print("=" * 100)
    print("SUPPLIER PACKAGE — one row per part. Answers, assumptions and questions, kept apart.")
    print("=" * 100)
    print(f"\n{'PART':<7}{'NAME':<22}{'STATUS':<15}{'area m2':>9}{'mass kg':>9}  what to do with it")
    for r in rows:
        print(f"{r['PART']:<7}{r['NAME']:<22}{r['STATUS']:<15}{str(r['SKIN_AREA_M2']):>9}"
              f"{str(r['CORE_MASS_KG']):>9}  {r['OFFER']}")

    quotable = [r for r in rows if r["OFFER"] == "quote this now"]
    area = sum(float(r["SKIN_AREA_M2"]) for r in quotable if r["SKIN_AREA_M2"])
    mass = sum(float(r["CORE_MASS_KG"]) for r in quotable if r["CORE_MASS_KG"])
    print(f"\n  quotable today: {len(quotable)} parts, {area:.3f} m2 of skin, "
          f"~{mass:.1f} kg of core at the provisional wall")
    print("  every one of them still needs the answers to the questions in the UNKNOWN columns")
    print("  before a file can become a part. The blocking ones are:")
    for k in ("build", "wall", "orientation", "flange"):
        print(f"    docs/13 Q{Q[k][0]:<4} {Q[k][1]}")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}  ({len(rows)} parts, {len(rows[0])} columns)")


main()
