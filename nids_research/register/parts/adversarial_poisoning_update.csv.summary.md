# Stage 1 discovery summary: adversarial / poisoning / update_security (prefix AP)

- Rows: 30 (AP-001 to AP-030). 28 are from 2024-2026 (93%). 2 are FOUNDATIONAL_PRE2024: AP-015 BARS (NDSS 2023) and AP-018 Chen et al. (USENIX Sec 2023).
- DOWNLOADED: 28. Each was checked as a real PDF over 50 KB, and its title page was matched against the registered title and authors.
- PAYWALLED: 2. AP-026 EnCP (S&P 2026) and AP-027 Stealthy Label-Inversion Drifts (RAID 2025) have only IEEE Xplore copies; no open copy was found.
- Priority 1: AP-001, 002, 003, 004, 006, 009, 014, 024, 026. Priority 2: 13 rows. Priority 3: 8 rows.

## Must-check items
| Item | Status |
|---|---|
| NetMasquerade (NDSS 2026) | AP-001, DOWNLOADED |
| PANTS (USENIX Sec 2025) | AP-002, DOWNLOADED |
| Host-space perturbations (AsiaCCS 2026) | AP-003, DOWNLOADED (arXiv); DOI confirmed via Crossref |
| PCAP-Backdoor | AP-004, DOWNLOADED (arXiv) |
| Constrained network adversarial attacks | AP-005, DOWNLOADED (arXiv) |
| Test-Time Poisoning (S&P 2024) | AP-006, DOWNLOADED (arXiv) |
| Persistent Backdoor Attacks in CL (USENIX Sec 2025) | AP-007, DOWNLOADED |
| Entente (NDSS 2026) | AP-008, DOWNLOADED |
| McFadden et al. (ACSAC Workshops 2024) | AP-009, DOWNLOADED (UCL author version) |
| Contorter (S&P 2026) | AP-010, DOWNLOADED (author PDF) |
| LogInject (USENIX Sec 2026) | AP-011, DOWNLOADED; context only |
| AIOpsDoom (USENIX Sec 2026) | AP-012, DOWNLOADED; context only |
| DeepRed | **FOUND**: AP-013, DOWNLOADED (USENIX proceedings PDF) |

Notes on corrected or new metadata:
- **PCAP-Backdoor** was published as "PCAP-Backdoor: Backdoor Generator in Network Traffic for Intrusion Detection Systems", ACM Transactions on Cyber-Physical Systems (2026), DOI 10.1145/3805033, with 4 authors. Two given names are UNVERIFIED. The arXiv version has 2 authors and a different title.
- **Constrained network adversarial attacks** was published at IEEE DCOSS-IoT 2025.
- **DeepRed:** Hajizadeh, Golchin, Nowroozi, Rigaki, Valeros, Garcia, Conti and Bauschert, "DeepRed: A Deep Learning-Powered Command and Control Framework for Multi-Stage Red Teaming Against ML-based Network Intrusion Detection Systems", USENIX WOOT 2025. Its abstract states "reduce detection rates by up to 20%", which matches the external report.

## Venues covered
- Top-4 security: NDSS 2023/2025/2026, USENIX Security 2023/2024/2025/2026, IEEE S&P 2024/2026.
- Other security venues: RAID 2024/2025, AsiaCCS 2026, ACSAC Workshops 2024, USENIX WOOT 2025, ESORICS 2024 workshops, TrustCom 2025, DCOSS-IoT 2025, ACM TCPS.
- ML venues: CVPR 2024, ICLR 2025, ESANN 2025.

## Searches run
- Seed lists: the project's prior report and the adversarial notes.
- Web searches:
  - DeepRed
  - Entente PDF
  - McFadden active-learning poisoning
  - LogInject
  - NIDS poisoning under drift and retraining
  - backdoors in traffic classifiers at top-4 venues
  - contaminated benign training for network anomaly detection
  - Stealthy Label-Inversion
  - test-time adaptation poisoning and defences
  - continual-learning poisoning
  - Adaptive Arms Race
  - XAI-explanation attacks on NIDS
  - Strategic Games, BARS, EnCP and SketchFeature PDFs
- Other lookups:
  - RAID 2025 proceedings table of contents (proceedings.com)
  - S&P 2026 accepted-papers list
  - Crossref API title and DOI lookups for venue confirmation
  - USENIX Security 2026 presentation pages

## Known gaps
- **Attacks on NIDS update loops:** none were found. No 2024-2026 top-venue paper directly attacks a NIDS retraining, active-learning or pseudo-labelling loop with network traffic. The closest evidence is:
  - malware: AP-009 and AP-017
  - generic ML: AP-006, AP-020, AP-021, AP-007 and AP-030
  - an attackable loop named but not tested: AP-024
- **Not registered:** "Mangiacapre et al." (IFIP Networking 2026, XAI-guided NIDS evasion). The IFIP PDF returned 403, and the authors and title could not be confirmed. Candidate for follow-up.
- **Not systematically browsed:** CCS 2024-2025, EuroS&P, TDSC/TIFS and AsiaCCS 2024/2025 tables of contents were only covered through searches. Crossref rate-limited (HTTP 429) near the end.
- **Supplementary marked UNKNOWN:** CVF supplementary material (AP-019, AP-021) and some proceedings were not checked.
- **Unclear threat model:** AP-027 may or may not model an adversarial label-inversion; its abstract was not read.
- **Other leads not registered** because of the row target:
  - FLANDRE (arXiv 2607.25439, federated NIDS under contamination)
  - Self-contained data cleaning (arXiv 2611.10856)
  - Mia & Pritom XAI attacks (arXiv 2510.03623)
  - Catillo et al. (ICISSP 2026)
  - HDDAF (Lara 2025)
  - Li/Akil/Bertino (arXiv 2604.06599)
  - Robust conformal ID (arXiv 2609.19241)
  - Beyond RTT (NDSS 2026)
  - CoLD (NDSS 2026)
  - MineShark (NDSS 2025)
