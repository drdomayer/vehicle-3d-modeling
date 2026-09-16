"""
panel_definition.py — the full manufacturing definition for every registered panel.

Three layers already exist and this is the fourth, not a replacement for any of them:

    panel_registry.py      WHICH parts exist, in what order they go on, how each is made
    panel_architecture.py  WHAT each depends on — shape driver, interface class, scan status
    panel_map.py           WHERE each one's boundary runs, proven to tile the body
    panel_definition.py    everything a manufacturer needs that is not geometry

Nothing here invents a donor dimension, a mounting hole or a fastener. Where a value depends on
the real car it says SCAN REQUIRED, and where it depends on a supplier answer it names the docs/13
question rather than choosing a number. Thickness is PROVISIONAL everywhere, because the material
and the technology are both unconfirmed.

READINESS is derived, not typed:

    READY NOW      the shape is ours and nothing it needs is blocked. Surfacing, boundaries,
                   flange topology and split architecture can all be built today; only the
                   mating interface waits.
    SCAN REQUIRED  the shape itself is governed by a donor feature. Building it early risks
                   rebuilding it, not just moving it.
    BLOCKED        it sits in or on the roof fold envelope, which exists nowhere as data.
                   docs/14 marks DECK_SPINE blocked and the scan plan puts session S2 first.

    python3 01_CAD/scripts/panel_definition.py          print the definitions
    python3 01_CAD/scripts/panel_definition.py --csv    write reports/panel_definition.csv
"""

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

_pa = {"__file__": os.path.join(HERE, "panel_architecture.py"), "__name__": "_pa"}
with open(os.path.join(HERE, "panel_architecture.py"), encoding="utf-8") as f:
    exec(f.read().split("\ndef main(argv):")[0], _pa)
PARTS, ARCH, SD_PANELS = _pa["PARTS"], _pa["ARCH"], _pa["SD_PANELS"]
PANEL_STATUS, interfaces, worst = _pa["PANEL_STATUS"], _pa["interfaces"], _pa["worst"]

# Panels that sit in or on the volume the soft top folds into. docs/14 marks DECK_SPINE BLOCKED
# and the buttress measures a 10 mm lip against a 93 mm intent for the same reason.
ROOF_BLOCKED = {"P17", "P18", "P19", "P20", "P23", "P33"}

