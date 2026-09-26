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

- 2026-09-16 (local, 2): одит по размер на лицата. **Външната обшивка никога не е била 16.99 m² —
  тя е 11.52.** Девет лица над 0.05 m² минаваха през `not_panel()` и се броят за обшивка, 3.95 m²
  общо; най-голямото е едно лице от 1.876 m² — подът на среза на кабината на Z 640, приписан на
  `P09`. Правилата филтрираха по `ny`, значи капак с нормала по X или Z минава недокоснат, колкото и
  да е голям. Поправено по подпис, не по списък: лежи върху равнината на среза, с нормала по нейната
  ос, проверено срещу `CABIN` и `ARCH_CUTS`. Маса на ядрото 63.2 → **42.9 kg**. Класификацията не
  мърда (6/3/10/19), значи не е стъпила на завишената площ. Проверка байт по байт на пилотните STL:
  `P28` беше две парчета — изтеглен. Изнесени пилоти: **3**, всичките едно парче. Региони, които не
  са една част: **P28, P07, P11, P15, P19** — решение на регистъра, не скан.

- 2026-09-16 (local, 3): взети са решенията по регистъра за трите региона, чиито две половини са
  доказано наши. **38 → 42 части.** `P28` става двойка `P28/P41` (устата на носа го дели по осевата
  линия — двойка, не разсечен панел); `P07` се дели на праг `P07/P08` (292–2122) и нов ъгъл
  `P39/P40 ROCKER_END` (2736–3000) зад задното колело, собствена част, защото и четирите му граници
  са наши или публикувани; `P19` става двойка `P19/P42` (капакът на двигателя заема центъра).
  `P11` и `P15` са отложени съзнателно — SCAN REQUIRED, формата им се преправя. Одит:
  **9 / 3 / 11 / 19**. Намерен и поправен **връх на 41 метра** в изнесеното ядро на `P01`:
  `use_even_offset` дели на косинуса на половинния ъгъл, а `P01` има шест върха с почти
  противоположни нормали от булевата операция на устата. `thickness_clamp` не помага и разбива
  стената (2595 → 934 cm³). Отстъп по нормалата дава ядро с bbox на самата проектна повърхност.
  Добавена преграда: ядро, което излиза от проектния габарит с повече от две дебелини, не се
  изнася. Изнесени пилоти: **6**, всеки проверен байт по байт.

- 2026-09-16 (local, 4): три поправки и един нов изход. **`panel_extract` мереше региони и ги
  наричаше части** — прагът излизаше 0.888 m² и 1841 mm широк, което е двойката, и това число
  отиваше към доставчик; сега всяка част се реже от своята страна (0.445 m², 269 mm), обшивката
  става 11.565 m². **Дясната половина се строи като огледало на лявата** — колата е симетрична по
  построение, осем от девет двойки съвпадат до 0.4%, а `P28/P41` се разминаваше с 30% заради
  тесселацията на устата; отделното извличане пак се сравнява и разликата се докладва.
  **Картата затваря с пълно счетоводство** — четирите нови причини за отхвърляне вече са в таблицата,
  преди това 267 лица излизаха от сметката без ред. Нов изход: **`supplier_package.py`** — един ред
  на част, 42 части, 33 колони, с ясна разлика между стойност / PROVISIONAL / UNKNOWN Qnn.
  **За котиране днес: 9 части, 3.782 m², ~14.1 kg** — всичките с проверен файл.

- 2026-09-16 (local, 5): **тялото се реже по граничните равнини преди приписване.** Досега лице се
  приписваше по центъра си, а тесселацията не е огледална — оттам `P28/P41` 0.142 срещу 0.099 и
  центроид на `P01` на 65 mm от оста. Обемът по ленти е симетричен до 0.2 литра, значи формата е
  била наред, приписването не. Сега обхватите свършват точно на граничните стойности; `P21` 0.928 →
  1.087, `P22` 0.617 → 0.457; фугите са истински споделени ръбове. Развъртането вече следва
  смущението (5.3/12.1/26.4/38.0 при 5/10/25/40 mm) вместо да е плоско — причината за оттеглените
  числа е премахната, не само назована. **Векторите на монтаж бяха обърнати на 28 части** — `+Z` за
  сплитера (отдолу) и за капака/deck-а/buttress-ите (отгоре) не могат да са едновременно верни, а
  всяка L част носеше `+Y`; поправени 8 по Z и 20 по Y, и екранът за демонтаж мина **36 → 0**.
  Нов изход `exploded_assembly.py`: **42.2 kg ядро, център на тежестта specX 1328 (55% назад между
  осите), Y −3.7 mm** като проверка за симетрия. Кадри в `04_ENGINEERING/statev_v01/exploded/`.
  За котиране: **9 части, 3.833 m², ~14.2 kg**, всичките с проверен файл.

- 2026-09-16 (local, 6): **празните полета станаха решения и деветте доказани панела са нарязани за
  печат.** `panel_production.py` държи всички решения в един блок с доводи: стена 3.0, фланец 30 +
  1 mm лепило, фуга 4, плот 350³ с 10 mm поле, езиче 20 mm. Фланецът се носи от панела, който се
  монтира пръв. Изход: **125 секции, ~14.1 kg ядро**, всяка легнала най-плоско и стъпила на Z 0,
  **118 от 125 едно парче**, седемте изключения — поименно в `print_schedule.csv`. Отхвърлен е
  дюбелът: през 3 mm стена не минава 6 mm щифт. Хлътването на фланеца и езичето е **рампа**, не
  стъпка — постоянното хлътване ги късаше от панела. Измерено и за колелата: гумата е **0–25 mm**
  на страна по-навътре отпред и **20–23 mm** отзад от най-широкото на каросерията.

