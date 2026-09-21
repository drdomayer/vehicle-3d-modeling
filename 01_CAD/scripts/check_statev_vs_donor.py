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
    exec(f.read().split("\ndef build():")[0].replace("import bpy", ""), _sk)
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


WIDEN = _sk["widening"]


def max_hw(spec_x, prof):
    """Section max half-width after the local widening around the axles."""
    return max(y + WIDEN(spec_x, z) for z, y in prof)


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


# Write the report as well as printing it, and do it without rewriting the body. Until 2026-09-21
# this file only printed, while the repo carried a donor_conflicts.txt that no script could
# regenerate: made once by redirecting stdout by hand on 2026-09-14 and then sitting for a week
# reading "fatal=2" as if it were live. CLAUDE.md supersedes this file for FIT measurement -- that
# is check_donor_fit.py, which measures the built surface -- but the question here is different and
# still live: does the SPECIFICATION conflict with the donor.
import contextlib as _cx
import io as _io

_buf = _io.StringIO()
with _cx.redirect_stdout(_buf):
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

    # body vs tyre. NOTE on what is and is not a conflict: below the arch line the tyre is SUPPOSED to
    # sit outside the body — that is what a wheel arch is, and every car has the rocker inboard of the
    # tread. The meaningful tests are (a) the section's widest point reaches past the tyre so the fender
    # covers the wheel, and (b) the arch aperture itself clears the tyre — that is the next block.
    print("  fender cover (section max vs tyre outer face):")
    for sec, lbl, half_track, width, arch_r, od in (
            ("S05", "front", d("track_front") / 2, 235, 350, PACKAGE["tyre_front_od"]),
            ("S11", "rear", d("track_rear") / 2, 275, 365, PACKAGE["tyre_rear_od"])):
        spec_x, _, prof = SECTIONS[sec]
        body = max_hw(spec_x, prof)
        outer = half_track + width / 2
        crown_z = od / 2 + arch_r                      # top of the arch aperture
        hw_crown = hw_at(prof, crown_z)
        hw_crown = None if hw_crown is None else hw_crown + WIDEN(spec_x, crown_z)
        print(f"    {sec} {lbl}: body max {body:.1f} vs tyre outer {outer:.1f} -> {body - outer:+.1f} | "
              f"at the arch crown Z {crown_z:.0f} the body is "
              f"{'above the section data' if hw_crown is None else f'{hw_crown:.1f}'}")
        if body - outer < 0:
            rec("fatal", f"{sec} fender cover", f"the tyre sticks {outer - body:.1f} mm beyond the widest "
                "point of the body — the fender does not cover the wheel.")
        if hw_crown is not None and hw_crown < outer:
            rec("check", f"{sec} arch crown", f"at the top of the arch (Z {crown_z:.0f}) the fender is only "
                f"{hw_crown:.1f} wide while the tyre's outer face is {outer:.1f}. The arch line follows the "
                "surface inboard there, so the aperture narrows at its crown — acceptable, but it means the "
                "fender does not crown over the wheel. If that is not the intended look, add width to "
                f"{sec} around Z {crown_z:.0f}.")

    # ---------------------------------------------------------------- 3b. wheel arch apertures
    print("\n[wheel arches]")
    ARCHES = _sk["ARCHES"]
    for key, (spec_x, radius, open_w, tod, twid) in ARCHES.items():
        half_track = (d("track_front") if key == "FRONT" else d("track_rear")) / 2.0
        sec = "S05" if key == "FRONT" else "S11"
        body = max_hw(SECTIONS[sec][0], SECTIONS[sec][2])
        outer = half_track + open_w / 2
        print(f"  {key}: R {radius} vs tyre R {tod/2:.1f} -> radial {radius - tod/2:+.1f} | "
              f"opening {open_w} vs tyre {twid} -> axial {(open_w-twid)/2:+.1f} each side | "
              f"outer edge Y {outer:.1f} vs body {body} at {sec} -> {body - outer:+.1f}")
        if radius - tod / 2 < 20:
            rec("fatal", f"{key} arch radius", f"only {radius - tod/2:.1f} mm between tyre and arch.")
        if outer > body:
            rec("check", f"{key} arch width", f"the arch aperture reaches Y {outer:.1f} but the body at "
                f"{sec} is {body:.1f} — the opening is {outer - body:.1f} mm wider than the surface it is cut "
                "into. Either the section grows to about "
                f"{outer + 10:.0f}, or the opening narrows to {2*(body - half_track):.0f}.")

    # ---------------------------------------------------------------- 4. body vs donor skin
    print("\n[body vs donor skin]  (donor plan ±30 mm)")
    print("  Only matters where the OEM skin is KEPT. Front bumper, fenders, hood and rear bumper are")
    print("  bolt-on and thrown away (docs/02), so sitting inside them there is fine — it is clearance.")
    print("  Doors keep their shut lines and rear quarters are welded: there the new skin is an overlay")
    print("  and must sit OUTSIDE the OEM surface.")
    RETAINED = [(-440, -2800)]        # repo X: door aperture through the welded rear quarters
    def retained(repo_x):
        return any(lo >= repo_x >= hi for lo, hi in RETAINED)
    tight = []
    for name, (spec_x, role, prof) in sorted(SECTIONS.items(), key=lambda kv: kv[1][0]):
        repo_x = -spec_x
        dn = donor_half_width(repo_x)
        if dn is None:
            continue
        st = max_hw(spec_x, prof)
        gap = st - dn
        keep = retained(repo_x)
        zone = "OVERLAY" if keep else "panel removed"
        flag = ""
        if keep and gap < 15:
            flag = "  <-- OVERLAY TOO TIGHT"
            tight.append((name, spec_x, role, gap))
        print(f"  {name} specX {spec_x:>5} (repo {repo_x:>5}) {role:<18} STATEV {st:>5.0f} | donor {dn:>5.0f} | "
              f"{gap:+6.0f} | {zone}{flag}")
    if tight:
        rec("check", "overlay too tight", "where the OEM skin is kept, the new skin must sit outside it with room "
            "for adhesive and a flange: "
            + ", ".join(f"{n} (specX {x}, {r}, {g:+.0f} mm)" for n, x, r, g in tight)
            + ". Under 15 mm there is no room for a bonded overlay.")

    # ---------------------------------------------------------------- 5. lighting
    print("\n[lighting]")
    pj = next(b for b in BOXES if b[0] == "PROJECTOR")
    _, _, pspec, py, pz, pdx, pdy, pdz, _, _ = pj
    prof = SECTIONS["S02"][2]
    body_at_z = hw_at(prof, pz) + WIDEN(pspec, pz)
    outer_end = abs(py) + pdy / 2
    print(f"  projector cavity {pdy}x{pdz}x{pdx} (Hella 90 mm bi-LED class), centre Y +-{py}, Z {pz}")
    print(f"  spans Y {abs(py)-pdy/2:.0f} … {outer_end:.0f} vs body {body_at_z:.0f} at that height -> "
          f"{body_at_z - outer_end:+.0f}")
    if outer_end > body_at_z:
        rec("fatal", "projector vs body", f"the cavity reaches Y {outer_end:.0f}, body is {body_at_z:.0f}.")
    low_edge = pz - pdz / 2
    print(f"  lit-surface lower edge Z {low_edge:.1f} vs the 500 mm minimum -> "
          f"{'OK' if low_edge >= 500 else 'ILLEGAL'}")
    if low_edge < 500:
        rec("fatal", "headlamp height", f"lower edge {low_edge:.0f} mm, below 500.")
    drl_lo = 350
    print(f"  DRL blade runs along the body's widest line; position lamps need >= {drl_lo} mm — the blade's "
          "own z_range property carries the built value")

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
    fin = next((b for b in BOXES if b[0] == "BUTTRESS"), None)
    fx_c, fsx = (fin[2], fin[5]) if fin else (1e9, 0)
    hoop_spec = -d("hoop_x")
    print(f"  fin specX {fx_c - fsx/2:.0f} … {fx_c + fsx/2:.0f} | roll hoop plane specX {hoop_spec}")
    if fin and fx_c - fsx / 2 < hoop_spec:
        rec("check", "aero fins", f"the fins start at specX {fx_c - fsx/2:.0f}, which is "
            f"{hoop_spec - (fx_c - fsx/2):.0f} mm AHEAD of the roll hoop plane (specX {hoop_spec}) — i.e. over the door "
            "opening and the seats. The design calls for fins rising BEHIND the hoops. Start them at specX "
            f"{hoop_spec} or later, or accept that they cut into the cabin aperture.")
    fin_y = abs(fin[3]) if fin else 0
    hoop_y = d("hoop_y")
    print(f"  fin Y ±{fin_y} vs roll hoop tube plane Y ±{hoop_y}")

    # ---------------------------------------------------------------- 8. deck vs donor roof
    print("\n[rear deck vs donor]")
    deck_max_z = max(z for _, z in _sk["DECK_SPINE"])
    but = next((b for b in BOXES if b[0] == "BUTTRESS"), None)
    but_top = (but[4] + but[7] / 2) if but else 0
    deck_start = min(x for x, _ in _sk["DECK_SPINE"])
    print(f"  deck centreline peak Z {deck_max_z} | buttress top Z {but_top:.0f} | "
          f"hoop tops Z {d('hoop_top_z')} | windshield header Z {d('ws_top_z')}")
    print(f"  deck starts at specX {deck_start} | hoop plane specX {-d('hoop_x')}")
    if deck_start < -d("hoop_x"):
        rec("check", "deck start", f"the deck begins at specX {deck_start}, ahead of the hoop plane "
            f"({-d('hoop_x')}) — that is over the seats, not over the engine.")
    if but_top > d("hoop_top_z"):
        rec("check", "buttress height", f"the buttresses reach Z {but_top:.0f}, above the hoop tops "
            f"({d('hoop_top_z')}) — the hoops stop reading as their own structure.")
    rec("fatal", "roof fold vs raised deck", "the deck and buttresses now sit at Z 960/1090 behind the "
        "hoops. That is exactly the volume the 986 soft top folds into. Either the deck is part of the "
        "lid that opens with the OEM clamshell, or the roof has to stow entirely beneath it. Nothing in "
        "either render or the written spec says which. This is the single highest-risk unknown in the "
        "whole project and it is only answerable on the real car — scan the roof in all four positions.")
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

_out = _buf.getvalue()
print(_out, end="")
if __name__ == "__main__":
    _p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      "04_ENGINEERING", "reports", "donor_conflicts.txt")
    os.makedirs(os.path.dirname(_p), exist_ok=True)
    with open(_p, "w", encoding="utf-8") as _f:
        _f.write(_out)
    print(f"\nwrote {_p}")