# Per-panel facts that are not derivable from the other three layers.
#   pid: (design function, mounting strategy, trim allowance mm, access/service, split note)
T_BONDED = "bonded flange to donor sheet + mechanical at the ends. Points SCAN REQUIRED."
T_BOLT = "bolts through flange into donor threads. Positions SCAN REQUIRED."
T_OURS = "bolts or bonded tabs onto OUR adjacent panel, not onto the donor."
DEF = {
    "P01": ("the wedge nose and its face", T_BOLT, 15, "removable for crash-beam access",
            "splits at the centreline and behind the light blade"),
    "P28": ("lower aero lip; first thing to ground out", T_OURS, 10,
            "replaceable alone without disturbing the fascia", "centreline split"),
    "P02": ("long low hood, two faint tension zones", T_BOLT, 15,
            "opens for frunk; hinge arc SCAN REQUIRED", "splits across, behind the vents"),
    "P03": ("sculpted fender over the front wheel", T_BOLT, 20,
            "off for wheelhouse and suspension", "splits at the arch crown"),
    "P04": ("sculpted fender over the front wheel", T_BOLT, 20,
            "off for wheelhouse and suspension", "splits at the arch crown"),
    "P05": ("insert closing the fender channel", T_OURS, 8, "clips out from inside the channel",
            "single piece on any machine"),
    "P06": ("insert closing the fender channel", T_OURS, 8, "clips out from inside the channel",
            "single piece on any machine"),
    "P07": ("thin structural rocker blade", T_BONDED, 12,
            "jack points must stay usable with it on", "splits at the door shut line"),
    "P08": ("thin structural rocker blade", T_BONDED, 12,
            "jack points must stay usable with it on", "splits at the door shut line"),
    "P09": ("door skin overlay carrying the side channel", "bonded to the OEM door skin; "
            "no fasteners through the door. SCAN REQUIRED for the surface it sits on.", 10,
            "door must open and the glass must drop", "splits at the channel, hidden in the void"),
    "P10": ("door skin overlay carrying the side channel", "bonded to the OEM door skin; "
            "no fasteners through the door. SCAN REQUIRED for the surface it sits on.", 10,
            "door must open and the glass must drop", "splits at the channel, hidden in the void"),
    "P11": ("intake mouth surround, ahead of the rear wheel", T_BONDED, 15,
            "duct behind it must stay reachable", "split at the mouth's own lip"),
    "P12": ("intake mouth surround, ahead of the rear wheel", T_BONDED, 15,
            "duct behind it must stay reachable", "split at the mouth's own lip"),
    "P13": ("the vertical blade dividing body from cavity", T_OURS, 6,
            "out before the intake surround", "single piece"),
    "P14": ("the vertical blade dividing body from cavity", T_OURS, 6,
            "out before the intake surround", "single piece"),
    "P15": ("muscular rear haunch, overlay on the welded quarter",
            "bonded overlay, plus a 30-40 mm flange the bodyshop cuts where no seam exists. "
            "Where that flange can land is SCAN REQUIRED.", 20,
            "not removable once bonded; accept that", "splits at the arch crown and the shut line"),
    "P16": ("muscular rear haunch, overlay on the welded quarter",
            "bonded overlay, plus a 30-40 mm flange the bodyshop cuts where no seam exists. "
            "Where that flange can land is SCAN REQUIRED.", 20,
            "not removable once bonded; accept that", "splits at the arch crown and the shut line"),
    "P17": ("buttress blade beside the deck", T_OURS, 12, "fixed; sits over the roof fold volume",
            "single piece, but the blade itself is BLOCKED"),
    "P18": ("buttress blade beside the deck", T_OURS, 12, "fixed; sits over the roof fold volume",
            "single piece, but the blade itself is BLOCKED"),
    "P19": ("deck skin over the roof mechanism", T_OURS, 15,
            "must clear the fold path in all four roof positions", "splits at the centreline"),
    "P20": ("engine cover carrying the louvres", T_BOLT, 12,
            "opens for the engine; aperture SCAN REQUIRED", "splits across, between louvre banks"),
    "P33": ("functional louvres, one common vanishing direction", T_OURS, 6,
            "removable as a bank for engine access", "prints flat, one piece per bank"),
    "P21": ("rear fascia; the light bar cuts the tail in two", T_BOLT, 15,
            "off for exhaust and light access", "splits at the centreline and outboard of the bar"),
    "P34": ("dark centre mask carrying the lettering", T_OURS, 8, "off with the fascia",
            "single piece"),
    "P36": ("plate recess and its lamp; legal requirement", T_OURS, 8, "lamp must be serviceable",
            "single piece"),
    "P22": ("large functional diffuser, few large fins", T_BOLT, 15,
            "first thing to ground out; replaceable alone", "splits between fin roots"),
    "P35": ("surround for exactly two central tips; sees exhaust heat",
            "mechanical only, no adhesive near the heat. SCAN REQUIRED for hanger positions.", 10,
            "off with the exhaust", "single piece"),
    "P23": ("integrated ducktail lip growing from the deck", T_OURS, 10,
            "off without disturbing the deck", "splits at the centreline"),
    "P24": ("housing for a bought E-marked module", T_OURS, 6, "module replaceable from behind",
            "single piece"),
    "P25": ("housing for a bought E-marked module", T_OURS, 6, "module replaceable from behind",
            "single piece"),
    "P26": ("housing for a bought E-marked module", T_OURS, 6, "module replaceable from behind",
            "single piece"),
    "P27": ("housing for a bought E-marked module", T_OURS, 6, "module replaceable from behind",
            "single piece"),
    "P29": ("body-colour surround framing the light blade", T_OURS, 8, "off with the fascia",
            "single piece"),
    "P30": ("body-colour surround framing the light blade", T_OURS, 8, "off with the fascia",
            "single piece"),
    "P31": ("visible structure inside the intake", T_OURS, 6, "out through the mouth",
            "single piece"),
    "P32": ("visible structure inside the intake", T_OURS, 6, "out through the mouth",
            "single piece"),
    "P37": ("cap over the OEM mirror body", "clips onto the OEM mirror. Its inner surface must "
            "match a mirror nobody has measured: SCAN REQUIRED.", 5, "clips off by hand",
            "single piece"),
    "P38": ("cap over the OEM mirror body", "clips onto the OEM mirror. Its inner surface must "
            "match a mirror nobody has measured: SCAN REQUIRED.", 5, "clips off by hand",
            "single piece"),
}

