"""
panel_registry.py — the numbered panel inventory, assembly order and BOM.

Fills the half of the exploded-assembly / manufacturing brief that does NOT need geometry:
part numbers, sides, assembly order, install and removal vectors, manufacturing method, material,
nominal thickness and status. The other half — flanges, overlaps, print splits, print orientation,
mass, centre of mass and the exploded view itself — needs real surfaces and is not faked here.

Part count is deliberately the minimum practical one, not the maximum. The diffuser fins are part
of the diffuser, not seven separate parts; the front is four parts rather than one huge clamshell.

    python3 01_CAD/scripts/panel_registry.py            print the register
    python3 01_CAD/scripts/panel_registry.py --csv      write 04_ENGINEERING/reports/panel_bom.csv
"""

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

_sd = {}
with open(os.path.join(HERE, "scan_dependency_report.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("def main(")[0], {"__file__": os.path.join(HERE, "scan_dependency_report.py"), "__name__": "_sd"}, _sd)
PANEL_STATUS = {k: v[2] for k, v in _sd["PANELS"].items()}

# Preliminary design values. Every one is subject to the composite shop's answers (docs/13).
PANEL_GAP_MM = 4.0            # between STATEV panels; donor shut lines keep the donor's gap
FLANGE_WIDTH_MM = (20, 35)
OVERLAP_MM = (10, 20)
NOMINAL_THICKNESS_MM = 2.5    # 2.0-3.0 depending on panel size and stiffness

# id: (object, side, design group, assembly step, install vector, manufacturing method, status key)
#   install vector is the direction the part travels onto the car, in repo axes (+X forward).
PARTS = [
    ("P01", "FRONT_FASCIA",        "-",  "FRONT", 3,  "+X", "printed master -> composite", "FRONT_CLAMSHELL"),
    ("P02", "HOOD",                "-",  "FRONT", 4,  "+Z", "printed master -> composite", "HOOD"),
    ("P03", "FRONT_FENDER_L",      "L",  "FRONT", 4,  "+Y", "printed master -> composite", "FRONT_FENDER"),
    ("P04", "FRONT_FENDER_R",      "R",  "FRONT", 4,  "-Y", "printed master -> composite", "FRONT_FENDER"),
    ("P05", "FENDER_CHANNEL_L",    "L",  "FRONT", 5,  "+Y", "direct print", "FRONT_FENDER"),
    ("P06", "FENDER_CHANNEL_R",    "R",  "FRONT", 5,  "-Y", "direct print", "FRONT_FENDER"),
    ("P07", "ROCKER_L",            "L",  "SIDE",  6,  "+Y", "printed master -> composite", "ROCKER"),
    ("P08", "ROCKER_R",            "R",  "SIDE",  6,  "-Y", "printed master -> composite", "ROCKER"),
    ("P09", "DOOR_SKIN_L",         "L",  "SIDE",  7,  "+Y", "printed master -> composite", "DOOR_SKIN"),
    ("P10", "DOOR_SKIN_R",         "R",  "SIDE",  7,  "-Y", "printed master -> composite", "DOOR_SKIN"),
    ("P11", "SIDE_INTAKE_L",       "L",  "SIDE",  8,  "+Y", "printed master -> composite", "SIDE_INTAKE"),
    ("P12", "SIDE_INTAKE_R",       "R",  "SIDE",  8,  "-Y", "printed master -> composite", "SIDE_INTAKE"),
    ("P13", "INTAKE_BLADE_L",      "L",  "SIDE",  9,  "+Y", "direct print or CNC", "SIDE_INTAKE"),
    ("P14", "INTAKE_BLADE_R",      "R",  "SIDE",  9,  "-Y", "direct print or CNC", "SIDE_INTAKE"),
    ("P15", "REAR_HAUNCH_L",       "L",  "REAR",  10, "+Y", "printed master -> composite", "REAR_HAUNCH"),
    ("P16", "REAR_HAUNCH_R",       "R",  "REAR",  10, "-Y", "printed master -> composite", "REAR_HAUNCH"),
    ("P17", "BUTTRESS_L",          "L",  "REAR",  11, "+Z", "printed master -> composite", "BUTTRESS"),
    ("P18", "BUTTRESS_R",          "R",  "REAR",  11, "+Z", "printed master -> composite", "BUTTRESS"),
    ("P19", "REAR_DECK",           "-",  "REAR",  12, "+Z", "printed master -> composite", "REAR_DECK"),
    ("P20", "ENGINE_COVER",        "-",  "REAR",  13, "+Z", "printed master -> composite", "ENGINE_COVER"),
    ("P21", "REAR_FASCIA",         "-",  "REAR",  14, "-X", "printed master -> composite", "REAR_FASCIA"),
    ("P22", "DIFFUSER",            "-",  "REAR",  15, "-X", "printed master -> composite", "DIFFUSER"),
    ("P23", "REAR_SPOILER",        "-",  "REAR",  16, "+Z", "direct print or composite", "REAR_SPOILER"),
    ("P24", "HEADLIGHT_HOUSING_L", "L",  "LIGHTS", 17, "+X", "direct print, ASA", "HEADLIGHT"),
    ("P25", "HEADLIGHT_HOUSING_R", "R",  "LIGHTS", 17, "+X", "direct print, ASA", "HEADLIGHT"),
    ("P26", "TAIL_HOUSING_L",      "L",  "LIGHTS", 18, "-X", "direct print, ASA", "TAIL_LIGHT"),
    ("P27", "TAIL_HOUSING_R",      "R",  "LIGHTS", 18, "-X", "direct print, ASA", "TAIL_LIGHT"),
]

ASSEMBLY_ORDER = [
    (1,  "donor hardpoints verified against the scan"),
    (2,  "mounting brackets and bonded tabs on the donor"),
    (3,  "front fascia"),
    (4,  "hood and front fenders"),
    (5,  "fender channel inserts"),
    (6,  "rockers"),
    (7,  "door skins"),
    (8,  "side intakes"),
    (9,  "intake blades"),
    (10, "rear haunches"),
    (11, "buttresses"),
    (12, "rear deck"),
    (13, "engine cover"),
    (14, "rear fascia"),
    (15, "diffuser"),
    (16, "rear spoiler"),
    (17, "headlight modules"),
    (18, "tail light modules"),
]

NOT_YET = [
    "flanges and their bolt patterns — need the scan and the shop's flange width",
    "panel overlaps — need adjacent surfaces to exist",
    "manufacturing splits and print orientation — need the shop's build volume (docs/13 Q9)",
    "mass and centre of mass — need solids with real thickness",
    "the exploded view itself — needs the panels",
    "door operation envelope — needs hinge positions from the scan",
]


def main(argv):
    print("=" * 96)
    print(f"STATEV 001 — panel register.  {len(PARTS)} parts, minimum practical count.")
    print(f"gap {PANEL_GAP_MM} mm | flange {FLANGE_WIDTH_MM[0]}-{FLANGE_WIDTH_MM[1]} mm | "
          f"overlap {OVERLAP_MM[0]}-{OVERLAP_MM[1]} mm | nominal thickness {NOMINAL_THICKNESS_MM} mm")
    print("These are preliminary and change with the composite shop's answers (docs/13).")
    print("=" * 96)
    print(f"\n{'ID':<5}{'PART':<22}{'SIDE':<6}{'GROUP':<8}{'STEP':<6}{'FIT':<5}{'STATUS':<8}METHOD")
    for pid, obj, side, grp, step, vec, method, key in PARTS:
        print(f"{pid:<5}{obj:<22}{side:<6}{grp:<8}{step:<6}{vec:<5}{PANEL_STATUS.get(key,'?'):<8}{method}")

    print("\nASSEMBLY ORDER")
    for n, what in ASSEMBLY_ORDER:
        print(f"  {n:>2}. {what}")

    print("\nREMOVAL: the reverse of the install vector, and the reverse of the assembly order.")
    print("Every part must come off without removing another, except: the intake blade comes out")
    print("before the intake, and the spoiler before the deck.")

    print("\nNOT IN THIS REGISTER YET — needs geometry or the shop's answers:")
    for n in NOT_YET:
        print(f"  - {n}")

    counts = {}
    for *_, key in PARTS:
        counts[PANEL_STATUS.get(key, "?")] = counts.get(PANEL_STATUS.get(key, "?"), 0) + 1
    print(f"\nstatus of the {len(PARTS)} parts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))

    if "--csv" in argv:
        out = os.path.join(REPO, "04_ENGINEERING/reports/panel_bom.csv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ID", "NAME", "SIDE", "DESIGN_GROUP", "ASSEMBLY_STEP", "INSTALL_VECTOR",
                        "MANUFACTURING_METHOD", "MATERIAL", "NOMINAL_THICKNESS_MM", "PANEL_GAP_MM",
                        "FLANGE_WIDTH_MM", "OVERLAP_MM", "STATUS", "LENGTH", "WIDTH", "HEIGHT",
                        "VOLUME", "ESTIMATED_MASS", "MOUNT_COUNT", "PRINT_SPLIT_COUNT"])
            for pid, obj, side, grp, step, vec, method, key in PARTS:
                mat = "ASA" if "ASA" in method else ("GRP composite" if "composite" in method else "PETG")
                w.writerow([pid, obj, side, grp, step, vec, method, mat, NOMINAL_THICKNESS_MM,
                            PANEL_GAP_MM, f"{FLANGE_WIDTH_MM[0]}-{FLANGE_WIDTH_MM[1]}",
                            f"{OVERLAP_MM[0]}-{OVERLAP_MM[1]}", PANEL_STATUS.get(key, "?"),
                            *["NEEDS_GEOMETRY"] * 5, "NEEDS_BUILD_VOLUME"])
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