- 2026-09-16 (local, 7): **„прилича ли на картинката" стана число.** `silhouette_overlay.py` слага
  модела и `ref-05` в една координатна система, калибрирана по бронзовите джанти (междуосие 2415 mm
  = 839.9 px → 2.8753 mm/px; двата центъра са на 2.2 px по височина, тоест изгледът е ортогонален до
  6 mm; земята се разминава със 7 px = 20 mm и това е лентата на грешката). Предницата следва
  референцията средно на **50 mm**; задницата стои постоянно **247 mm по-ниско** — решението от
  14 септември (deck 960 → 880, buttress 1090 → 985) вече с цена в милиметри. Носът съвпада до
  **23 mm**, опашката е **256 mm по-дълга**. Два детектора бяха отхвърлени, защото даваха плосък
  1411 mm — фонова винетка и заливане върху подплатено платно. **Находка: `ref-07` и `ref-08` ги
  няма в репото**, макар `CLAUDE.md` да ги сочи като визуален авторитет.

- 2026-09-16 (local, 8): **оттеглени числата от (local, 7) — камерата беше огледална.** Ротация
  (90,0,0) слага дясната ос на камерата върху repo +X, което е напред, тоест рендърът беше с носа
  надясно и таблицата сравняваше нашия нос срещу опашката на рендера. Поправено (камера на +Y,
  ротация 90,0,180) и добавена липсващата проверка: **рендърът срещу самия меш съвпада до 3 mm**.
  Вярното: средно **95 mm**; **предницата е 17–147 mm по-ниска**, най-зле при specX −300..0 —
  короната на предния калник; **задницата 93 mm** по-ниска, не 247; опашката **297 mm** по-дълга.

- 2026-09-16 (local, 9): **v021 — предницата съвпада с рендера до 3 mm, задницата до 21.** Ново поле
  `FRONT_CREST` (гребен на предния калник, снет от силуета на ref-05; калибровката потвърдена от
  основата на стъклото — 969 срещу донорските 970) и `DECK_SPINE` държан равен на 880 зад задната ос.
  Възлите на 1760 и 2100 не са пипани — те са в обхвата на предполагаемия обем на сгъване.
  Средно отклонение **95 → 15 mm**. Заключените непокътнати; осветление 0, опаковане 0, карта
  unassigned 0, демонтаж 0. Одит **10/2/11/19**. Панелният път презчислен: **124 секции, 15.1 kg**.
  `P02` мина PROCEED, но на артефакт (капакът свършва на 385, не 420) и **не влиза в производството**.

- 2026-09-16 (local, 10): **v022 — напасване по донора, мерено срещу построеното тяло.**
  `check_statev_vs_donor.py` сравняваше спецификацията с донора и не вижда петте характерни полета;
  нов `check_donor_fit.py` мери повърхността, която съществува. Две негови мерки бяха счупени и са
  поправени преди доклад (отворът на арката мерен на самата ос; планът на донора мащабиран втори
  път, макар вече да е в mm). Три корекции в рамките на заключеното: **предно разширение 6 → 58,
  спад 620 → 900** (предната гума беше 23 mm пред каросерията при короната на арката — сега 5.1);
  **`FLANK_PULL` 0.88 → 0.95** (задното крило е overlay с 1 mm въздух над OEM обшивката).
  Нова присъда **`SCAN`** за мерки, чиято разлика е под собствената грешка на донорското число.
  Наслагването не е регресирало: средно **15 mm**, предница **3 mm**. Панели: 124 секции, 134 STL,
  0 извън плота.

- 2026-09-16 (local, 11): **тестът с отблясъците от `docs/16` е пуснат пак, вече като измерване.**
  Първият ми опит мереше удължение на изо-ленти и даде медиана **34 211:1** и PASS — топологията
  отговаряше, не формата (на loft лицата са в ринги, лента с ширина едно лице има ширина нула).
  Вярната мярка е **отношението на двете главни кривини**: 1 = сфера = балон, 0 = цилиндър = дълъг
  отблясък. Оценителят се самотества при всяко пускане (сфера 1.00, цилиндър 0.00, равнина плоска).
  Резултат върху v022: **медиана 0.31, 43% цилиндрични — MIXED.** Най-балонна е зоната на предния
  калник (0.42). Тоест силуетът съвпада до 3 mm, а повърхностите са наполовина контролирани — точно
  каквото `docs/16` предсказва за loft през сечения.

- 2026-09-17 (local, 12): **v023 — балонът е локализиран и намален.** Разбивката по X зона × Z лента
  показа, че предният калник е лош на всяка лента (най-зле Z 660–800 на 0.54), докато задното рамо
  дава 0.22 на същата логика — защото **задницата получи `flank()` на 14 септември, предницата
  никога**. Добавено поле `front_flank` (specX −700..500, Z 480..800, pull 0.82), отделна функция, за
  да не мести задницата. Предният калник **0.42 → 0.27**; цяло тяло **0.31 → 0.29**, цилиндрични
  46%. Сваляне на лентата до 380 беше опитано и отхвърлено — прави лентата под нея по-лоша (0.46 →
  0.56), рампата сама е кривина в две посоки. Страничен ефект: предната гума вече не стърчи
  (−5.1 → **+7.5 mm**), донорските CHECK-ове **4 → 3**. Силуетът непроменен (15 mm / 3 mm отпред).
  Панели: 124 секции, 117/124 едно парче, 134 STL, 0 извън плота.

