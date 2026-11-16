"""Stage 2 pre-check: verify every DOWNLOADED PDF in the frozen Stage 1 register.

For each row with fulltext_status == DOWNLOADED it checks that
  1. the file exists and `file` identifies it as a PDF,
  2. `pdfinfo` reports a page count,
  3. `pdftotext` extracts a non-trivial amount of text (written to ../pdfs_text/<id>.txt),
  4. the registered title matches the first two pages: the share of the title's distinctive
     words (length > 3) found there.
Writes progress/pdf_integrity.csv and prints a summary. The frozen register is only read.
PDFs are treated as untrusted data: they are only passed as arguments to poppler tools.
"""
import csv
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "register", "frozen", "corpus_register_stage1.csv")
TXT = os.path.join(ROOT, "pdfs_text")
OUT = os.path.join(ROOT, "progress", "pdf_integrity.csv")
os.makedirs(TXT, exist_ok=True)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=180)


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3]


rows = list(csv.DictReader(open(REG, encoding="utf-8")))
out = []
for r in rows:
    if r["fulltext_status"] != "DOWNLOADED":
        continue
    pid, pdf = r["paper_id"], os.path.join(ROOT, r["local_pdf"])
    rec = {"paper_id": pid, "title": r["title"], "year": r["year"], "priority": r["priority"],
           "exists": "N", "is_pdf": "N", "pages": "", "text_chars": "", "title_match": "",
           "verdict": ""}
    if os.path.isfile(pdf):
        rec["exists"] = "Y"
        rec["is_pdf"] = "Y" if "PDF document" in run(["file", "-b", pdf]).stdout else "N"
        m = re.search(r"Pages:\s+(\d+)", run(["pdfinfo", pdf]).stdout)
        rec["pages"] = m.group(1) if m else ""
        txt_path = os.path.join(TXT, pid + ".txt")
        run(["pdftotext", "-layout", pdf, txt_path])
        full = open(txt_path, encoding="utf-8", errors="replace").read() if os.path.exists(txt_path) else ""
        rec["text_chars"] = str(len(full))
        first = run(["pdftotext", "-l", "2", pdf, "-"]).stdout.lower()
        tw = words(r["title"].split("(")[0]) or words(r["title"])
        hit = sum(1 for w in tw if w in first)
        rec["title_match"] = f"{hit / len(tw):.2f}" if tw else ""
    ok = (rec["exists"] == "Y" and rec["is_pdf"] == "Y" and rec["pages"]
          and int(rec["text_chars"] or 0) > 5000)
    tm = float(rec["title_match"] or 0)
    rec["verdict"] = ("OK" if ok and tm >= 0.6 else
                      "CHECK_TITLE" if ok else
                      "UNREADABLE" if rec["exists"] == "Y" else "MISSING")
    out.append(rec)

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()), quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows(out)

from collections import Counter
inw = [o for o in out if o["year"] in ("2024", "2025", "2026")]
print("DOWNLOADED rows checked:", len(out), "| verdicts:", dict(Counter(o["verdict"] for o in out)))
print("2024-2026 rows:", len(inw), "| verdicts:", dict(Counter(o["verdict"] for o in inw)))
for o in out:
    if o["verdict"] != "OK":
        print(o["verdict"], o["paper_id"], o["pages"], o["text_chars"], o["title_match"], "|", o["title"][:80])
