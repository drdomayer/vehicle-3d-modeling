# STATEV 001 — project memory for Claude Code

Read this file first, then `docs/` in numeric order. Reference renders are in
`07_PRESENTATION/references/` — open them (they are images, read them) before
giving any design opinion. Communicate with the owner in **Bulgarian** (technical
terms in English are fine). Be direct, concrete, dense. No fluff, no cheerleading.

## What this project is

A one-off boutique sports car under the owner's own brand **STATEV**. First car:
**STATEV 001** — a 2-seat mid-engine roadster with completely new composite
bodywork and a custom interior on a **Porsche Boxster 986 (1997–2004)** donor.
Nothing of the donor should be visible except the windshield frame and the
twin roll hoops. Someone seeing the car should ask "what is that?" — not
"is that a Boxster?".

The owner (Miro) is a product manager with CS/cybersecurity background, hands-on
with Linux/Docker/AWS, **not** a CAD/surface designer. He is learning Blender to
do the body design himself. Height ~190 cm — cabin fit is a hard constraint.

## Decisions already made (do not reopen without new facts)

| Topic | Decision | Why |
|---|---|---|
| Donor | Porsche 986 Boxster 2.5/2.7, ideally 2003–04 facelift (glass rear window) | Only mid-engine 2-seat base at ≤ €6k that fits 190 cm; mid-engine proportion is 80% of the "new car" look |
| Rejected donors | BMW E46/E36 coupe, BMW Z4 E86, 350Z, MR2, Z3, MX-5 | Front-engine + retained greenhouse always reads as the donor (see ref-01, ref-02); MR2/MX-5 too small |
| Design direction | **Radical futuristic** (Czinger 21C / Zenvo Aurora / Koenigsegg Gemera language): layered panels with negative space, floating fenders, thin light blades, aero fins behind the roll hoops, open rear structure over diffuser | ref-05 approved as "мега яко"; earlier modern-retro / Вардарец direction is superseded |
| Roof | Keep the OEM powered folding soft top. No fixed hardtop for now (possible phase-2 removable composite fastback) | Rain usability. Design is judged roof-down; closed roof is "rain mode" |
| Rear deck | Raised/extended deck behind the roll hoops with tall fins so the closed roof meets the deck in one continuous line | Hides the Boxster roof hump when closed. Must not block the fold path, rear-window bottom edge, or engine-lid opening |
| Surfacing | Crisp, tense, hypercar; NOT soft/Porsche-like; NO fake vents — every opening functional | ref-03/ref-04 rejected as "boring" |
| Lights | E-marked modules in custom 3D-printed housings: Hella 90 mm bi-LED projectors (low/high), Hella LEDayFlex (DRL/position blade), Hella Shapeline (rear functions), red E-marked reflectors | Only road-legal way to get thin light blades. Never modify a module's lens |
| Manufacturing (one-off) | 3D-printed PLA/PETG master per panel → fiberglass laminated **directly over the print** (print = core) → filler/sand/prime → paint. **No molds** for the one-off | Saves €3–5k and months. Molds only if a kit is sold later |
| Panel attachment | Front: fenders/bumper/hood are bolt-on on 986 — replaced outright. Rear quarters are welded: new composite quarter as **overlay** on the OEM skin (~70%) + bodyshop cuts a 30–40 mm flange where there is no natural seam (~30%), so it sits flush | Structure, wheelhouse, suspension points untouched |
| Seams rule | New panel edges land only on lines that already exist (door shut, sill bottom, lamp opening, engine lid gap, roll-hoop cover) | No visible "step" |
| Engine | Keep 2.7 (220–228 hp) for phase 1. 450 hp dream is phase 2 (3.4/3.6 swap) | Budget |
| Wheels | 19", realistic tyre sidewall, bronze finish. Ground clearance target 120 mm (road legal) | Renders with 22" and 60 mm clearance are lies |
| Colour/interior | Dark metallic green, bronze wheels, tan leather | Brand look |
| Software | **Blender** (free) for all surfacing, driven by owner's hands + Claude via **Blender MCP**. Plasticity (one-time licence) later for thickness/flanges/splitting if Blender is painful. Fusion 360 not required. No paid subscriptions | Owner's constraint: no subscription burn |
| Scanning | Own cheap scanner (Revopoint Range 2 / POP 3, €500–900) bought before the donor; MetroX only if scanning becomes a service | Cheapest path to ±0.1–0.5 mm on mating surfaces |
| Printing | Outsourced to a print-farm/person for now. Own large printer (Modix BIG-180X class) only after the first panels are validated | Capex after validation, not before |
| Design before donor | Yes — build a **hardpoint cage** from published 986 dimensions + blueprint + artist model, design panels with **15–20 mm air** to anything OEM, then buy/scan the car and realign | Owner has no donor yet |
| Budget | Donor ≤ €6k. Whole one-off ≈ €31–60k, realistic target ~€40k. No €3–8k freelance surface designer (owner does it) | See docs/06-budget.md |

