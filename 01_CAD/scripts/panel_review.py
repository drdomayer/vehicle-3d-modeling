"""
panel_review.py — every registered part, one row: how it compares with the render and what it
still needs before the shop can print it. Writes docs/19-panel-by-panel.md.

    python3 01_CAD/scripts/panel_review.py

The FACTS come from the reports (register, audit, print schedules) and from the STL files
themselves (closed or not, read here the way print_qc reads them), so they cannot go stale while
the reports are current. The COMPARISON with ref-09 and the poster is written by hand in NOTES,
because no number says "the vent has five slats in the render and four on the car"; each note
names what matches, what differs, and who can close it. Written 2026-10-02 at the owner's request
for a panel-by-panel review against the render, ready for print.
"""
import collections
import csv
import os
import struct

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REP = os.path.join(REPO, "04_ENGINEERING", "reports")
OUT = os.path.join(REPO, "docs", "19-panel-by-panel.md")

# (match, differs, who closes it) per part, against ref-09 and the poster (ref-10 once saved)
NOTES = {
    "P01": ("нос като кутия с фаска, централна уста, ъглови джобове, DRL в канал на предния ръб",
            "рендерът е силно фасетиран: V-образни черни входове с остри ръбове, лицето е от равнини; "
            "нашето лице е гладко с правоъгълни отвори",
            "скулптиране на лицето (ти) или етап 02"),
    "P28": ("карбонова устна под устата, по цялата ширина", "в рендера има крайни пластини", "дребно, мое"),
    "P41": ("огледало на P28", "като P28", "дребно, мое"),
    "P43": ("рамка в устата с печатна шестоъгълна мрежа, гланцово черна (v058)",
            "в рендера клетките са по-ситни", "готово; купешка мрежа влиза в същата рамка"),
    "P54": ("шестоъгълна решетка в ъгловия вход, наклонена с фаската", "като рендера", "готово"),
    "P55": ("огледало на P54", "като P54", "готово"),
    "P56": ("шестоъгълна решетка в задния ъглов вент", "като рендера", "готово"),
    "P57": ("огледало на P56", "като P56", "готово"),
    "P02": ("капакът е купол между гребените, без ръб по оста", "в рендера двата вента са по-близо до "
            "стъклото и по-големи", "shape-only: край при cowl-а е донорски (скан)"),
    "P03": ("гребен на 780, стена + плато, ширина 1850", "в рендера калникът е по-остър и плаващ "
            "над арката", "shape-only: задният край е донорската врата (скан)"),
    "P04": ("огледало на P03", "като P03", "като P03"),
    "P05": ("шест диагонални ламели в отвор към арката (v059)", "в рендера отворът е трапец и е "
            "по-напред; нашият стои навътре от гребена (v027)", "готово"),
    "P06": ("огледало на P05", "като P05", "като P05"),
    "P07": ("карбоново острие на прага с подрез", "рендерът има плоска карбонова пола", "готово"),
    "P08": ("огледало на P07", "като P07", "готово"),
    "P39": ("ъгълът на прага зад задното колело, тест панел за печат", "—", "готово; от v055 по-малък"),
    "P40": ("огледало на P39", "—", "готово"),
    "P09": ("вратата навън от донора до 918 с канал", "рендерът има голяма вдлъбната повърхност, "
            "която се издига към scoop-а; нашата талия е вътре в OEM вратата (docs/14 I)",
            "твое решение по страната + скан"),
    "P10": ("огледало на P09", "като P09", "като P09"),
    "P11": ("обрамчение на входа, предният ръб наклонен назад", "scoop-ът в рендера е много по-голям; "
            "нашият е ограничен от донорския отвор 1900–2080", "рязане на OEM панела = твое решение"),
    "P12": ("огледало на P11", "като P11", "като P11"),
    "P13": ("карбоново острие 22 mm в устата, пред арката", "в рендера острието е извито и по-високо",
            "мое, дребно"),
    "P14": ("огледало на P13", "като P13", "като P13"),
    "P31": ("канал от устата към пленума, следва кожата отвътре", "скрит", "маршрут: скан"),
    "P32": ("огледало на P31", "скрит", "маршрут: скан"),
    "P15": ("стена до 800 и плато на нивото на deck-а", "в рендера хълбокът е по-гладък, без купол",
            "скулптиране (ти) / скан за покрива"),
    "P16": ("огледало на P15", "като P15", "като P15"),
    "P17": ("платно 40 mm навън от предполагаемия обем на покрива", "в рендера е по-тънко и по-високо",
            "скан S2"),
    "P18": ("огледало на P17", "като P17", "скан S2"),
    "P19": ("—", "в рендера deck с ламели", "скан S2 (обем на покрива)"),
    "P42": ("—", "като P19", "скан S2"),
    "P20": ("—", "в рендера 6 големи ламели на капака на двигателя", "скан S2"),
    "P33": ("—", "като P20", "скан S2"),
    "P21": ("плоска задна плоскост с прорез за стопа и L-краища, номер в гнездо, два кръгли ауспуха",
            "в рендера долната част е черна и стопът е по-тънък; надписът STATEV е значка",
            "решение за значката (ти)"),
    "P22": ("карбонов дифузьор: тунел между два крака от v055", "в рендера тунелът е по-дълбок",
            "мое: по-стръмен под, ако дълбочината трябва"),
    "P44": ("перка в тунела, долният ръб на линията на краката", "по 3 на страна от v059, като рендера",
            "готово"),
    "P45": ("огледало на P44", "като P44", "като P44"),
    "P46": ("външна перка в тунела", "като P44", "като P44"),
    "P47": ("огледало на P46", "като P44", "като P44"),
    "P58": ("трета, крайна перка на Y 390", "като рендера", "готово"),
    "P59": ("огледало на P58", "като P58", "готово"),
    "P24": ("корпус около 90 mm модул, следва кожата отвътре", "скрит", "готово"),
    "P25": ("огледало на P24", "скрит", "готово"),
    "P26": ("корпус около стопа с L-край, следва кожата отвътре", "скрит", "готово"),
    "P27": ("огледало на P26", "скрит", "готово"),
    "P60": ("значка STATEV на 2 mm подложка в черната лента (v060)", "като рендера", "готово"),
    "P61": ("карбонова крайна пластина на сплитера под ъгловия вход (v060)", "като рендера", "готово"),
    "P62": ("огледало на P61", "като P61", "готово"),
    "P37": ("—", "огледала в рендера", "позиция на огледалото: донор или купешко (ти)"),
    "P38": ("—", "като P37", "като P37"),
}