# Strategies that are the same for every panel and belong in one place, not repeated 38 times.
COMMON = {
    "FLANGE": "20-35 mm wide, 10-20 mm overlap. PROVISIONAL until docs/13 Q15.",
    "INTERLOCK": "tongue-and-groove at every print split. Clearance PROVISIONAL until Q35/Q36.",
    "THICKNESS": "PROVISIONAL. Stack is print core + surface prep + laminate + local reinforcement; "
                 "core wall from Q30, laminate from Q12, infill from Q37.",
    "ORIENTATION": "class-A face up or vertical, never down onto supports; a supported face must be "
                   "one that ends up inside the car. Overhang limit from Q32.",
    "SUPPORT": "target support-free. Where unavoidable, the supported face is an inner face. Who "
               "removes them and what prep the surface then needs: Q33.",
    "GAP": "4 mm between STATEV panels; donor shut lines keep the donor's own gap. Q14.",
}


def readiness(pid):
    if pid in ROOF_BLOCKED:
        return "BLOCKED"
    if ARCH[pid][0] == "DONOR":
        return "SCAN REQUIRED"
    return "READY NOW"


def risk(pid, key):
    drv = ARCH[pid][0]
    st = PANEL_STATUS.get(key, "?")
    if pid in ROOF_BLOCKED:
        return "HIGH"
    if drv == "DONOR" and st == "RED":
        return "HIGH"
    if drv == "DONOR" or st == "RED":
        return "MEDIUM"
    return "LOW"


def rows():
    out = []
    for pid, obj, side, grp, step, vec, method, key in PARTS:
        drv, removable, governed = ARCH[pid]
        fn, mount, trim, access, split = DEF[pid]
        scan_items = [s for c, s, *_ in interfaces(key) if c == "C"]
        out.append(dict(
            PANEL_ID=pid, NAME=obj, ZONE=grp, DESIGN_FUNCTION=fn,
            BOUNDARY_REASON=governed, DONOR_INTERFACE=", ".join(scan_items) or "none",
            MOUNTING=mount, REMOVABLE=removable, FLANGE=COMMON["FLANGE"],
            INTERLOCK=COMMON["INTERLOCK"], THICKNESS=COMMON["THICKNESS"],
            PRINT_ORIENTATION=COMMON["ORIENTATION"], SPLIT_STRATEGY=split,
            SUPPORT=COMMON["SUPPORT"], TRIM_ALLOWANCE_MM=trim, ASSEMBLY_STEP=step,
            INSTALL_VECTOR=vec, ACCESS=access, SHAPE_DRIVER=drv,
            INTERFACE_CLASS=worst(key), SCAN_STATUS=PANEL_STATUS.get(key, "?"),
            READINESS=readiness(pid), RISK=risk(pid, key), STATUS="PROPOSED, not approved"))
    return out


def main(argv):
    R = rows()
    print("=" * 110)
    print("STATEV 001 — PANEL MANUFACTURING DEFINITION.  38 panels. Nothing approved, nothing frozen.")
    print("=" * 110)
    for tag in ("READY NOW", "SCAN REQUIRED", "BLOCKED"):
        sel = [r for r in R if r["READINESS"] == tag]
        print(f"\n{tag}   —   {len(sel)} panels")
        print(f"  {'ID':<6}{'NAME':<24}{'ZONE':<8}{'DRIVER':<7}{'RISK':<8}{'DESIGN FUNCTION'}")
        for r in sel:
            print(f"  {r['PANEL_ID']:<6}{r['NAME']:<24}{r['ZONE']:<8}{r['SHAPE_DRIVER']:<7}"
                  f"{r['RISK']:<8}{r['DESIGN_FUNCTION']}")
    print("\n\nCOMMON STRATEGIES — one place, not repeated per panel")
    for k, v in COMMON.items():
        print(f"  {k:<14}{v}")
    print(f"\n  risk: HIGH {sum(1 for r in R if r['RISK']=='HIGH')}   "
          f"MEDIUM {sum(1 for r in R if r['RISK']=='MEDIUM')}   "
          f"LOW {sum(1 for r in R if r['RISK']=='LOW')}")
    if "--csv" in argv:
        out = os.path.join(REPO, "04_ENGINEERING", "reports", "panel_definition.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(R[0]))
            w.writeheader()
            w.writerows(R)
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
