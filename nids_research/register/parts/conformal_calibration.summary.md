# Stage 1 discovery summary: conformal + calibration (prefix CP)

- Rows: 36 (CP-001 to CP-036). 31 are from 2024–2026; 5 are FOUNDATIONAL_PRE2024 (CP-007, CP-015, CP-020, CP-023, CP-027).
- Priority: 11 at P1, 21 at P2, 4 at P3.
- Full text: 31 DOWNLOADED (all confirmed PDFs over 50 KB in `nids_research/pdfs/CP-*.pdf`). 3 PAYWALLED: CP-001 EnCP (IEEE Xplore), CP-004 ConFID (Elsevier), CP-036 Pal et al. TDSC. 2 OA_NOT_RETRIEVED: CP-003 HTCCA (Springer CC-BY, blocked by a JavaScript client challenge) and CP-005 (MDPI, HTTP 409 bot protection). These two are open access and can be fetched manually.

## Must-check items
- EnCP (CP-001): confirmed via Crossref. IEEE S&P 2026, pp. 156–174, DOI 10.1109/SP63933.2026.00043. No arXiv or author PDF found, so marked PAYWALLED.
- Robust Conformal IDS, arXiv 2609.19241 (CP-002): confirmed. Single author, Zhenpeng Li. Submitted to TDSC. The arXiv date (2026-07-22) does not match the 2609 ID. Downloaded.
- ConFID (CP-004): authors now confirmed via Crossref: Farsimadan, Moradi, Palmieri. Internet of Things 40:102078 (2026). Paywalled.
- FIRCE (CP-006): arXiv 2605.01962, accepted at IEEE SmartNets 2026 according to the arXiv comment. Proceedings DOI not found. Downloaded.
- C-PP-COAD, arXiv 2505.01783 (CP-014): authors now confirmed: Farzaneh and Simeone. Preprint. Downloaded.
- Hybrid conformal abstention paper (CP-003): FOUND. Muhammad Zeeshan Younas, "Operationally calibrated open-world zero-day intrusion detection using hybrid conformal abstention", Journal of Computer Virology and Hacking Techniques 23, article 4. Published online 2026-11-09, open access, DOI 10.1007/s11416-026-00692-3. The Crossref abstract confirms the method name HTCCA and the figure of 19.6% UNKNOWN-only detection at 1% FPR with entropy. The 30.6% figure is still UNVERIFIED because the abstract was truncated.

## Venues covered
IEEE S&P; ICLR 2024 and 2025; ICML 2024 and 2025 (PMLR 235/267); NeurIPS 2021 and 2024; JMLR; Annals of Statistics; Annals of Applied Statistics; JASA; JRSS-B; NEJSDS; IEEE TDSC; Journal of Computer Virology and Hacking Techniques; Internet of Things (Elsevier); MDPI Applied Sciences; IEEE SmartNets; arXiv.

## Searches run
- arXiv API: ID lookups; title/abstract queries for conformal+intrusion, Neyman–Pearson classification, and selective/abstention with guarantees.
- Crossref bibliographic queries for: HTCCA, ConFID, EnCP, Pal TDSC, the Annals of Statistics, JRSS-B, JASA and AoAS items, NP classification, and CPS conformal false alarm.
- Unpaywall OA checks.
- PMLR v235/v267 index scans for conformal, selective, outlier, FDR and e-value titles.
- JMLR page and ICLR proceedings (via web search).
- Web searches for the HTCCA title, EnCP, ConFID, conformal NIDS with FPR guarantees, and conformal drift for malware/IDS.
- DBLP, Semantic Scholar (rate-limited) and OpenReview (challenge) were unusable.

## Known gaps
- 30.6% HTCCA figure unverified. HTCCA and CP-005 PDFs need manual download.
- EnCP certificate form unread (paywalled). No preprint found.
- CP-020 (ACI, NeurIPS 2021) venue was not re-confirmed on a proceedings page in this session.
- Not registered, as candidates for later: the 2026 Reliability Engineering & System Safety conformal false-alarm paper for CPS (not re-located in Crossref); HADAR-UAV (conformal Deep SVDD); Kalan & Kpotufe 2024 NP rates (arXiv 2402.09560, venue unknown); Liang/Ren/Chen 2602.16537 online CP training-conditional regret (this is the paper project notes called "DriftOCP", but the arXiv title differs); Zhenpeng Li 2608.05199; Tong et al. NP umbrella (Sci. Adv. 2018); TRANSCEND (USENIX Sec 2017); Tibshirani et al. weighted CP 2019; PMLR v267 items such as "Model Uncertainty Quantification by CP in Continual Learning" and "Enhancing Adversarial Robustness with CP".
- No 2024–2026 top-security-venue NIDS paper found that gives a conformal FPR guarantee under drift or poisoning. The closest are CP-002 (preprint), CP-003/CP-004 (minor journals) and EnCP (generic, not NIDS).
