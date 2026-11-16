# Stage 1 discovery summary: guarantees + encrypted (prefix GE)

- Rows: 35 (GE-001 to GE-035). 26 rows (74%) are from 2024 to 2026. 9 rows are pre-2024 (2019 to 2023) and are flagged FOUNDATIONAL_PRE2024 where relevant.
- DOWNLOADED: 30. Each was checked as a real PDF over 50 KB at `nids_research/pdfs/GE-xxx.pdf`.
- PAYWALLED / no open copy: 5.
  - GE-016 tFusion, CCS 2025
  - GE-017 MM4flow, CCS 2025
  - GE-018 CCS 2025 dynamic network conditions
  - GE-019 TrafficFormer, S&P 2025
  - GE-020 EnCP, S&P 2026. Neither arXiv nor IEEE Xplore was checked for this one, and fulltext_url is UNVERIFIED.
- Priority 1 rows:
  - CertTA
  - Colossus (PQC drift)
  - RAID 2024 TLS1.2→1.3 C2
  - RAPIER
  - Robust Conformal IDS (arXiv 2609.19241)
  - CCS 2025 dynamic-conditions classifier
  - EnCP
  - Gibbs & Candès (JMLR 2024)
  - Angelopoulos et al. (ICML 2024)
  - Bashari et al. (ICML 2025, contaminated reference data)

## Venues covered
USENIX Security, IEEE S&P, ACM CCS, NDSS, RAID, SIGCOMM, IMC (accepted), INFOCOM, IWQoS, ICML (2019/2024/2025), NeurIPS (2022/2023/2024), ICLR 2022, COPA 2024 (PMLR), JMLR, Annals of Statistics, Information and Inference, NEJSDS, Foundations and Trends in Statistics, Infocommunications Journal, and arXiv preprints.

## Searches and sources used
- Seeds came from the prior Stage 1 report and `encrypted_pq_traffic.md`. Each was re-confirmed on a primary page.
- arXiv API, by id and by title search: CertTA, BARS, RAPIER, MM4flow, TrafficFormer, the TLS 1.3 C2 paper, ECH, QUIC lateral movement, RS-Del, EnCP, conformal+contaminated, and DoH malicious/tunnel.
- Official CCS 2025 accepted-papers JSON, filtered for traffic/encrypted/certified/conformal.
- S&P 2026 accepted list (EnCP).
- NDSS 2026 accepted list, filtered for encrypted, TLS, QUIC and conformal. Nothing new for these categories.
- EuroS&P 2026 accepted page. The QUIC lateral-movement paper was not found there, so it was not registered.
- Proceedings indexes: PMLR v230, v235 and v267, and JMLR v25.
- Crossref, for the AoS, IMA, NEJSDS and FnT venues.
- Zhuotao Liu group page (MM4flow, TrafficFormer, CCS 2025 #558).
- Web search on tFusion, MM4flow, and ECH impact on detection.

## Known gaps
- ACM DL returns 403 to curl, so the three CCS 2025 traffic papers have no full text. tFusion's numbers exist only in a secondary source.
- EnCP has no open copy, so its certificate form is still unverified.
- ECH/DoH coverage is thin. The only ECH detection paper found is GE-035, in a non-target journal. There are no 2024–2026 DoH malicious-traffic papers at the target venues; arXiv searches came back empty.
- "QUIC-Aware Lateral Movement Detection" (EuroS&P 2026) was not registered because it could not be confirmed on a primary page.
- Robust statistics and impossibility work is limited to the conformal/OOD literature: Barber et al. limits, Fang et al., and contaminated-calibration papers GE-027 and GE-034. Not registered:
  - COLT-style lower bounds for learning under adversarial or Huber contamination (e.g., the targeted-poisoning optimal-learning line)
  - high-dimensional robust-estimation results (Diakonikolas–Kane)
  - arXiv 2610.15458 (split-conformal interval length under Huber contamination)
- Change-point / ARL coverage is limited to e-detectors (GE-030) and Podkopaev & Ramdas (GE-032). The backward-confidence-sequence change detection paper (arXiv 2302.02544) was identified but not registered.
- Supplementary=Y/N is based on a count of "appendix" mentions in the extracted text, not a manual check.
- Several venues rest on the arXiv comment only and the proceedings page was not opened: Jeary (NeurIPS 2024), MalMoE (INFOCOM 2026), Podkopaev (ICLR 2022), Mind the Gap (IMC 2026), and Fang (NeurIPS 2022).
- Note for other workers: the scratchpad is shared, and another worker overwrote my `add.py`. My scripts are now in the scratchpad's `ge_worker/` folder.
