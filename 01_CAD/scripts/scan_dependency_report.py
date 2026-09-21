"""
scan_dependency_report.py — map every STATEV panel onto what we actually know about the donor.

Answers the question the panel architecture ends with: "map every panel to the 986 scan and report
where the scan is missing or conflicts with the design". There is no scan. So this reports, per
panel, which donor facts we hold, where they came from and how good they are, and exactly what the
scan must supply before that panel can become geometry.

Status per panel:
  GREEN  — design intent complete and no donor interface is in doubt; surfacing can start
  YELLOW — intent complete, but at least one interface needs the scan before geometry is trusted
  RED    — blocked: a fact the panel cannot exist without is missing entirely

Runs outside Blender:  python3 01_CAD/scripts/scan_dependency_report.py
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
_ns = {}
with open(os.path.join(HERE, "cage_986.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("# ------------------------------------------------- helpers")[0].split(
        "# ---------------------------------------------------------------- helpers")[0]
         .replace("import bpy", ""), _ns)
DIMS = _ns["DIMS"]

# panel -> (known donor facts we hold, what only the scan can give, status)
PANELS = {
    "FRONT_CLAMSHELL": (
        ["front_overhang", "width_oem", "ground_clear_oem"],
        ["crash beam position and its brackets — the STATEV nose sits 57 mm behind the OEM bumper face",
         "bumper and fender mounting points",
         "radiator position and the space in front of it"],
        "RED"),
    "HOOD": (
        ["cowl_x", "cowl_z", "width_oem"],
        ["hinge positions and swing arc", "frunk aperture and its flange", "washer bottle / latch"],
        "YELLOW"),
    "FRONT_FENDER": (
        ["track_front", "wheelbase", "front_overhang"],
        ["fender mounting points", "wheelhouse liner and its clearance",
         "steering lock envelope — the kingpin axis is unknown, so the swept volume is a worst case"],
        "YELLOW"),
    "DOOR_SKIN": (
        ["door_front_x", "door_rear_x"],
        ["the OEM door's outer surface — the new skin is an overlay and must sit on it",
         "hinge and check-strap positions", "glass drop path and seal line"],
        "YELLOW"),
    "ROCKER": (
        ["door_front_x", "door_rear_x", "jack_front_y_total", "jack_rear_y_total"],
        ["sill profile and where a bonded flange can land", "jack point access after the panel is on"],
        "YELLOW"),
    "SIDE_INTAKE": (
        ["side_intake_x"],
        ["the real opening's shape, not just its X", "duct route from the opening to the plenum",
         "what is behind the opening on this particular car"],
        "RED"),
    "REAR_HAUNCH": (
        ["track_rear", "wheelbase", "width_oem"],
        ["the welded quarter's outer surface — the overlay bonds to it",
         "where the bodyshop can cut a 30–40 mm flange without touching structure",
         "wheelhouse and full suspension travel"],
        "RED"),
    "BUTTRESS": (
        ["hoop_x", "hoop_top_z", "hoop_y", "rollbar_mount_front_y_total", "rollbar_mount_rear_y_total"],
        ["roll-bar tube diameter and its real envelope",
         "whether a bonded subframe can pick up on the roll-bar mounts"],
        "YELLOW"),
    "REAR_DECK": (
        ["hoop_x", "hoop_top_z", "ws_top_z"],
        ["THE ROOF FOLD ENVELOPE in all four positions — closed, half, open, clamshell raised",
         "whether the deck must move with the clamshell or the roof stows beneath it",
         "engine lid aperture"],
        "RED"),
    "ENGINE_COVER": (
        ["hoop_x"],
        ["engine lid aperture and hinge", "engine bay top surface — how low the louvred panel can sit",
         "heat map: where the hot air actually needs to leave"],
        "RED"),
    "REAR_FASCIA": (
        ["rear_overhang", "length_oem"],
        ["rear bumper mounting points and crash structure", "exhaust hanger positions"],
        "YELLOW"),
    "REAR_SPOILER": (
        [],
        ["the rear deck surface it grows out of — blocked behind REAR_DECK"],
        "RED"),
    "DIFFUSER": (
        ["ground_clear_oem"],
        ["underbody and rear subframe", "exhaust routing and silencer position",
         "how low a fin can go before it is the first thing to ground out"],
        "RED"),
    "HEADLIGHT": (
        [],
        ["the front structure the housing bolts to", "beam aim check on the real car"],
        "YELLOW"),
    "TAIL_LIGHT": (
        [],
        ["the rear panel it mounts into — comes with REAR_FASCIA"],
        "YELLOW"),
}

ORDER = {"RED": 0, "YELLOW": 1, "GREEN": 2}


def main():
    print("=" * 100)
    print("STATEV 001 — panel vs donor knowledge.  THERE IS NO SCAN.")
    print("Every donor number below comes from a CC-BY drawing at 9 mm/px or the workshop manual.")
    print("=" * 100)

    counts = {"RED": 0, "YELLOW": 0, "GREEN": 0}
    for name, (known, needs, status) in sorted(PANELS.items(), key=lambda kv: (ORDER[kv[1][2]], kv[0])):
        counts[status] += 1
        print(f"\n[{status}] {name}")
        if known:
            print("  hold:")
            for k in known:
                v, src = DIMS[k]
                print(f"    {k:<30} {v:>8}   ({src})")
        else:
            print("  hold:  nothing donor-side")
        print("  scan must supply:")
        for n in needs:
            print(f"    - {n}")

    print("\n" + "=" * 100)
    print(f"RED {counts['RED']}   YELLOW {counts['YELLOW']}   GREEN {counts['GREEN']}"
          f"   of {len(PANELS)} panels")
    print("\nNo panel is GREEN. Not one exterior panel can become trusted geometry before the car is")
    print("scanned. The design intent is complete and regenerable; the interfaces are not knowable.")
    print("\nThe single item that unblocks the most: the roof fold envelope in four positions. It")
    print("gates REAR_DECK, which gates ENGINE_COVER, REAR_SPOILER and the whole rear group.")


# ---------------------------------------------------------------- capture plan
# Every "scan must supply" line above, grouped by what you physically do to the car to get it.
# Ordered so nothing has to be undone and re-done. The car is disassembled progressively.
SESSIONS = [
    ("S1  CAR COMPLETE, ROOF DOWN, ON ITS WHEELS", [
        "full exterior skin with all OEM panels on — the reference every panel is measured against",
        "door shut lines, sill, quarter surfaces where the overlay will bond",
        "tape measure control dims: wheelbase, both tracks, width over the arches, windshield height",
        "photograph every badge, seam and trim line before anything comes off",
    ]),
    ("S2  ROOF IN FOUR POSITIONS  ← do this before touching anything else", [
        "roof CLOSED",
        "roof HALF — mid travel, the widest point of the sweep",
        "roof OPEN and stowed",
        "clamshell lid RAISED, looking into the stowage well",
        "film the full cycle from the side and from above as well as scanning",
        "WHY FIRST: this gates REAR_DECK, which gates ENGINE_COVER, REAR_SPOILER and the whole rear",
    ]),
    ("S3  DOORS AND GLASS", [
        "door fully open — hinge positions, check strap, swing arc",
        "glass fully up and fully down — drop path and seal line",
        "door outer surface on its own, for the overlay skin",
    ]),
    ("S4  FRONT BUMPER AND FENDERS OFF", [
        "crash beam and its brackets — the STATEV nose sits 57 mm behind the OEM bumper face",
        "bumper and fender mounting points",
        "radiators, condensers, ducting, and the free space in front of them",
        "wheelhouse liners and the space behind them for the fender channel",
    ]),
    ("S5  ENGINE LID AND REAR BUMPER OFF", [
        "engine lid aperture and hinge",
        "engine bay top surface — how low the louvred panel can sit",
        "rear bumper mounts and crash structure",
        "exhaust hangers and silencer position",
        "the real side-intake opening: shape, not just its X, and what is behind it",
    ]),
    ("S6  UNDERSIDE, CAR RAISED", [
        "underbody and rear subframe for the diffuser",
        "sill profile where a bonded flange can land, and jack point access",
        "front and rear suspension at static ride height",
    ]),
    ("S7  SUSPENSION AT TRAVEL EXTREMES  (needs the car supported)", [
        "front wheels at full left and full right lock — the real steering envelope",
        "suspension at full compression and full extension if it can be safely forced",
        "WHY: the kingpin axis is unknown, so today's steering sweep is a worst case guess",
    ]),
    ("S8  INTERIOR", [
        "seat in the position a 190 cm driver actually uses",
        "dashboard, console, steering position",
        "headroom to the windshield header and to the hoops",
    ]),
]


def capture_plan():
    print("\n" + "=" * 100)
    print("CAPTURE PLAN — what to scan, in what order, and why")
    print("=" * 100)
    for title, items in SESSIONS:
        print(f"\n{title}")
        for i in items:
            print(f"   - {i}")
    print("\n" + "-" * 100)
    print("Rules that save a second trip:")
    print("  - S2 first. If the roof data is missing or wrong, the whole rear is blocked again.")
    print("  - Scan each session BEFORE removing the next set of parts. Nothing goes back on.")
    print("  - Every session gets tape-measure control dimensions, so the scan can be checked.")
    print("  - Photograph everything you unbolt, in place, before it moves.")


# Write the report as well as printing it. Until 2026-09-21 this file only printed, while CLAUDE.md
# and the decision log both name 04_ENGINEERING/reports/scan_dependency.txt as "its output" — the file in the repo had been
# made once by redirecting stdout by hand and then sat there for a week looking like live data.
# A report no script can regenerate is worse than no report.
import io as _io
import contextlib as _cx

# GUARDED, and the guard is not cosmetic. panel_registry.py pulls this file's tables in by
# exec'ing its source, so anything at module level here runs there too — an unguarded version of
# this block called main() inside panel_registry's namespace and died on a name it does not have.
if __name__ == "__main__":
    _buf = _io.StringIO()
    with _cx.redirect_stdout(_buf):
        main()
        capture_plan()
    _out = _buf.getvalue()
    print(_out, end="")
    _p = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                      "04_ENGINEERING", "reports", "scan_dependency.txt")
    os.makedirs(os.path.dirname(_p), exist_ok=True)
    with open(_p, "w", encoding="utf-8") as _f:
        _f.write(_out)
    print(f"\nwrote {_p}")

