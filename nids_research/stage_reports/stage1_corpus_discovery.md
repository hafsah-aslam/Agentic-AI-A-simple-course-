# Stage 1 — Corpus discovery: end-of-stage report

Hypothesis under test (not an established gap): *Can an adaptive NIDS maintain reliable detection of
unseen attacks and controlled false alarms under temporal distribution shift when an adversary can
manipulate the observations or the model-update process?*

## 1. What was completed

Six discovery passes, one per pair of categories, each following `register/DISCOVERY_PROTOCOL.md`:
identify the original publication, confirm title/authors/venue/year on a primary page (publisher,
proceedings, arXiv, Crossref), and attempt to download the complete PDF. Full text was counted as
available **only** when a real PDF (> 50 KB) was written to `pdfs/` and its title page matched.
The six part-registers were merged and de-duplicated (`register/merge_register.py` →
`register/corpus_register.csv`).

| Register part | Rows | Downloaded | Not downloaded |
|---|---|---|---|
| zero_day + generalization (ZD) | 30 | 27 | 3 |
| drift + continual (DC) | 34 | 28 | 6 |
| conformal + calibration (CP) | 36 | 31 | 5 |
| adversarial + poisoning + update_security (AP) | 30 | 28 | 2 |
| guarantees + encrypted (GE) | 35 | 30 | 5 |
| evaluation (EV) | 34 | 32 | 2 |
| **Total rows** | **199** | | |

After de-duplication (same paper registered by several passes, plus two near-duplicates merged by
hand: RAPIER GE-008 = EV-022; TESSERACT 2019 DC-021 = its 2024 extended version EV-019):

| | Count |
|---|---|
| Unique papers registered | **164** |
| — 2024–2026 corpus | **140** |
| — foundational / pre-2024 (not counted toward the corpus) | 24 |
| 2024–2026 papers with full text DOWNLOADED | **123** |
| 2024–2026 papers paywalled | 13 |
| 2024–2026 papers open access but not retrievable by script | 4 |
| 2024–2026 peer-reviewed / preprint | 108 / 32 |
| 2024–2026 priority 1 / 2 / 3 | 41 / 66 / 33 |

**Number of papers fully examined (Level A): 0.** Stage 1 only registers and verifies access; every
row is evidence level C. Level A begins in Stage 2.

Category coverage of the 2024–2026 corpus (a paper may carry several tags): zero_day 27,
generalization 22, drift 49, continual 26, conformal 26, calibration 26, adversarial 27,
poisoning 20, update_security 17, guarantees 27, encrypted 18, evaluation 49. Every category meets
the 10–20 target except that encrypted (18) and update_security (17) are at the low end.

## 2. Sources of the "second report" claims (identity only — claims NOT yet audited)

| Second-report item | Register id | Identity found | Full text |
|---|---|---|---|
| CLEAR | DC-011 | Fathima, Khraisat, Ibrahim, Li, *Knowledge-Based Systems* 352:116878 (2026), DOI 10.1016/j.knosys.2026.116878; SSRN preprint 10.2139/ssrn.5490606 (2025) | **PAYWALLED** — none of the six reported figures can be checked yet |
| Cross-domain study (ensemble −~50 %, LSTM −~30.4 %) | — | **NOT FOUND** after four searches; no substitute registered. Nearest unconfirmed candidate HDSE-IDS (ZD-029, *Connection Science* 2025) — its abstract does not contain the figures | ZD-029 paywalled/blocked |
| DeepRed | AP-013 | Hajizadeh et al., USENIX WOOT 2025; abstract states detection rates reduced "by up to 20%" | Downloaded |
| Hybrid conformal abstention (HTCCA) | CP-003 | M. Z. Younas, *J. Computer Virology and Hacking Techniques* 23:4 (2026), DOI 10.1007/s11416-026-00692-3, CC-BY | Open access but blocked by a JavaScript challenge — **needs manual download**. The abstract confirms the 19.6 % entropy figure at 1 % target benign FPR; 30.6 % not yet seen |
| Strategic selection and forgetting in continual NIDS | DC-010 | SSF, IEEE INFOCOM 2025, DOI 10.1109/infocom55648.2025.11044615 | Downloaded |
| Drift-Aware Continual Generative Behavioral Detection | DC-012 | DC-GenAIS, Alhalangy & Eltayeb, MDPI *Information* 17(9):852 (2026) | Open access but HTTP 403 — **needs manual download** |
| CADE (original) | DC-020 | Yang et al., USENIX Security 2021 (foundational) | Downloaded |
| Deep-learning NIDS surveys | EV-012, EV-026–030 | six surveys registered, tagged "SURVEY — for reference discovery only" | Downloaded |

