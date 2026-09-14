"""
statev_skeleton.py — STATEV 001 master surface skeleton v0.1 (design spec, not production CAD).

Builds the 15 master cross-sections S00–S14, longitudinal rails through them, and placeholder
envelopes for every discrete element of the v0.1 dimensional specification. Nothing here is a
surface: sections are curves, elements are wireframe boxes. Loft only after the wireframe is
judged correct (owner's call), per the agreed pipeline:
    sections -> rails -> visual check -> loft -> panel split -> thicken -> STL.

COORDINATES — the spec was written with +X toward the rear; this repo uses +X FORWARD
(see CLAUDE.md and cage_986.py). Every spec X is negated on import: x_repo = -x_spec.
Each object carries `spec_x_mm` so the original number stays traceable.
Y: repo +Y = LEFT (spec used +Y = right). Geometry is symmetric, so only the _L/_R naming differs.

Run after cage_986.py. Re-running rebuilds the STATEV_001 collection tree.
Status of every number: "spec" = from the v0.1 package, "derived" = computed here,
"PLACED" = position not given in the spec, chosen here and flagged for the owner.
"""

import bpy
import os

COLL_ROOT = "STATEV_001"
PFX = "STATEV_"          # every object this script owns carries it (prompt §6, §9)
SCRIPTS_DIR = (os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals()
               else "/Users/miroslavstatev/vehicle-3d-modeling/01_CAD/scripts")

# ---------------------------------------------------------------- package targets (mm)
PACKAGE = {
    "wheelbase": 2415,
    "length": 4370,
    "width_max_rear": 1850,
    "width_max_front": 1800,
    "height": 1285,
    "ground_clearance": 120,
    "front_overhang": 950,          # spec X of the front tip, negated -> repo +950
    "rear_overhang": 1005,
    "tyre_front": "235/35R19",
    "tyre_front_od": 647,
    "tyre_rear": "275/35R19",
    "tyre_rear_od": 675,
}

# ---------------------------------------------------------------- master cross-sections
# name: (spec_x, role, [(z, half_width_y), ...] bottom -> top)
SECTIONS = {
    "S00": (-950, "front tip",        [(120, 120), (250, 280), (350, 350), (450, 300)]),
    "S01": (-850, "front mask",       [(120, 300), (250, 470), (350, 550), (450, 580), (550, 500)]),
    "S02": (-700, "headlights",       [(120, 500), (250, 650), (400, 720), (550, 700), (650, 600)]),
    "S03": (-500, "front fender in",  [(120, 650), (250, 780), (400, 820), (550, 810), (700, 700)]),
    "S04": (-250, "ahead of arch",    [(120, 720), (250, 830), (400, 870), (550, 850), (700, 720)]),
    "S05": (0,    "FRONT AXLE",       [(120, 730), (250, 850), (400, 900), (550, 860), (700, 720)]),
    "S06": (350,  "behind front arch",[(120, 720), (250, 820), (400, 850), (550, 830), (700, 700)]),
    "S07": (800,  "door centre",      [(120, 700), (250, 800), (400, 850), (550, 875), (700, 820), (800, 700)]),
    "S08": (1200, "side intake start",[(120, 700), (250, 800), (400, 860), (550, 880), (700, 820), (800, 700)]),
    "S09": (1600, "side intake deep", [(120, 720), (250, 830), (400, 900), (550, 915), (700, 850), (800, 720)]),
    "S10": (2000, "rear haunch start",[(120, 730), (250, 850), (400, 900), (550, 925), (700, 920), (800, 850), (900, 700)]),
    "S11": (2415, "REAR AXLE",        [(120, 750), (250, 870), (400, 915), (550, 925), (700, 900), (800, 820), (900, 700)]),
    "S12": (2800, "behind rear wheel",[(120, 720), (250, 850), (400, 900), (550, 900), (700, 820), (800, 700), (900, 550)]),
    "S13": (3200, "rear fascia",      [(120, 650), (250, 780), (400, 820), (550, 780), (650, 650), (750, 500)]),
    "S14": (3420, "rear tip",         [(120, 350), (250, 500), (400, 550), (500, 450), (600, 300)]),
}

RAIL_LEVELS = [120, 250, 400, 550, 700, 800, 900]

# ---------------------------------------------------------------- engineering decisions
# Taken here, not asked of the owner, per the agreed priority order:
#   A donor hardpoints  B physical clearance  C STATEV proportions  D surface continuity
#   E functional airflow  F manufacturability  G provisional dimensions
# When G loses to A–F, the dimension changes and the reason is recorded.
DECISIONS = {
    "headlight": "The 650x100x65 bar centred at Y +-570 was dropped (it stuck 215 mm outside the "
                 "body). Split into what the two things actually are: a thin DRL/position blade that "
                 "follows the body's widest line across the nose and kicks up into the fender, and a "
                 "separate projector cavity sized for a real Hella 90 mm bi-LED module "
                 "(110x110x150 incl. heatsink). Priority C+D over G; docs/04 already decided "
                 "E-marked modules in custom housings.",
    "side_intake": "The sculpted channel now runs to specX 2080, the donor's real opening, instead of "
                   "stopping at 1800. Priority A+E over G. The visible shape is still free; the "
                   "airflow path is not.",
    "arches": "Sections are NOT hand-tuned one by one. A smooth cosine widening is blended around "
              "each axle so the body grows around the wheel and the arch aperture stays inside the "
              "surface: +18 mm front, +34 mm rear at the axle, tapering to zero over +-600 mm and "
              "only across the Z band the arch spans. Priority B+D over G.",
    "aero_fins": "Fins start at the roll-hoop plane (specX 1760) instead of 1450, keeping the spec'd "
                 "750 mm length by extending the tail to 2510. Priority A over G — at 1450 they sat "
                 "over the door aperture and the seats.",
    "door_skin": "Length taken from the donor aperture between the shut lines (1195), not the spec's "
                 "1050. Priority A over G — the skin has to land on the locked shut lines.",
    "hood": "Rear edge extended back to the windshield base (specX 420) instead of 80. Priority D+F "
            "over G — the 340 mm strip belonged to no panel.",
}

# local widening around each axle: (spec_x, delta_mm, taper_half_length_mm, z_lo, z_hi)
# Cut back 2026-09-14 to hit the 1850 target. The width comes out of the volume around the wheels,
# not out of the cabin or the shoulder line.
AXLE_WIDENING = [
    (0,     6, 600, 200, 700),
    (2415,  0, 600, 200, 750),
]

# wheel arch apertures (msg1 §4): key -> (spec_x, radius, opening_width_y, tyre_od, tyre_width)
# radius is measured from the wheel centre; opening width is the axial size of the aperture.
ARCHES = {
    "FRONT": (0,    350, 350, 647, 235),
    "REAR":  (2415, 365, 370, 675, 275),
}

# diffuser central tunnel (msg1 §18): width 500 inside the 1500 wide diffuser
DIFFUSER_TUNNEL = (3145, 0, 230, 550, 500, 220)   # spec_x, y, z, size_x, size_y, size_z

# door character line (msg1 §11): the surface crease, front/middle/rear heights on the door
DOOR_CHAR_LINE_Z = {"front": 420, "middle": 500, "rear": 520}

