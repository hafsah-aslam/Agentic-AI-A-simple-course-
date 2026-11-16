"""Rebuild the Stage 2 progress register from the evidence on disk.

Counts come ONLY from extraction files that exist (`extractions/<paper_id>.md`) and their
front-matter `status:` field — never from logs or memory — so a paper is reported as read only
if its record exists. Writes progress/progress_register.csv and prints the counts.
"""
import csv
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "register", "frozen", "corpus_register_stage1.csv")
ADD = os.path.join(ROOT, "register", "stage2_additions.csv")
OUT = os.path.join(ROOT, "progress", "progress_register.csv")

rows = list(csv.DictReader(open(REG, encoding="utf-8")))
if os.path.exists(ADD):
    rows += list(csv.DictReader(open(ADD, encoding="utf-8")))


def front(path):
    meta = {}
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        meta[k.strip()] = v.split("#")[0].strip()
    return meta


ext = {}
for p in glob.glob(os.path.join(ROOT, "extractions", "*.md")):
    pid = os.path.basename(p)[:-3]
    if pid in ("TEMPLATE", "READING_PROTOCOL") or pid.startswith("_"):
        continue
    ext[pid] = front(p)

out = []
for r in rows:
    pid = r["paper_id"]
    e = ext.get(pid, {})
    st = e.get("status", "").upper()
    if st in ("FULL", "PARTIAL"):
        state = st
    elif r["fulltext_status"] == "DOWNLOADED":
        state = "UNREAD"
    else:
        state = "UNAVAILABLE"
    in_window = r["year"] in ("2024", "2025", "2026") and "FOUNDATIONAL_PRE2024" not in r["notes"]
    out.append({"paper_id": pid, "title": r["title"], "year": r["year"], "priority": r["priority"],
                "in_2024_2026_corpus": "Y" if in_window else "N", "state": state,
                "pages_read": e.get("pages_read", ""), "pages_total": e.get("pages_total", ""),
                "extraction_file": f"extractions/{pid}.md" if e else ""})

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()), quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows(out)

from collections import Counter
win = [o for o in out if o["in_2024_2026_corpus"] == "Y"]
print("2024-2026 corpus:", len(win), dict(Counter(o["state"] for o in win)))
print("foundational/pre-2024:", len(out) - len(win), dict(Counter(o["state"] for o in out if o not in win)))
orphans = sorted(set(ext) - {o["paper_id"] for o in out})
if orphans:
    print("extraction files with no register row:", orphans)
print("FULL-TEXT (Level A) papers in 2024-2026 corpus:", sum(o["state"] == "FULL" for o in win))
