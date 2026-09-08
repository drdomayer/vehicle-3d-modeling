# vehicle-3d-modeling — STATEV 001

Boutique one-off sports car: new composite body + interior on a Porsche Boxster 986 base.

Start here:
1. `CLAUDE.md` — project memory (decisions, constraints, status). Claude Code reads it automatically.
2. `docs/` — brief, hardpoints, design direction, lighting/legal, manufacturing, budget, roadmap, tools, decision log.
3. `07_PRESENTATION/references/` — renders. `CHOSEN` = target, `REJECTED` = history.
4. `01_CAD/scripts/cage_986.py` — regenerable hardpoint cage for Blender.

Folders:
```
00_SCAN/          scans of the donor (raw, cleaned)
01_CAD/           scripts, STEP/IGES exports
02_DESIGN/        .blend files: exterior / interior / lighting
03_PRINT/         STL/3MF split for the printer + exploded-view PDFs
04_ENGINEERING/   clearance, tyre envelope, roof fold path, lamp positions
05_MOULD/         (only if a kit is made)
06_COMPOSITE/     layup notes, materials
07_PRESENTATION/  references, renders, branding
docs/             project documentation
```