# ---------------------------------------------------------------- discrete elements
# name: (collection, spec_x_centre, y_centre, z_centre, size_x, size_y, size_z, status, note)
# y_centre None -> mirrored pair is built at ±|y|
BOXES = [
    # --- lighting
    ("PROJECTOR",   "04_LIGHTING", -700,  560,  570,  150,  110,  110, "DECIDED",
     "cavity for ONE real Hella 90 mm bi-LED module (low+high): 110 dia x ~150 deep incl. heatsink. "
     "Lit-surface lower edge 515 mm, above the 500 mm legal minimum. Sits inside the body: at S02 "
     "Z 570 the half-width is 680, the cavity spans Y 505..615. Replaces the 650x100x65 bar."),
    ("PROJECTOR_2", "04_LIGHTING", -700,  420,  570,  150,  110,  110, "OPTIONAL",
     "room for a second module if low and high are split across two units; delete if one bi-LED is used"),
    ("TAIL_BAR",    "04_LIGHTING", 3230,    0,  700,   45, 1560,   38, "LOCKED",
     "thin full-width blade across the tail. Z 700 sits on the S13 shoulder (top control point 750)."),
    ("TAIL_END",    "04_LIGHTING", 3150,  790,  700,  120,   40,   38, "LOCKED",
     "L termination: the blade turns forward onto the quarter at each outboard end. I had dropped "
     "this when I read the render as a plain bar — the locked intent is blade PLUS sharp L ends. "
     "Explicitly NOT a Lamborghini-style separate triangular lamp; the light stays integrated "
     "into the body."),
    ("HOOD_VENT",   "02_BODY",     -600,  250,  610,  380,  130,   25, "DECIDED",
     "pair of hood extractors, in both renders and absent from the written spec. Functional: they are "
     "the hot-air exit from the radiator duct, so they must line up with it (RAD_DUCT ends at specX "
     "-680). Size is read off the render proportions - PROVISIONAL until the radiator is scanned."),
    # --- front
    ("FRONT_CLAMSHELL", "02_BODY", -400,    0,  450, 1100, 1800,  660, "DESIGN_GROUP",
     "envelope X -950..150, Y +-900, Z 120..780. This is a DESIGN GROUP, not one physical part: it "
     "must read as one coherent front, but the manufactured split into nose / hood / left fender / "
     "right fender is decided by mounting, servicing and the shop's build volume, not by styling."),
    ("HOOD",        "02_BODY",     -265,    0,  585, 1370, 1500,  270, "DECIDED",
     "rear edge extended from specX 80 back to the windshield base at 420, closing the 340 mm strip "
     "that belonged to no panel. Z 450 at the front edge to 720 at the rear - envelope only"),
    ("FRONT_FENDER","02_BODY",     -200,  875,  490,  900,   50,  480, "spec",
     "X -650..250, Y 850..900, Z 250..730; a shell, not a flare over the OEM fender"),
    ("FRONT_MASK",  "02_BODY",     -870,    0,  310,  100,  650,  150, "spec", "mask panel envelope"),
    ("RAD_INTAKE",  "02_BODY",     -830,    0,  320,  140,  560,  140, "spec",
     "central opening: spec X -900..-760, Y +-280, Z 250..390"),
    ("RAD_DUCT",    "05_MECHANICAL",-755,   0,  320,  150,  500,  100, "spec",
     "duct behind the opening; real radiator position comes from the scan"),
    ("FENDER_CHANNEL","03_AERO",    325,  835,  500,  350,   90,  180, "PLACED",
     "hot-air exit behind the front wheel; spec gives X 150..500 and the section but no Z/Y centre"),
    # --- sides
    ("DOOR_SKIN",   "02_BODY",     1038,  850,  545, 1195,   30,  650, "DECIDED",
     "length taken from the donor aperture between the shut lines (1195), not the spec's 1050 — the "
     "shut lines are locked. Z centre still PLACED: the spec only gives the crease at Z 420/500/520"),
    ("REAR_HAUNCH", "02_BODY",     2375,  887,  575,  950,   75,  550, "spec",
     "X 1900..2850, Y 850..925, Z 300..850; loft through 5-7 sections, not one sculpted blob"),
    ("REAR_DECK",   "02_BODY",     2575,    0,  750, 1450, 1850,  200, "spec",
     "X 1850..3300, width 1500..1850, Z 650..850; thin skin, must not box in the engine bay"),
    ("DOOR_VENT",   "03_AERO",      480,  845,  560,   70,   55,  260, "DECIDED",
     "tall narrow slot at the LEADING EDGE of the door, ref-08 side view. Reads as the hot-air exit "
     "from the front wheel well / radiator, so it pairs with FENDER_CHANNEL and HOOD_VENT. Sits just "
     "behind the donor's front shut line (specX 440) - the line is locked, the vent is not on it."),
    ("ROCKER_CHANNEL", "03_AERO",  1038,  810,  240, 1195,   80,   90, "DECIDED",
     "deep undercut along the sill, running the full length of the door aperture, ref-08. Feeds the "
     "side intake and visually lowers the car. Length taken from the donor shut lines, not the render."),
    ("REAR_SPOILER", "03_AERO",    3120,    0,  770,  240, 1450,   55, "DECIDED",
     "integrated lip / ducktail growing out of the rear deck, NOT a fixed wing on stalks. The render "
     "does not need a wing and a wing would read as a track conversion rather than a designed tail."),
    ("ROCKER",      "02_BODY",     1038,  830,  260, 1300,   60,  140, "DECIDED",
     "thin low technical rocker, deliberately NOT a massive side skirt. Visually links front aero to "
     "the door to the diffuser and makes the car read low without dropping the chassis."),
    ("BRAKE_DUCT_F", "05_MECHANICAL", -330, 700,  330,  260,  140,  140, "DECIDED",
     "front brake cooling: enclosed duct from ahead of the wheel to the disc. Functional, not a "
     "styling slot. Exact routing needs the scan of the suspension and liner."),
    ("BRAKE_DUCT_R", "05_MECHANICAL", 2080, 780,  360,  220,  130,  130, "DECIDED",
     "rear brake cooling, fed off the side-intake path. Small and functional."),
    ("SIDE_INTAKE", "03_AERO",     1640,  887,  485,  880,   75,  270, "DECIDED",
     "sculpted channel extended from specX 1200..1800 to 1200..2080 so it runs into the donor's real "
     "opening. Outer shape stays a styling choice; the airflow path does not."),
    ("INTAKE_INLET", "03_AERO",    1990,  870,  520,  180,  110,  180, "derived",
     "the DONOR opening: specX 1900..2080 from the side blueprint. This is the mouth that has to "
     "feed the engine; the sculpted channel must run into it"),
    ("INTAKE_DUCT",  "05_MECHANICAL", 2150, 650,  520,  320,  400,  180, "PROVISIONAL",
     "inlet -> engine bay. Path guessed; the real duct route comes from the scan of the engine bay"),
    ("INTAKE_OUTLET","05_MECHANICAL", 2300, 300,  600,  150,  300,  200, "PROVISIONAL",
     "connection to the intake plenum. Position guessed"),
    ("INTAKE_BLADE","03_AERO",     1500,  887,  485,  400,   30,  180, "spec",
     "vertical blade inside the intake, 180 high, 25-35 thick"),
    # --- rear
    ("BUTTRESS",    "03_AERO",     2180,  600,  940,  840,  220,  300, "DECIDED",
     "replaces the spec's free-standing AERO_FIN. Neither reference render has separate fins — both "
     "show raised shoulders growing out of the haunch behind the hoops, with the louvred deck sunk "
     "between them. specX 1760..2600, top 1090 (145 below the hoop tops so the hoops stay readable "
     "as their own structure). Y +-600 puts the inner face close to the roll-bar mounts at +-566, "
     "which is where a bonded subframe would pick up."),
    ("ENGINE_COVER","02_BODY",     2400,    0,  790,  800, 1050,  100, "spec", "cover envelope"),
    ("REAR_FASCIA", "02_BODY",     3310,    0,  520,  220, 1500,  500, "derived",
     "between S13 and S14; envelope only"),
    ("DIFFUSER",    "03_AERO",     3145,    0,  240,  550, 1500,  220, "spec",
     "X 2870..3420, width 1500, height 180-250, centre tunnel 500"),
    ("EXHAUST",     "05_MECHANICAL",3220,   65,  430,  200,   95,   95, "spec",
     "twin centre outlet, 90-100 dia, Y +-65"),
]

# repeating features: (name, collection, count, spec_x_start, spec_x_end, y, z, size_x, size_y, size_z, status)
LOUVERS = ("LOUVER", "02_BODY", 8, 2100, 2700, 0, 800, 40, 450, 12, "spec")
DIFFUSER_FINS = ("DIFFUSER_FIN", "03_AERO", 7, 2870, 3420, None, 230, 550, 16, 200, "spec")