- 2026-09-17 (local, 13): **v024 — етап 03 започна.** `stage03_elements.py` строи наслоените
  елементи върху ядрото: **джобове с вертикални стени и остър ръб** вместо вдлъбнатини, и **остриета
  като отделни обекти с въздух зад тях**. Първи две: страничният вход (джоб + острие 22 mm →
  `P13/P14`) и прорезът в предния калник (през горнището в арката + лайсна 14 mm → `P05/P06`).
  Всичко е **панел по панел** — елементите носят `panel_id` и минават през извличането, одита,
  пилота и производството като части. Картата научи новите джобове (`X_INTAKE`, `X_FENDER_SLOT`) и
  затваря с unassigned 0. Части 23 → **27**, одит **14 PROCEED / 2 / 11 / 15**, обшивка **13.05 m²**.
  **13 пилотни STL, 130 секции, 121/130 едно парче, 144 STL, 0 извън плота.** Заключените непокътнати.

- 2026-09-17 (local, 14): **v025 — задницата и фаровете отворени.** Същият механизъм: джоб с остър
  ръб и част, стояща в него. Задна централна маска `P34`, гнездо за номер `P36`, обрамчение на
  ауспуха `P35` (**една част** — една греда с два отвора, защото регистърът го води като една и
  преградата за свързаност би отказала две), и **фарът като острие, не кухина** — прорез през носа с
  рамка 18 mm → `P29/P30`. Нищо не е близо до `ROOF_BLOCKED` зоната. Части **27 → 32**, одит
  **19 PROCEED / 2 / 11 / 10**, обшивка **13.99 m²**. **18 пилотни STL, 147 секции, 135/147 едно
  парче, 166 STL, 0 извън плота.** За котиране: 18 части, 5.40 m², ~20.1 kg.

- 2026-09-17 (local, 15): **v026 — корпусите и каналите. BLOCKED 19 → 6.** Корпус на фара
  `P24/P25` (черупка 5 mm около `PROJECTOR` обвивката, отворена отпред — модулът не се пипа) и канал
  на входа `P31/P32` (loft през `INTAKE_INLET/DUCT/OUTLET`; формата е наша, **маршрутът е
  PROVISIONAL**, затова пада в SCAN REQUIRED). **`P37/P38 MIRROR_CAP` НЕ е построена** — в скелета
  няма кутия за огледало, значи позицията му е донорска и измислянето ѝ не е опция. Части **32 →
  36**, одит **21 PROCEED / 2 / 13 / 6**, обшивка **15.72 m²**. **20 пилотни STL, 157 секции,
  143/157 едно парче, 178 STL, 0 извън плота.** За котиране: 20 части, 5.75 m², ~21.4 kg.
  Шестте останали BLOCKED са всички зад покрива или без обвивка — **нито един не е блокиран от нещо,
  което мога да построя**.

- 2026-09-17 (local, 16): **v027 — три версии бяха пуснати, без целта да е мерена.** v024–v026
  минаха само на счетоводните проверки; наслагването и кривината не бяха пускани. Пуснати сега:
  **предницата беше регресирала 3 → 21 mm** — лайсната на канала стърчеше 75–109 mm над каросерията
  (фиксиран връх Z 974 срещу корона 865–899), а прорезът беше **яхнал гребена** при Y 470–660 и
  изяждаше 18 mm от короната. Прорезът преместен на **Y 385–545**, лайсната **следва повърхността**
  и седи 12 mm под нея. Предница обратно на **3 mm**. Процесният дефект е затворен с код:
  **`check_goal.py`** пуска двете измервания, които СА целта, сравнява със записана база и казва
  REGRESSED; кривината се предава през файл, чиято **възраст се проверява**. База: front 3.00,
  rear 21.00, mean 15.00, curvature 0.30.

- 2026-09-17 (local, 17): **v028 — `ref-05` влезе в сцената като `REF05_SIDE` в колекция
  `REF_TARGET`, на верен мащаб и ПРОВЕРЕНА числено**: пиксел (393, 491.1) → specX 0.0 / Z −0.0;
  задната главина → specX **2415.0**, точно междуосието; центърът на предното колело е 10.3 mm
  встрани, което е в записаната лента. Геометрията е **идентична на v027**.
  **Отхвърлено съзнателно:** image-to-3D подложка от `ref-05` (Hyper3D/Hunyuan остават изключени) —
  генериран меш измисля каквото не вижда и не може да се провери; и калибриране на 3/4 изгледите —
  собственикът каза, че размерите са добре, значи още размери не е отговорът.
  **Рендъри на всеки панел: НЕ** — всяка генерация е различна кола, а панел сам не дава на
  калибровката за какво да се хване. **Това, което помага, е комплект четири ортогонални изгледа на
  същата кола** (страна, отпред, отзад, отгоре) — всеки носи колела, значи собствена калибровка от
  публикуваната следа и междуосие. Планът е най-голямата сляпа зона.

- 2026-09-17 (local, 18): **v029 — планът е поправен, 5.9% → 2.3%.** Първо оттеглих собствения си
  резултат: бях нормализирал по **огледалата** — спайк при 37–41%, пет станции, ~220 mm дълъг и
  ~140 mm стърчащ, а нашата кола няма огледала. Делил съм всичко на число 18% по-голямо от истинския
  максимум, оттам и половината от „средата е пълна". Лентата вече се изключва по станция.
  Трите поправки, всичките **само в план, без Z член**, за да не мръдне силуетът: **нос** `S00–S02`
  разширени (−142 → +5 mm); **опашка** `S14` стеснен + нова станция `S13b` на 3320, защото първият
  опит преборщи 96% с 84 mm (+375 → +46 mm); **талия** ново поле `WAIST` през specX 930–1540
  (+73 → +42 mm). Среден план **22 mm на 1850 широка кола, 1.2%**. Силует непокътнат: 3 mm отпред.
  `check_goal.py` вече пази и трите числа. **20 пилотни STL, 163 секции, 184 файла, 0 извън плота.**

