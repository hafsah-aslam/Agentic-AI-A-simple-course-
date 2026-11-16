# NIDS Datasets, Benchmarks, and Evaluation Pitfalls (2024–2026)

Scope note: about 20 tool calls (searches, fetches, and one full-text extraction). Every item below is tagged as one of:
- **[VERIFIED-primary]**: checked on arXiv, the publisher or institutional record, or the paper's full text.
- **[VERIFIED-secondary]**: seen only in search-result snippets or in another paper's summary.
- **[BACKGROUND, not re-verified]**: comes from prior knowledge and was not re-checked here.
- **UNVERIFIED**: candidates I could not confirm. These are listed under Gaps.

Coverage of the top-tier venues on the list (USENIX Security, IEEE S&P, CCS, NDSS) for 2024–2026 NIDS-dataset critiques is thin in these notes. Search did not surface such papers directly, and the Gaps section names candidates to check in the proceedings.

## Q1/Q2: Which 2024–2026 papers address NIDS dataset and evaluation flaws, and what did each find?

### Takeaway
The strongest peer-reviewed 2024 critique is Flood, Engelen, Aspinall & Desmet, "Bad Design Smells in Benchmark NIDS Datasets" (IEEE EuroS&P 2024). It audits seven benchmark datasets and finds that one or two features often separate the classes almost perfectly. Its central point is that a standard train/test split on these datasets amounts to training and testing on the same attack class, which is a form of leakage. Cantone et al. (IEEE Access 2024) show the practical result: near-perfect scores within one dataset fall to roughly chance across datasets, even between the corrected CIC variants. 2025–2026 work, mostly arXiv and journals, adds evidence that random flow splits and session-level leakage inflate results. Arp et al.'s CACM 2024 "Pitfalls" article is the canonical evaluation checklist.

### Cited Findings

