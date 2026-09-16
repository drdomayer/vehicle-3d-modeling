"""
panel_architecture.py — the manufacturing layer on top of the panel register.

panel_registry.py says WHICH parts exist and in what order they go on. This says HOW each one is
made and, more importantly, WHAT IT DEPENDS ON. It adds nothing to the parts list: PARTS is
imported, so there is exactly one inventory.

The field that matters most here is SHAPE_DRIVER. It is not the same question as "does this panel
need the scan" — every panel needs the scan for its mating surfaces. It asks whether the scan can
change the panel's SHAPE or only its position and its flange:

    OURS   the outer shape is our design. The scan moves where it sits, not what it is.
           Safe to surface now; after the scan it is a local correction at the interface.
    DONOR  the outer shape is governed by donor features — an arch opening, a shut line, the
           surface it overlays. A 25 mm error in the donor estimate changes the panel, not its
           position. Surfacing these early is the work most at risk.
    MIXED  one edge is governed, the rest is ours.

INTERFACE_CLASS is derived, not typed in, and it classifies the INTERFACE rather than the panel.
Classifying whole panels was the first attempt and it was useless: every panel has at least one
scan-only unknown, so every panel came out C and the column discriminated nothing. One panel can
hold interfaces of all three classes, and that is the thing worth knowing.

    A  the interface is to a donor feature with a PUBLISHED dimension — workshop manual accuracy
    B  the interface is to a feature estimated from the CC-BY blueprint, "approx", +-15-30 mm
    C  the interface is to a feature with no estimate at all: it exists only as a scan-only
       unknown, so today there is no number to be wrong about

A panel's own class is the worst of its interfaces, because that is what governs its fit.

Nothing here invents a donor dimension, a mounting point or a fastener. Everything that depends on
the printer or the composite shop is a named parameter pointing at its question in docs/13.

    python3 01_CAD/scripts/panel_architecture.py           print the architecture
    python3 01_CAD/scripts/panel_architecture.py --csv     write reports/panel_architecture.csv
"""

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

