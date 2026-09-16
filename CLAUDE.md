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

## Freeze rule

Zones are approved and then frozen. A frozen zone's defining data cannot change: the build itself
refuses to run and names what changed. This is code, not a convention — `01_CAD/scripts/freeze.py`,
checked at the top of `build()`. Unfreezing requires an explicit command and a recorded reason.
See `docs/17-staged-plan-and-freeze-rule.md`. Never work around it by editing the state file.

## Visual authority

The latest approved infographic is the **visual design authority**. CAD does not redesign the car;
it translates the approved design into manufacturable panels against real 986 hardpoints. The locked
elements are listed in `docs/14-locked-visual-decisions.md` — read it before touching any styling
feature. If an engineering constraint forces a change, make the **smallest possible** change to the
affected surface and record it there with the reason. Never redesign the surrounding area.

## Hard constraints (never violate)

1. **Packaging first.** Never design a panel independent of the scanned/known
   mechanical envelope. Render → "does it fit?" is forbidden; envelope → geometry
   → design → engineering → prototype is the order.
2. Wheelbase 2415 mm (workshop manual) and wheel centres are fixed. Windshield frame, rake and
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

## Remote vs local sessions

Two kinds of Claude Code sessions work in this repo. Keep them on separate
branches and never let them diverge for more than one session.

**Remote (claude.ai/code, cloud container)**
- Scope: docs, `CLAUDE.md`, Blender Python scripts, `.gitignore`, README,
  reference images. No Blender is available, so no `.blend` work and no MCP.
- Works on a `claude/...` branch. At the end of every session: commit, push,
  and **merge into `main`** (PR or fast-forward) so local always starts from
  the latest state. Do not leave remote work unmerged across sessions.
- Never touch `02_DESIGN/**/*.blend` from remote (binary, non-mergeable).

