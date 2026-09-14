"""
freeze.py — the FREEZE RULE, as machinery rather than a promise.

Once a zone is approved it is frozen. From then on the build REFUSES to run if anything that
defines that zone has changed, and says exactly what changed. Unfreezing is an explicit act with
a reason recorded. This exists because the front, the side intake and the tail lights each drifted
once already, and a rule that lives only in a document does not stop that.

    python3 01_CAD/scripts/freeze.py                      status
    python3 01_CAD/scripts/freeze.py FRONT --freeze       "FRONT DESIGN APPROVED"
    python3 01_CAD/scripts/freeze.py FRONT --unfreeze "why"

Zones and what belongs to each are in ZONES. The hash covers the data that defines the zone's
geometry — its sections and its elements — so a change to a note or a comment does not trip it,
but a changed dimension does.
"""

import hashlib
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "data", "freeze_state.json")

# zone -> (section names, element name prefixes, extra module-level tables)
ZONES = {
    "FRONT":  (["S00", "S01", "S02", "S03"],
               ["FRONT_CLAMSHELL", "HOOD", "FRONT_FENDER", "FRONT_MASK", "RAD_INTAKE", "RAD_DUCT",
                "HOOD_VENT", "FENDER_CHANNEL", "BRAKE_DUCT_F"],
               ["HOOD_SPINE"]),
    "SIDE":   (["S04", "S05", "S06", "S07", "S08", "S09"],
               ["DOOR_SKIN", "DOOR_VENT", "ROCKER", "ROCKER_CHANNEL", "SIDE_INTAKE", "INTAKE_INLET",
                "INTAKE_DUCT", "INTAKE_OUTLET", "INTAKE_BLADE"],
               ["ARCHES", "DOOR_CHAR_LINE_Z"]),
    "REAR":   (["S10", "S11", "S12", "S13", "S14"],
               ["REAR_HAUNCH", "BUTTRESS", "REAR_DECK", "ENGINE_COVER", "REAR_FASCIA",
                "REAR_SPOILER", "DIFFUSER", "EXHAUST", "BRAKE_DUCT_R"],
               ["DECK_SPINE", "DIFFUSER_TUNNEL", "LOUVERS", "DIFFUSER_FINS"]),
    "ROOF":   ([], [], []),          # roof envelopes are provisional; freezing is meaningless yet
    "LIGHTS": ([], ["PROJECTOR", "DRL", "TAIL_BAR", "TAIL_END"], ["DRL_PATH", "DRL_SECTION"]),
}


def _skel():
    ns = {}
    with open(os.path.join(HERE, "statev_skeleton.py"), "r", encoding="utf-8") as f:
        exec(f.read().split("def build(")[0].replace("import bpy", ""), ns)
    return ns


def zone_hash(zone, ns=None):
    """Stable hash of everything that defines a zone's geometry."""
    ns = ns or _skel()
    secs, prefixes, extras = ZONES[zone]
    blob = []
    for s in secs:
        if s in ns["SECTIONS"]:
            x, _role, prof = ns["SECTIONS"][s]
            blob.append(f"{s}:{x}:{[list(p) for p in prof]}")
    for b in ns["BOXES"]:
        if any(b[0] == p or b[0].startswith(p + "_") for p in prefixes):
            blob.append(f"{b[0]}:{b[2:8]}")          # collection, x, y, z, sx, sy, sz
    for e in extras:
        if e in ns:
            blob.append(f"{e}:{ns[e]}")
    return hashlib.sha256("|".join(sorted(blob)).encode()).hexdigest()[:16]


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {z: {"state": "OPEN", "hash": None, "frozen_at": None, "history": []} for z in ZONES}


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(st, f, indent=1)


def check(raise_on_violation=True):
    """Called by the build. Returns a list of violations; raises on the first if asked to."""
    st, ns, bad = load(), _skel(), []
    for z, rec in st.items():
        if rec["state"] != "FROZEN":
            continue
        now = zone_hash(z, ns)
        if now != rec["hash"]:
            bad.append(f"{z} is FROZEN (since {rec['frozen_at']}) but its defining data changed "
                       f"[{rec['hash']} -> {now}]. Either revert the change, or run:  "
                       f"python3 01_CAD/scripts/freeze.py {z} --unfreeze \"reason\"")
    if bad and raise_on_violation:
        raise RuntimeError("FREEZE RULE VIOLATED\n  " + "\n  ".join(bad))
    return bad


def main(argv):
    st = load()
    if len(argv) < 2:
        print(f"{'ZONE':<8} {'STATE':<8} {'HASH':<18} SINCE")
        ns = _skel()
        for z, rec in st.items():
            now = zone_hash(z, ns)
            drift = "" if rec["state"] != "FROZEN" or now == rec["hash"] else f"  <-- DRIFTED (now {now})"
            print(f"{z:<8} {rec['state']:<8} {str(rec['hash']):<18} {rec['frozen_at'] or '-'}{drift}")
        print("\nA frozen zone cannot be rebuilt after its data changes. That is the point.")
        return 0

    zone = argv[1].upper()
    if zone not in ZONES:
        print(f"unknown zone {zone}; known: {', '.join(ZONES)}")
        return 1
    if "--freeze" in argv:
        h = zone_hash(zone)
        st[zone].update(state="FROZEN", hash=h, frozen_at=str(date.today()))
        st[zone]["history"].append(f"{date.today()} FROZEN at {h}")
        save(st)
        print(f"{zone} FROZEN at {h}. The build now refuses to run if it changes.")
    elif "--unfreeze" in argv:
        i = argv.index("--unfreeze")
        reason = argv[i + 1] if len(argv) > i + 1 else ""
        if not reason:
            print("unfreezing needs a reason: freeze.py ZONE --unfreeze \"why\"")
            return 1
        st[zone].update(state="OPEN", hash=None)
        st[zone]["history"].append(f"{date.today()} UNFROZEN: {reason}")
        save(st)
        print(f"{zone} OPEN. Reason recorded: {reason}")
    else:
        print("use --freeze or --unfreeze \"reason\"")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