def read(name):
    p = os.path.join(REP, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stl_clean(path):
    """Closed, manifold, consistently wound, positive volume -- print_qc's OWN check, imported, so
    this table and the print QC can never disagree (a looser rounding here first called P01
    unclean while print_qc read it clean)."""
    qc = {"__file__": os.path.join(REPO, "01_CAD/scripts/print_qc.py"), "__name__": "_qc"}
    with open(qc["__file__"], encoding="utf-8") as f:
        exec(f.read().split("\ndef main(")[0], qc)      # the functions only, not its run
    r = qc["check"](path)
    return (not r.get("empty") and not r.get("unreadable") and r.get("holes", 1) == 0
            and r.get("nonmanifold", 1) == 0 and r.get("winding", 1) == 0
            and r.get("volume_cm3", 0) > 0)


def main():
    bom = {r["ID"]: r for r in read("panel_bom.csv")}
    audit = {r["PANEL"]: r for r in read("manufacturing_audit.csv")}
    files = collections.defaultdict(list)
    for tier, rows in (("за лепене", read("print_schedule.csv")), ("shape-only", read("shape_only_schedule.csv"))):
        for r in rows:
            files[r["PANEL"]].append((tier, r))
    lines = ["# 19 — Панел по панел: сравнение с рендера и готовност за печат", "",
             "*Генерира се от `01_CAD/scripts/panel_review.py`. Не се пише на ръка: фактите идват от "
             "регистъра, одита, графиците за печат и самите STL файлове; сравнението с ref-09 е в "
             "`NOTES` в скрипта.*", "",
             "Колони: **финиш** (боя / карбон / гланцово черно / скрит), **присъда** от одита, "
             "**файлове** (брой, всички затворени ли са, побират ли се в референтния плот 1800×600×1800), "
             "**размер** на най-голямото парче в mm, после какво съвпада с рендера, какво се различава и "
             "кой може да го затвори.", ""]
    groups = collections.OrderedDict()
    for pid, b in bom.items():
        groups.setdefault(b["DESIGN_GROUP"], []).append(pid)
    tot = collections.Counter()
    for grp, pids in groups.items():
        lines += [f"## {grp}", "",
                  "| част | име | финиш | присъда | файлове | размер mm | съвпада | различава се | затваря |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for pid in pids:
            b, a = bom[pid], audit.get(pid, {})
            fl = files.get(pid, [])
            if fl:
                paths = [os.path.join(REPO, r["FILE"]) for _, r in fl]
                clean = sum(stl_clean(p) for p in paths)
                fits = sum(r["FITS_BED"] == "yes" for _, r in fl)
                big = max(fl, key=lambda t: float(t[1]["X_MM"]) * float(t[1]["Y_MM"]))[1]
                ftxt = f"{len(fl)} {fl[0][0]}, {clean}/{len(fl)} чисти, {fits}/{len(fl)} в плота"
                stxt = f"{float(big['X_MM']):.0f}×{float(big['Y_MM']):.0f}×{float(big['Z_MM']):.0f}"
                tot["files"] += len(fl)
                tot["clean"] += clean
                tot["parts_with_files"] += 1
            else:
                ftxt, stxt = "няма файл", "—"
            m, d, w = NOTES.get(pid, ("?", "?", "?"))
            lines.append(f"| {pid} | {b['NAME']} | {b.get('FINISH', '?')} | {a.get('VERDICT', '?')} | "
                         f"{ftxt} | {stxt} | {m} | {d} | {w} |")
        lines.append("")
    lines += ["## Сума", "",
              f"- Части в регистъра: **{len(bom)}**; с файл за печат: **{tot['parts_with_files']}**.",
              f"- Файлове: **{tot['files']}**, затворени и манифолд: **{tot['clean']}**.",
              "- Без файл и защо: скан S2 (deck, капак на двигателя, ламели, платната са shape-only), "
              "огледала (няма позиция).", ""]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  {len(bom)} parts, {tot['parts_with_files']} with files, {tot['files']} files, "
          f"{tot['clean']} clean\n  wrote {OUT}")


if __name__ == "__main__":
    main()