**Local (owner's MacBook, Blender + Blender MCP)**
- Scope: everything that needs Blender: cage generation via MCP, measurements,
  clearance checks, splitting, STL/3MF export, `.blend` files, screenshots.
- **Before starting: `git pull` on `main`.** Never start Blender work on a
  stale checkout.
- **After finishing (or before closing Blender): commit and `git push`.**
  Commit at every finished stage, not only at the end of the day.
- `.blend` files are committed only from local. If a `.blend` is being edited,
  do not pull a branch that also changes it — resolve by taking the local copy.

**Both modes, every session**
- Update the **Current status** section below at the end of the session: date,
  what was done, what is next. This is the hand-over between remote and local.
- Record every decision in `docs/09-decision-log.md` (newest on top).
- Conflicts in `CLAUDE.md`/`docs/` are resolved by keeping both entries in
  chronological order, never by dropping one side.

## Current status (update this section as work progresses)

- 2026-09-08: Repo created. Blender 5.2 installed on MacBook Pro M1 Pro 32 GB,
  Blender MCP addon installed and running on port 9876. Claude Desktop MCP
  config being set up. No donor yet. No scan yet. No CAD yet.
- 2026-09-08 (remote): project scaffold (CLAUDE.md, docs 00–09, references,
  cage script) imported into the repo on branch `claude/remote-work-setup-yx9v18`;
  remote/local working rules added. Still to do on local: run the cage script
  in Blender via MCP and confirm which DIMS are TODO.
- 2026-09-08 (local): `01_CAD/scripts/cage_986.py` изпълнен в Blender 5.2 през
  Blender MCP. Колекция `CAGE_986` се строи чисто (22 обекта: 4 гуми, 4 clearance
  ринга, 4 wheel-centre empties, OEM + TARGET envelope, windshield centreline,
  2 roll hoops, 2 side-intake empties, headlamp 500 mm plane, CAGE_INFO).
  Проверени bbox: X от -3286 до +1114 mm, Y ±925, Z 0–1290. Overhang сумата
  затваря: 1035 + 2416 + 870 = 4321. 8 DIMS са TODO (виж по-долу).
  Открит бъг: `clearance_*` ринговете са на Z = od/2 + buffer (338 mm) вместо
  концентрично на колелото (320 mm) — `make_wheel` слага z = radius.
- 2026-09-09 (local): Blender MCP връзката потвърдена от Claude Code (Desktop
  app, Code tab). Бъгът с `clearance_*` ринговете оправен — `make_wheel` вече
  приема `z`, ринговете са концентрични на колелото (Z = 320 mm, OD 676 =
  640 + 2×18). Клетката прегенерирана през MCP: 22 обекта, 8 TODO DIMS
  непроменени. Ортографски screenshots (профил = Blender FRONT view, отгоре =
  TOP) записани в `04_ENGINEERING/cage/cage_986_{side,top}.png`. Клетката не
  се пази като `.blend` — регенерира се от скрипта. Hyper3D/Hunyuan image-to-3D
  в MCP addon-а са изключени (може да се включат от N-панела, ако потрябва 3D
  скица-подложка от ref-05; резултатът не е панел за печат).
- 2026-09-09 (local, продължение): без покупка на чертеж. Свалени официалният 986
  workshop manual (Group 0a General + Group 5 Body, OCR, локално извън git) и CC BY
  профил от getoutlines.com. От manual-а: междуосие 2415, дължина 4315 RoW, клирънс
  95 RoW, следа по размер джанта, structure dimensions (roll-bar/soft-top screw
  points). От чертежа (4.153 mm/px, калибриран по колелата): навеси 1007/893, cowl,
  windshield header, hoop x/z, door lines, side intake — всички `approx` ±15 mm.
  Клетката: 27 обекта, само `hoop_y` е TODO; чертежът е image empty
  `BLUEPRINT_side_ccby` на y = −1.0 m. Screenshot: `04_ENGINEERING/cage/cage_986_side_blueprint.png`.
- 2026-09-09 (local, 3): `01_CAD/scripts/block_986.py` — приблизителен 3D обем на
  986 (`BLOCK_986_approx` в `UNDERLAY_986`): силует от чертежа × 1780 × предположен
  план, superellipse сечения, изрязани ниши. 4319 × 1780, z 130–1063. Underlay за
  обем, ±30–50 mm; не е повърхност за фланци. Screenshots в `04_ENGINEERING/cage/`.
- 2026-09-09 (local, 4): 4-изгледен CC BY чертеж (getoutlines 1996, 509×519) свален
  и обработен: `01_CAD/scripts/extract_blueprint_986.py` (Pillow, извън Blender) →
  `01_CAD/scripts/data/986_plan_section.json` (план на полуширината по x, сечения
  отпред/отзад, ±30 mm). `block_986.py` вече ползва измерен план + сечение вместо
  предположения. `hoop_y` = 350 approx (седалки в плана ±357, mounts ±566/552) — вече
  **няма TODO в DIMS**; всичко approx/published до скана. Screenshots
  `04_ENGINEERING/cage/block_986_{persp,top,front}.png`.
- 2026-09-14 (local): приет STATEV 001 dimensional spec v0.1 (`docs/10-statev-001-spec-v01.md`).
  `01_CAD/scripts/statev_skeleton.py` строи колекция `STATEV_001` — 72 обекта: 15 сечения
  S00–S14 като curves, 14 надлъжни rails, envelope кутии за фарове/DRL/маска/радиатор/intake/
  перки/deck/ламели/стопове/дифузьор/ауспух, STATEV 19" колела на донорската следа.
  `check_statev_vs_donor.py` дава конфликтен доклад: 3 fatal (главини Y, фар извън каросерията,
  intake не съвпада с реалния отвор), 3 за проверка (преден навес срещу crash beam, S00–S03/S06
  навътре от OEM обшивката, перките пред roll hoops), 1 отворен (покрив/капак — само от скана).
  Screenshots: `04_ENGINEERING/statev_v01/skeleton_{side,top,front,persp,debug_side}.png`. **Без loft.**
- 2026-09-14 (local, 2): допълнен до пълния обхват на двете съобщения — 105 обекта в 9 колекции.
  Добавени: envelope кутии за clamshell/капак/калници/врати/рамена/deck, колекции
  00_DONOR_HARDPOINTS (указател към CAGE_986) / 06_ROOF (2 PROVISIONAL обвивки) / 07_INTERIOR /
  99_DEBUG (размерни линии + STEER_SWEEP), 6 материала, `STATEV_001_ROOT` с 26 параметъра,
  L-образни стопове. Файл `02_DESIGN/exterior/STATEV_001_v001.blend`. Две нови находки:
  door skin 1050 срещу отвор 1195, и 340 mm между капака и cowl-а без панел.
- 2026-09-14 (local, 3): затворен и последният пропуск спрямо промпта — 140 обекта. Префикс
  `STATEV_` навсякъде, сечения `STATEV_S00..S14`, ET/джанти параметри, intake като
  inlet/duct/outlet, материалите прикачени към обектите, 5 диагностични камери, клирънс за
  двигателен отсек и roll hoops, и 10 **warning обекта** (`STATEV_WARN_*`), които се
  преизчисляват при всяко пускане — поправено число маха маркера.
- 2026-09-14 (local, 4): трети одит намери още 4 пропуска от първото съобщение — добавени
  арки на колелата (дъги с радиус/ширина на отвора), централен тунел на дифузьора, характерна
  линия на вратата, и публикуваните structure points P08/P10/P11/P13/P21/P22 в клетката
  (клетка 45 обекта, STATEV 151). Нова находка: отворите на арките са по-широки от каросерията
  със 7.5 mm отпред и 24 mm отзад. Файл `STATEV_001_v002.blend`. Докладът: 3 fatal, 7 за проверка.
- 2026-09-14 (local, 5): втора итерация — решенията се взимат от CAD страната по йерархия
  A–G, не се питат като числа. Шест решения (фар, intake, арки, перки, врата, капак) в
  `DECISIONS`. Гладко разширение около осите вместо ръчна настройка на сечения. Поправена
  грешна логика в проверката: „навътре от OEM“ има значение само там, където обшивката остава.
  Докладът: 11 → 3 items. Диагностични изгледи в `04_ENGINEERING/statev_v01/review/`
  (side, front, top, front 3/4, rear 3/4 + три donor/STATEV overlay). Файл `STATEV_001_v003.blend`.
- 2026-09-14 (local, 6): `statev_preview_loft.py` — preview повърхност през сеченията с изрязан
  отвор на кабината, за да има какво да се прецени. 4370 × 1906 × 790. Показа три неща: ширината
  стана 1906 заради разширението около осите; короната на deck-а беше моя измислица и е ограничена
  от deck spine-а; арките бяха дъги на постоянно Y, а трябва да лежат върху повърхността (162 mm
  разминаване при върха) — препостроени. Файл `STATEV_001_v003.blend`.
- 2026-09-14 (local, 7): QC пробег. Намерен тих срив: `statev_skeleton.py` падаше на `next(...)`
  за изтрития "HEADLIGHT" и строеше сцената наполовина (без root, камери, материали, debug) —
  последните няколко записа на .blend са били непълни. Поправено, `v003` презаписан. Чисто:
  трите скрипта минават, 133 обекта, 0 non-manifold ръба, 0 дублирани имена, острието не се сече
  с корпуса на фара, DRL Z 350–545 (законов минимум 250).
- 2026-09-14 (local, 8): нова референция (ref-07, по-разработена, с donor overlay и roof
  mechanism панели) приета като текуща цел. Спецификацията изравнена с нея: deck от равнината на
  дъгите нагоре (Z 960 вместо 800, започва на specX 1760 вместо 1450), перките заменени с
  buttress-и Y ±600, L-образният стоп заменен с права лента 1560, добавени hood vents.
  Нов риск №1: deck и buttress на Z 960/1090 стоят в обема, където се сгъва покривът — решава се
  само на реалната кола. Файл `STATEV_001_v004.blend`.
- 2026-09-14 (local, 9): ref-08 (трета инфографика) — добавени `DOOR_VENT_L/R` (вертикален слот
  в предния ръб на вратата), `ROCKER_CHANNEL_L/R` (подрез по прага), `REAR_SPOILER` (плоско перо
  над стопа). 138 обекта. `docs/11-what-i-need-to-build-panels.md` описва какво може и какво не
  може да дойде от ChatGPT, и какво блокира пътя до файлове за принт.
- 2026-09-14 (local, 10): панелите ще се правят от външна композитна фирма в България, която ще
  ги шкури и боядисва. `docs/12` — готов промпт за ChatGPT (описание на формата по панели, без
  милиметри). `docs/13` — въпросник към фирмата; техните отговори определят разрязването,
  дебелините, фланците и формата на файловете, затова се пита ПРЕДИ да се чертае фуга.
- 2026-09-14 (local, 11): визуалните решения заключени в `docs/14-locked-visual-decisions.md`.
  Поправена моя грешка: бях прочел рендера като права лента и махнал L-края на стопа — върнат като
  `TAIL_BAR` + `TAIL_END_L/R`. `FRONT_CLAMSHELL` маркиран като дизайнерска група, не един панел.
  `DECK_SPINE` маркиран **BLOCKED** — височините са от рендера и стоят в обема на сгъване на
  покрива; редът е обем на покрива първо, deck после, а обемът идва само от скан. 140 обекта.
- 2026-09-14 (local, 12): написан `HOOD_SPINE` — осевият профил от върха на носа до основата на
  стъклото, 8 точки. Последната е донорска и се проверява автоматично. Preview-то вече взима
  короната отпред от нея вместо от предположение. Файл `STATEV_001_v005.blend`.
- 2026-09-14 (local, 13): Panel Architecture v0.1 приета (мина трите проверки) и интегрирана.
  Добавени `ROCKER`, `BRAKE_DUCT_F/R`, таблица `AIRFLOW` (6 системи), колекция `08_PANEL_SEAMS`
  (9 фуги, всяка с причина), spoiler-ът стана ducktail. 164 обекта в 10 колекции.
  `scan_dependency_report.py` картира всеки панел срещу донорското знание: **7 RED, 8 YELLOW,
  0 GREEN.** Нито един панел не може да стане достоверна геометрия преди скана.
- 2026-09-14 (local, 14): `docs/15` — последното, което външна спецификация може да даде в тази
  фаза: характер на повърхността по зони (кривина, посока на отблясъка, напрежение, ръбове,
  преходи). Това е разликата между preview-то и рендера — езикът живее в кривината, не в
  сеченията. След него ChatGPT няма какво повече да даде, докато няма кола.
- 2026-09-14 (local, 15): Surface Behaviour Specification приета (`docs/16`). 17 зони с кривина,
  посока на отблясъка, напрежение, ръбове, преходи и типична грешка — като данни в `SURFACE`.
  Карта на непрекъснатостта `CONTINUITY` (16 прехода, G0/G1/G2; G2 НЕ се гони навсякъде).
  Критичното правило: без един глобален loft, повърхността е мрежа от patch-ове.
  **Preview-то нарушава точно това по конструкция** — то е инструмент за пропорция и се хвърля,
  когато започне сърфирането. Пуснат тестът с отблясъците: **FAIL, ballooned** — кръгли меки
  отблясъци, нито една дълга лента, никъде прекъсване на светлината, защото трите негативни
  пространства не съществуват в сеченията. Изходи в `04_ENGINEERING/statev_v01/surface_test/`.
  Файл `STATEV_001_v006.blend`.
- 2026-09-14 (local, 16): външната верига приключи за тази фаза — архитектура, фуги, въздушни
  пътища, характер на повърхността и измерим критерий са налице. Добавен план за сканиране в
  `scan_dependency_report.py`: осем сесии, подредени така, че нищо да не се сваля и връща пак.
  **S2 (покривът в четирите положения) е първи** — той разблокира цялата задна група.
  Изход в `04_ENGINEERING/reports/scan_dependency.txt`.
- 2026-09-14 (local, 17): приет петстепенният план (`docs/17`): големи обеми → зони → детайли →
  производствена версия → производство, с четири контролни точки. **FREEZE правилото е
  машинария, не обещание** — `freeze.py` + състояние в `data/freeze_state.json`, проверката се
  вика в началото на `build()`. Тествано: замразена зона, преместен елемент с 5 mm, строежът
  отказа и назова зоната и двата хеша; след връщане мина чисто.
- 2026-09-14 (local, 18): одит на всичко получено от чата срещу направеното. Имената на
  обектите са пълни (23 от 23). Открит пропуск: exploded-assembly / manufacturing промптът
  никога не беше изпълнен. Изпълнена е неговата половина, която не иска геометрия —
  `panel_registry.py`: 27 части P01–P27 (минимален практичен брой), страна, дизайнерска група,
  ред на сглобяване, вектор на монтаж, метод на производство, материал, статус, и BOM в CSV.
  Другата половина (фланци, overlaps, splits, ориентация за печат, маса, център на тежестта,
  самият exploded view) иска реални повърхности и е изрично изброена като неизпълнена.
- 2026-09-14 (local, 19): **ЕТАП 01 изпълнен.** `statev_master_volumes.py` заменя preview-то.
  Колекции `STATEV_MASTER/{FRONT,SIDE,REAR,ROOF,DETAILS}`. Обем 4.629 → 3.826 m3, 2294 лица,
  1019/504/771 по зони. Петте семейства празнини са реални: кабина, 4 арки, предни канали,
  канал от вратата към intake-а, заден подрез. Кадри в `04_ENGINEERING/statev_v01/stage01/`.
  Файл `STATEV_001_v007.blend`. Три бъга по пътя са документирани в `docs/17`: маркерът за рязане
  на скриптове, обърнати нормали на loft, и скрит обект изпада от булевата операция. Редът на
  рязане е фиксиран — каналите преди арките.
- 2026-09-14 (local, 20): SURFACE_LOCK_01, първи проход. Поправени 5 параметрични бъга: скок на
  короната при cowl-а (170 mm за 1 mm — най-голямата чупка), стъпка между характерите на зоните,
  фасетиране (изглаждане на контролните данни, не модификатор), buttress от кутия в loft-нато
  острие обединено с кожата, и задно рамо с гаусов пик вместо вертикална стена. 5722 лица.
  Остават 5 визуални проблема, всички от вида „скулптиране“, не „параметър“ — виж `docs/17`.
  Откат `v008`, ново `v009`.
- 2026-09-14 (local, 21): характерът е скулптиран като **пет параметрични полета**, не ръчно:
  основна странична линия (13-точкова траектория, +13 mm при линията), рамо на предния калник
  (+20 mm гаусово около предната ос), праг (−30 mm под Z 315 между арките), опашка (0.86 стеснение
  и −90 mm корона от specX 2800), buttress връх (0.20 от базата вместо 0.55). Всички числа са в
  началото на `statev_master_volumes.py`. Откат `v009`, ново `v010`.
- 2026-09-14 (local, 22): диагностичен pass без промяна на геометрия. Заключеното е непокътнато;
  ширината обаче излезе **1960 срещу целта 1850**. Трите най-слаби повърхности: фланкът на задното
  рамо (няма вертикален участък), носът (долният преден отвор изобщо не е изрязан — пропуск в
  режещите семейства), прагът (меко хлътване вместо ръб). Кадри в `04_ENGINEERING/statev_v01/diag/`.
- 2026-09-14 (local, 23): четирите корекции направени. Нос: добавено режещо семейство
  `NOSE_MOUTH` — устата е реална празнина. Заден фланк: ново поле `flank()`, почти вертикален
  участък Z 300–660 между specX 1900–3050. Праг: преход 55 → 18 mm. Ширина: разширението около
  осите 18/34 → 6/0 плюс таван 925 → **точно 1850**. Следствие: отворът на задната арка се стесни
  370 → 320, остават 22.5 mm странично до гумата. Откат `v010`, ново `v011`.
- 2026-09-14 (local, 24): финален surface pass. Нос: устата свалена, за да има 80 mm острие над
  нея, плюс изтъняване −46 mm над Z 350. Заден фланк: горно затихване 70 → 34 mm и +16 mm рамо
  над вертикалния участък. Праг: дълбочината непокътната, преходът 18 → 10 mm. Задна арка:
  оставена на 320. **Нито един заключен параметър не е мръднал** — 4370 / 1850 / 2415 / 1465 /
  1528 и четирите центъра на колела. Чисти кадри без гайдове в `04_ENGINEERING/statev_v01/clean/`.
  Откат `v011`, ново `v012`.
- 2026-09-14 (local, 25): преработена задна архитектура върху донора. Deck 960 → 880, buttress
  връх 1090 → 985, ширина 210 → 300, начало 1760 → 1600, спад на короната 90 → 140. Височината на
  тялото пада 968 → 864. **Ролбарите НЕ са пипани** — те са донорски на Z 1235; кулите бяха моите
  buttress-и. Компромис: deck-ът се отдалечава от „покривът среща deck-а в една линия“, което се
  донастройва след скана. Откат `v012`, ново `v013`.
- 2026-09-14 (local, 26): primary surfaces, итерация 2. Намерена причината за „отделната плоча“
  отзад: `crown = max(crown, z_top+10)` качваше короната над deck spine-а. Сега spine-ът командва
  зад дъгите. Добавен `BELT_DIP` −48 mm в средата, за да изчезне „плоската платформа“. Преден
  калник усилен 20 → 34 и стеснен, плюс талия между носа и калника. Обем 3.802 → 3.599.
  Заключените са непокътнати. Откат `v013`, ново `v014`. Одобрение още не е дадено.
- 2026-09-14 (local, 27): **v015.** Върхът на задното рамо преместен от specX 2000 на 2400 — 15 mm
  от задната ос вместо 415 mm пред нея; издигането на buttress-а е гаусиан върху оста, не синус,
  който свършва рано, така че масата стои над гумата, а не над седалките. Опашката вече пада
  монотонно (625, 570, 557, 513 при 3050/3200/3300/3420); `DECK_SPINE` е удължен до 3420, за да не
  може резервната корона да вдига последната станция със 106 mm. Предна ширина +24 mm до 1773.7
  през по-високо и по-широко поле на калника (gain 34 → 52, център Z 600, лента 180).
  **Поправена моя грешна диагноза:** „208 mm cowl cliff" сравняваше короната на капака по осевата
  линия с горнището на вратата до отвора на кабината — две различни неща. Реалното число беше
  beltline 820 срещу основа на стъклото 970. Откат v014.
- 2026-09-14 (local, 28): **v016 — architecture correction pass.** Първопричината за липсващите
  празнини беше реална: cutter-ите се оразмеряваха от **суровия** профил, а тялото се строи от
  **оформения**, така че cutter-ът излизаше изцяло вътре в тялото и го издълбаваше, вместо да го
  отваря — затова три от четирите празнини мереха 0.0 mm, докато всеки boolean докладваше успех.
  Преден канал 0 → 128, страничен вход 0 → 84, заден undercut 106 → 193. Стъпката от 201 mm в
  задната корона при specX 2800 премахната: **buttress-ът стана profile geometry, не boolean** —
  стъпил на `DECK_SPINE` с гаусова височина с връх на задната ос, така че haunch, blade, deck и
  опашка са една лофтната повърхност. Два последователни union-а, а после и един двучерупков union,
  бяха сривали меша; превръщането му в профил премахна чупливостта, вместо да я заобиколи.
  Beltline подобрен, но недостатъчно (139 отзад, още 217 при A-стълба). Каналът на вратата остана
  нерешен след три опита и това беше **казано**, а не опитано четвърти път. Откат v015.
- 2026-09-14 (local, 29): **v017 — ТЕКУЩА БАЗА.** Каналът на вратата спря да се реже и стана част
  от профила, както buttress-ът в v016, и е **едно поле** от задния ръб на предната арка до входа,
  а не преден канал и канал на вратата, които се срещат. Празнините се прилагат **последни**, след
  всичко, което разширява — character полетата ги издърпваха обратно навън. Мярката е сменена на
  **хордова дълбочина**: max-minus-min дава нула винаги когато фланкът зад канала пада, тоест по
  цялата дължина на колата. По тази мярка v016 беше **отрицателен** почти навсякъде (повърхността
  се издуваше там, където трябваше да е каналът); v017 дава 50–85 mm с най-голяма промяна между
  съседни станции 6 mm през вратата. Beltline: `BELT_LIFT` заменен с `BELT_Z` — абсолютна
  проектирана линия на горнището на вратата; gap до стъклото 273/164/154/200/202/206/174/170 стана
  114/104/114/126/129/129/123/115, една дъга с максимална стъпка 12 mm. Booleans: 15 → 6 (остават
  само кабината, четирите арки и устата на носа). Лица 5530 → 8486 (резолюция на сечението 40 → 60).
  **Странични ефекти, признати и неодобрени:** горнището на предния калник се вдигна със 161 mm при
  specX 350 (678 → 839), и страничният канал вече не започва над колелото. И двете са вписани в
  `docs/14`. Заключената донорска геометрия е проверено идентична с v016. Откат v016.
- 2026-09-15 (local, 30): документационен cleanup, без нито една промяна по геометрия. Този блок
  беше спрял на v014; decision log-ът беше спрял преди v015; двете промени в заключена визуална
  зона не бяха вписани; четири доклада от v014/v015/v016 носеха имена без версия, а аз бях казал на
  собственика да ги дава на ChatGPT. Преименувани са с версия в името. Махната е мъртвата таблица
  `REAR_UNDERCUT`, заменена от `REAR_UNDERCUT_FIELD` във v017.

- 2026-09-15 (local, 31): **v018 — refinement pass. ТЕКУЩА БАЗА.** Четири точки, две от които се
  оказаха диагностицирани грешно от мен и това е казано, а не заобиколено.
  **Преден калник:** излишъкът над v016 намален от +161 на +85 mm при specX 350 след шест
  контролирани теста (`CABIN_X0` 285→340, `CABIN_RAMP` 155→110, `BELT_Z` получава (345,755),
  (420,912) и (560,838)). Двата параметъра местят калника и горнището на вратата почти 1:1 —
  изглаждането по X ги свързва; изричната ниска стойност на `BELT_Z` отпред е единственият лост,
  който ги разделя, и той насища. Не е върнато на 678 заради **формата на линията**: v016 е
  приблизително плоска около 700 mm и има 31 mm хлътване при specX 300, докато v018 се качва
  монотонно. (Първоначалната обосновка тук — „короната на арката е 673.5, значи оставаха само
  няколко милиметра тяло над отвора" — е **оттеглена**: предната арка е цилиндър с радиус 350
  върху оста и затваря при specX ±350, тоест при specX 350 няма отвор, над който да се мери
  материал. При specX 0 v016 носи 700.4, а v018 — 702.9.) Цена: процепът при A-стълба
  114 → 134 mm; от specX 1000 назад линията не мърда изобщо.
  **Канал на вратата: НЕ Е ПИПАН.** „Хлътването" 80/66/65/80 при specX 715–820 беше **моя грешка в
  измерването**, не дефект в полето: идваше от бинване на Z през 30 mm преди вземането на рамото.
  Точно измерено върху самите ринги, съседните разлики там са 2 и 4 mm — най-малките на колата.
  **Ръб на deck-а:** гребенът беше една контролна точка и resample-ът го заобляше. Сега са две —
  стръмен подход, после гребен. По-остър на 5 от 8 станции, по-мек на нито една, корона ±0.69 mm.
  **Нос:** тялото НЕ беше с малко сечения (през 17–33 mm, 14 през устата). Фасетата беше самият
  cutter — правоъгълник през шест станции на до 80 mm. Преизчислен през Catmull-Rom на 12 mm и с
  радиус 26 mm по двата вътрешни ъгъла. Лица 8486 → 8899, всички в носа.
  **Заден undercut:** само оценен, непроменен. Препоръка B — омекотяване чрез по-бързо отпускане.
  Заключеното е проверено идентично. Откат v017.

- 2026-09-15 (local, 32): **v019 — ТЕКУЩА БАЗА.** Един параметър: `REAR_UNDERCUT_FIELD.xb`
  3150 → 2950, избран след контролиран A/B/C експеримент върху точната v018 база, в който xb беше
  единствената разлика. 3050 отхвърлен — визуалната промяна недостатъчна. 2850 отхвърлен —
  отпускането става ненужно рязко, 58 mm срещу 50 в самия v018. **2950 е визуален избор, не
  изведена инженерна стойност**; единствените котви са край на задната арка 2780 и начало на
  дифузьора 3145. Върхът 287.3 mm при specX 2870 е запазен; максималната разлика между съседни
  станции пада на 46.5 от 50. Силуетът и всички заключени размери са проверено непроменени —
  целият diff на проследеното дърво е един ред. v019 е регенерируем от source-а: изпълнен директно
  от файла, дава 9959 върха, 8899 лица, обем 3.911282 и върхов хеш `8a29a19d…fe265`, идентичен с
  валидирания експеримент. Записано и че **`xa` е мъртъв лост** — местенето му 2560 → 2780 променя
  дълбочината с най-много 1 mm, защото между тези станции лентата е вътре в отвора на арката.
  Калникът остава на ~763 mm без ново поле. Booleans: шест режещи елемента, седем операции, защото
  устата на носа е огледална — непроменено. Откат v018.

- 2026-09-15 (local, 33): решенията по CHECKPOINT 01 взети и записани. **CHECKPOINT 01 минава за
  FRONT, SIDE и REAR по профила; ROOF остава BLOCKED** до сесия S2. За целта е въведено ново
  правило за частичен checkpoint в `docs/17` с три условия — минаването не е freeze и нищо не е
  замразено. Двете отклонения в `docs/14` са приети като работни линии: калникът на ~763 mm и
  началото на страничната линия иззад арката. Осемте предложени части са приети — регистърът расте
  **27 → 38 части**, редът на сглобяване 18 → 26 стъпки. Построена е **веригата от повърхност до
  файл за печат** (`panel_pipeline.py`): извличане, ядро, измерване, разрязване, ориентация,
  експорт, със 17 доставчикови стойности като `None` и номера на въпроса от `docs/13`. Етапите,
  които нямат стойност, спират и я назовават, вместо да гадаят. Пробен пуск даде първия истински
  STL в проекта — 2968 триъгълника. Панелен статус: 15 RED, 23 YELLOW от 38.

- 2026-09-16 (local): измерена е донорската зависимост вместо да се предполага. `donor_exposure.py`
  отговаря на двоичния въпрос „огражда ли тази approx стойност този панел“, като мести всяка от
  четирите по записаната ѝ лента. **Оттеглени са количествените числа от по-рано същия ден** —
  28.0/42.5/60.1/62.3 mm са стъпката на мрежата, не изместване: при смущение 2 mm P15 дава същите
  60.1 както при 40 mm. Вярното: където донорска стойност огражда панел, фугата пътува колкото е
  сгрешена оценката, 15–30 mm срещу 15 mm припуск. Поправена грешка в `manufacturing_audit.py` —
  срезовете на арките бяха обявени за approx заради tyre OD, а вертикалният им център е наша
  аритметика (235/35R19 → 647.1, 275/35R19 → 675.1); цялата геометрия чете точно четири донорски
  стойности, две от които публикувани. `P07/P08 ROCKER` минава PROCEED с доказателство и от двете
  половини. Одит: **6 / 3 / 10 / 19**. Веригата на P07 намери две структурни неща: огледалните
  региони се изнасяха като двойка (поправено — реже се по знака на Y), и P07 не е една част —
  задната арка го сече на праг 284–2122 и опашка 2708–3000. Веригата отказва да изнесе STL за
  регион, който не е част. PROCEED са 6, изнесени пилоти остават 4.

- **Текуща база: `02_DESIGN/exterior/STATEV_001_v019.blend`. Откат: v018.**
  Авторитетни източници: геометрия — v019.blend, регенерируем от `statev_master_volumes.py`;
  измервания — `04_ENGINEERING/reports/v019_report.txt`; решения — `docs/09-decision-log.md`;
  заключени визуални решения — `docs/14-locked-visual-decisions.md`. Всеки доклад с версия в
  името е исторически и НЕ е текущ.
- Next: **етап 02 — реални повърхности по зони**, patch-базирани по `docs/16`, при спазена карта
  на непрекъснатостта 5×G0 / 10×G1 / 2×G2. Това е единственото, което стои между регистъра от 38
  имена и реални панели. Веригата до файл за печат вече чака да ѝ дадат повърхности.
  По-рано: Калникът е приет като
  работна линия на ~763 mm, undercut-ът е решен с `xb = 2950`. Решено е да се работи **без да се
  чака сканът**: цялата наша форма и панелна архитектура се строят сега, а сканът остава като
  последен fitting/validation етап. Монтажният интерфейс се строи ПОСЛЕДЕН и отделно от формата на
  панела, за да е преподравняването смяна на параметър, а не премоделиране. Нито една зона не е
  замразена — CHECKPOINT 01 не е минат и собственикът не е дал одобрение на силуета.
  Успоредно: учебна стъпка 1 — **капак на огледало** (после корпус за Hella модул, после преден
  калник — не носът). Отворено и чака скана: `hoop_y`, roof fold envelope, engine-lid opening.

## How to work in this repo

- `01_CAD/scripts/` — Blender Python. The cage must always be regenerable from
  script; never hand-edit cage objects. `block_986.py` (run after `cage_986.py`)
  rebuilds the approximate 986 volume underlay; edit its assumption constants, not the mesh.
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
