"""
check_statev_vs_donor.py — confront the STATEV 001 v0.1 skeleton with the donor hardpoints.

Reads DIMS from cage_986.py and the plan/section tables from data/986_plan_section.json,
then reports every place where the v0.1 spec disagrees with the 986 or with itself.
Prints a table; changes nothing in the scene. Run after statev_skeleton.py.

Repo coordinates throughout (+X forward). Spec X values are shown as spec_x for traceability.
"""

import json
import os

REPO = "/Users/miroslavstatev/vehicle-3d-modeling"
HERE = os.path.join(REPO, "01_CAD/scripts")

_ns = {}
with open(os.path.join(HERE, "cage_986.py"), "r", encoding="utf-8") as f:
    head = f.read().split("# ---------------------------------------------------------------- helpers")[0]
exec(head.replace("import bpy", ""), _ns)          # runs outside Blender too
DIMS = _ns["DIMS"]
with open(os.path.join(HERE, "data", "986_plan_section.json"), "r", encoding="utf-8") as f:
    PS = json.load(f)
_sk = {}
with open(os.path.join(HERE, "statev_skeleton.py"), "r", encoding="utf-8") as f:
    exec(f.read().split("def mm(")[0].replace("import bpy", ""), _sk)
SECTIONS, PACKAGE, BOXES = _sk["SECTIONS"], _sk["PACKAGE"], _sk["BOXES"]


def d(k):
    return DIMS[k][0]


