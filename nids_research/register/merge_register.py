"""Merge the per-category Stage 1 registers into one de-duplicated corpus register.

Usage:  python3 merge_register.py
Reads   parts/*.csv  (schema in ../README.md)
Writes  corpus_register.csv  and prints a status summary.

De-duplication key: normalised title (lower-case, alphanumerics only). When the same paper
appears in several parts, categories are unioned, the best full-text status is kept, the
lowest (most important) priority is kept, and all source paper_ids are recorded in `notes`.
"""
import csv
import glob
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["paper_id", "title", "authors", "year", "venue", "venue_type", "peer_reviewed",
          "doi_or_url", "fulltext_url", "fulltext_status", "local_pdf", "supplementary",
          "categories", "priority", "closest_competitors", "notes", "evidence_level"]
STATUS_RANK = {"DOWNLOADED": 0, "ACCESSIBLE_NOT_DOWNLOADED": 1, "PAYWALLED": 2, "NOT_FOUND": 3}


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def main():
    merged = {}
    bad = []
    for path in sorted(glob.glob(os.path.join(HERE, "parts", "*.csv"))):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if not row.get("title"):
                    bad.append((os.path.basename(path), row.get("paper_id")))
                    continue
                row = {k: (row.get(k) or "").strip() for k in FIELDS}
                key = norm_title(row["title"])
                if key not in merged:
                    merged[key] = row
                    continue
                cur = merged[key]
                cats = set(filter(None, cur["categories"].split(";"))) | \
                       set(filter(None, row["categories"].split(";")))
                cur["categories"] = ";".join(sorted(cats))
                if STATUS_RANK.get(row["fulltext_status"], 9) < STATUS_RANK.get(cur["fulltext_status"], 9):
                    for k in ("fulltext_url", "fulltext_status", "local_pdf"):
                        cur[k] = row[k]
                try:
                    cur["priority"] = str(min(int(cur["priority"] or 9), int(row["priority"] or 9)))
                except ValueError:
                    pass
                cur["notes"] = (cur["notes"] + f" | also registered as {row['paper_id']}").strip(" |")

    rows = sorted(merged.values(), key=lambda r: (r["priority"], r["year"], r["title"]))
    with open(os.path.join(HERE, "corpus_register.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    in_window = [r for r in rows if r["year"] in ("2024", "2025", "2026")
                 and "FOUNDATIONAL_PRE2024" not in r["notes"]]
    print(f"unique papers: {len(rows)}   (2024-2026 corpus: {len(in_window)}, "
          f"foundational/older: {len(rows) - len(in_window)})")
    print("full-text status (all):", dict(Counter(r["fulltext_status"] for r in rows)))
    print("full-text status (2024-2026):", dict(Counter(r["fulltext_status"] for r in in_window)))
    print("peer reviewed (2024-2026):", dict(Counter(r["peer_reviewed"] for r in in_window)))
    print("priority (2024-2026):", dict(Counter(r["priority"] for r in in_window)))
    cat = Counter(c for r in in_window for c in r["categories"].split(";") if c)
    print("category coverage (2024-2026):", dict(sorted(cat.items())))
    if bad:
        print("rows skipped (no title):", bad)


if __name__ == "__main__":
    main()