## 3. Findings supported by evidence at this stage (metadata level only)

These are observations about *what was found where*, not claims about paper content:

1. **Conformal guarantees for NIDS appear only outside the top security venues.** The NIDS-specific
   conformal papers found are a preprint (CP-002), two smaller-journal papers (CP-003, CP-004) and an
   MDPI paper (CP-005). EnCP (AP-026, S&P 2026) is generic ML and its certificate is unread because
   the paper is paywalled.
2. **The relevant statistical machinery exists in ML venues.** The register holds online conformal
   under arbitrary shift (CP-018, JMLR 2024; CP-019, ICML 2024), poisoning of conformal prediction
   (CP-010, ICML 2024), poisoning-robust conformal (CP-009, ICLR 2025) and conformal outlier detection
   with contaminated reference data (CP-028, ICML 2025). Stage 4 must test whether these already
   answer most of the hypothesis.
3. **Update-loop attacks** on NIDS specifically were not found by any pass; the closest are on
   malware (AP-009, DC-007, DC-008), test-time adaptation (AP-006) and generic continual learning.
   This remains a metadata-level signal until Stage 2 reads these papers.

## 4. Unresolved questions and limitations

- **Access.** 17 papers (13 of them in 2024–2026) could not be downloaded. Six of the 41 priority-1
  papers are among them: EnCP, NIDP, Label-Inversion Drifts, the CCS 2025 dynamic-conditions paper,
  ConFID, and both open-access calibration papers CP-003/CP-005. ACM DL, IEEE Xplore and Elsevier
  refused automated access; MDPI and Springer blocked scripted downloads.
- **Coverage.** DBLP, Semantic Scholar and OpenReview blocked automated access, so venue tables of
  contents were not systematically browsed for EuroS&P, ACSAC main track, AsiaCCS, TDSC, TIFS, TNSM,
  Computers & Security, Computer Networks, or for continual/test-time-adaptation work at
  NeurIPS/ICML/ICLR. The earlier proceedings sweeps (`research_notes/…/sweep_*.md`) partially cover
  the security venues.
- **Metadata to re-check in Stage 2:** venues stated only in arXiv comments (KnowML EuroS&P 2026,
  Retrofit USENIX Sec 2026, EV-011 CCS 2026, ZD-020 CCS 2026, FIRCE SmartNets 2026); NIDP author list
  (program page and Crossref disagree); the arXiv-vs-published equivalence of EV-008 ("R+R"), Huynh
  et al. EV-004, and PCAP-Backdoor AP-004 (title and author list changed on publication).
- The `supplementary` field was set partly by searching PDF text for "appendix"; treat it as approximate.
- Non-standard status values from two passes (BLOCKED_403, FAILED_DOWNLOAD, NOT_DOWNLOADED,
  OA_NOT_RETRIEVED) are kept as written; all mean "not on disk".

## 5. Work remaining and whether Stage 2 is justified

**Stage 2 is justified.** 123 downloaded 2024–2026 papers exceed the 100-paper minimum available for
full-text reading, and 35 of the 41 priority-1 papers are on disk.

Proposed reading order:
1. the 35 downloaded priority-1 papers;
2. the 66 priority-2 papers;
3. priority-3 papers as needed to pass 100 Level-A papers.

Each Level-A record goes to `extractions/<paper_id>.md` using the section-5 template (A–G) of the
master instruction. A paper is marked Level A only if every listed section was located.

**Manual help that would materially improve the investigation** (publisher blocks prevent scripted
download; upload the PDFs if you have access):
- CP-003 hybrid conformal abstention (open access, Springer) — needed for the Stage 3 audit
- DC-012 DC-GenAIS (open access, MDPI) — needed for the Stage 3 audit
- DC-011 CLEAR (Elsevier) — needed for the Stage 3 audit
- AP-026 EnCP (IEEE S&P 2026) — closest conformal + poisoning competitor
- DC-026 NIDP and AP-027 Label-Inversion Drifts (RAID 2025, IEEE)
- CP-005 target-FPR calibration (open access, MDPI) and CP-004 ConFID (Elsevier)
- GE-018 CCS 2025 dynamic-conditions encrypted-traffic paper (ACM)