def donor_half_width(repo_x):
    """986 outer half-width at a given repo X, from the 4-view plan table (±30 mm)."""
    tbl = sorted(PS["plan_half_width"], key=lambda t: t[0])
    xs = [t[0] for t in tbl]
    ys = [t[1] for t in tbl]
    if repo_x < xs[0] or repo_x > xs[-1]:
        return None
    for i in range(len(xs) - 1):
        if xs[i] <= repo_x <= xs[i + 1]:
            t = 0.0 if xs[i + 1] == xs[i] else (repo_x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


def hw_at(prof, z):
    zs = [p[0] for p in prof]
    ys = [p[1] for p in prof]
    if z < zs[0] or z > zs[-1]:
        return None
    for i in range(len(zs) - 1):
        if zs[i] <= z <= zs[i + 1]:
            t = 0.0 if zs[i + 1] == zs[i] else (z - zs[i]) / (zs[i + 1] - zs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


issues = []


def rec(sev, topic, msg):
    issues.append((sev, topic, msg))


print("=" * 100)
print("STATEV 001 v0.1  vs  Porsche 986 donor — conflict report")
print("=" * 100)

# ---------------------------------------------------------------- 1. package arithmetic
L = PACKAGE["front_overhang"] + PACKAGE["wheelbase"] + PACKAGE["rear_overhang"]
print(f"\n[package] {PACKAGE['front_overhang']} + {PACKAGE['wheelbase']} + {PACKAGE['rear_overhang']} "
      f"= {L} mm vs stated length {PACKAGE['length']} -> {'OK' if L == PACKAGE['length'] else 'MISMATCH'}")
print(f"[package] wheelbase {PACKAGE['wheelbase']} vs donor {d('wheelbase')} -> "
      f"{'OK' if PACKAGE['wheelbase'] == d('wheelbase') else 'MISMATCH'}")
if PACKAGE["length"] != DIMS["target_length"][0]:
    rec("note", "length", f"v0.1 targets {PACKAGE['length']} mm; DIMS target_length is "
        f"{DIMS['target_length'][0]} mm. Pick one — updating DIMS to {PACKAGE['length']}.")
if PACKAGE["height"] != DIMS["target_height"][0]:
    rec("note", "height", f"v0.1 targets {PACKAGE['height']} mm; DIMS target_height is "
        f"{DIMS['target_height'][0]}. Donor windshield header sits at {d('ws_top_z')} and the hoops at "
        f"{d('hoop_top_z')} — both above the tallest section (900), so height is set by the donor, not by the spec.")

# ---------------------------------------------------------------- 2. overhangs vs donor body
f_delta = PACKAGE["front_overhang"] - d("front_overhang")
r_delta = PACKAGE["rear_overhang"] - d("rear_overhang")
print(f"\n[overhang] front: STATEV {PACKAGE['front_overhang']} vs donor {d('front_overhang')} "
      f"-> {f_delta:+d} mm")
print(f"[overhang] rear:  STATEV {PACKAGE['rear_overhang']} vs donor {d('rear_overhang')} -> {r_delta:+d} mm")
if f_delta < 0:
    rec("check", "front overhang", f"the STATEV nose is {abs(f_delta)} mm BEHIND the donor's front bumper face. "
        "The OEM crash beam and its brackets live inside that space — clearance to the beam must be "
        "confirmed on the scan before the nose section is locked.")

# ---------------------------------------------------------------- 3. wheels and track
print("\n[wheels]")
for lbl, half_track, od, width, arch_r in (
        ("front", d("track_front") / 2, PACKAGE["tyre_front_od"], 235, 350),
        ("rear", d("track_rear") / 2, PACKAGE["tyre_rear_od"], 275, 365)):
    outer = half_track + width / 2
    print(f"  {lbl}: donor half-track {half_track:.1f} + tyre {width}/2 -> outer face Y {outer:.1f} mm | "
          f"tyre R {od/2:.1f}, arch R {arch_r} -> radial gap {arch_r - od/2:.1f} mm")
rec("fatal", "hub Y", "the spec puts the wheel centres at Y ±875 (front) / ±900 (rear). The donor track is "
    f"{d('track_front')}/{d('track_rear')}, i.e. ±{d('track_front')/2:.1f}/±{d('track_rear')/2:.1f}. "
    "The spec numbers need +285/+272 mm of extra track — impossible without new hubs/suspension. "
    "Wheel centres are a locked hardpoint; the skeleton uses the donor track. "
    "The spec's own text agrees: hub Y comes from the scan.")

# body vs tyre at the axle sections
for sec, lbl, half_track, width in (("S05", "front", d("track_front") / 2, 235),
                                    ("S11", "rear", d("track_rear") / 2, 275)):
    prof = SECTIONS[sec][2]
    body = max(y for _, y in prof)
    outer = half_track + width / 2
    print(f"  {sec} {lbl}: body max half-width {body} vs tyre outer face {outer:.1f} -> "
          f"{body - outer:+.1f} mm of body outboard of the tyre")
    if body - outer < 0:
        rec("fatal", f"{sec} tyre", f"the tyre sticks {outer - body:.1f} mm outside the body envelope.")

# ---------------------------------------------------------------- 4. body vs donor skin
print("\n[body vs donor skin]  (donor plan ±30 mm; negative = STATEV is INSIDE the OEM skin)")
tight = []
for name, (spec_x, role, prof) in sorted(SECTIONS.items(), key=lambda kv: kv[1][0]):
    repo_x = -spec_x
    dn = donor_half_width(repo_x)
    if dn is None:
        continue
    st = max(y for _, y in prof)
    gap = st - dn
    flag = "  <-- inside OEM" if gap < 0 else ("  <-- under 15 mm" if gap < 15 else "")
    print(f"  {name} specX {spec_x:>5} (repo {repo_x:>5}) {role:<18} STATEV {st:>5.0f} | donor {dn:>5.0f} | {gap:+6.0f}{flag}")
    if gap < 15:
        tight.append((name, spec_x, role, gap))
if tight:
    rec("check", "body vs OEM skin", "sections where the new body is inside, or within 15 mm of, the OEM outer skin: "
        + ", ".join(f"{n} (specX {x}, {r}, {g:+.0f} mm)" for n, x, r, g in tight)
        + ". The doors keep their OEM shut lines, so a door skin cannot sit inboard of the OEM door. "
          "Either widen those sections or accept a flush overlay of near-zero thickness.")

# ---------------------------------------------------------------- 5. headlights
print("\n[headlights]")
hl = next(b for b in BOXES if b[0] == "HEADLIGHT")
_, _, spec_x, y_c, z_c, sx_, sy_, sz_, _, _ = hl
prof = SECTIONS["S02"][2]
body_at_z = hw_at(prof, z_c)
outer_end = abs(y_c) + sy_ / 2
inner_end = abs(y_c) - sy_ / 2
print(f"  housing {sy_} long, centre Y ±{y_c}, Z {z_c} -> spans Y {inner_end:.0f} … {outer_end:.0f}")
print(f"  S02 body half-width at Z {z_c} = {body_at_z:.0f} mm")
if outer_end > body_at_z:
    rec("fatal", "headlight vs body", f"the housing's outer end reaches Y {outer_end:.0f} but the body at that "
        f"height is only {body_at_z:.0f} wide — it protrudes {outer_end - body_at_z:.0f} mm into thin air. "
        "Fix by one of: centre it at Y ±"
        f"{body_at_z - sy_/2:.0f}, shorten it to {2*(body_at_z - inner_end):.0f} mm, or run the blade "
        "diagonally (inner end low, outer end high) instead of straight along Y.")
low_edge = z_c - sz_ / 2
print(f"  lower edge of the housing Z {low_edge:.1f} vs legal minimum 500 -> "
      f"{'OK' if low_edge >= 500 else 'ILLEGAL'}")
if low_edge < 500:
    rec("fatal", "headlamp height", f"lower edge at {low_edge:.0f} mm, below the 500 mm minimum.")

# ---------------------------------------------------------------- 6. side intake vs the real opening
print("\n[side intake]")
intake = next(b for b in BOXES if b[0] == "SIDE_INTAKE")
ix_c, isx = intake[2], intake[5]
spec_lead = -d("side_intake_x")          # donor leading edge in spec X
spec_trail = 1900
print(f"  spec envelope: specX {ix_c - isx/2:.0f} … {ix_c + isx/2:.0f}")
print(f"  donor opening: specX {spec_trail} … {spec_lead:.0f}  (repo {-spec_lead:.0f} … {-spec_trail})")
if ix_c + isx / 2 < spec_trail:
    rec("fatal", "side intake", f"the spec's intake ends at specX {ix_c + isx/2:.0f}, but the donor's real opening "
        f"starts at specX {spec_trail} and runs to {spec_lead:.0f}. They do not overlap — as drawn the intake sits "
        "entirely on the door skin and feeds nothing. Hard constraint: the opening must feed the engine and every "
        f"opening is functional. Extend the channel to at least specX {spec_lead:.0f}.")

# ---------------------------------------------------------------- 6b. door skin vs the door aperture
print("\n[door skin]")
door = next(b for b in BOXES if b[0] == "DOOR_SKIN")
dsk_len = door[5]
ap_front, ap_rear = -d("door_front_x"), -d("door_rear_x")     # in spec X
aperture = abs(ap_rear - ap_front)
print(f"  spec door skin {dsk_len} long | donor shut lines specX {ap_front:.0f} … {ap_rear:.0f} "
      f"-> aperture {aperture:.0f} mm")
if abs(dsk_len - aperture) > 20:
    rec("check", "door skin", f"the spec's skin is {dsk_len} mm long but the donor door aperture between the "
        f"shut lines is {aperture:.0f} mm — a {aperture - dsk_len:.0f} mm shortfall. The shut lines are locked, "
        "so the skin has to span them exactly; take the length from the aperture, not from the spec.")

# ---------------------------------------------------------------- 6c. hood rear edge vs the cowl
print("\n[hood]")
hood = next(b for b in BOXES if b[0] == "HOOD")
hood_rear = hood[2] + hood[5] / 2.0
cowl_spec = -d("cowl_x")
print(f"  hood rear edge specX {hood_rear:.0f} | windshield base (cowl) specX {cowl_spec:.0f}")
if cowl_spec - hood_rear > 50:
    rec("check", "hood / cowl", f"the hood stops at specX {hood_rear:.0f} but the windshield base is at specX "
        f"{cowl_spec:.0f} — {cowl_spec - hood_rear:.0f} mm of body between them is unassigned. Either the hood "
        "runs back to the cowl or a separate cowl panel has to be added to the panel list.")

# ---------------------------------------------------------------- 7. aero fins vs roll hoops
print("\n[aero fins]")
fin = next(b for b in BOXES if b[0] == "AERO_FIN")
fx_c, fsx = fin[2], fin[5]
hoop_spec = -d("hoop_x")
print(f"  fin specX {fx_c - fsx/2:.0f} … {fx_c + fsx/2:.0f} | roll hoop plane specX {hoop_spec}")
if fx_c - fsx / 2 < hoop_spec:
    rec("check", "aero fins", f"the fins start at specX {fx_c - fsx/2:.0f}, which is "
        f"{hoop_spec - (fx_c - fsx/2):.0f} mm AHEAD of the roll hoop plane (specX {hoop_spec}) — i.e. over the door "
        "opening and the seats. The design calls for fins rising BEHIND the hoops. Start them at specX "
        f"{hoop_spec} or later, or accept that they cut into the cabin aperture.")
fin_y = abs(fin[3])
hoop_y = d("hoop_y")
print(f"  fin Y ±{fin_y} vs roll hoop tube plane Y ±{hoop_y}")

# ---------------------------------------------------------------- 8. deck vs donor roof
print("\n[rear deck vs donor]")
deck_max_z = max(z for _, z in _sk["DECK_SPINE"])
print(f"  deck spine peak Z {deck_max_z} | roll hoop top Z {d('hoop_top_z')} | windshield header Z {d('ws_top_z')}")
if deck_max_z < d("hoop_top_z"):
    print(f"  deck sits {d('hoop_top_z') - deck_max_z} mm below the hoop tops — the closed soft top has to bridge that")
rec("open", "roof", "the soft-top fold envelope, the engine-lid aperture and the clamshell path are still unknown. "
    "The deck peak (Z 800) and the louvre field (specX 2100–2700) both sit over them. Nothing behind the hoops "
    "can be locked before the scan.")

# ---------------------------------------------------------------- summary
print("\n" + "=" * 100)
order = {"fatal": 0, "check": 1, "note": 2, "open": 3}
for sev, topic, msg in sorted(issues, key=lambda i: order[i[0]]):
    print(f"[{sev.upper():5}] {topic}: {msg}\n")
print(f"{len(issues)} items: "
      + ", ".join(f"{k}={sum(1 for i in issues if i[0] == k)}" for k in order))
