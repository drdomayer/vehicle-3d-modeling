"""
check_docs.py — does the prose point at things that exist?

WHY IT EXISTS. On 2026-09-21 three reports turned out to be orphans: CLAUDE.md and the decision log
named a script as "the output of" a file that no script wrote, so the file sat for a week looking
like live data. That is not a one-off. On 2026-09-16 the same shape of thing was found the other way
round — CLAUDE.md named ref-07 and ref-08 as the visual authority and neither image was in the repo.
A document that points at something that is not there is worse than one that says nothing, because
it is believed.

Nothing in this project checked prose against the filesystem. Code has check_goal, check_reports and
the freeze rule; the documents that TELL you what to run had nothing at all.

WHAT IT CHECKS. Every backticked path in CLAUDE.md and docs/*.md that looks like a repo path or a
file, against the filesystem. Globs are expanded and count as satisfied if anything matches.

WHAT IT CANNOT DO, and this is the larger half: it checks that a path EXISTS, not that the sentence
around it is true. "scan_dependency_report.py writes scan_dependency.txt" passes as soon as both
files exist, whether or not the first writes the second. That one needed a human reading the code.

    python3 01_CAD/scripts/check_docs.py
"""

import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS = ["CLAUDE.md"] + sorted(glob.glob(os.path.join(REPO, "docs", "*.md")))

# A backticked token counts as a path if it has a directory in it or a known extension. Prose in
# this repo also backticks identifiers -- ring(), FLANK_PULL, G0 -- and those are not paths.
DIRS = ("01_CAD/", "02_DESIGN/", "03_PRINT/", "04_ENGINEERING/", "07_PRESENTATION/", "docs/",
        "data/")
EXTS = (".py", ".blend", ".png", ".jpg", ".jpeg", ".md", ".csv", ".txt", ".stl", ".json", ".3mf")

# The decision log is excluded, with the reason, rather than silently. By its own rule -- "не трий
# стари редове" -- it records what was true on a date, so it legitimately names files that have
# since been replaced: boundary_sensitivity.py became donor_exposure.py on 2026-09-16 and the entry
# that says so must keep the old name. A history that only mentions things that still exist is not
# a history.
SKIP_DOC = {"docs/09-decision-log.md": "a log records what was true on a date; dead names belong"}


def expand(tok):
    """Shell-style {a,b} in prose is one sentence about several files, not a glob."""
    m = re.search(r"\{([^{}]*)\}", tok)
    if not m:
        return [tok]
    out = []
    for part in m.group(1).split(","):
        out += expand(tok[:m.start()] + part + tok[m.end():])
    return out


def looks_like_path(tok):
    if tok.endswith("()") or "(" in tok or " " in tok or tok.startswith("."):
        return False
    if any(tok.startswith(d) for d in DIRS):
        return True
    return tok.endswith(EXTS) and not tok.isupper()


def main():
    print("=" * 84)
    print("DOC LINKS — every path the prose points at, against the filesystem")
    print("=" * 84)
    missing, ok, seen = [], 0, set()
    skipped = 0
    for doc in DOCS:
        rel_doc = os.path.relpath(doc, REPO)
        if rel_doc in SKIP_DOC:
            skipped += 1
            continue
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        for tok in re.findall(r"`([^`\n]{3,120})`", text):
            tok = tok.strip().rstrip(".,;:")
            if not looks_like_path(tok):
                continue
            key = (rel_doc, tok)
            if key in seen:
                continue
            seen.add(key)
            for one in expand(tok):
                # "docs/16" is how this repo refers to docs/16-surface-behaviour.md in prose, so a
                # docs reference with no extension is matched as a prefix.
                pats = [os.path.join(REPO, one), os.path.join(REPO, "01_CAD", "scripts", one)]
                if one.startswith("docs/") and not one.endswith(".md"):
                    pats.append(os.path.join(REPO, one + "*"))
                if "/" not in one:
                    pats += [os.path.join(REPO, "docs", one), os.path.join(REPO, "**", one)]
                if any(glob.glob(p, recursive=True) for p in pats):
                    ok += 1
                else:
                    missing.append((rel_doc, one))
    by_doc = {}
    for d, t in missing:
        by_doc.setdefault(d, []).append(t)
    for d in sorted(by_doc):
        print(f"\n  {d}")
        for t in sorted(set(by_doc[d])):
            print(f"    MISSING  {t}")
    print(f"\n  {ok} paths resolve, {len(missing)} do not, {skipped} document(s) skipped "
          f"(listed in SKIP_DOC with a reason)")
    if missing:
        print("\n  A document that points at something that is not there is worse than one that says")
        print("  nothing, because it is believed. Either the file is missing or the prose is stale;")
        print("  both are worth one minute each.")
    print("\n  It checks that a path EXISTS, not that the sentence around it is true.")
    return 1 if missing else 0


sys.exit(main())