## Hard constraints (never violate)

1. **Packaging first.** Never design a panel independent of the scanned/known
   mechanical envelope. Render → "does it fit?" is forbidden; envelope → geometry
   → design → engineering → prototype is the order.
2. Wheelbase 2416 mm and wheel centres are fixed. Windshield frame, rake and
   roll hoops are fixed. Door cut lines fixed. Side intake stays ahead of the
   rear wheel and feeds the engine.
3. 15–20 mm clearance to all OEM structure until the real car is scanned.
4. No 3D-printed thermoplastic replaces any structural/safety part (crash beam,
   mounts, hinges, seat/steering structure).
5. Road legality in Bulgaria is a design input, not an afterthought: headlamps
   ≥ 500 mm from ground, side-visible indicators, rear reflectors, plate light,
   E-marked lamp modules unmodified.
6. AI proposes, checks, explains. Critical engineering is verified physically or
   by a professional. Do not let the owner skip a fit-test on a single printed
   panel before printing the rest.

## Current status (update this section as work progresses)

- 2026-09-08: Repo created. Blender 5.2 installed on MacBook Pro M1 Pro 32 GB,
  Blender MCP addon installed and running on port 9876. Claude Desktop MCP
  config being set up. No donor yet. No scan yet. No CAD yet.
- Next: run `01_CAD/scripts/cage_986.py` in Blender (via MCP or Text Editor),
  verify it against the-blueprints.com 986 drawing (to be purchased, €22),
  then start the first surface: **front fender**, not the nose.

## How to work in this repo

- `01_CAD/scripts/` — Blender Python. The cage must always be regenerable from
  script; never hand-edit cage objects.
- `02_DESIGN/exterior/` — `.blend` files, one per panel family
  (`front_clamshell.blend`, `rear_deck.blend`, …). Commit at every finished stage.
- `03_PRINT/` — STL/3MF split for the printer + a PDF exploded view per panel:
  part number, print orientation, material, infill. Ask the printer for build
  volume before splitting. 3–4 mm walls, tongue-and-groove alignment keys.
- `04_ENGINEERING/` — clearance checks, tyre envelope, roof fold path, lamp
  positions.
- `07_PRESENTATION/references/` — image references. Filenames say what is
  CHOSEN vs REJECTED. Never treat a REJECTED render as a target.
- Units: **millimetres in docs, metres in Blender** (Blender scene unit scale =
  1.0, length = mm display is fine). Car axis convention in the cage script:
  X = forward, Y = left, Z = up, origin = front-axle centre on the ground.
- When using Blender MCP: build/measure/split/export with code; the free-form
  surfaces themselves are the owner's manual work in Blender. Offer to check
  and correct, do not pretend to sculpt class-A surfaces with primitives.
- Learning path the owner agreed to: mirror cap → lamp housing → front fender.
  Do not push him to the nose first.

## Open questions

- Exact 986 hardpoints (windshield base/top, roll hoop position/height, door
  cut lines, engine-lid opening, roof fold envelope) — placeholders in the cage
  until the blueprint and the scan arrive.
- Front/rear overhang split of the 986 (published: length 4321, wheelbase 2416).
- Whether the raised rear deck must move with the top's clamshell — check on
  the real mechanism.
- Print farm build volume (determines panel splitting).
- BG individual-approval route and required documentation for a rebodied car.