- 2026-09-18 (local): **v030 — картата на непрекъснатостта от `docs/16` стана машинария.** Измерено на
  v029 при specX 1200: сечението носи 794° завъртане, а 60-точковият resample доставя 524 —
  **една трета от характера се изхвърля от семплирането** — и от останалото само две места са ръбове.
  Каналът на вратата, устната му и рамото над него бяха рула от 4–13° на стъпка, разлени на 70–90 mm,
  а `docs/16` иска **G0** там. Бележката в `VOID_FIELDS` от 15 септември беше поставила диагнозата
  вярно и я беше отложила за „повърхност, която още не съществува"; тя съществува.
  `resample_anchored` + `feature_anchors`: всяка станция закотвя sample точно върху **десет**
  наименувани надлъжни линии, фиксиран брой, всяка от таблица непрекъсната по X, за да не изчезва
  котва между съседни станции — точно това счупи вътрешния ръб на buttress-а на 15 септември.
  Устната на канала се **затваря** за 18 mm вместо да избледнява (нищо не се добавя навън, значи
  1850 е недосегаема), и `trans` на задния undercut 72 → 24, защото вече е разрешим.
  **Устна 12° → 67° медиана; заден undercut 2.6–3.4° → 48.8°.** Един ръб за цялата страна, не по един
  на поле. Файл `STATEV_001_v030.blend`.

- 2026-09-18 (local, 2): **`edge_test.py` — измерването, което този проект никога не е имал.**
  Три числа описваха формата и **нито едно не вижда ръб**: силует и план сравняват контури, а
  `highlight_test.py` взима медиана по ~6000 върха — затварянето на устната вдигна ъгъла от 12° на
  74° и премести медианата с **0.01**. Тестът е **двустранен**: G0 иска 40–110°, G1 8–40°, G2 под 9°,
  и G2 линия на 40° пада толкова шумно, колкото G0 на 4°. Мери се върху построения меш след булевите.
  **6 в лента / 1 записано изключение / 0 дефекта** от 7 измерими; 12 прехода нямат таблица с
  височина и са изброени по име. Три мои грешки в самия тест намерени и поправени **преди** да бъдат
  докладвани като дефекти в колата: мерех вертикалната стена на задната арка вместо хълбока (90° и
  124°); очевидният филтър „и двете лица да носят Y" изхвърли седем от девет проби на гребена и
  обяви медиана от две проби; и бях класифицирал `FRONT_CREST` като G2, докато той е външната горна
  линия на калника, тоест G1. Добавена преграда: под 4 проби няма присъда.

- 2026-09-18 (local, 3): **`ortho_views.py` — липсващата стъпка беше цял процес.** `model_side.png` и
  `model_plan.png` са ВХОДОВЕ на две от трите измервания и до днес не идваха от нито един скрипт;
  стар PNG не пада, а сравнява старата геометрия и печата „nothing regressed". Първата ми версия
  рендърираше с авто-кадриране и `silhouette_overlay` върна **441 mm** срещу 15 — заради твърдия
  контракт (1680×560, 2.8753 mm/px, предна ос в пиксел 417.4, 521.7), не заради геометрията. Затова
  **не рендърира**: маската е измерване, а рендърът слага engine, материали, светлини и colour
  management между меша и числото. Растеризира се от върховете, контрактът се assert-ва. Проверено:
  v029 през новия път дава **точно базата 15 / 3 / 21 / 2.3 / 0.29**. `check_goal.py` вече проверява
  възрастта на четири входа и носи пета метрика `edge_defects` с допуск 0.
  Нова база: **front 4 / rear 22 / mean 16 / plan 2.4% / curvature 0.28 / edge_defects 0.**

- 2026-09-18 (local, 4): **донорските CHECK 4 → 3, и нула проблемни файлове за печат.**
  „Air over the welded quarter" даваше our skin 579 срещу donor 883 при specX 2116 — мерех **пода на
  джоба** на входа, който stage 03 реже при specX 1955–2165. Вярното е **+34 mm въздух**, присъда
  `SCAN`. Пети път измерване намира дупка и я докладва като панел. Две находки в производството:
  `plan_cuts` не си пазеше място за стената, която `thicken()` добавя след плана (310 + 20 + 4 = 334
  при 330 използваеми), и `P21` отиде от 6 на 34 секции по две парчета, защото острият undercut ръб
  кара черупката да се сгъва в решетката. Верният извод не беше да омекотя ръба, а че **файл с две
  несвързани твърдини не е част** — разделят се. **273 от 273 секции едно парче, 0 извън плота,**
  за първи път в проекта. Одит 21/2/13/6 непроменен, осветление 0, packaging непроменен.

- 2026-09-18 (local, 5): **донорските CHECK 3 → 1.** Мярката за арките докладваше желателното условие
  като проблем: сравняваше проектирания отвор с полуширината на тялото и вдигаше CHECK винаги когато
  отворът е по-широк (26.2 mm отпред, 24.8 отзад). Но режещият цилиндър на арка **трябва** да излиза
  извън обшивката, иначе остава мост през отвора; `open_w` извън обшивката е запас на инструмента, а
  видимият ръб е силуетът на тялото. Старият тест можеше да мине само ако цилиндърът се стесни,
  докато спре да реже. Заменена с мярката, която има следствие — има ли останала обшивка вътре в
  цилиндъра: **нула върха и на двете арки**, потвърдено и директно (при предната ос няма нищо под
  Z 600, при задната под Z 680). Остава един CHECK: носът +57 mm вътре в навеса на донора, извън
  ±15–30 mm лентата, значи истински — иска crash beam геометрия.