**P1. Flood, Engelen, Aspinall, Desmet: "Bad Design Smells in Benchmark NIDS Datasets", IEEE EuroS&P 2024, pp. 658–675 (Vienna, 8–12 July 2024) [VERIFIED-primary]**
- Bibliographic record — [DBLP](https://dblp.org/rec/conf/eurosp/FloodEAD24.html); [IEEE Xplore 10629000](https://ieeexplore.ieee.org/document/10629000); [author final draft PDF](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Problem:** synthetic benchmark NIDS datasets are rarely audited, and design choices made while generating them create experimental bias — [final draft, abstract](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Datasets:** ISCX 2012, CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15, CTU-13, Bot-IoT, and ToN-IoT, covering 65+ attack classes — [final draft, Table legend and contributions](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Method:** manual analysis of the data, then six lightweight heuristics to measure each "smell". The authors also reviewed 38 papers (2015–2023) from USENIX Security, S&P, EuroS&P, CCS, AsiaCCS, CNS, RAID, DIMVA, KDD, InfoCOM, WWW, SAC, ACSAC, and CIKM, and re-ran 4 of them in detail — [final draft](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **The six smells**, as given in the text: (1) many datasets contain data with low diversity or highly dependent features; (2) poorly designed simulation testbeds; (3) unclear labelling logic, where background services are labelled as attacks; (4) inaccurate ground truth from the generation process; (5) simple configuration mistakes; (6) problems in traffic generation, such as traffic distributions collapsing — [final draft, §5](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Key numbers and findings:**
  - On UNSW-NB15, the Protocol and TTL features alone separate benign from malicious with 98% accuracy. These artifacts come from the testbed and are unrelated to how the attacks work — [final draft, §4](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
  - A simple, gradient-free attack that perturbs TTL and protocol "achieves identical performance to AJSMA on UNSW NB15", which undercuts a published adversarial-robustness evaluation — [final draft](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
  - In the re-analysis of Singla et al.'s adversarial domain adaptation (ADA) on UNSW-NB15, removing the problematic classes and samples shrinks ADA's reported advantage to a 1.5% gap. The authors conclude that "without modification, UNSW NB15 is unsuitable for evaluating the ability of classifiers to generalise between attack categories" — [final draft](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
  - "It is often trivial to get perfect classification accuracy using a single feature that is unrelated to the underlying mechanism of an attack" — [final draft, §1](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
  - In CIC-IDS2017, the train and test sets overlap almost entirely under the standard pipeline (their Fig. 4). The DoS Hulk class has poor diversity because network conditions and the target page were fixed. Data regenerated with DetGen across 60 bandwidth and page-size combinations raised the class's diversity scores to 0.89 and 0.62 — [final draft, §6.1](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
  - In CSE-CIC-IDS2018's Infiltration class, several benign flows were duplicated — [final draft, §5](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
  - The heuristics score much better on general tabular anomaly datasets (ODDS), which suggests the problems are specific to NIDS data — [final draft](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Recommendations:**
  - Define generalisation explicitly, and avoid training and testing on attack data from the same class and dataset; evaluate across classes and datasets instead.
  - Do not use the dataset-provided feature sets by default.
  - Justify performance by linking important features to how the attack works, and drop features that are inexplicably discriminative.
  - Test model "fragility" with unguided perturbations to expose shortcut features.
  - Dataset creators should provide several diverse test scenarios that differ in space or time "as in TESSERACT", flag shortcut artifacts with naive baseline models, focus on a specific class of attacks, include normal use of the attacked service, and ship BPF filters and documentation that map flows back to PCAPs.
  - Source: [final draft, §6](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Award:** described as Best Paper by one arXiv paper and as Distinguished Paper in an Edinburgh thesis. The sources conflict and I did not confirm either — [arXiv 2509.16038](https://arxiv.org/pdf/2509.16038v2); [ERA Edinburgh](https://era.ed.ac.uk/bitstreams/f235af63-4123-4f6a-a795-433e8b930ec7/download)
- **Stated limitations:** the paper has a §8 on limitations, which I did not extract.
- **Unstated limitations (my assessment):** it covers synthetic or testbed datasets only, with no real-network or ISP traces. It does not propose a replacement benchmark. The heuristics are proxies and are not validated against ground truth.

**P2. Cantone, Marrocco, Bria: "On the Cross-Dataset Generalization of Machine Learning for Network Intrusion Detection", IEEE Access 12:144489–144508, 2024; arXiv:2402.10974 (Feb 2024) [VERIFIED-primary]**
- **Datasets:** CIC-IDS2017, CSE-CIC-IDS2018, LycoS-IDS2017, and LycoS-Unicas-IDS2018. The last is new: the authors built it by applying the LycoS corrections to CSE-CIC-IDS2018 — [arXiv abs](https://arxiv.org/abs/2402.10974)
- **Method:** four ML classifiers trained and tested across the four datasets, plus visual analysis of the data — [arXiv abs](https://arxiv.org/abs/2402.10974)
- **Finding:** classification is "nearly perfect" within a dataset. Across datasets, accuracy is "largely commensurate with random chance" except for a few attack and dataset combinations. The authors attribute this to anomalies in the data — [arXiv abs](https://arxiv.org/abs/2402.10974)
- **Implication:** even CIC-2017 → CIC-2018, two datasets from the same lab with similar tooling and corrected labels, does not transfer. Cross-dataset evaluation within the CIC family is a demanding test, not an easy one.
- A secondary summary attributes to "Liu et al." estimated labelling-error rates of 6.67% for CIC-IDS2017 and 7.53% for CSE-CIC-IDS2018, with some attack categories above 75% corrupted. This came from a search-result summary citing 2402.10974; the abstract does not contain it — [secondary: search summary of arXiv 2402.10974 HTML](https://arxiv.org/html/2402.10974v1). Probable original: Liu, Engelen, Lynar, Essam, Joosen, "Error Prevalence in NIDS datasets: A Case Study on CIC-IDS-2017 and CSE-CIC-IDS-2018" (IEEE CNS 2022), which is BACKGROUND, pre-2024 — [CPS-VO record](https://archive.cps-vo.org/node/97449). The exact numbers are UNVERIFIED against the primary source.

**P3. Lanvin, Gimenez, Han, Majorczyk, Mé, Totel: "Errors in the CICIDS2017 Dataset and the Significant Differences in Detection Performances It Makes" (Springer LNCS, CRiSIS 2022 proceedings, online 2023) [VERIFIED-secondary; BACKGROUND, pre-2024 venue]**
- Reports capture and labelling flaws in CIC-IDS2017: misordered packets, incoherent timestamps, duplicated traffic, and attacks that were mislabelled or not labelled. It proposes fixes and measures how detection results change — [ResearchGate](https://www.researchgate.net/publication/370796116_Errors_in_the_CICIDS2017_Dataset_and_the_Significant_Differences_in_Detection_Performances_It_Makes); [SpringerProfessional](https://www.springerprofessional.de/en/errors-in-the-cicids2017-dataset-and-the-significant-differences/25357470). The 2024 date in some listings is inconsistent and was not confirmed.

**P4. Arp, Quiring, Pendlebury, Warnecke, Pierazzi, Wressnegger, Cavallaro, Rieck: "Pitfalls in Machine Learning for Computer Security", Communications of the ACM 67(11):104–112, Nov 2024, DOI 10.1145/3643456 [VERIFIED-primary bibliographic record]**
- This is the CACM Research Highlight version of the USENIX Security 2022 "Dos and Don'ts" paper. It defines ten pitfalls with matching "dos", finds them widespread in a review of 30 top-venue papers, and shows experimentally that they produce overly optimistic results — [TU Wien repositum](https://repositum.tuwien.at/handle/20.500.12708/204487); [UCL Discovery PDF](https://discovery.ucl.ac.uk/10212285/1/3643456.pdf); [mlsec.org PDF](https://mlsec.org/docs/2024-cacm.pdf)
- It has a companion Technical Perspective, "Machine Learning in Computer Security is Difficult to Fix" (DOI 10.1145/3655635) — [CACM](https://cacm.acm.org/research-highlights/technical-perspective-machine-learning-in-computer-security-is-difficult-to-fix)
- The USENIX 2022 original names sampling bias, label inaccuracy, data snooping, spurious correlations, biased parameter selection, inappropriate baselines, inappropriate performance measures, base-rate fallacy, lab-only evaluation, and inappropriate threat model — [USENIX Sec '22 PDF](https://www.usenix.org/system/files/sec22-arp.pdf) [BACKGROUND]

**P5. Huynh, Hesford, Cheng, Wan, Kim, Kim, Hong: "Expectations Versus Reality: Evaluating Intrusion Detection Systems in Practice", DSN-S 2025 (supplemental volume), pp. 56–62, DOI 10.1109/DSN-S65789.2025.00042 [VERIFIED-primary record]**
- A reproducibility and practice study. Many recent ML NIDS had problems with preprocessing, code availability, and reproducibility. Only four could be fully evaluated: HELAD, AOC-IDS, NEGSC, and SLIPS. No system was best on every dataset. NEGSC had the highest average F1 at 0.8147, while HELAD reached F1 = 0.9902 on CTU-13 alone — [SKKU ScholarX record](https://scholarx.skku.edu/item/3212e252-c317-4da4-b4f2-4032ea636699)
- **Datasets:** CIC-IDS2017, UNSW-NB15, Mirai, CTU-13, and Bot-IoT — [same](https://scholarx.skku.edu/item/3212e252-c317-4da4-b4f2-4032ea636699)
- **Unstated limitation:** a short supplemental (workshop-level) paper with only four systems, and it relies on the flawed legacy datasets described in P1.

**P6. Goldschmidt & Chudá: "Network Intrusion Datasets: A Survey, Limitations, and Recommendations", Computers & Security 156 (2025) 104510; arXiv:2502.06688 [VERIFIED-primary]**
- A systematic review of 89 public NIDS datasets compared on 13 properties. It covers dataset popularity in recent NIDS research and gives best practices for choosing, generating, and using datasets — [arXiv abs](https://arxiv.org/abs/2502.06688). The specific recommendations were not extracted (Gap).

**P7. "Introducing a Comprehensive, Continuous, and Collaborative Survey of Intrusion Detection Datasets", arXiv:2408.02521 (2024) [VERIFIED-secondary; authors not extracted]**
- A living survey of IDS datasets — [arXiv PDF](https://arxiv.org/pdf/2408.02521)

**P8. Luay, Layeghy, Hosseininoorbin, Sarhan, Moustafa, Portmann: "Temporal Analysis of NetFlow Datasets for Network Intrusion Detection Systems", arXiv:2503.04404 (v1 Mar 2025; v3 Aug 2026; DOI 10.1109/ACCESS.2026.3688204 linked) [VERIFIED-primary]**
- Existing NetFlow NIDS datasets lack temporal features. The authors release versions that add inter-arrival and duration features and run time-frequency analysis — [arXiv abs](https://arxiv.org/abs/2503.04404). The group's NetFlow v2/v3 dataset family is listed at [UQ NIDS datasets page](https://staff.itee.uq.edu.au/marius/NIDS_datasets/).

**P9. El Mahdaouy, Ait Yahia, Oualil, Berrada: "Deep Learning for Contextualized NetFlow-Based Network Intrusion Detection: Methods, Data, Evaluation and Deployment", arXiv:2602.05594 (Feb 2026; survey or position paper) [VERIFIED-primary abstract]**
- Names these pitfalls: temporal leakage, data splitting, dataset design flaws, limited diversity, and weak cross-dataset generalization. It also covers operational constraints: streaming state, memory growth, latency budgets, and compression. It argues for "rigorous, causal evaluation" — [arXiv abs](https://arxiv.org/abs/2602.05594)
- A search snippet says it cites MAWIFlow, built from MAWILab v1.1, with temporally distinct samples from 2011–2021 — [secondary: arXiv HTML](https://arxiv.org/html/2602.05594v1) (not confirmed in full text)

**P10. Roy & Minu: "Unmasking Shortcut Learning in IoT Intrusion Detection: A Forensic, Multi-Paradigm Evaluation of Feature Dependence and Data Leakage", arXiv:2609.28725 (Sept 2026, under review) [VERIFIED-primary abstract; not peer-reviewed]**
- **Dataset:** CyberFlowIoT-GICAP, with 3,617,388 flows from 126 PCAP sessions, 849,395 of them benign. Uses PCAP-disjoint splits — [arXiv abs](https://arxiv.org/abs/2609.28725)
- **Findings:**
  - Behavioural flow features alone give Macro-F1 of about 92.6% for LightGBM, RF, and MLP alike.
  - Adding raw timestamps lifts tree models to 99.28%, which is a temporal shortcut.
  - DNS beaconing recall falls from 27.78% to 0% without contextual features.
  - Random flow splitting inflates attack recall by up to 14 points because of intra-session leakage.
  - Source: [arXiv abs](https://arxiv.org/abs/2609.28725)
- The paper proposes a 4-point evaluation checklist, which I did not extract.

**P11. "Do Transformers Actually Help Intrusion Detection? A Temporal Sequence Evaluation on CIC-IDS2017", arXiv:2606.11098 (2026) [VERIFIED-secondary; authors not extracted]**
- Rebuilds CIC-IDS2017 as ordered flow sequences and compares 9 architectures under random and leakage-free splits. A padding cue under random splits hides a 67× increase in the Transformer's false-alarm rate that only leakage-free evaluation shows — [arXiv abs](https://arxiv.org/abs/2606.11098)

**P12. A leakage-safe re-evaluation of ML IDS for RPL-based IoT (ROUT-4-2023 dataset), ScienceDirect 2026 [VERIFIED-secondary; title, authors, and journal not confirmed]**
- After deduplication and out-of-fold stacking, accuracy falls from about 83% on a random split to about 73% (binary) on a temporal split, which points to concept drift inside each run — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2307187726004943)

**P13. ConCap: "Practical Network Traffic Generation for (ML- and) Flow-based Intrusion Detection Systems", arXiv:2509.16038 (2025) [VERIFIED-secondary]**
- A traffic-generation tool written in response to the Bad Smells critique — [arXiv](https://arxiv.org/pdf/2509.16038)

**P14. Graph-NIDS and provenance re-evaluations (adjacent area, host provenance rather than network flows)**
- "A First-Principles Evaluation of Graph-Based Network Intrusion Detection Systems", arXiv:2609.12263. It reportedly cites a graph-NIDS re-evaluation titled "From claims to crashes", described as ACSAC 2025. Neither the title nor the venue was confirmed — [arXiv](https://arxiv.org/pdf/2609.12263)
- Guerra et al., "How Benchmarks and Evaluation Protocols Shape Conclusions in Provenance-Based Intrusion Detection" (DARPA TC E3, temporally separated tests). A simple allowlist of executable names and paths matches or beats the learned PIDS baselines — [deeplearn.org mirror](https://deeplearn.org/arxiv/821316/how-benchmarks-and-evaluation-protocols-shape-conclusions-in-provenance-based-intrusion-detection). Venue is unverified.
- Bilot & Pasquier's ;login: summary (Aug 2025) of two USENIX Security 2025 PIDS papers argues that current PIDS are not ready for real-world use — [USENIX](https://www.usenix.org/node/315189) [VERIFIED-secondary]

### Inferences
- Taken together, P1 + P2 + P11 + P10 make the case that random-split, in-dataset results on CIC-IDS2017, CSE-CIC-IDS2018, or UNSW-NB15 are not evidence of generalization. A USENIX 2027 paper should treat in-dataset numbers only as sanity checks.
- The evaluation axes reviewers now expect are: (i) temporal splits that keep sessions and PCAPs disjoint, (ii) cross-dataset transfer, (iii) leave-attack-class-out testing, (iv) shortcut probes such as single-feature baselines, TTL and IP ablations, and perturbation fragility, and (v) deployment cost (latency and memory).
- Most 2025–2026 evidence is still on arXiv or in journals rather than at top-4 venues. That suggests an opening at top venues for a rigorous temporal and cross-network benchmark.

### Gaps
The following candidates are UNVERIFIED and could not be confirmed in this session's budget. Check each against the proceedings.
- Wickramasinghe et al., "SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers" (believed IEEE S&P 2025): shortcut and leakage issues in traffic classification.
- Any USENIX Security, CCS, or NDSS 2024–2026 paper on NIDS label errors or temporal drift. None was found.
- Apruzzese et al., "SoK: Pragmatic Assessment of ML for Network Intrusion Detection" (EuroS&P 2023). This is BACKGROUND and was not re-verified.
- Engelen, Rimmer, Joosen, "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study" (2021); LycoS-IDS2017 (2021, [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3486622.3493973)); and Sommer & Paxson 2010 "Outside the Closed World". These are BACKGROUND only.
- The stated limitations of P1 (§8), the recommendations of P6, and the checklist of P10 were not extracted.
- Base-rate and class-imbalance work specific to NIDS in 2024–2026: no dedicated paper was found. The base-rate fallacy is covered generically by P4.

## Q3: Which public datasets support temporal, cross-network, leave-family-out, PCAP, and realistic-benign evaluation?

### Takeaway
No single public dataset clearly satisfies all five criteria. For multi-month or multi-year temporal evaluation with real benign traffic, the options are real-network traces with weak or heuristic labels: UGR'16 (3 months, ISP NetFlow) and MAWI/MAWILab, from which MAWIFlow covers 2011–2021. Synthetic testbeds (CIC, UNSW, ToN-IoT, Bot-IoT) offer PCAP and many attack families, but they span days, carry shortcut artifacts, and P1 judges them unsuitable for cross-category generalization without modification. Many 2025–2026 releases are IoT-focused, single-topology, short-duration captures.

### Cited Findings (dataset table)
Column key: Temp = multi-month temporal; X-net = cross-network; LOFO = leave-one-family-out; PCAP = raw PCAP available; Real benign = realistic benign traffic.

| Dataset | Year | Size / span | Temp | X-net | LOFO | PCAP | Real benign | Access / license | Known problems (source) |
|---|---|---|---|---|---|---|---|---|---|
| CIC-IDS2017 / LycoS-IDS2017 | 2017 / 2021 | 5 working days [BACKGROUND] | No | Paired with CIC-2018 as transfer target; transfer ≈ chance ([Cantone 2024](https://arxiv.org/abs/2402.10974)) | Limited: class boundaries blurred, train/test overlap ([Flood 2024](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)) | Yes [BACKGROUND] | No (scripted) | UNB CIC, free with registration [BACKGROUND] | Label errors, duplicates, misordering ([Lanvin](https://www.researchgate.net/publication/370796116_Errors_in_the_CICIDS2017_Dataset_and_the_Significant_Differences_in_Detection_Performances_It_Makes)); single-feature shortcuts ([Flood](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)) |
| CSE-CIC-IDS2018 / LycoS-Unicas-IDS2018 | 2018 / 2024 | ~10 days on AWS [BACKGROUND] | No | Same as above | Limited | Yes [BACKGROUND] | No | AWS open data [BACKGROUND] | Duplicated benign flows in Infiltration ([Flood](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)); label-error estimate 7.53% (secondary, see P2) |
| UNSW-NB15 | 2015 | ~100 GB PCAP, 2 capture sessions [BACKGROUND] | No | No | Explicitly "unsuitable" across attack categories without modification ([Flood](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)) | Yes [BACKGROUND] | Synthetic (IXIA) | UNSW site [BACKGROUND] | TTL and protocol give 98% separation ([Flood](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)) |
| CTU-13 | 2011–2014 | 13 botnet scenarios | No | Partial (scenarios differ) | Yes, by botnet family | Yes [BACKGROUND] | Real campus background | CTU site [BACKGROUND] | Artifacts in Scenario 4; otherwise praised for granular labels ([Flood](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)) |
| UGR'16 | 2016 | 3 months, Tier-3 ISP NetFlow ([search summary of survey](https://arxiv.org/pdf/2502.06688)) | Yes | No | Partial | No (NetFlow only) | Yes (real ISP) | Public (UGR) [BACKGROUND] | Labels partly heuristic [BACKGROUND] |
| MAWILab / MAWIFlow | MAWIFlow 2025–26? | 2011–2021 (secondary) ([arXiv 2602.05594](https://arxiv.org/html/2602.05594v1)) | Yes | Partial (single backbone link) | No (anomaly labels, not attack families) | MAWI traces anonymized and header-only [BACKGROUND] | Yes | Public [BACKGROUND] | Weak labels from combined detectors [BACKGROUND] |
| NetFlow v2/v3 family (NF-UNSW, NF-ToN-IoT, NF-CSE-CIC, NF-BoT-IoT) | 2021–2025 | Derived from the sources | No | Yes: shared feature set lets models be applied across datasets | Inherits source issues | No (flows) | Inherits | UQ page ([UQ](https://staff.itee.uq.edu.au/marius/NIDS_datasets/)) | Inherits source artifacts; temporal-feature versions released ([Luay 2025](https://arxiv.org/abs/2503.04404)) |
| Gotham Dataset 2025 (IoT) | 2025 | Duration not stated | Unknown | No | Unknown | Yes, PCAP plus labelled CSV ([arXiv 2502.03134](https://arxiv.org/abs/2502.03134)) | Emulated IoT | arXiv / repository | Single testbed |
| CyberFlowIoT-GICAP | 2026 | 3.6M flows, 126 PCAP sessions ([arXiv 2609.28725](https://arxiv.org/abs/2609.28725)) | No | No | Unknown | Yes (sessions) | Testbed | Unknown | Static IP/MAC and timestamp shortcuts ([same](https://arxiv.org/abs/2609.28725)) |
| NIDS_Network_Benchmark APT | 2025 | Single simulated topology, single time period | No | No | No | No, flow CSV only ([IEEE DataPort](https://ieee-dataport.org/documents/nidsnetworkbenchmark-dataset-apt-novel-network-intrusion-detection-dataset-advanced)) | Simulated | IEEE DataPort | Self-described limits on diversity |
| Multi-source Cybersecurity LAN dataset | 2025–26? | 93 PCAPs, 1,114,057 benign unidirectional flows; span not stated ([Zenodo](https://zenodo.org/records/23388938)) | Unknown | No | No (benign only) | Yes | Virtualized enterprise | Zenodo | Benign-only |
| CIC 2023–2026 releases: CIC IoT 2023, CICEV2023 DDoS, Modbus 2023, Datasense IIoT 2025, CIC-DGG 2025 (graph), CIC-YNU-IoTMal 2026 | 2023–2026 | Not stated on index ([UNB CIC index](https://www.unb.ca/cic/datasets/index.html)) | Unverified | Unverified | Unverified | CIC says PCAP/CSV mapping is per-dataset ([same](https://www.unb.ca/cic/datasets/index.html)) | Testbed | UNB CIC | Same generation methodology as CIC-2017/2018, so P1's critique likely applies (inference) |

### Inferences
- **(a) Temporal:** use UGR'16 and MAWI/MAWIFlow for months or years of drift with real benign traffic. Accept weak labels, and inject or replay attacks with care.
- **(b) Cross-network:** the NetFlow v2/v3 shared-feature family gives a common feature space. Cantone 2024 shows transfer is near chance, which makes it a hard but credible testbed, provided reviewers do not attribute the failure solely to dataset artifacts.
- **(c) Leave-family-out:** CTU-13, where each scenario is a botnet family, is cleaner than UNSW-NB15 or the CIC sets. P1 recommends cross-class and cross-dataset protocols and synthetic diversification (DetGen, ConCap).
- **(d) PCAP:** CIC, UNSW, CTU, Gotham, and the Zenodo LAN set have PCAP. UGR'16 and the UQ NetFlow sets do not.
- **(e) Realistic benign:** real-network sources (UGR'16, MAWI, the CTU background) beat every testbed.

### Gaps
- The time spans, sizes, and licenses of the CIC 2024–2026 datasets (CIC IoV2024, CICIoMT2024, CICAPT-IIoT2024, Datasense 2025) were not verified on their individual pages.
- UNSW-NB15, CIC-IDS2017, and CSE-CIC-IDS2018 sizes and spans come from prior knowledge and were not re-checked.
- MAWIFlow: the exact paper, authors, and labels are unverified.
- Not checked: LUFlow, UWF-ZeekData22/24, CESNET-TLS-Year22 / CESNET-QUIC22 (year-long traffic-classification datasets), Kitsune, 5G-NIDD, HIKARI-2021, and the BCCC re-releases of CIC-IDS2017.

## Q4: What evaluation checklist do recent critiques recommend?

### Takeaway
Combining Arp et al. (CACM 2024), Flood et al. (EuroS&P 2024), and the 2025–2026 leakage studies gives a checklist that targets realistic splits, shortcut detection, base-rate-aware metrics, and deployment realism.

### Cited Findings
- **Arp et al.:** avoid ten pitfalls covering sampling bias, label inaccuracy, data snooping (including temporal snooping), spurious correlations, biased parameter selection, inappropriate baselines, inappropriate measures, base-rate fallacy, lab-only evaluation, and inappropriate threat models — [USENIX '22](https://www.usenix.org/system/files/sec22-arp.pdf); [CACM 2024](https://mlsec.org/docs/2024-cacm.pdf)
- **Flood et al.:**
  - Define the axis of generalization.
  - Do not train and test on the same attack class from the same dataset; use cross-class and cross-dataset evaluation.
  - Do not use the provided features blindly.
  - Tie important features to how the attack works, and drop inexplicable ones.
  - Run perturbation-fragility tests for shortcuts.
  - Dataset creators should provide spatially or temporally distinct test sets (TESSERACT-style), naive-baseline shortcut reports, normal use of the attacked service, and BPF filters linking flows to PCAP.
  - Source: [final draft §6](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)
- **Roy & Minu 2026:** use PCAP- and session-disjoint splits instead of random flow splits (up to 14 points of recall inflation), and ablate timestamp and identifier features — [arXiv 2609.28725](https://arxiv.org/abs/2609.28725)
- **Leakage-free and temporal splits** change conclusions: a 67× FPR gap was masked in one study ([arXiv 2606.11098](https://arxiv.org/abs/2606.11098)), and accuracy fell from 83% to 73% under a temporal split in another ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2307187726004943))
- **Operational constraints:** report streaming state, memory, latency, and compression costs — [arXiv 2602.05594](https://arxiv.org/abs/2602.05594)
- **Reproducibility:** release code and preprocessing. Many systems could not be reproduced, and no system was best on every dataset — [DSN-S 2025](https://scholarx.skku.edu/item/3212e252-c317-4da4-b4f2-4032ea636699)

### Inferences
Proposed checklist for a USENIX 2027 submission, synthesized from the sources above:
1. Deduplicate, and split by time and by session or PCAP; fit preprocessing on training data only.
2. Report cross-dataset results (shared NetFlow feature space) and leave-attack-family-out results.
3. Run single-feature and TTL/IP/timestamp ablation baselines.
4. Use base-rate-realistic metrics, such as FPR at a fixed alert budget and precision at realistic prevalence.
5. Compare against simple baselines like allowlists and rules.
6. Measure drift over months on a real-traffic source.
7. Release code and preprocessing.

### Gaps
- No 2024–2026 top-venue paper offering a NIDS-specific checklist (a "Dos and Don'ts for NIDS") was found. The checklists in P6 and P10 were not extracted.