# Rear deck centreline: (spec_x, z). This is the SUNKEN louvred panel between the buttresses, not
# the highest line of the car — ref-06/07 show the louvres recessed between two raised shoulders.
# It starts at the roll-hoop plane; ahead of that is the cabin, not deck.
# Heights are tied to the donor: the hoop tops (1235) set the ceiling, the deck sits under them.
# Centreline of the front body (Y = 0): (spec_x, z). THE line you judge in side view, and the one
# thing the written spec never gave — its sections describe how WIDE the body is at a height, never
# how TALL it is in the middle. Authored here from the ref-08 silhouette, anchored at both ends by
# facts: the nose tip sits just above the splitter, and the last point IS the donor's windshield
# base, which is not a choice. Between them the line is a translation of the approved render.
# The cabin aperture (specX 420..1760) has no body centreline; DECK_SPINE picks up behind the hoops.
HOOD_SPINE = [(-950, 400), (-850, 470), (-700, 565), (-500, 660),
              (-250, 725), (0, 770), (200, 820), (420, 970)]
HOOD_SPINE_NOTE = ("last point = donor cowl (windshield base), locked. Nose tip height is the design "
                   "call; everything between is the ref-08 side silhouette.")

# BLOCKED BY THE ROOF ENVELOPE. These heights come from the render, and they sit inside the volume
# the 986 soft top folds into. The locked rule is: model the ORIGINAL roof envelope first, then shape
# the deck around it. We cannot — the fold path is unknown until the car is scanned in all four roof
# positions. Treat every Z here as the maximum the design wants, not as a value that has been cleared.
# Lowered 2026-09-14 after comparing against the real 986 side profile. At 960 the deck read as a
# separate tower behind the cabin. On the donor the deck is a low continuation of the body, and the
# roll hoops are slim things standing clear of it — that is the architecture we build on.
# NOTE: this moves away from "the closed roof meets the deck in one line" until the scan gives us
# the real closed-roof line. The two cannot both be satisfied on guessed numbers.
# Extended to 3420. It used to stop at 3200, after which the fallback crown took over and LIFTED
# the last station by 106 mm. The spine now governs all the way to the tail and only falls.
DECK_SPINE = [(1760, 880), (2100, 868), (2415, 845), (2800, 760), (3200, 640), (3420, 545)]
DECK_STATUS = "BLOCKED: roof fold envelope unknown — scan the roof closed / half / open / clamshell up"

# Airflow systems: name -> (inlet element, path, outlet element). Every opening on the car must
# appear here. If something has no row, it is decorative and gets deleted — project rule.
AIRFLOW = {
    "front_cooling":  ("RAD_INTAKE", "RAD_DUCT", "HOOD_VENT + FENDER_CHANNEL"),
    "front_brakes":   ("BRAKE_DUCT_F inlet, ahead of the wheel", "enclosed duct", "wheel / disc"),
    "engine_intake":  ("SIDE_INTAKE + INTAKE_INLET", "INTAKE_DUCT", "INTAKE_OUTLET -> plenum"),
    "engine_cooling": ("side / rear intake", "engine bay", "ENGINE_COVER louvres"),
    "rear_brakes":    ("BRAKE_DUCT_R, off the side-intake path", "short duct", "wheel / disc"),
    "diffuser":       ("underbody", "DIFFUSER_TUNNEL expansion", "rear, between the fins"),
}

# Panel seams. Every one needs an engineering reason; decorative lines are forbidden.
# name: (reason, [(spec_x, y, z), ...] polyline)
PANEL_SEAMS = {
    "HOOD_to_FRONT_BODY":   ("frunk access and service; the hood is a separate physical panel",
                             [(420, 0, 970), (300, 420, 880), (120, 620, 800), (-100, 700, 745)]),
    "FRONT_FENDER_to_DOOR": ("donor front shut line — locked",
                             [(440, 700, 300), (440, 845, 560), (440, 800, 800)]),
    "DOOR_SHUT_FRONT":      ("donor shut line — locked, the skin must land on it",
                             [(440, 855, 250), (440, 870, 550), (440, 800, 800)]),
    "DOOR_SHUT_REAR":       ("donor shut line — locked",
                             [(1635, 855, 250), (1635, 890, 550), (1635, 810, 800)]),
    "ROCKER_to_UPPER_BODY": ("rocker is a separate removable panel; kerb damage is replaceable",
                             [(440, 840, 330), (1038, 850, 330), (1635, 850, 330)]),
    "REAR_HAUNCH_to_DOOR":  ("panel removal; the haunch is an overlay on welded quarter",
                             [(1635, 890, 250), (1635, 915, 560), (1635, 830, 820)]),
    "ENGINE_COVER_to_DECK": ("engine access — must open",
                             [(2000, 0, 950), (2000, 400, 930), (2000, 560, 900)]),
    "REAR_FASCIA_to_DECK":  ("exhaust and diffuser access; separate from the cover",
                             [(3000, 0, 800), (3000, 450, 790), (3000, 700, 740)]),
    "DIFFUSER_to_FASCIA":   ("diffuser is replaceable and is the first thing to ground out",
                             [(3050, 0, 330), (3050, 450, 330), (3050, 700, 330)]),
}

# Surface behaviour per zone (docs/16). Not geometry — the rules the surfacing must obey.
# curvature / highlight / tension / edges / transition / the mistake to avoid.
SURFACE = {
    "NOSE":              ("longitudinally almost flat, slightly convex across", "one long near-horizontal band narrowing to the centre", "front edge and the outer tips of the lights", "outer edges sharp; centre-to-intake defined but not knife-edged throughout", "tangent to hood, clear direction change at the lights", "no rounded supercar nose, do not lift the centre"),
    "HOOD":              ("long, low, gently convex centre with two faint raised tension zones", "two long diagonals running back to the windshield base", "strongest along the outer hood lines, centre stays calm", "long controlled edges, small radius", "continuous into the windshield base", "no power bulge, no muscle-car hood"),
    "FRONT_FENDER_TOP":  ("strongly convex over the wheel but only locally, then releasing fast toward the centre", "one strong diagonal band over the arch", "maximum directly above the front tyre", "clean arch edge; from it the surface stretches up to the hood", "tangent to hood, must not read as a sphere", "not a separate round balloon"),
    "FRONT_FENDER_SIDE": ("convex at the arch turning concave into the channel", "the highlight BREAKS in the channel — light must disappear", "along the upper outer edge of the fender", "sharp transition edge into the open channel", "a clear break, not a soft fillet", "do not fill the void with material — the void is the hypercar read"),
    "HEADLIGHT_SURROUND":("slightly concave around the lamp", "the lamps interrupt the hood/fender reflection", "around the outer edge of the module", "sharp inboard, softer toward the hood", "integrated into the surface, not sitting on it", "not a Lamborghini-style separate pocket"),
    "FRONT_LOWER_INTAKE":("the surface breaks inward sharply — a real hole", "light nearly vanishes inside", "maximum at the upper lip", "sharp upper edge, softer lower transition", "clear break", "not a huge smile; technical, low and wide"),
    "DOOR_UPPER":        ("gently convex in the upper half, then drawing in", "one long clean longitudinal band", "strongest along the shoulder line", "as few edges as possible", "quiet", "no decorative creases"),
    "DOOR_CHANNEL":      ("surface collapses inward into a deep channel", "highlight terminates in the channel", "along the upper lip of the channel", "sharp entry edge", "surface -> inward collapse -> channel -> blade -> intake", "must look like air cut the car, not like a styling dent"),
    "SIDE_INTAKE_MOUTH": ("convex outer frame, deeply concave interior", "highlight breaks completely at the mouth", "front and top lips", "sharp; the vertical blade separates body from cavity", "clear break", "not a huge Lamborghini scoop — narrower and tenser"),
    "ROCKER":            ("nearly flat across, lifting slightly toward the rear haunch", "one long horizontal band", "along the top edge", "thin structural blade", "quiet", "not a thick side skirt"),
    "REAR_HAUNCH_TOP":   ("strongly convex over the rear wheel, asymmetric, not a clean arc", "one broad band along the shoulder", "maximum just behind the cabin", "rises, holds tension, draws back to the tail", "into the deck", "not a round classic widebody muscle"),
    "REAR_HAUNCH_SIDE":  ("convex above, near vertical, concave below", "band breaks low", "upper outer edge", "clear lower undercut", "into the diffuser", "do not fill the volume down to the floor"),
    "BUTTRESS":          ("starts low at the front, rises, then releases into the deck", "one narrow longitudinal highlight", "along both defined edges", "two clear edges, inner and outer", "structure, not a hump", "not soft and rounded"),
    "REAR_DECK":         ("structurally calm around the roof mechanism", "quiet", "low — this area must not fight the mechanism", "thin skin over a technical mechanism", "into the cover and the fascia", "no aggressive forms where the roof has to stow"),
    "ENGINE_COVER":      ("gently convex around the louvres, falling to the fascia", "interrupted by the louvres, which share one perspective", "moderate", "louvres are real openings on one common vanishing direction", "into the fascia", "not a giant flat grille"),
    "REAR_FASCIA":       ("wide but light; the light blade cuts the tail in two", "the blade is the dominant horizontal", "low — mass is what we are avoiding here", "dark technical zone beneath the blade", "into the diffuser", "no four exhausts, no decorative openings"),
    "DIFFUSER":          ("relatively flat in the centre, expanding out to the fins", "broken by the fins", "at the fin roots", "clear sharp vertical fins", "a real tunnel, not a black plastic bumper", "fewer and larger fins, not ten small ones"),
}