- 2026-09-21 (local): **v031 — фугите. Геометрията е непокътната** (9579 лица, 4.222 m3, заключените
  проверени), сменени са само кривите на фугите. Измерих деветте фуги срещу построената обшивка за
  първи път: **всичките са извън нея**, средно 25–152 mm, най-зле 210. Писани са на ръка на
  14 септември и повърхността е минала през v017–v030 без те да я последват. Грешното е по-тясно от
  „фугите са грешни": **равнините им са верни и са границите на панелите** — `panel_map.B` извежда
  всяка граница по име от тях и числата съвпадат; нищо не чете координатите им. Значи равнините
  носеха тежест, а кривите бяха остаряла декорация, показваща несъществуваща линия.
  Фугата вече е само намерение — `station` / `rail` / `profile` — а кривата се генерира от
  сечението. Генерирането от `ring()` обаче остави 9.7 mm средно и 56 при капака, защото *число от
  ВХОДА на лофт не е факт за изхода му* (предупреждението до `built_hw()`); затова всяка точка се
  снима с лъч върху построения меш, и **всяка страна върху собствената си половина**, защото
  тесселацията не е огледална. **0.00 mm по всичките 18 криви.**

- 2026-09-21 (local, 2): **покритие на картата 7 → 14 от 17 прехода.** Разграничението, което
  промени въпроса: класът е за ПОВЪРХНОСТТА, фугата е за ПАНЕЛИТЕ. G0 чупка на истинска кола много
  често е 4 mm процеп между две допирателни повърхности — фуга е доказателство, че светлината се
  чупи, но **не прави G1 изпълнен**, защото процепът е чупка, не преход. Трети вид доказателство:
  отвор (уста на носа, прорез на фара, уста на входа) — там светлината спира физически.
  Остават три без нищо: двата buttress прехода (BLOCKED до скан S2) и `NOSE → HOOD`, който няма
  дефинирана граница и не се запълва с измислена линия.

- 2026-09-21 (local, 3): **докладите могат да остареят, без нищо да забележи.** Тръгна от 53 mm
  разминаване в обхвата на прага; оказа се, че `manufacturing_audit.csv` е от **v026** и е оцелял
  през четири версии, докато одитът е пускан и докладван. `check_reports.py` затваря дупката общо и
  на два въпроса: съответства ли СТРОЕЖЪТ на скриптовете (sha в `data/last_build.json`, подпечатан
  от `build()`), и съответства ли всеки ДОКЛАД на строежа (mtime срещу времето на строежа). Само
  mtime не става — `git checkout` пипа скрипт, без да го променя, и всичко светва червено.
  Три доклада не се пишеха от нито един скрипт (правени веднъж с ръчно пренасочване на 14 септ.);
  още четири — само зад флаг. При презаписа **четири от седемте смениха съдържание**:
  `panel_register.txt` твърдеше 27 части / RED 11, а регистърът е **42 / RED 17** от 16 септември.
  Покрай това: `panel_registry.py` цепеше `scan_dependency_report.py` по маркер `def main(argv):`,
  какъвто там няма — значи е exec-вал целия модул, спиран само от `__main__` guard-а. Поправено.
  **Остава един стар доклад: `donor_exposure.csv`** — иска Blender, който падна по време на
  сесията; пуска се при следващото отваряне.

- 2026-09-21 (local, 4): **кривината получи адрес, а един параметричен опит падна на измерването.**
  Хълбокът Z 800–879 (0.61) беше атакуван с линейчата лента — A/B със силата като единствена
  разлика показа, че **премества** проблема: ръбът на deck-а се оправя (0.43 → 0.19), самата лента
  става по-лоша (0.61 → 0.77), зоната е нула. Махнато, числата остават в кода. Изводът е самият
  отрицателен резултат: тази лента не е достижима от поле върху цели сечения, а всички character
  полета са такива — тоест това е скулптиране, както `CLAUDE.md` казва от началото.
  Измерено и признато: **устната от v030 струва лентата над себе си** (врата Z 640–719: 0.79 с нея
  срещу 0.54 без), а медианата по тялото го скри. Устната остава — `docs/16` я иска и тя мери 67°.
  Поправка на собственото ми заключение: на по-фини ленти тази зона е 0.71–0.78 и БЕЗ устната,
  значи устната добавя ~0.13, но не я е създала.
  `highlight_test.py` вече печата **WHERE TO SCULPT** — зона × лента от 80 mm, с `flat %`, защото
  лента, която е предимно плоска, дава само преходните си върхове, а те са сферични по природа.
  Осемте цели са поименни. Геометрията е непроменена: проверено с `check_goal` по петте метрики и
  с побайтова регенерация на 273-те STL.

- 2026-09-21 (local, 5): **v032 — изглаждането по X смесваше несвързани части. Най-голямата
  единична печалба досега.** Преглед на v030: твърдях две неща и проверих едното. Котвите наистина
  са фиксиран брой (10 от 10 на всичките 91 станции). Но **разпределението на семплите се мени между
  съседни станции на 60 от 90 стъпки, до 38 семпъла разбъркване** — значи индекс k е различно място
  от ринг на ринг, а `build()` изглажда именно по индекс. Първата поправка (едно споделено
  разпределение) падна на измерването: по-лошо изглаждане и стъпка до 186 mm. Верният лост е друг —
  съседът вече е **най-близката точка** в прозорец ±6, а не същият индекс.
  Кривина **0.28 → 0.24**, цилиндрични 51%, `highlight_test` чете **PASS за първи път**, четири от
  шест зони „controlled". Обем непроменен, заключените проверени, силует и план без промяна.
  Странично: задният undercut 48.8° → 62.5°, а **прагът 47.4° → 39.7°** — влиза в G1 и конфликтът от
  `docs/14` раздел D отпада сам. **Но:** осемте най-лоши ленти са още балон и най-лошата се влоши
  (врата Z 640–719: 0.79 → 0.86). Медианата и списъкът с ленти казват различни неща и двете са верни.
  Панели: 303 от 303 секции едно парче, одит 21/2/13/6 непроменен.

