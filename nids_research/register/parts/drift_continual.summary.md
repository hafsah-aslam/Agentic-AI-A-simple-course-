# Stage 1 discovery summary: drift + continual (prefix DC)

CSV: `drift_continual.csv`. It has 34 rows, all at evidence level C. IDs run DC-001 to DC-034, but DC-027 sits between DC-026 and DC-028 in the file rather than in numeric order.

- **Years:** 26 rows are from 2024–2026 (76%). 8 rows are FOUNDATIONAL_PRE2024: CADE, TESSERACT, Transcend, Transcending Transcend, OWAD, INSOMNIA, Chen et al. USENIX'23, and Kuppa'22.
- **Priority:** 8 rows are priority 1, 17 are priority 2 and 9 are priority 3.
- **Full-text status:**
  - DOWNLOADED: 28. Each file was checked as a PDF over 50 KB and stored in `nids_research/pdfs/DC-xxx.pdf`.
  - PAYWALLED: 4.
    - DC-009, label-inversion drifts, RAID'25 (IEEE).
    - DC-011, CLEAR, KBS (Elsevier); the SSRN preprint also returned 403.
    - DC-018, ReCDA, KDD'24. Unpaywall lists an ACM open-access copy, but ACM DL returns 403 to curl.
    - DC-026, NIDP, RAID'25 (IEEE).
  - BLOCKED_403: 1. DC-012, DC-GenAIS, is CC BY open access, but MDPI and preprints.org both returned 403.
  - FAILED_DOWNLOAD: 1. DC-025, INSOMNIA. The connection to the s2lab host was reset through the proxy. A uniba repository preprint exists but was not tried.

## Must-check items
| Item | Result |
|---|---|
| CADE | DC-020, the original USENIX Security 2021 paper. Downloaded and registered as FOUNDATIONAL_PRE2024. |
| TESSERACT | DC-021, foundational. |
| Transcend | DC-022, foundational. |
| Transcending Transcend | DC-023, foundational. |
| DREAM | DC-002, CCS 2025, DOI confirmed. |
| Li et al. NDSS 2025 | DC-003. |
| Retrofit | DC-001. USENIX Security 2026, per the arXiv comment; the USENIX page was not checked. |
| ADAPT | DC-004, RAID 2025, confirmed in the TOC and in Crossref. |
| Label-Inversion Drifts | DC-009, RAID 2025. Confirmed, but paywalled. |
| Aurora | DC-005. |
| Fernández-Barrios | DC-006. |
| Li/Akil/Bertino | DC-007. |
| OWAD | DC-024. |
| INSOMNIA | DC-025. |
| "CLEAR" | FOUND as DC-011: Fathima, Khraisat, Ibrahim and Li, Knowledge-Based Systems 2026, plus an SSRN 2025 preprint. The external report's numbers (F1 ~0.89, FPR ~0.08, zero-day ~88%, forgetting -24%, 17–22 ms, <40 MB) are UNVERIFIED because no abstract or full text could be retrieved. |
| "strategic selection and forgetting" | FOUND as DC-010, SSF, IEEE INFOCOM 2025. |
| "Drift-Aware Continual Generative Behavioral Detection" | FOUND as DC-012, DC-GenAIS, MDPI *Information* 17(9):852, 2026. |

## Venues covered
- Security: USENIX Security (2017, 2019, 2021, 2023, 2026), IEEE S&P (2022, 2024), ACM CCS 2025, NDSS (2023, 2025), RAID (2024, 2025), ACSAC Workshops 2024 and AISec 2021.
- Networking: INFOCOM 2025 and PACMNET/CoNEXT 2026.
- ML and other venues: KDD 2024, DAC 2025, Knowledge-Based Systems and MDPI *Information*.
- arXiv preprints: 12.

## Searches run
- The RAID 2025 proceedings TOC (proceedings.com), with keyword grep.
- arXiv API queries:
  - "concept drift" + "intrusion detection"
  - "continual learning" + "intrusion detection"
  - drift + malware + poisoning
  - test-time adaptation in the security domain
  - test-time poisoning
  - TESSERACT and ReCDA by name
- Crossref, Semantic Scholar and Unpaywall lookups for venue, DOI and open-access status.
- Web searches for each must-check item, for CLEAR and DC-GenAIS, for USENIX 2025 malware drift work, and for NIDS drift papers in TIFS and TDSC.

## Known gaps
- DBLP was blocked by a bot challenge, so venue tables for EuroS&P, ACSAC main track, AsiaCCS, TDSC, TIFS, TNSM, Computers & Security and Computer Networks were not swept systematically. No drift/continual NIDS paper from those venues is registered, which is a coverage gap.
- I did not search NeurIPS, ICML or ICLR systematically for continual or test-time adaptation methods. Only Cong et al. (S&P'24, test-time poisoning) represents adversarial TTA.
- Seen but not registered:
  - MORPH, arXiv 2401.12790.
  - Kalný et al., arXiv 2604.22629.
  - Sabbah et al., arXiv 2605.24294.
  - CITADEL, arXiv 2508.19450.
  - "Quantifying Catastrophic Forgetting in IoT IDS", arXiv 2603.00363.
  - Future Internet 2025, continual IDS (10.3390/fi17100456).
  - Mathematics 2026, MMD + coresets (10.3390/math14142595).
  - "Deep Continual Learning Framework for Zero-Day NIDS Under Concept Drift", SSRN 6538249.
  - FedPromptZero, Internet of Things 2026.
  - Cantone et al., IEEE Access 2024. This is cross-dataset work and belongs to the generalization category.
- Unconfirmed venue facts:
  - Retrofit's USENIX 2026 acceptance comes only from the arXiv comment.
  - Several arXiv rows may have later venues that I did not check.
- I flagged supplementary material automatically by detecting "appendix" in the second half of the PDF text. Treat these values as approximate.