# Continuity between zones. G0 = deliberate structural break, G1 = character transition,
# G2 = main body surfaces. Chasing G2 everywhere is what makes CAD models look like soap.
CONTINUITY = {
    ("NOSE", "HOOD"): "G1", ("HOOD", "FRONT_FENDER_TOP"): "G2",
    ("FRONT_FENDER_TOP", "FRONT_FENDER_SIDE"): "G1",
    ("FRONT_FENDER_SIDE", "DOOR_UPPER"): "G0",
    ("HOOD", "HEADLIGHT_SURROUND"): "G1", ("NOSE", "FRONT_LOWER_INTAKE"): "G0",
    ("DOOR_UPPER", "DOOR_CHANNEL"): "G0", ("DOOR_CHANNEL", "SIDE_INTAKE_MOUTH"): "G1",
    ("DOOR_UPPER", "ROCKER"): "G1", ("DOOR_UPPER", "REAR_HAUNCH_TOP"): "G2",
    ("REAR_HAUNCH_TOP", "REAR_HAUNCH_SIDE"): "G1",
    ("REAR_HAUNCH_TOP", "BUTTRESS"): "G0", ("BUTTRESS", "REAR_DECK"): "G1",
    ("REAR_DECK", "ENGINE_COVER"): "G1", ("ENGINE_COVER", "REAR_FASCIA"): "G1",
    ("REAR_FASCIA", "DIFFUSER"): "G0", ("REAR_HAUNCH_SIDE", "DIFFUSER"): "G1",
}

# The shoulder line, as ONE idea rather than separate lines: low -> tight -> rising -> muscular -> tapering
SHOULDER_LINE = "front fender low -> slight dip at the door -> rises behind the cabin -> peak over the rear wheel -> draws back to the tail; no visible kink"

# The three negative-space regions. These are the reason the car reads as exotic.
NEGATIVE_SPACE = ["front fender channel, behind the front wheel — the most aggressive void at the front",
                  "door / side-intake channel — the main side character element",
                  "rear lower body under the haunch into the diffuser — thin skin, visible dark structure behind"]

SUBCOLLS = ["00_DONOR_HARDPOINTS", "01_MASTER_SKELETON", "02_BODY", "03_AERO",
            "04_LIGHTING", "05_MECHANICAL", "06_ROOF", "07_INTERIOR",
            "08_PANEL_SEAMS", "99_DEBUG"]

# Parametric properties carried on the STATEV_001_ROOT empty (prompt §28). Editable; the build
# reads SECTIONS/BOXES, so changing a value here documents intent — rerun the script to apply.
ROOT_PROPS = {
    "wheelbase": 2415, "overall_length": 4370, "rear_width": 1850, "front_width": 1800,
    "target_height": 1285, "ground_clearance": 120,
    "front_track": 1465, "rear_track": 1528,          # donor, published — NOT a design variable
    "front_wheel_diameter": 647, "rear_wheel_diameter": 675,
    "front_tyre_width": 235, "rear_tyre_width": 275,
    "headlight_length": 650, "headlight_height": 65,
    "side_intake_length": 600, "side_intake_height": 220,
    "rear_fin_height": 350, "diffuser_width": 1500, "diffuser_length": 550,
    "exhaust_diameter": 95,
    # rim and offset are design variables; these are typical 986 19" values, PROVISIONAL until the
    # wheels are actually bought and the arch clearance is measured on the car.
    "front_rim": "8.5Jx19", "front_wheel_et": 50,
    "rear_rim": "10Jx19", "rear_wheel_et": 45,
    "wheel_et_status": "PROVISIONAL — ET sets how far the tyre sits inside the arch; verify on the car",
}

# Viewport materials for visualisation only (prompt §26): name -> (rgba, metallic, roughness)
MATERIALS = {
    "STATEV_BODY":     ((0.045, 0.115, 0.075, 1.0), 0.85, 0.25),   # dark metallic green
    "STATEV_WHEELS":   ((0.36, 0.24, 0.10, 1.0), 0.95, 0.35),      # bronze
    "STATEV_INTERIOR": ((0.42, 0.29, 0.17, 1.0), 0.00, 0.65),      # tan leather
    "STATEV_GLASS":    ((0.03, 0.03, 0.04, 0.25), 0.00, 0.05),
    "STATEV_CARBON":   ((0.02, 0.02, 0.02, 1.0), 0.40, 0.35),
    "STATEV_LIGHT":    ((1.0, 0.97, 0.90, 1.0), 0.00, 0.10),       # emissive
}


def donor_dims():
    """DIMS from cage_986.py — the donor hardpoints, published or blueprint-derived."""
    import os
    here = SCRIPTS_DIR
    ns = {}
    with open(os.path.join(here, "cage_986.py"), "r", encoding="utf-8") as fh:
        head = fh.read().split("# ---------------------------------------------------------------- helpers")[0]
    exec(head.replace("import bpy", ""), ns)
    return {k: v[0] for k, v in ns["DIMS"].items()}


def mm(v):
    return v / 1000.0


def sx(spec_x):
    """spec X (+ = rearward) -> repo X (+ = forward)."""
    return -spec_x


def reset_tree():
    root = bpy.data.collections.get(COLL_ROOT)
    if root:
        for c in list(root.children):
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
        for ob in list(root.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        root = bpy.data.collections.new(COLL_ROOT)
        bpy.context.scene.collection.children.link(root)
    subs = {}
    for name in SUBCOLLS:
        c = bpy.data.collections.new(name)
        root.children.link(c)
        subs[name] = c
    return root, subs


def poly_curve(name, coll, points_m, color, cyclic=False, bevel=0.0):
    name = name if name.startswith(PFX) else PFX + name
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points_m) - 1)
    for i, (x, y, z) in enumerate(points_m):
        sp.points[i].co = (x, y, z, 1.0)
    sp.use_cyclic_u = cyclic
    if bevel:
        cu.bevel_depth = bevel
    ob = bpy.data.objects.new(name, cu)
    ob.color = color
    ob.show_in_front = True
    coll.objects.link(ob)
    return ob


def box(name, coll, centre_mm, size_mm, color, note="", status="spec", spec_x=None):
    name = name if name.startswith(PFX) else PFX + name
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=[mm(v) for v in centre_mm])
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = tuple(mm(s) for s in size_mm)
    ob.display_type = "WIRE"
    ob.color = color
    ob.show_in_front = True
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    ob["statev_v01"] = True
    ob["status"] = status
    ob["size_mm"] = list(size_mm)
    ob["centre_mm"] = list(centre_mm)
    if spec_x is not None:
        ob["spec_x_mm"] = spec_x
    if note:
        ob["note"] = note
    return ob


# DRL / position blade: (spec_x, target_half_width). Z is solved so the point lands ON the body's
# upper shoulder at that width — the blade follows the widest line of the nose and kicks into the
# fender, instead of being a straight bar hanging in space.
DRL_PATH = [(-888, 120), (-878, 260), (-862, 400), (-838, 520), (-805, 610),
            (-762, 680), (-710, 730), (-650, 775), (-585, 810)]