- 2026-09-21 (local, 6): **v033 — ОТТЕГЛЯМ v032; геометрията е върната на v031.** Проверих
  собственото си твърдение с мярка, която не зависи от подредбата на върховете: повърхността като
  функция `y(x, z)` на фиксирана мрежа. Двете версии са **една и съща кола** (17.37 срещу 17.25 mm
  по X). Кривината падна 0.279 → 0.242, защото оценителят чете едно-пръстена на върха, а смяната ги
  подреди по посоката на повърхността. Същата грешка направих и в другото си число за v032 —
  „15.85 срещу 9.27" е втора разлика **по индекс**. Оттеглям и „прагът се разреши сам" и
  „undercut 62.5°": `edge_test` мери dihedral върху меша, значи същият артефакт. v032 струваше и
  реални неща: 2 изродени лица и най-лош скок между нормали 120.6° → 154.6°.
  **Четвърти път в проекта число от дискретизацията се докладва като факт за повърхността.**
  Затова `surface_probe.py` вече мери ungameable числото при всяко пускане и е вързано в
  `check_goal.py` като контрола: подобри ли се кривината, а `surf_*` не — повърхността не е мръднала.
  Геометрия: 9579 лица, 4.222 m3, кривина 0.28, устна 66.9°, undercut 48.8°, праг 47.4° (изключението
  пак важи), 273 от 273 секции едно парче.

- 2026-09-21 (local, 7): **разлагане 2×2 на v030 — сменил съм три неща наведнъж и съм приписал
  общия резултат на всяко от тях.** Устната: clip-ът сам дава **68.0°** и с обикновения resample,
  котвите добавят ~2 — твърдението стои, това е дизайнерска промяна. Undercut: обосновката е
  **невярна** — „2.6–3.4°" е от 15 септември върху v017 геометрия; при trans 72 и обикновен resample
  ръбът вече дава 47.1°. `trans` 24 остава, но защото при включени котви дава 44.4 срещу 36.3 (седем
  проби, слабо число). Котвите: не устната и не undercut-а, а **прагът** — 12.2° срещу 47.7°. Полето
  му е 10 mm преход, а семпъл на ~38 mm не може да го покаже; котвите **разкриха** ръб, който
  дизайнът винаги е имал. Значи прагът чете 47° защото вече се вижда, не защото е изострен —
  въпросът към теб в `docs/14` D стои, но вече се знае какво точно се решава.

- 2026-09-21 (local, 8): **v034 — `edge_test` показва и дизайна до меша, и намери моя регресия.**
  Загубата от представяне (дизайн минус меш) излезе най-голяма на **предния гребен: 38.6 срещу 55.2,
  тоест 16.6° не се показват**. Причината: `resample_anchored` няма snap-а на локалните максимуми от
  `resample` (струваше 2.1 mm средно), а гребенът е двуточкова черта 26×30 mm при семплиране на 38.
  Верният лек е **котва** — бях го пропуснал, защото се долепя след `pts`. Сега: **52.0° при дизайн
  55.5, загубата 11.3 → 3.5**, обем непроменен, 279 от 279 секции едно парче.
  **Находка, не дефект:** 52° е извън G1, но дизайнът винаги е бил 55.5 — линията стана видима, не
  по-остра. Това е **същият въпрос като прага**, и е един: две от G1 линиите на `docs/16` са
  проектирани на ~50°; или лентата 8–40 е твърде тясна за такъв език, или и двете са по-твърди от
  спецификацията. Изчаква твоето решение; нищо не е пипано.
  Контролата `surf_x_mm` скочи 17.37 → 19.15 и `check_goal` го обяви REGRESSED — правилно: добавен
  семпъл в ъгъл наистина мени повърхността. Причината е записана и базата е обновена.

- 2026-09-21 (local, 9): **v035 — одитирах собствената си контрола и тя имаше два бъга.**
  `surface_probe.py` взимаше първото пресичане след сортиране по Z, а сечението не е монотонно по Z
  (гребен, после корона) — при specX −333 върна полуширина 31.5 mm там, където съседите дават 511 и
  730. И преградата за почти хоризонтална повърхност искаше двете съседни проби да съществуват,
  значи семпъл под 10 mm от върха не се тестваше. Заедно: средното надуто ~4 пъти, най-лошото ~15.
  `|d²y/dx²|` е **4.71**, не 17.37. **Оттеглям всяко `surf_*` число отпреди поправката и двете
  присъди REGRESSED.** Премерени наново, гребенът и обединеният долен ръб са неутрални за
  повърхността (разлики под 0.05 при допуск 1.0).
  Геометрия: долният ръб вече е **една** котвена двойка вместо две (прагът свършва на 1820,
  undercut-ът почва на 2260, но и двете се слагаха навсякъде и се изтласкваха). Резултат:
  **undercut 46.5 → 69.5°, праг 46.1 → 49.8° при дизайн 49.6.** 248 от 248 секции едно парче.
  Поуката: **контрола, която никой не одитира, е просто още едно число за вярване.**

