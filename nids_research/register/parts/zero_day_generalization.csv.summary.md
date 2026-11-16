# Stage 1 discovery summary: zero_day + generalization (prefix ZD)

- Rows: 30 (ZD-001 to ZD-030). Priority 1: 7, priority 2: 14, priority 3: 9.
- Years 2024–2026: 25 of 30 (83%). Pre-2024 rows: netFound (arXiv, first posted 2023, v5 in 2026), plus four FOUNDATIONAL_PRE2024 rows: CADE, HyperVision, Corsini & Yang OOD-for-NIDS, Talpini et al. UQ.
- Peer-reviewed: 20. Preprints: 10.
- DOWNLOADED: 27. Every one was checked with `file`, is larger than 50 KB, and is stored in `nids_research/pdfs/ZD-xxx.pdf`.
- PAYWALLED: 3.
  - ZD-006 NIDP (RAID 2025). The computer.org PDF returns "Unauthorized" and no arXiv copy was found.
  - ZD-007 TrafficFormer (S&P 2025). Only the IEEE CSDL copy exists.
  - ZD-029 HDSE-IDS (Connection Science). It is CC BY-NC open access, but T&F returned 403 to automated download.

## Must-check competitors
| Competitor | ID | Status |
|---|---|---|
| KnowML (EuroS&P 2026) | ZD-001 | arXiv v2; acceptance stated in the arXiv comment |
| TIPSO-GAN (NDSS 2026) | ZD-002 | Official PDF |
| PANDORA (NDSS 2026) | ZD-003 | Official PDF |
| Mateen (RAID 2024) | ZD-004 | Author PDF |
| netFound | ZD-005 | arXiv only. No peer-reviewed venue found |
| NIDP (RAID 2025) | ZD-006 | Paywalled. DOI 10.1109/RAID67961.2025.00053. The program page and Crossref disagree on the author list (Han Zhu; Chenyang vs Chengyang Mo) |
| TrafficFormer (S&P 2025) | ZD-007 | Paywalled. DOI 10.1109/SP61157.2025.00102 |
| Cantone et al. (IEEE Access 2024) | ZD-008 | arXiv copy |

- KAIROS-style novelty claims: not registered. KAIROS-type work is host provenance, not network, so it does not meet the network-relevance condition.
- Cross-domain study reporting an ensemble drop of ~50% and an LSTM drop of ~30.4%: **NOT FOUND.**
  - I ran four web searches (exact-phrase and paraphrase) and checked candidates. Hakim et al. (arXiv 2607.00553, ZD-019) does not contain "30.4". Almuhanna & Dardouri (Frontiers in AI 2025) does not contain these figures.
  - None of the 30 downloaded PDFs contains "30.4" in its text.
  - HDSE-IDS (ZD-029) is the closest unverified candidate: a cross-domain stacked ensemble with LSTM baselines. Its abstract does not state these figures, and its full text could not be fetched.
  - I did not substitute a similar paper.

## Venues covered
NDSS (2023, 2024, 2026), RAID (2024, 2025), IEEE S&P 2025, EuroS&P 2026, USENIX Security (2021, 2024), ACM CCS 2026 (accepted per arXiv), NeurIPS 2025, DAC 2025, IEEE CNS 2023, IEEE TNSM, IEEE TVT, Computers & Security, IEEE Access, Connection Science, MDPI Applied Sciences, and arXiv.

## Searches run
- arXiv API:
  - id lookups for the prior-report seeds
  - abstract searches for "open-set" + "intrusion detection"
  - abstract searches for "out-of-distribution" + intrusion detection / network traffic
  - abstract searches for cross-dataset, cross-domain, domain adaptation or domain generalization + intrusion detection
  - title searches for NIDP and TrafficFormer
- Crossref title lookups: NIDP, TrafficFormer, Zero-X, CND-IDS, Corsini, HDSE.
- Official pages: RAID 2025 program, NDSS paper pages, USENIX presentation page, the TrafficFormer author page, and the ACSAC 2024/2025 paper lists.
- Web searches: the ensemble 50% / LSTM 30.4% study (4 variants), NIDP, TrafficFormer, HyperVision, and CCS/AsiaCCS/USENIX 2025 unknown-attack traffic detection.

## Known gaps
- I did not systematically scan the CCS 2024/2025, AsiaCCS, SIGCOMM, NSDI, CoNEXT, INFOCOM, NOMS, IMC, ICML/ICLR/KDD/AAAI, TDSC, TIFS or Computer Networks lists. The ACSAC 2024 page returned only a stub.
- Candidates seen but not registered:
  - ACSAC 2025 "R+R: From Claims to Crashes" (graph NIDS re-evaluation). Its link to arXiv 2503.20281 is unconfirmed.
  - "Lightweight Dynamic Open-Set IDS for IIoT" (TIFS 2025, DOI 10.1109/TIFS.2025.3546849, unverified).
  - Medoid Prototype Alignment for cross-plant unknown attacks (arXiv 2604.25544).
  - FBID (arXiv 2608.04073).
  - TAO-Net (arXiv 2512.15753).
  - Lens NFM (arXiv 2402.03646).
  - NetVAD (arXiv 2606.01452, IEEE ISI).
  - The 2026 Frontiers mini-review on joint cross-dataset / unknown-attack evaluation (exact title not confirmed).
  - The RAID 2025 label-inversion drift paper (drift worker's scope).
- Venue/DOI confirmations still pending:
  - KnowML, CCS 2026 FreqMix (ZD-020): acceptance comes from arXiv comments; no proceedings DOI yet.
  - ZD-018: venue unstated.
  - HyperVision DOI: taken from a search snippet.
- `supplementary` is mostly UNKNOWN. It is Y only where appendix headings were found in the PDF text.