DRL_INSET = 15          # mm inboard of the surface so the blade sits in a recess
DRL_SECTION = (14, 12)  # height x depth of the lit element


def section_profile(spec_x):
    """Widened profile interpolated between the two bracketing master sections."""
    items = sorted(((v[0], v[2]) for v in SECTIONS.values()), key=lambda t: t[0])
    xs = [i[0] for i in items]
    if spec_x <= xs[0]:
        base = items[0][1]
    elif spec_x >= xs[-1]:
        base = items[-1][1]
    else:
        for i in range(len(xs) - 1):
            if xs[i] <= spec_x <= xs[i + 1]:
                t = (spec_x - xs[i]) / (xs[i + 1] - xs[i])
                a, b = items[i][1], items[i + 1][1]
                zs = sorted({z for z, _ in a} | {z for z, _ in b})
                base = []
                for z in zs:
                    ya, yb = half_width_at(a, z), half_width_at(b, z)
                    if ya is None or yb is None:
                        continue
                    base.append((z, ya + t * (yb - ya)))
                break
    return [(z, y + widening(spec_x, z)) for z, y in base]


def z_at_half_width(spec_x, target_y):
    """Height on the UPPER branch of the section where the body is target_y wide. None if never."""
    prof = section_profile(spec_x)
    y_max = max(y for _, y in prof)
    target_y = min(target_y, y_max - 2)
    z_at_max = max((z for z, y in prof if abs(y - y_max) < 1e-6), default=prof[0][0])
    upper = [(z, y) for z, y in prof if z >= z_at_max]
    for i in range(len(upper) - 1):
        (z0, y0), (z1, y1) = upper[i], upper[i + 1]
        if (y0 - target_y) * (y1 - target_y) <= 0 and y0 != y1:
            return z0 + (target_y - y0) / (y1 - y0) * (z1 - z0)
    return z_at_max


def widening(spec_x, z):
    """Smooth local growth of the body around an axle, so the arch aperture fits inside the
    surface without anyone editing a single section by hand."""
    import math as _w
    add = 0.0
    for ax, delta, taper, z_lo, z_hi in AXLE_WIDENING:
        dx = abs(spec_x - ax)
        if dx >= taper or not (z_lo <= z <= z_hi):
            continue
        fx = 0.5 * (1.0 + _w.cos(_w.pi * dx / taper))                  # 1 at the axle -> 0 at taper
        zc, zh = (z_lo + z_hi) / 2.0, (z_hi - z_lo) / 2.0
        fz = 0.5 * (1.0 + _w.cos(_w.pi * min(1.0, abs(z - zc) / zh)))  # peak mid-band -> 0 at edges
        add = max(add, delta * fx * fz)
    return add