- 2026-09-21 (local, 10): **край до край: сглобявам обратно отпечатаните файлове и меря колата.**
  Дотук всяка мярка за форма беше върху ТЯЛОТО, а се строят 248 секции; между тях стоят шест
  операции и никоя не беше проверявана. Първо липсваше самата възможност: `lay_flat` запичаше
  трансформацията и я хвърляше, тоест **файловете нямаха адрес по колата**. Сега я връща и
  `placement.json` я носи. `assembly_check.py` дели въпроса на два:
  **веригата е вярна** — върху повърхност с файлове медиана **0.00 mm**, 99-и персентил 2.49,
  **99.4% в 8 mm**; **колата не е цяла** — покритие 35.5%.
  После: **10.9 m² форма, която е наша, изобщо не се произвеждаше.** Трите причини за SCAN REQUIRED
  не са едно и също — overlay (външната форма е наша), мърдаща граница (формата е наша), и обем на
  сгъване на покрива (формата НЕ е наша). Първите две вече излизат като **SHAPE ONLY** в отделна
  директория, не в пакета за доставчик. Покритие **35.5% → 76.2%**.
  Намерен и дефект по заключен размер: **ядрото излизаше 3.5 mm извън 925.** Първото ми обяснение
  (обърнати нормали) беше вярно като наблюдение, но **не беше причината** — `face_outward()` не
  промени нищо. Проследено стъпка по стъпка на `P15`: повърхност 925.00 → стена на панела 925.00 и
  нула отворени ръба → рязане 925.21 → **второ удебеляване 928.14.** Всяка секция се удебеляваше
  втори път, само за да се затворят срезовете, а `solidify` не знае, че го молят да запуши дупка:
  строи втора стена и на външната повърхност я строи навън. Заменено с `cap_cuts()`.
  **Проверено: ширина 1856.9 → 1851.1 при заключени 1850**, остатъкът 0.55 mm на страна е езичето.
  Точност непроменена (медиана 0.00 mm, 99.4% в 8 mm). `face_outward()` остава — нужна е за първото
  удебеляване — но не беше решението.

- 2026-09-21 (local, 11): **одит на отпечатаните файлове — никой не ги беше отварял.**
  `print_qc.py` ги чете както слайсерът: затворено ли е, манифолд ли е, положителен ли е обемът.
  Първо одитирах одитора — квантоването беше в „метри" върху файлове в милиметри, тоест под шума на
  float32 — и той броеше един дефект два пъти.
  **Оттеглих `cap_cuts` същия ден:** беше по-лошо от това, което замени (13 отворени ръба,
  352 non-manifold, безсмислен обем срещу 0 и 16). Поправил бях 3.5 mm, като счупих телата.
  Верният ред: **реже се повърхността, стената се слага веднъж на ниво секция** — затваря по
  построение, върви навътре, външното лице остава на проектната повърхност. P01 секция
  924 837 → 460 478 cm³. **Поправка на собствената ми първа формулировка:** докладваната маса НЕ е
  била завишена (смята се от панела, който винаги е с една стена) — завишен е бил **материалът,
  който файловете щяха да изядат**, около два пъти.
  **349 от 417 дефектни → 105 от 315**, и остатъкът е само non-manifold ръбове. Проследен е до
  `solidify`; два лека са опитани и отхвърлени с числа (`NON_MANIFOLD` режим взривява P01 до 1711 mm;
  сливане по разстояние не мърда нищо). **Не е поправен — следваща задача.**
  Сглобяване: ширина **1852.2 при заключени 1850**, точност непроменена (медиана 0.00 mm,
  99.4% в 8 mm), покритие 76.2%.

- 2026-09-21 (local, 12): **файловете за печат са чисти, 8 дефектни от 497** (беше 349 от 417).
  Non-manifold ръбовете се проследиха до **прищипнат връх** — броят им съвпада едно към едно
  (P01 2 и 2, P21 9 и 9, P07 0 и 0). Две площи, съединени в точка, не са една част и биха се
  разпаднали; разделят се. И два файла излизаха **обърнати наопаки** (обем −700.9 cm³): за
  затворено тяло знакът на обема е точният тест, не радиалната догадка — но поправката трябваше да
  е **след** разделянето на парчета, не преди. Остават 8 файла с по 1–11 ръба, друг механизъм,
  неатакуван днес.
  Сглобяване: 497 файла, ширина 1852.2 при заключени 1850, медиана 0.00 mm, 99.4% в 8 mm,
  покритие 76.2%.

- 2026-09-21 (local, 13): **v036 — стопът съществува за първи път.** `docs/14` го заключва като
  тънко широко острие с L-образни краища; обвивките бяха в скелета от 14 септември, `check_lighting`
  ги отчиташе като заградени, но **нищо не беше изрязано** — `check_packaging` ги чете 115.5 mm ПОД
  повърхността. Построен по модела на фара: прорез + корпус с 5 mm стена и 6 mm въздух, отворен
  назад, всички числа от LOCKED обвивките. Първият ми L-образен корпус излезе на две несвързани
  парчета (union на два ОТВОРЕНИ shell-а не свързва) — поправено чрез обединяване на затворените
  кутии преди изваждането. **Одит 21/2/13/6 → 23/2/13/4.**
  **P23 REAR_SPOILER не се строи:** обвивката му е 125.7 mm ВЪТРЕ в тялото — ducktail-ът вече е в
  профила на опашката, значи P23 е въпрос към регистъра, не към моделирането.
  505 файла, 11 дефектни (2%), покритие 76.7%, осемте метрики плоски.

- 2026-09-26 (local): **лявата и дясната страна се режеха различно.** `P07` даваше 34 секции,
  `P08` — 18, при идентични мешове и идентичен план. Клетката взима езичето само в ПОЛОЖИТЕЛНАТА
  посока на оста, а тя е абсолютна — отляво стига навън, отдясно навътре. Дясната секция вече е
  **огледало** на лявата, както `panel_map` вече прави за извличането. **12 от 12 двойки съвпадат**,
  и ширината на сглобеното пада **1852.2 → точно 1850.0**: оттеглям записаното на 21 септември, че
  остатъкът е „езичето по дизайн".
  **`fit_test.py`:** твърдо ограничение 6 има съдържание — панел, избран от данните
  (`P39 ROCKER_END_L`, 0.080 m², 3 секции, зад задното колело), шест допускания, които един печат
  проверява, шест ориентира за шублер и линия, четири етапа на мерене, и мащабът вместо измислен
  допуск. 531 файла, 11 дефектни (2%), покритие 76.7%, осемте метрики плоски.