_pr = {}
with open(os.path.join(HERE, "panel_registry.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("\ndef main(argv):")[0],
         {"__file__": os.path.join(HERE, "panel_registry.py"), "__name__": "_pr"}, _pr)
PARTS = _pr["PARTS"]
PANEL_STATUS = _pr["PANEL_STATUS"]

_sd = {}
with open(os.path.join(HERE, "scan_dependency_report.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("\ndef main(argv):")[0],
         {"__file__": os.path.join(HERE, "scan_dependency_report.py"), "__name__": "_sd"}, _sd)
SD_PANELS = _sd["PANELS"]          # key -> (dims used, scan-only unknowns, status)

# cage_986.py imports bpy, so it cannot be executed outside Blender. DIMS is a plain literal and
# is read by parsing, not by running the module — which also means this cannot pick up anything
# that was computed rather than written down.
import ast
with open(os.path.join(HERE, "cage_986.py"), "r", encoding="utf-8") as f:
    _src = f.read()
_i = _src.index("DIMS = {")
_j = _src.index("\n}", _i) + 2
DIMS = ast.literal_eval(_src[_i + len("DIMS = "):_j])   # name -> (value, provenance)


# --------------------------------------------------------------- the sandwich, as architecture
# Not a thickness. A stack, in which only the print core is ours to decide before the suppliers
# answer. Every number below is a PARAMETER with the question that sets it.
LAMINATE_STACK = [
    ("PRINT_CORE", "printed master, stays in the part as the core",
     "wall from docs/13 Q30, infill and perimeters from Q37, material from Q27/Q28"),
    ("SURFACE_PREP", "filler and primer over the print, to kill the layer lines",
     "allowance from docs/13 Q20 — how the shop wants the part to arrive"),
    ("LAMINATE", "glass over the prepared print; the print does not come out",
     "layers and thickness from docs/13 Q12"),
    ("LOCAL_REINFORCEMENT", "extra glass only where the panel is loaded or held",
     "where = mounting zones and free edges; how much from docs/13 Q12/Q16"),
]

# Where local reinforcement is needed, as a rule rather than a number.
REINFORCE_RULE = [
    "every mounting zone, out to at least the flange width (docs/13 Q15)",
    "every free edge that is not bonded to a neighbour",
    "any flat area larger than the printer can lay without lifting (docs/13 Q31)",
    "the leading edge of anything that can be kicked, kerbed or grounded",
]

# Joining, for a panel that has to be printed in sections. Parametric until the printer answers.
JOIN_RULES = [
    ("SPLIT_PLANE", "flat unless the printer says curved is fine (docs/13 Q34)"),
    ("KEY", "tongue-and-groove or dowel, form from docs/13 Q35"),
    ("KEY_CLEARANCE", "from docs/13 Q35 — not chosen here"),
    ("BOND_GAP", "from docs/13 Q36 — the adhesive's gap, not a modelling guess"),
    ("SPLIT_LOCATION", "never on a visible character line; behind a seam or inside a void"),
    ("RULE", "if a panel does not fit the machine, the SPLIT changes — never the design"),
]

# Print orientation, as a rule. The value needs Q32 (max unsupported overhang) and Q33 (who
# removes supports and whether the surface under one needs extra prep before lamination).
ORIENT_RULES = [
    "the class-A face goes UP or VERTICAL, never down onto supports",
    "if a face must be supported, it is a face that ends up inside the car",
    "the longest dimension lies in the build plate's longest axis (docs/13 Q26)",
    "no overhang steeper than Q32 without redesigning the split, not the surface",
]


# --------------------------------------------------------------- per-part architecture
# pid: (shape driver, removable after assembly, what the outer shape is governed by)
ARCH = {
    "P01": ("OURS",  "yes", "our nose form; the donor only sets how far forward it may sit"),
    "P02": ("MIXED", "yes", "outer shape ours; rear edge lands on the donor cowl"),
    "P03": ("DONOR", "yes", "arch opening and the front shut line govern it"),
    "P04": ("DONOR", "yes", "arch opening and the front shut line govern it"),
    "P05": ("OURS",  "yes", "insert inside our own channel"),
    "P06": ("OURS",  "yes", "insert inside our own channel"),
    "P07": ("MIXED", "yes", "outer form ours; the sill profile governs where it can bond"),
    "P08": ("MIXED", "yes", "outer form ours; the sill profile governs where it can bond"),
    "P39": ("OURS",  "yes", "our corner behind the rear wheel; all four of its edges are ours "
                            "or published, so nothing donor-derived shapes it"),
    "P40": ("OURS",  "yes", "our corner behind the rear wheel; all four of its edges are ours "
                            "or published, so nothing donor-derived shapes it"),
    "P09": ("DONOR", "yes", "overlay on the OEM door skin, between two donor shut lines"),
    "P10": ("DONOR", "yes", "overlay on the OEM door skin, between two donor shut lines"),
    "P11": ("DONOR", "yes", "the real opening behind it governs the mouth"),
    "P12": ("DONOR", "yes", "the real opening behind it governs the mouth"),
    "P13": ("OURS",  "yes", "blade inside our own mouth"),
    "P14": ("OURS",  "yes", "blade inside our own mouth"),
    "P15": ("DONOR", "no",  "overlay bonded to the welded quarter; the quarter governs it"),
    "P16": ("DONOR", "no",  "overlay bonded to the welded quarter; the quarter governs it"),
    "P17": ("MIXED", "no",  "our blade, but it sits in the roof fold envelope"),
    "P18": ("MIXED", "no",  "our blade, but it sits in the roof fold envelope"),
    "P19": ("MIXED", "no",  "our deck, height governed by the roof fold envelope"),
    "P42": ("MIXED", "no",  "our deck, height governed by the roof fold envelope"),
    "P20": ("MIXED", "yes", "our cover, aperture governed by the donor engine lid"),
    "P21": ("OURS",  "yes", "our rear form"),
    "P22": ("OURS",  "yes", "our diffuser; only its top edge meets the donor floor"),
    "P23": ("OURS",  "yes", "our ducktail"),
    "P24": ("OURS",  "yes", "housing around a bought E-marked module; the module is fixed"),
    "P25": ("OURS",  "yes", "housing around a bought E-marked module; the module is fixed"),
    "P26": ("OURS",  "yes", "housing around a bought E-marked module; the module is fixed"),
    "P27": ("OURS",  "yes", "housing around a bought E-marked module; the module is fixed"),
    # approved 2026-09-15, formerly PROPOSED_PARTS
    "P28": ("OURS",  "yes", "our splitter; the first thing to ground out, so replaceable alone"),
    "P41": ("OURS",  "yes", "our splitter; the first thing to ground out, so replaceable alone"),
    "P29": ("OURS",  "yes", "body-colour surround around a bought module; the module is fixed"),
    "P30": ("OURS",  "yes", "body-colour surround around a bought module; the module is fixed"),
    "P31": ("DONOR", "yes", "what the eye sees through the intake; the real opening governs it"),
    "P32": ("DONOR", "yes", "what the eye sees through the intake; the real opening governs it"),
    "P33": ("MIXED", "yes", "our louvres; the engine lid aperture governs where they can sit"),
    "P34": ("OURS",  "yes", "our centre mask between the light bar and the diffuser"),
    "P35": ("OURS",  "yes", "our surround around bought tips; sees exhaust heat"),
    "P36": ("OURS",  "yes", "our recess; the plate size is legislated, not donor"),
    "P37": ("DONOR", "yes", "cap over the OEM mirror body — its inner surface must match it"),
    "P38": ("DONOR", "yes", "cap over the OEM mirror body — its inner surface must match it"),
}

# --------------------------------------------------------------- parts the render shows and the
# register does not yet carry. PROPOSED — they are NOT in PARTS and nothing downstream uses them
# until the owner approves. Each one cites why it must be a separate part rather than a feature.
# All eight proposals were approved on 2026-09-15 and moved into panel_registry.PARTS as P28-P38.
# The list is kept empty rather than deleted, so the next proposal has an obvious place to go and
# so it stays visible that proposals are staged here before they become parts.
PROPOSED_PARTS = [
]


def interfaces(key):
    """Every fit-critical interface of one panel group, each classified A / B / C.
    Derived entirely from labels already recorded elsewhere; nothing is typed in here."""
    dims, scan_only, _status = SD_PANELS[key]
    out = []
    for d in dims:
        if d not in DIMS:
            continue
        val, label = DIMS[d]
        cls = "A" if label == "published" else "B"
        out.append((cls, d, f"{val}", label))
    for s in scan_only:
        out.append(("C", s, "-", "no estimate exists"))
    return out


def worst(key):
    cs = [c for c, *_ in interfaces(key)]
    for c in "CBA":
        if c in cs:
            return c
    return "-"


def main(argv):
    w = "--csv" in argv
    print("=" * 108)
    print("STATEV 001 — PANEL ARCHITECTURE.  Manufacturing layer over the register.")
    print("Nothing below invents a donor dimension, a mounting point or a fastener.")
    print("=" * 108)

    print("\nA. PANEL MASTER LIST\n")
    print(f"{'ID':<5}{'PART':<22}{'GRP':<7}{'SHAPE':<7}{'IF':<4}{'REMOV':<7}{'SCAN':<7}"
          f"{'ITS INTERFACES, BY CLASS'}")
    rows = []
    for pid, obj, side, grp, step, vec, method, key in PARTS:
        drv, removable, why = ARCH[pid]
        ifs = interfaces(key)
        cls = worst(key)
        prov = " ".join(f"{c}{sum(1 for x, *_ in ifs if x == c)}" for c in "ABC")
        print(f"{pid:<5}{obj:<22}{grp:<7}{drv:<7}{cls:<4}{removable:<7}"
              f"{PANEL_STATUS.get(key,'?'):<7}{prov}")
        rows.append(dict(ID=pid, PART=obj, SIDE=side, GROUP=grp, ASSEMBLY_STEP=step,
                         INSTALL_VECTOR=vec, METHOD=method, SHAPE_DRIVER=drv,
                         INTERFACE_CLASS=cls, REMOVABLE=removable,
                         SCAN_STATUS=PANEL_STATUS.get(key, "?"), INTERFACES_ABC=prov,
                         SHAPE_GOVERNED_BY=why))

    n_ours = sum(1 for r in rows if r["SHAPE_DRIVER"] == "OURS")
    n_donor = sum(1 for r in rows if r["SHAPE_DRIVER"] == "DONOR")
    n_mixed = len(rows) - n_ours - n_donor
    print(f"\n  shape driver: OURS {n_ours}   MIXED {n_mixed}   DONOR {n_donor}   of {len(rows)}")
    print(f"  worst interface class per panel: " + "   ".join(
        f"{c} {sum(1 for r in rows if r['INTERFACE_CLASS'] == c)}" for c in "ABC"))
    print("  Read it this way: the OURS parts can be surfaced now and the scan will move them,")
    print("  not reshape them. The DONOR parts are the ones where early surfacing is at risk.")

    print("\n\nB. WHAT THE SCAN CAN STILL CHANGE, PER GROUP\n")
    tally = {"A": 0, "B": 0, "C": 0}
    for key in sorted(SD_PANELS):
        _dims, _scan, status = SD_PANELS[key]
        print(f"  {key:<18} worst class {worst(key)}   scan status {status}")
        for cls, name, val, basis in interfaces(key):
            tally[cls] += 1
            print(f"      {cls}  {name:<52} {val:<8} {basis}")
    print(f"\n  fit-critical interfaces in total: " +
          "   ".join(f"{c} {tally[c]}" for c in "ABC"))
    print("  A moves by manual accuracy. B moves by up to 15-30 mm. C has no number yet at all.")

    print("\n\nC. THE SANDWICH, AS ARCHITECTURE\n")
    for name, what, param in LAMINATE_STACK:
        print(f"  {name:<22} {what}")
        print(f"  {'':<22} parameter: {param}")
    print("\n  local reinforcement goes:")
    for r in REINFORCE_RULE:
        print(f"    - {r}")

    print("\n\nD. SPLIT AND JOIN RULES\n")
    for k, v in JOIN_RULES:
        print(f"  {k:<16} {v}")
    print("\n  print orientation:")
    for r in ORIENT_RULES:
        print(f"    - {r}")

    print("\n\nE. PROPOSED ADDITIONS — NOT IN THE REGISTER, NOT APPROVED\n")
    for name, side, grp, drv, why in PROPOSED_PARTS:
        print(f"  {name:<26}{grp:<7}{drv:<7}{why}")
    if PROPOSED_PARTS:
        print(f"\n  {len(PROPOSED_PARTS)} proposals. None is in PARTS; nothing downstream uses them.")
    else:
        print("  none open. The eight from 2026-09-15 were approved and are now P28-P38 in the")
        print("  register. P37/P38, the mirror caps, went in with SHAPE_DRIVER=DONOR rather than")
        print("  OURS: a cap over the OEM mirror has to match a mirror body nobody has measured,")
        print("  which corrects the claim in docs/11 that it is a donor-free part.")

    print("\n\nF. FIRST FIT-TEST PANEL — TWO OF THEM, AND THEY ANSWER DIFFERENT QUESTIONS\n")
    print("  BEFORE the scan:  MIRROR_CAP  (proposed, not yet registered)")
    print("    It is the only part with no donor interface at all, so it can be printed now. What")
    print("    it tests is the PIPELINE, not the fit: surface -> thickness -> split -> print ->")
    print("    lay-up -> filler -> paint. Every mistake found here is found on a part worth hours,")
    print("    not weeks.")
    print("\n  AFTER the scan:   P03 FRONT_FENDER_L")
    print("    It carries the most risk in one part: a wheel arch, a donor shut line, a bolt-on")
    print("    donor interface, two panel junctions and a mounting region. docs/13 Q24 already")
    print("    commits to one fender first, and CLAUDE.md's learning path already ends there.")
    print("    It cannot be fit-tested before the scan, which is exactly why it is second.")

    if w:
        out = os.path.join(REPO, "04_ENGINEERING", "reports", "panel_architecture.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