def half_width_at(profile, z):
    """Interpolate a section's half-width at height z. Returns None above the section's top."""
    zs = [p[0] for p in profile]
    ys = [p[1] for p in profile]
    if z < zs[0] or z > zs[-1]:
        return None
    for i in range(len(zs) - 1):
        if zs[i] <= z <= zs[i + 1]:
            t = 0.0 if zs[i + 1] == zs[i] else (z - zs[i]) / (zs[i + 1] - zs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


def build():
    # FREEZE RULE — refuse to rebuild if an approved zone's defining data has changed.
    try:
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("_freeze", os.path.join(SCRIPTS_DIR, "freeze.py"))
        _fz = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_fz)
        _fz.check()
    except FileNotFoundError:
        pass
    except RuntimeError:
        raise

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 1.0

    root, subs = reset_tree()
    D = donor_dims()
    CYAN = (0.15, 0.75, 0.85, 1.0)
    YELL = (0.95, 0.75, 0.15, 1.0)
    MAG = (0.85, 0.25, 0.65, 1.0)
    GREEN = (0.35, 0.80, 0.40, 1.0)
    WHITE = (0.90, 0.90, 0.90, 1.0)

    # ---- cross-sections: left side bottom->top, across the top, right side top->bottom
    for name, (spec_x, role, prof) in SECTIONS.items():
        x = mm(sx(spec_x))
        prof_w = [(z, y + widening(spec_x, z)) for z, y in prof]         # local growth around the axles
        pts = [(x, mm(y), mm(z)) for z, y in prof_w]                     # left (+Y)
        pts += [(x, mm(-y), mm(z)) for z, y in reversed(prof_w)]         # right (-Y)
        ob = poly_curve(name, subs["01_MASTER_SKELETON"], pts, CYAN)
        ob["statev_v01"] = True
        ob["status"] = "spec"
        ob["spec_x_mm"] = spec_x
        ob["repo_x_mm"] = sx(spec_x)
        ob["role"] = role
        ob["profile_z_halfwidth_mm"] = [list(p) for p in prof]
        ob["profile_after_widening_mm"] = [[z, round(y, 1)] for z, y in prof_w]
        ob["axle_widening_mm"] = round(max(widening(spec_x, z) for z, _ in prof), 1)
        ob["note"] = "open at the floor (underside not specified) and flat across the top of the data"

    # ---- longitudinal rails at constant Z through every section that reaches that height
    order = sorted(SECTIONS.items(), key=lambda kv: kv[1][0])
    for z in RAIL_LEVELS:
        for side, sgn in (("L", 1), ("R", -1)):
            pts = []
            for name, (spec_x, role, prof) in order:
                hw = half_width_at(prof, z)
                if hw is not None:
                    hw += widening(spec_x, z)
                    pts.append((mm(sx(spec_x)), mm(sgn * hw), mm(z)))
            if len(pts) > 1:
                ob = poly_curve(f"RAIL_Z{z:04d}_{side}", subs["01_MASTER_SKELETON"], pts, YELL)
                ob["statev_v01"] = True
                ob["status"] = "derived"
                ob["z_mm"] = z
                ob["sections"] = len(pts)

    # ---- panel seams (08) — every one carries its engineering reason as a property
    for nm, (reason, pts) in PANEL_SEAMS.items():
        for suffix, sgn in ((("_L", 1), ("_R", -1)) if any(y for _, y, _ in pts) else (("", 1),)):
            ob = poly_curve(f"SEAM_{nm}{suffix}", subs["08_PANEL_SEAMS"],
                            [(mm(sx(x)), mm(sgn * y), mm(z)) for x, y, z in pts],
                            (0.95, 0.45, 0.10, 1.0))
            ob["status"] = "DECIDED"
            ob["reason"] = reason
            ob["locked_by_donor"] = "donor shut line" in reason or "locked" in reason
            ob["note"] = ("panel boundary. A seam exists only for a reason - donor line, access, "
                          "removal, manufacture or mounting. Decorative seams are forbidden.")

    # ---- front centreline (hood line)
    ob = poly_curve("HOOD_SPINE", subs["02_BODY"],
                    [(mm(sx(x)), 0.0, mm(z)) for x, z in HOOD_SPINE], (0.95, 0.75, 0.15, 1.0))
    ob["statev_v01"] = True
    ob["status"] = "DECIDED"
    ob["points_specx_z_mm"] = [list(pt) for pt in HOOD_SPINE]
    ob["note"] = HOOD_SPINE_NOTE
    ob["cowl_z_donor"] = D["cowl_z"]
    if abs(HOOD_SPINE[-1][1] - D["cowl_z"]) > 1:
        ob["MISMATCH"] = f"last point {HOOD_SPINE[-1][1]} != donor cowl {D['cowl_z']}"

    # ---- rear deck spine (centreline)
    ob = poly_curve("DECK_SPINE", subs["02_BODY"],
                    [(mm(sx(x)), 0.0, mm(z)) for x, z in DECK_SPINE], GREEN)
    ob["statev_v01"] = True
    ob["status"] = "spec"
    ob["points_specx_z_mm"] = [list(p) for p in DECK_SPINE]

    # ---- discrete element envelopes
    colors = {"02_BODY": WHITE, "03_AERO": MAG, "04_LIGHTING": YELL, "05_MECHANICAL": GREEN}
    for (nm, coll, spec_x, y, z, sxx, sy, sz, status, note) in BOXES:
        c = subs[coll]
        col = colors[coll]
        if y in (0, None):
            box(nm, c, (sx(spec_x), 0, z), (sxx, sy, sz), col, note, status, spec_x)
        else:
            for suffix, sgn in (("_L", 1), ("_R", -1)):
                box(nm + suffix, c, (sx(spec_x), sgn * abs(y), z), (sxx, sy, sz), col, note, status, spec_x)

    # ---- louvers in the rear deck
    nm, coll, n, x0, x1, y, z, sxx, sy, sz, status = LOUVERS
    step = (x1 - x0) / (n - 1)
    for i in range(n):
        spec_x = x0 + i * step
        box(f"{nm}_{i+1:02d}", subs[coll], (sx(spec_x), y, z), (sxx, sy, sz), WHITE,
            "real opening, follows the deck curve once lofted", status, round(spec_x, 1))

    # ---- diffuser fins
    nm, coll, n, x0, x1, _, z, sxx, sy, sz, status = DIFFUSER_FINS
    spec_x = (x0 + x1) / 2.0
    spacing = 150            # 7 fins x 150 = 900 inside the 1500 wide diffuser
    for i in range(n):
        y = (i - (n - 1) / 2.0) * spacing
        box(f"{nm}_{i+1:02d}", subs[coll], (sx(spec_x), y, z), (sxx, sy, sz), MAG,
            "5-7 fins, 120-180 spacing; centre tunnel 500 wide", status, spec_x)

    # ---- STATEV 19" wheels at the DONOR track (spec's Y hub numbers are not usable — see check script)
    import math
    for nm, spec_x, od, wdt, half_track in (
        ("WHEEL_F", 0, PACKAGE["tyre_front_od"], 235, 732.5),
        ("WHEEL_R", 2415, PACKAGE["tyre_rear_od"], 275, 764.0),
    ):
        for suffix, sgn in (("_L", 1), ("_R", -1)):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=mm(od / 2), depth=mm(wdt), vertices=48,
                location=(mm(sx(spec_x)), mm(sgn * half_track), mm(od / 2)))
            w = bpy.context.active_object
            w.name = PFX + nm + suffix
            w.rotation_euler = (math.radians(90), 0, 0)
            w.display_type = "WIRE"
            w.color = WHITE
            w.show_in_front = True
            for c in w.users_collection:
                c.objects.unlink(w)
            subs["05_MECHANICAL"].objects.link(w)
            w["statev_v01"] = True
            w["status"] = "derived"
            w["note"] = ("STATEV 19in tyre at the DONOR track (1465/1528). The v0.1 spec's hub Y of "
                         "875/900 would need a +285/+272 mm wider track — not possible on the 986.")


    # ---- wheel arch apertures. The visible arch line is a curve ON the body surface, not an arc at
    # a constant Y: as the arch climbs, the fender narrows, so the line has to follow it. The inboard
    # edge is inside the wheelhouse and is drawn as a plain arc — it is not a visible line.
    import math as _a
    for side_key, (spec_x, radius, open_w, tod, twid) in ARCHES.items():
        half_track = (D["track_front"] if side_key == "FRONT" else D["track_rear"]) / 2.0
        y_cap = half_track + open_w / 2                      # aperture half-width from the spec
        y_in = half_track - open_w / 2
        for suffix, sgn in (("_L", 1), ("_R", -1)):
            out_pts, in_pts, ys = [], [], []
            for i in range(37):
                ang = _a.pi * i / 36                          # front -> over the top -> rear
                ax = spec_x - radius * _a.cos(ang)            # spec X walks with the arc
                z = tod / 2 + radius * _a.sin(ang)
                prof = section_profile(ax)
                hw = half_width_at(prof, z)
                if hw is None:                                # above the section data: hold its top
                    hw = prof[-1][1]
                y = min(hw - 12, y_cap)                       # 12 mm inboard of the surface
                ys.append(y)
                out_pts.append((mm(sx(ax)), mm(sgn * y), mm(z)))
                in_pts.append((mm(sx(ax)), mm(sgn * y_in), mm(z)))
            for edge, pts in (("out", out_pts), ("in", in_pts)):
                ob = poly_curve(f"ARCH_{side_key}{suffix}_{edge}", subs["02_BODY"], pts,
                                (0.20, 0.70, 0.90, 1.0))
                ob["status"] = "DECIDED" if edge == "out" else "derived"
                ob["spec_x_mm"] = spec_x
                ob["arch_radius_mm"] = radius
                ob["arch_opening_width_mm"] = open_w
                ob["radial_gap_to_tyre_mm"] = round(radius - tod / 2, 1)
                ob["axial_gap_each_side_mm"] = round((open_w - twid) / 2.0, 1)
                if edge == "out":
                    ob["outer_edge_y_range_mm"] = [round(min(ys), 1), round(max(ys), 1)]
                    ob["note"] = ("visible arch line, solved onto the body surface at every angle. "
                                  "Where the fender narrows, the line comes inboard with it — it is "
                                  "NOT a constant-Y arc. Final validation needs the real lofted "
                                  "surface at full bump and full steer.")
                else:
                    ob["note"] = "inboard edge of the aperture, inside the wheelhouse — not a visible line"

    # ---- DRL / position blade, lying on the body's shoulder line
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        pts, zs = [], []
        for spec_x, ty in DRL_PATH:
            z = z_at_half_width(spec_x, ty)
            y = min(ty, max(v for _, v in section_profile(spec_x)) - 2) - DRL_INSET
            zs.append(z)
            pts.append((mm(sx(spec_x)), mm(sgn * y), mm(z)))
        ob = poly_curve(f"DRL_BLADE{suffix}", subs["04_LIGHTING"], pts, (1.0, 0.97, 0.90, 1.0))
        ob.data.bevel_depth = mm(DRL_SECTION[0] / 2.0)
        ob.data.bevel_resolution = 2
        ob["status"] = "DECIDED"
        ob["section_h_d_mm"] = list(DRL_SECTION)
        ob["length_mm"] = round(sum(
            ((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2 +
             (pts[i + 1][2] - pts[i][2]) ** 2) ** 0.5 for i in range(len(pts) - 1)) * 1000, 1)
        ob["z_range_mm"] = [round(min(zs), 1), round(max(zs), 1)]
        ob["note"] = ("position/DRL blade. Follows the widest line of the nose and kicks up into the "
                      "fender. Z is solved from the sections, not assumed, so it lies on the surface. "
                      "Position lamps need >=350 mm; the headlamp height rule applies to the projector.")

    # ---- diffuser central tunnel
    tx, ty, tz, tdx, tdy, tdz = DIFFUSER_TUNNEL
    box("DIFFUSER_TUNNEL", subs["03_AERO"], (sx(tx), ty, tz), (tdx, tdy, tdz),
        (0.85, 0.25, 0.65, 1.0),
        "central tunnel, 500 wide inside the 1500 diffuser; the fins sit either side of it",
        "spec", tx)

    # ---- door character line (the crease the spec describes by three heights)
    dc = DOOR_CHAR_LINE_Z
    dfx, drx = -D["door_front_x"], -D["door_rear_x"]          # spec X of the shut lines
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        pts = [(mm(sx(dfx)), mm(sgn * 850), mm(dc["front"])),
               (mm(sx((dfx + drx) / 2)), mm(sgn * 862), mm(dc["middle"])),
               (mm(sx(drx)), mm(sgn * 850), mm(dc["rear"]))]
        ob = poly_curve(f"DOOR_CHAR_LINE{suffix}", subs["02_BODY"], pts, (0.20, 0.70, 0.90, 1.0))
        ob["status"] = "spec"
        ob["heights_mm"] = [dc["front"], dc["middle"], dc["rear"]]
        ob["note"] = ("design crease on the door: Z 420 front, 500 middle, 520 rear. X taken from "
                      "the donor shut lines, Y from the section half-widths")

    # ---- 00_DONOR_HARDPOINTS: pointer only. The cage stays a separate top-level collection so
    #      donor reference geometry is never mixed into STATEV geometry (prompt §27, §33).
    ptr = bpy.data.objects.new(PFX + "DONOR_HARDPOINTS__see_CAGE_986", None)
    ptr.empty_display_type = "SPHERE"
    ptr.empty_display_size = 0.25
    subs["00_DONOR_HARDPOINTS"].objects.link(ptr)
    ptr["note"] = ("Donor hardpoints live in the CAGE_986 collection, rebuilt by cage_986.py. "
                   "Not duplicated here on purpose: one source of truth, never edited by hand.")
    ptr["locked"] = ("windshield frame and rake, A-pillars, header, door glass, door shut lines, "
                     "wheel centres, wheelbase, roll hoops, roof mechanism, side-intake hardpoint")
    for k in ("wheelbase", "track_front", "track_rear", "cowl_x", "cowl_z", "ws_top_x", "ws_top_z",
              "hoop_x", "hoop_top_z", "hoop_y", "door_front_x", "door_rear_x", "side_intake_x"):
        ptr[f"donor_{k}"] = D[k]

    # ---- 06_ROOF: clearance envelopes around the OEM soft top. PROVISIONAL — the fold path and
    #      the clamshell are unknown until the car is scanned; nothing here may be treated as fact.
    roof_boxes = [
        ("ROOF_CLOSED_ENVELOPE",
         (D["ws_top_x"] + D["hoop_x"]) / 2.0, 0, (D["ws_top_z"] + 900) / 2.0,
         abs(D["hoop_x"] - D["ws_top_x"]) + 300, 1400, D["ws_top_z"] - 900,
         "closed soft top between the windshield header and the hoops; the raised deck must meet "
         "this line without a step"),
        ("ROOF_FOLD_ENVELOPE",
         D["hoop_x"] - 260, 0, 850, 520, 1300, 300,
         "stowage volume behind the seats. Size and path are GUESSED - the real fold envelope is "
         "the single most important thing to capture on the scan"),
    ]
    for nm, x, y, z, dx, dy, dz, note in roof_boxes:
        b = box(nm, subs["06_ROOF"], (x, y, z), (dx, dy, dz), (0.95, 0.25, 0.25, 1.0),
                note, "PROVISIONAL")
        b["do_not_trust"] = True

    # ---- 07_INTERIOR: seat centrelines from the measured plan view; cabin fit for 190 cm needs the scan
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        e = bpy.data.objects.new(PFX + f"SEAT_CENTRELINE{suffix}", None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.3
        e.location = (mm(sx(1500)), mm(sgn * 357), mm(500))
        subs["07_INTERIOR"].objects.link(e)
        e["status"] = "derived"
        e["note"] = ("seat centreline +-357 measured on the 4-view plan; X is PLACED. "
                     "Owner is 190 cm - seat travel and headroom are a hard constraint, "
                     "checkable only on the real car")

    # ---- 99_DEBUG: dimension guides and provisional clearance envelopes (prompt §30)
    dbg = subs["99_DEBUG"]
    RED = (0.95, 0.25, 0.25, 1.0)

    def dim_line(name, p0, p1, label):
        ob = poly_curve(name, dbg, [tuple(mm(v) for v in p0), tuple(mm(v) for v in p1)], RED)
        ob["status"] = "derived"
        ob["label"] = label
        cu = bpy.data.curves.new(name + "_TXT", "FONT")
        cu.body = label
        cu.size = 0.06
        t = bpy.data.objects.new(name + "_TXT", cu)
        t.location = tuple(mm((a + b) / 2.0) for a, b in zip(p0, p1))
        t.rotation_euler = (1.5708, 0, 0)
        t.color = RED
        dbg.objects.link(t)
        return ob

    nose, tail = sx(-950), sx(3420)
    dim_line("DIM_length", (nose, 0, -250), (tail, 0, -250), f"length {PACKAGE['length']}")
    dim_line("DIM_wheelbase", (0, 0, -450), (sx(2415), 0, -450), f"wheelbase {PACKAGE['wheelbase']}")
    dim_line("DIM_width_rear", (sx(2415), -925, -250), (sx(2415), 925, -250),
             f"max width {PACKAGE['width_max_rear']}")
    dim_line("DIM_track_front", (0, -D["track_front"] / 2, -150), (0, D["track_front"] / 2, -150),
             f"front track {D['track_front']} (donor)")
    dim_line("DIM_track_rear", (sx(2415), -D["track_rear"] / 2, -350), (sx(2415), D["track_rear"] / 2, -350),
             f"rear track {D['track_rear']} (donor)")
    dim_line("DIM_height", (sx(1760), 1100, 0), (sx(1760), 1100, PACKAGE["height"]),
             f"height {PACKAGE['height']}")
    dim_line("DIM_ground_clearance", (sx(800), 1100, 0), (sx(800), 1100, PACKAGE["ground_clearance"]),
             f"clearance {PACKAGE['ground_clearance']}")

    # steering sweep, worst case: tyre footprint rotated +-35 deg about a vertical axis through the
    # wheel centre. The real kingpin axis is inboard and raked, so this over-states the outboard reach.
    import math as _m
    th = _m.radians(35)
    od, wd = PACKAGE["tyre_front_od"], 235
    swept_x = od * _m.cos(th) + wd * _m.sin(th)
    swept_y = od * _m.sin(th) + wd * _m.cos(th)
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        b = box(f"STEER_SWEEP{suffix}", dbg, (0, sgn * D["track_front"] / 2, od / 2),
                (swept_x + 2 * D["oem_buffer"], swept_y + 2 * D["oem_buffer"], od + 2 * D["oem_buffer"]),
                RED,
                f"worst-case +-35 deg sweep about the wheel centre, +{D['oem_buffer']} mm buffer. "
                "PROVISIONAL: kingpin axis unknown until the scan, so the true outboard reach is less.",
                "PROVISIONAL")
        b["do_not_trust"] = True

    # ---- engine bay and roll-hoop clearance (prompt §30)
    eng = box("ENGINE_BAY_ENVELOPE", dbg, (D["hoop_x"] - 440, 0, 600), (760, 900, 600), RED,
              "mid engine between the hoops and the rear axle. Engine mounts P9 are at Y +-188.5 "
              "(published); the box size around them is GUESSED. Nothing may close this volume in.",
              "PROVISIONAL")
    eng["do_not_trust"] = True
    eng["donor_engine_mount_y_total"] = D["jack_front_y_total"] and 377.0
    for suffix, sgn in (("_L", 1), ("_R", -1)):
        h = box(f"ROLLHOOP_CLEARANCE{suffix}", dbg,
                (D["hoop_x"], sgn * D["hoop_y"], (600 + D["hoop_top_z"]) / 2.0),
                (120 + 2 * D["oem_buffer"], 120 + 2 * D["oem_buffer"],
                 D["hoop_top_z"] - 600 + D["oem_buffer"]), RED,
                "keep-out around the roll hoop tube. Tube diameter not measured yet — 120 mm "
                "assumed plus the standard buffer. The hoops are a locked safety structure.",
                "PROVISIONAL")
        h["do_not_trust"] = True

    # ---- warning objects: recomputed live, so a fixed number makes the marker disappear (prompt §30)
    WARN = (1.0, 0.15, 0.0, 1.0)

    def warn(name, centre, size, text):
        b = box(name, dbg, centre, size, WARN, text, "WARNING")
        b["WARNING"] = True
        cu = bpy.data.curves.new(PFX + name + "_TXT", "FONT")
        cu.body = "! " + text.split(".")[0]
        cu.size = 0.05
        t = bpy.data.objects.new(PFX + name + "_TXT", cu)
        t.location = (mm(centre[0]), mm(centre[1]), mm(centre[2] + size[2] / 2 + 60))
        t.rotation_euler = (1.5708, 0, 0)
        t.color = WARN
        dbg.objects.link(t)
        return b

    def find_box(nm):
        """A renamed or deleted element must not kill the build — the warning just does not fire."""
        return next((b for b in BOXES if b[0] == nm), None)

    n_warn = 0
    # W1 — hub Y
    spec_hub_f = 875
    if abs(spec_hub_f - D["track_front"] / 2) > 5:
        warn("WARN_hub_Y", (0, (spec_hub_f + D["track_front"] / 2) / 2, PACKAGE["tyre_front_od"] / 2),
             (200, spec_hub_f - D["track_front"] / 2, 200),
             f"spec hub Y {spec_hub_f} vs donor {D['track_front']/2:.0f}: needs "
             f"{2*(spec_hub_f - D['track_front']/2):.0f} mm more track, impossible")
        n_warn += 1
    # W2 — headlight beyond the body
    hl = find_box("PROJECTOR")
    hl_out = (abs(hl[3]) + hl[6] / 2) if hl else 0
    body_at = half_width_at(SECTIONS["S02"][2], hl[4]) + widening(hl[2], hl[4]) if hl else 0
    if hl and body_at and hl_out > body_at:
        for sgn in (1, -1):
            warn(f"WARN_projector_{'L' if sgn > 0 else 'R'}",
                 (sx(hl[2]), sgn * (body_at + hl_out) / 2, hl[4]),
                 (hl[5], hl_out - body_at, hl[7]),
                 f"projector cavity reaches Y {hl_out:.0f}, body is {body_at:.0f} — "
                 f"{hl_out - body_at:.0f} mm outside the surface")
            n_warn += 1
    # W3 — side intake does not reach the donor opening
    si = find_box("SIDE_INTAKE")
    si_end = (si[2] + si[5] / 2) if si else 1e9
    donor_open = 1900
    if si_end < donor_open:
        for sgn in (1, -1):
            warn(f"WARN_intake_gap_{'L' if sgn > 0 else 'R'}",
                 (sx((si_end + donor_open) / 2), sgn * 870, 520),
                 (donor_open - si_end, 120, 180),
                 f"{donor_open - si_end:.0f} mm gap between the sculpted intake and the real opening — "
                 "as drawn it feeds nothing")
            n_warn += 1
    # W4 — door skin shorter than the aperture
    ds = find_box("DOOR_SKIN")
    aperture = abs(D["door_rear_x"] - D["door_front_x"])
    if ds and abs(ds[5] - aperture) > 20:
        for sgn in (1, -1):
            warn(f"WARN_door_skin_{'L' if sgn > 0 else 'R'}",
                 (sx(ds[2]), sgn * ds[3], ds[4]), (aperture, 60, ds[7]),
                 f"skin {ds[5]} vs door aperture {aperture:.0f} — {aperture - ds[5]:.0f} mm short of the shut lines")
            n_warn += 1
    # W5 — unassigned strip between hood and cowl
    hd = find_box("HOOD")
    hd_rear, cowl_spec = ((hd[2] + hd[5] / 2) if hd else 1e9), -D["cowl_x"]
    if hd and cowl_spec - hd_rear > 50:
        warn("WARN_cowl_strip", (sx((hd_rear + cowl_spec) / 2), 0, D["cowl_z"] - 80),
             (cowl_spec - hd_rear, 1400, 120),
             f"{cowl_spec - hd_rear:.0f} mm between the hood's rear edge and the windshield base "
             "belongs to no panel")
        n_warn += 1
    # W6 — fins ahead of the hoops
    fin = find_box("AERO_FIN")
    fin_start, hoop_spec = ((fin[2] - fin[5] / 2) if fin else 1e9), -D["hoop_x"]
    if fin and fin_start < hoop_spec:
        for sgn in (1, -1):
            warn(f"WARN_fin_ahead_{'L' if sgn > 0 else 'R'}",
                 (sx((fin_start + hoop_spec) / 2), sgn * abs(fin[3]), fin[4]),
                 (hoop_spec - fin_start, fin[6], fin[7]),
                 f"fin starts {hoop_spec - fin_start:.0f} mm ahead of the roll hoop, over the cabin aperture")
            n_warn += 1

    # ---- materials (visualisation only)
    for nm, (rgba, metal, rough) in MATERIALS.items():
        mat = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
        mat.use_nodes = True
        mat.diffuse_color = rgba
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = rgba
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = metal
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = rough
            if nm == "STATEV_LIGHT" and "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 3.0
                bsdf.inputs["Emission Color"].default_value = rgba
            if nm == "STATEV_GLASS":
                mat.blend_method = "BLEND"
                if "Alpha" in bsdf.inputs:
                    bsdf.inputs["Alpha"].default_value = 0.25

    # ---- assign materials to what they belong to (prompt §26)
    def assign(ob, mat_name):
        m = bpy.data.materials.get(mat_name)
        if m and ob.type == "MESH":
            ob.data.materials.clear()
            ob.data.materials.append(m)
    for ob in root.all_objects:
        n = ob.name
        if "_TXT" in n or n.startswith(PFX + "WARN") or ob.users_collection[0].name == "99_DEBUG":
            continue
        if "WHEEL_" in n:
            assign(ob, "STATEV_WHEELS")
        elif any(k in n for k in ("HEADLIGHT", "DRL", "TAIL_", "PROJECTOR")):
            assign(ob, "STATEV_LIGHT")
        elif any(k in n for k in ("BLADE", "FIN", "DIFFUSER", "SPLITTER", "CHANNEL")):
            assign(ob, "STATEV_CARBON")
        elif "SEAT" in n:
            assign(ob, "STATEV_INTERIOR")
        elif ob.users_collection[0].name == "06_ROOF":
            assign(ob, "STATEV_GLASS")
        elif ob.users_collection[0].name in ("02_BODY", "03_AERO"):
            assign(ob, "STATEV_BODY")

    # ---- diagnostic cameras (prompt §30)
    import math as _mm
    cam_defs = [
        ("CAM_side",  (12000, 0, 650),      (_mm.radians(90), 0, _mm.radians(90)),  "ORTHO", 5.2),
        ("CAM_front", (12000, 0, 650),      (_mm.radians(90), 0, 0),                "ORTHO", 2.6),
        ("CAM_rear",  (-12000, 0, 650),     (_mm.radians(90), 0, _mm.radians(180)), "ORTHO", 2.6),
        ("CAM_top",   (-1200, 0, 12000),    (0, 0, _mm.radians(90)),                "ORTHO", 5.2),
        ("CAM_three_quarter", (4200, 3400, 1900),
         (_mm.radians(72), 0, _mm.radians(129)), "PERSP", 0),
    ]
    for nm, loc, rot, typ, ortho in cam_defs:
        cd = bpy.data.cameras.new(PFX + nm)
        cd.type = typ
        if typ == "ORTHO":
            cd.ortho_scale = ortho
        else:
            cd.lens = 85
        c = bpy.data.objects.new(PFX + nm, cd)
        c.location = tuple(mm(v) for v in loc)
        c.rotation_euler = rot
        dbg.objects.link(c)
        c.hide_viewport = True      # kept out of the viewport so "frame selected" ignores them
        c["note"] = "diagnostic view; ortho cameras are for proportion checks, not renders"
    # CAM_side is the one a proportion judgement should be made from
    bpy.context.scene.camera = bpy.data.objects[PFX + "CAM_side"]

    # ---- parametric root
    rt = bpy.data.objects.new(PFX + "001_ROOT", None)
    rt.empty_display_type = "ARROWS"
    rt.empty_display_size = 0.5
    root.objects.link(rt)
    for k, v in ROOT_PROPS.items():
        rt[k] = v
    rt["spec"] = "STATEV 001 dimensional specification v0.1 (2026-09-14) — see docs/10"
    rt["axis"] = "repo convention: +X forward, +Y left, +Z up, origin = front axle on the ground"
    rt["spec_axis"] = "source spec used +X rearward, +Y right — every spec X is negated on import"
    rt["status"] = "design targets, not production CAD; the scan is master for all donor hardpoints"
    rt["front_track_locked"] = True
    rt["rear_track_locked"] = True
    for ob in root.all_objects:
        if ob is not rt and ob.parent is None:
            ob.parent = rt
            ob.matrix_parent_inverse = rt.matrix_world.inverted()

    n_obj = len(root.all_objects)
    print(f"{COLL_ROOT} rebuilt: {n_obj} objects in {len(SUBCOLLS)} collections | "
          f"{len(SECTIONS)} sections, {len(RAIL_LEVELS)} rail levels, {len(MATERIALS)} materials | "
          f"spec X negated to repo X (+X forward)")
    return root


build()
