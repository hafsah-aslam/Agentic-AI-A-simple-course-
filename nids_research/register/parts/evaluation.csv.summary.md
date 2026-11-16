# Stage 1 discovery summary: `evaluation` (prefix EV)

## Counts
- Rows: 34 (EV-001 to EV-034). 32 are from 2024–2026; 2 are FOUNDATIONAL_PRE2024 (EV-031 Dos and Don'ts, USENIX Sec 2022; EV-032 SoK Pragmatic Assessment, EuroS&P 2023).
- Priority: 6 rows at P1, 14 at P2, 14 at P3.
- Full text: 32 DOWNLOADED (each checked as a PDF over 50 KB with `file`/`pdfinfo`), 1 PAYWALLED, 1 NOT_DOWNLOADED.
  - EV-034 (ESORICS 2025, diversity and generalization): PAYWALLED. I found no open copy.
  - EV-015 (UWF-ZeekData24, MDPI *Data*): NOT_DOWNLOADED. It is open access, but MDPI's bot protection blocked the download from here. A manual download should work.
- Surveys registered "for reference discovery only": EV-012 (Goldschmidt & Chudá, Computers & Security 2025), EV-026 (CSET 2024 living dataset survey), EV-027 (Xu et al. 2025, DL-based IDS survey), EV-028 (El Mahdaouy et al. 2026, contextualized NetFlow DL), EV-029 (Feng & Sakurai 2025, NIDS evolution to LLMs), EV-030 (Parlanti & Catania 2025, temporal or time-aware IDS taxonomy).
- Dataset papers registered: EV-002 (LycoS-Unicas-IDS2018), EV-013 (MAWIFlow), EV-014 (CESNET-TLS-Year22), EV-015 (UWF-ZeekData24), EV-016 (NetFlow temporal variants). EV-009 uses the CyberFlowIoT-GICAP dataset.

## Venues covered
USENIX Security 2022/2024/2025, IEEE S&P 2025, NDSS 2024 (plus NDSS 2027 acceptance per arXiv), ACM CCS 2026 (acceptance per arXiv) with the AISec 2024 workshop, IEEE EuroS&P 2023/2024, ACSAC 2025, AsiaCCS 2025, ESORICS 2025, DSN-S 2025, IEEE SaTML 2026, ICISSP 2026, CSET 2024, CACM, Computers & Security, Computer Networks, IEEE Access, Scientific Data, MDPI Data, and arXiv preprints.

## Key verification notes
- **ACSAC 2025 "R+R: From Claims to Crashes" (EV-008):** the title and the 5 authors are confirmed on the ACSAC 2025 papers page. The full text used is arXiv 2503.20281, "Are We There Yet?", which has the identical author list. I have not checked that the two versions are equivalent.
- **"A First-Principles Evaluation of Graph-Based NIDS" (EV-011):** the arXiv comment says it was accepted to CCS 2026. I did not confirm this on the CCS program.
- **Guerra et al. (EV-020):** the arXiv comment says it was accepted at NDSS 2027. Not confirmed on the NDSS site.
- **Huynh et al. DSN-S 2025 (EV-004):** the version downloaded is arXiv v3, whose author order and conclusions differ from the DSN-S abstract (NEGSC vs DNN reported as best). The IEEE version is likely paywalled.
- **AsiaCCS 2025 venue for EV-021:** inferred from the ACM DOI prefix 10.1145/3708821.
- **CESNET-TLS-Year22 (EV-014):** the author list was corrected against the PDF.
- **MAWIFlow coverage:** arXiv v1 uses the years 2011, 2016 and 2021. The 2007–2024 coverage of the ICISSP version comes from a secondary source only.

## Searches run
- **arXiv API metadata lookups** (about 30 IDs), plus arXiv full-text searches on leakage, shortcut learning, temporal split and base rate.
- **Web searches:**
  - the ACSAC 2025 R+R paper (and the ACSAC 2025 papers page), Huynh DSN-S, MAWIFlow, CESNET-TLS-Year22, UWF-ZeekData24, CICIoV2024/CICIoMT2024 and the Guerra PIDS paper;
  - NDSS 2024 RAPIER, CIC-IDS2017 label errors and relabelling, and temporal-split / realistic-FPR NIDS evaluation;
  - surveys: continual-learning NIDS, zero-day NIDS, DL-NIDS and open-set NIDS;
  - AISec 2024 Apruzzese et al., and ESORICS 2025 Nougnanke et al.
- **Reference-list mining** (pdftotext) of surveys EV-027, EV-028, EV-029 and EV-030.

## Known gaps
- **No dedicated 2024–2026 continual-learning NIDS survey or zero-day NIDS survey** was found at a top venue. The closest are:
  - Por et al., a systematic literature review on AI-based zero-day detection (IEEE Access 12, 2024). UNVERIFIED and not registered.
  - "A comprehensive survey on continual anomaly detection" (Neurocomputing, ScienceDirect S0925231226025166). UNVERIFIED and not registered.
  - "Unknown, Atypical and Polymorphic Network Intrusion Detection: A Systematic Survey" (IEEE TNSM; DOI 10.1109/TNSM.2023.3298533, i.e. 2023/2024). Not registered.
- **CIC 2024–2026 dataset papers were not registered.** These are CICIoMT2024 (Internet of Things v.28, 2024), CICIoV2024 (Internet of Things 101209, 2024) and CICAPT-IIoT (arXiv 2407.11278). They are Elsevier/paywalled or host-provenance, and their metadata was seen only on UNB pages.
- **Other datasets not registered:** LUFlow, 5G-NIDD and the Gotham 2025 dataset (arXiv 2502.03134, confirmed but not registered), and CESNET-QUIC22 (2023).
- **No top-4 2024–2026 paper dedicated to NIDS operating points** (TPR at FPR ≤1e-4, alert budgets) was found. The coverage comes from the SOC measurement (EV-005), Arp et al. (EV-003/EV-031), EV-011 (calibration) and EV-020 (validation-only thresholding).
- **The ScienceDirect 2026 ROUT-4-2023 leakage-safe re-evaluation** (S2307187726004943) remains unconfirmed and is not registered.
- **Supplementary flags:** marked Y only where appendices were visible. Several are UNKNOWN.

## Survey-derived candidate primary papers (2024–2026), for other workers
Every item below is UNVERIFIED (taken from survey reference lists only) unless marked otherwise. Source survey in brackets.
1. Apruzzese, Fass, Pierazzi. "When Adversarial Perturbations meet Concept Drift: an Exploratory Analysis on ML-NIDS". AISec 2024. CONFIRMED and registered as EV-033. [EV-028]
2. Nougnanke, Blanc, Robert. "How Dataset Diversity Affects Generalization in ML-Based NIDS". ESORICS 2025. CONFIRMED and registered as EV-034. [EV-028]
3. Nakıp & Gelenbe. "Online Self-Supervised Deep Learning for Intrusion Detection Systems". IEEE TIFS 19:5668–5683, 2024. (continual, drift) [EV-028]
4. Wu, Sun, Chen, Alazab, Liu, Xiang. "TCG-IDS: Robust Network Intrusion Detection via Temporal Contrastive Graph Learning". IEEE TIFS, 2025. (generalization) [EV-027]
5. Mao et al. "FeCoGraph: Label-Aware Federated Graph Contrastive Learning for Few-Shot Network Intrusion Detection". IEEE TIFS, 2025. (zero_day / few-shot) [EV-027]
6. Hsieh et al. "NetVigil: Robust and Low-Cost Anomaly Detection for East-West Data Center Security". NSDI 2024. (zero_day, anomaly) [EV-027]
7. Liu, Inam, Goyal, Riddle, Westfall, Bates. "What We Talk About When We Talk About Logs: Understanding the Effects of Dataset Quality on Endpoint Threat Detection Research". IEEE S&P 2025. (evaluation, host) [EV-027]
8. Peng et al. "AutoLabel: Automated Fine-Grained Log Labeling for Cyber Attack Dataset Generation". USENIX Security 2025. (evaluation, labels) [EV-027]
9. Wei et al. "HEN: A Novel Hybrid Explainable Neural Network Based Framework for Robust Network Intrusion Detection". Science China Information Sciences, 2024. (adversarial) [EV-027]
10. Sun, Yun, Li, Yin, Xie. "AdvTG: An Adversarial Traffic Generation Framework to Deceive DL-based Malicious Traffic Detection Models". ACM WWW 2025. (adversarial) [EV-029]
11. elShehaby & Matrawy. "Adversarial Evasion Attacks Practicality in Networks: Testing the Impact of Dynamic Learning". arXiv 2306.05494 (v3 2025; first posted 2023). (adversarial, update_security) [EV-029]
12. Paya, Arroni, García-Díaz, Gómez. "Apollon: A Robust Defense System against Adversarial Machine Learning Attacks in Intrusion Detection Systems". Computers & Security 136:103546, 2024. (adversarial) [EV-029]
13. Koukoulis, Syrigos, Korakis. "Self-supervised Transformer-based Contrastive Learning for Intrusion Detection Systems". arXiv 2505.08816; IFIP Networking 2025 per earlier notes. (zero_day, generalization) [EV-029, EV-028]
14. Guerra, Chapuis, Duc, Mozharovskyi, Nguyen. "Self-supervised Learning of Graph Representations for Network Intrusion Detection" (GraphIDS). 2025; NeurIPS 2025 per a search snippet. (zero_day) [EV-028]
15. Van Langendonck, Castell-Uroz, Barlet-Ros. "PPT-GNN: A Practical Pretrained Spatio-Temporal Graph Neural Network for Network Security". IEEE EuroS&PW 2025. (generalization) [EV-028]
16. Wali, Farrukh, Khan, Bastian. "MeTA: Towards a Unified, Multimodal Dataset for Network Intrusion Detection Systems". IEEE Data Descriptions, 2024. (evaluation, dataset) [EV-028]
17. Shyaa et al. "Reinforcement Learning-Based Voting for Feature Drift-Aware Intrusion Detection: An Incremental Learning Framework". IEEE Access 13, 2025. (drift, continual) [EV-028]
18. Hu, Ma, Wang, Liu. "Dual Adaptive Windows toward Concept-Drift in Online Network Intrusion Detection". ICCS 2025 (Springer). (drift) [EV-028]
19. Yang, Mou, Xia, Fan. "MEDA: MoE-based Concept Drift Adaptation for In-Vehicle Network Intrusion Detection". IEEE ICCT 2024. (drift) [EV-028]
20. Hasan & Tasnim. "Generalizable Intrusion Detection for IoT: A Cost-Sensitive Multimodal Approach". DCOSS-IoT 2025. (generalization) [EV-028]
21. Mansour Bahar et al. "Continuum: Detecting APT Attacks through Spatial-Temporal Graph Neural Networks". 2025, preprint. (zero_day) [EV-028]
22. Farrukh, Wali, Khan, Bastian. "XG-NID: Dual-Modality Network Intrusion Detection using a Heterogeneous GNN and LLM". Expert Systems with Applications, 2025. [EV-028]
23. Wu et al. "An Active Learning Framework using Deep Q-Network for Zero-Day Attack Detection". Computers & Security 139:103713, 2024. (zero_day, continual) [EV-030]
24. Pinto, Amorim, Maia, Praça. "A Review on Intrusion Detection Datasets: Tools, Processes, and Features". Computer Networks 262:111177, 2025. (evaluation; a survey) [EV-030]
25. da Silva Ruffo et al. "Generative Adversarial Networks to Detect Intrusion and Anomaly in IP Flow-based Networks". Future Generation Computer Systems 163, 2025. (zero_day) [EV-030]
26. Zhong, Lin, Zhang, Xu. "A Survey on Graph Neural Networks for Intrusion Detection Systems: Methods, Trends and Challenges". Computers & Security 141:103821, 2024. (a survey) [EV-028]
27. Yang et al. "Large Language Models for Network Intrusion Detection Systems: Foundations, Implementations, and Future Directions". arXiv 2507.04752, 2025. (a survey) [EV-029]
28. Vassilev, Oprea et al. "Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations". NIST AI 100-2, 2025. (adversarial, poisoning; tech report) [EV-029]
29. Amalapuram et al. "SOUL: A Semi-supervised Open-world continUal Learning method for Network Intrusion Detection". arXiv 2412.00911, 2024. CONFIRMED on arXiv; venue unknown. (continual, zero_day) [found by search, not by a survey]
30. Fuhrman, Gungor, Rosing. "CND-IDS: Continual Novelty Detection for Intrusion Detection Systems". DAC 2025 (arXiv 2502.14094). CONFIRMED via the arXiv comment. (continual, zero_day) [found by search]