- 2026-09-26 (local, 2): **28% от секциите са люспи — измерено, диагностицирано, НЕ поправено.**
  149 от 531 са под 40 mm, 68 под 20. Причината е геометрична: 3D решетка върху тънка извита
  черупка оставя ъглова отломка във всяка клетка, която черупката само докосва. Опитът да ги слея
  направи **311 → 623 секции**; грешката беше в събирането на езичето (приемаше лице срещу коя да е
  клетка от групата вместо срещу външната ѝ граница). Върнато, находката е записана в кода.
  Истинският лек вероятно е рязане по двете повърхностни посоки на черупката, не по световните оси.

- 2026-09-26 (local, 3): **ревю и документ за печатницата.** Поправена неточност в записа за
  люспите (причината за провала на сливането **не е установена**; по-вероятен е механизмът с
  острова, не езичето). `fit_test` ориентирите вече са само върху външната повърхност.
  `03_PRINT/README.md` се **генерира** от `handoff.json` (решения + бройки от производствения
  пробег) и от резултата на `print_qc` — не на ръка, за да не остарява. 531 файла, 11 дефектни,
  ширина точно 1850.0, осемте метрики плоски, 23 доклада current.

- 2026-09-26 (local, 4): **люспите — истинската причина беше моят `split_pinch`, не решетката.**
  Проследено етап по етап на P21: рязането дава 3 люспи, удебеляването — 45. `split_pinch`
  откъсваше едно-две лица при прищипване и `solidify` ги правеше призмички. Записът, който
  обвиняваше решетката, е поправен. Три промени, всяка премерена: ветрило под 600 mm² се изтрива;
  тестът брои ветрила, не гранични ръбове (папийонката се хваща, non-manifold → 0); малко-но-реално
  ветрило остава закачено вместо да стане люспа. **Секции 531 → 422, люспи под 40 mm 149 → 59.**
  Точност и ширина непроменени. 13 файла с non-manifold (3%) — цената на третото правило.

- **Текуща база: `02_DESIGN/exterior/STATEV_001_v036.blend`. Откат: v035.**
  Авторитетни източници: геометрия — `statev_master_volumes.py` (v030.blend е регенерируем от него);
  измервания — `check_goal.py` (силует, план, кривина, ръбове) и
  `04_ENGINEERING/reports/edge_test.txt`; решения — `docs/09-decision-log.md`;
  заключени визуални решения — `docs/14-locked-visual-decisions.md`. Всеки доклад с версия в
  името е исторически и НЕ е текущ.
- Next: **решение по прага** (`docs/14` раздел D — 47° при G1 лента 8–40; или лентата е твърде
  тясна, или преходът се връща на ~18 mm). После `NOSE → HOOD` — единственият преход без каквото и
  да е доказателство, който НЕ е блокиран от скана; границата му е в `SECTIONS` S00–S03 и местенето
  ѝ е дизайнерско решение, не поправка. И **етап 02 — реални повърхности по зони**, patch-базирани
  по `docs/16`, при спазена карта на непрекъснатостта 5×G0 / 10×G1 / 2×G2. Това е единственото, което стои между регистъра от 38
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
- `02_DESIGN/exterior/` — `.blend` files, **one per version of the whole car**
  (`STATEV_001_v031.blend`), plus `EXPERIMENT_*_UNAPPROVED.blend` for A/B runs.
  Commit at every finished stage. *(This line said "one per panel family —
  front_clamshell.blend, rear_deck.blend" until 2026-09-21 and neither file has ever
  existed. The plan changed at v001 and the note did not: the body is ONE parametric
  build and panels are extracted from it by `panel_extract.py`, so a panel is a region
  of the model, not its own file. `check_docs.py` found it.)*
- `03_PRINT/` — STL/3MF split for the printer + a PDF exploded view per panel:
  part number, print orientation, material, infill. Ask the printer for build
  volume before splitting. 3–4 mm walls, tongue-and-groove alignment keys.
- `04_ENGINEERING/` — clearance checks, tyre envelope, roof fold path, lamp
  positions.
- **Преди да цитираш число от доклад — и преди комит — пусни двете проверки.**
  `python3 01_CAD/scripts/check_goal.py` казва дали силуетът, планът, кривината и ръбовете са
  мръднали спрямо записаната база. `python3 01_CAD/scripts/check_reports.py` казва дали строежът
  отговаря на скриптовете и дали всеки доклад отговаря на строежа. На 21 септември един доклад
  беше на четири версии назад и твърдеше 27 части вместо 42 — беше пускан, но не записван.
  Доклад с версия в името е исторически и не се проверява.
  **И правилото, което струва най-скъпо всеки път, когато го забравя:** число, прочетено от меша —
  кривина, dihedral, втора разлика по индекс — се мени, когато върховете се преподредят, без формата
  да е мръднала. Преди да обявиш подобрение на повърхността, виж дали `surf_x_mm` / `surf_z_mm` са го
  потвърдили. Ако не са, подобрил си мярката, не колата.
  `python3 01_CAD/scripts/check_docs.py` проверява дали всеки път, посочен в `CLAUDE.md` и
  `docs/*.md`, съществува. Той намери, че този файл е описвал структура на `02_DESIGN/exterior/`,
  която никога не е съществувала. Проверява СЪЩЕСТВУВАНЕ, не истинност на изречението.
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
