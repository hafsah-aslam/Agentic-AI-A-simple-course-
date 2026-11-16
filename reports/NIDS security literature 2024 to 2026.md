# Stage 1 maps a thin, critique-heavy NIDS frontier

**Stage 1 (literature extraction and understanding) of a staged research-discovery project targeting USENIX Security 2027 Cycle 2.** This report extracts and organizes only what the research notes contain. It does not propose ideas or recommendations (Stage 2+).

Between 2024 and 2026, top-tier security venues published few network-flow NIDS papers and many critiques. The direct detection competitors are a small group: **KnowML** (EuroS&P 2026, benign-only training, reported FPR ≤ 0.0137%), **TIPSO-GAN** (NDSS 2026, leave-one-family-out mean F1 92.3), **PANDORA** (NDSS 2026, zero-shot detection under domain shift) and **Mateen** (RAID 2024, adaptation to benign drift with 1% labelling). The robustness frontier is set by **PANTS** and **CertTA** (both USENIX Security 2025) and by **NetMasquerade** (NDSS 2026), a hard-label black-box attack with over 96.65% success that evades certified defences. Critiques make up much of the rest. Benchmark datasets carry single-feature shortcuts (EuroS&P 2024). Cross-dataset transfer falls to roughly chance (IEEE Access 2024). Most "encrypted" traffic classifiers were trained on unencrypted data (S&P 2025). Only 0.01% of real SOC network alerts are tied to true attacks (USENIX Security 2024).

Across all scanned venue-years, the notes found no paper giving a formal FPR guarantee under drift for NIDS and no paper measuring post-quantum TLS effects on detectors. Attacks on NIDS retraining and update loops appear only indirectly. These are early Stage 3 signals, not established gaps, for two reasons. Most extractions are abstract-level or title-only. Coverage also has holes: AsiaCCS 2024 was not scanned, DBLP was blocked everywhere, and many S&P and RAID 2025 papers are title-only.

The binding target is USENIX Security 2027 Cycle 2: registration **January 19, 2027**, submission **January 26, 2027**, a 13-page body, a mandatory Open Science Appendix, and Network Security as the required primary topic for ML-for-NIDS papers ([CFP](https://www.usenix.org/conference/usenixsecurity27/call-for-papers)).

**How to read verification labels.** Each paper carries the verification level recorded in the source notes:
- **FULL TEXT**: the researcher read the full PDF.
- **PARTIAL TEXT**: first pages, slides, or targeted sections only.
- **ABSTRACT**: official abstract page or arXiv abstract.
- **SECONDARY**: search snippet, aggregator, or another paper's summary.
- **TITLE ONLY / UNVERIFIED**: confirmed on an official list, but no content was retrieved.

Where two notes disagree about how deeply a paper was read, both labels are shown. "Unstated limitations" are always the note-writers' own readings, not claims made by the papers. Fields the notes did not extract say "not extracted", and nothing has been inferred to fill them.

---

## The verified evidence base: paper-by-paper extraction

The extraction is split into three tiers:
- **Tier 1:** the papers that most constrain a USENIX 2027 NIDS contribution, given in full field tables.
- **Tier 2:** important adjacent papers, in compact tables.
- **Tier 3:** the master table.

In every Tier 1 table, "Demonstrates", "Claims" and "Untested" are kept separate on purpose.

### Tier 1A — Detection under unseen attacks and drift

**Mateen: Adaptive Ensemble Learning for Network Anomaly Detection** — verification: **FULL TEXT** ([PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf); [RAID 2024 PDF](https://raid2024.github.io/papers/raid2024-11.pdf))

| Field | Extraction |
|---|---|
| Authors / venue / year | Fahad Alotaibi, Sergio Maffeis (Imperial College London); RAID 2024, Padua; DOI 10.1145/3678890.3678901; code at ICL-ml4csec/Mateen |
| Problem | Offline one-class deep autoencoder (DAE) NIDS assume benign behaviour is static. "Benign shift" makes them flag new benign behaviour, so false positives rise over time |
| Threat model | No adversary is modelled in the evaluation. The labelling/update loop is named as a poisoning vector and left as future work |
| Hypothesis | Shift can be detected from anomaly-score distributions and fixed with a small, representative labelled subset, without adding false alarms from benign change |
| Mechanism | Ensemble of DAEs trained on benign data, scored by MSE. A two-sample Kolmogorov–Smirnov test (p < 0.05) compares score ECDFs between a reference set and each batch. Shifted batches trigger selection of informative and representative samples for human labelling. Models are then updated incrementally or replaced. Members within 10% of the best F1 are merged with weight α found by grid search, and underperformers are dropped. No update happens if F1 on the selected subset is at least t = 99% |
| Datasets | CICIDS2017, CSE-CIC-IDS2018, Kitsune, plus synthetic mKitsune (constant malicious ratio) and rKitsune (recurring concept). Kitsune has no timestamps, so file order was used. Simulated covariate shift was built from IDS18 |
| Evaluation protocol | "Time-aware" splits. Baselines: No-Update DAE, OWAD (NDSS 2023), INSOMNIA (AISec 2021), CADE (USENIX Sec 2021). Labelling budget δ = 1% (500 samples per batch), with a sweep over 0.5–10%. Random label flips at 10%, 30% and 50% |
| Key results | AUC-ROC 96.79% (IDS17), 98.17% (IDS18), 94.76% (mKitsune), beating the best baseline by 2.23, 4.36 and 14.78 points. F1 +4.13% on IDS17 ("light change") and +72.6% on Kitsune ("heavy change"). In one comparison OWAD and INSOMNIA reached only 90.01% and 78.98% accuracy with 5,000 labels. Hyperparameter mean AUC-ROC 96.19 (std 0.64) |
| Stated limitations | Labelling cost in dynamic networks. Labelling latency. Label estimators can cause "self-poisoning". The loop "is a potential vector for poisoning the ensemble" through label flipping and backdoors. Evasive samples disguised as benign. Use of synthetic data ("consistent with recent work on NIDS") |
| Unstated limitations (note-writer) | No TPR at low FPR, only AUC-ROC, F1 and accuracy. Analysts are assumed to label correctly. Malicious traffic is assumed to look anomalous. Evaluation is offline replay of artefact-laden CIC data. Noise is random, not adversarial |
| Deployment assumptions | A trusted analyst labels about 1% of traffic per batch. Benign and malicious traffic stay separable by reconstruction error |
| Demonstrates / claims / untested | **Demonstrates** AUC and F1 gains under benign drift with 1% labels on lab data. **Claims** avoidance of false alarms caused by benign change. **Untested:** adaptive poisoning through the label channel, low-FPR operating points, real enterprise traffic |
| Unresolved questions | Can an adversary steer which samples get selected and relabelled? Does the KS trigger fire under slow or adversarial drift? |

**TIPSO-GAN: Malicious Network Traffic Detection Using a Novel Optimized GAN** — verification: **PARTIAL TEXT** (abstract, research questions and zero-day results table) ([NDSS page](https://www.ndss-symposium.org/ndss-paper/tipso-gan-malicious-network-traffic-detection-using-a-novel-optimized-generative-adversarial-network/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf))

| Field | Extraction |
|---|---|
| Authors / venue / year | Ernest Akpaku, Jinfu Chen (Jiangsu University), Joshua Ofoeda (UPS Ghana); NDSS 2026; DOI 10.14722/ndss.2026.243241 |
| Problem | Malicious traffic detection that also covers zero-day families |
| Threat model | The authors list mimicry, poisoning, black-box transfer and adaptive attacks as evaluated (§VI-G). The notes did **not verify** how these attackers were parameterized |
| Hypothesis | Zero-day capability comes from "unsupervised fine-tuning on normal traffic", with deviations from the learned benign manifold flagged |
| Mechanism | GAN training framed as particle swarm optimization (adaptive inertia, diversity preservation, reinitialization of stagnant particles), plus transfer learning, Temporal-Decaying Multi-Head Self-Attention, and a reconstruction + focal loss |
| Datasets | CIC-IDS2018, CICAPT-IIoT2024, CIC-DDoS2019 |
| Evaluation protocol | Leave-one-family-out (LOFO) on CIC-IDS2018 with six held-out families (DoS, Brute Force, Botnet, Infiltration, Web Attacks, Heartbleed), five seeds. Cross-dataset train→test pairs across the three corpora |
| Key results | In-distribution F1 99.1 / 98.9 / 98.7. Macro PR-AUC 0.999 on CICAPT-IIoT2024. LOFO mean F1 **92.3 ± 0.6**. Cross-dataset F1 **79–83**, recall > 0.80. Latency 0.42 ms, about 2,400 flows/s, 2.1 GB footprint |
| Stated limitations | Not extracted |
| Unstated limitations (note-writer) | All corpora are CIC lab data, so the cross-dataset tests share a generator lineage. Heartbleed and Infiltration have very few flows, yet per-family F1 is about 90–93. Base rate in held-out folds and TPR at fixed low FPR were not found in the parts read |
| Deployment assumptions | Not extracted |
| Demonstrates / claims / untested | **Demonstrates** LOFO and cross-CIC numbers. **Claims** robustness to adaptive, mimicry and poisoning attacks (§VI-G, unverified by the notes). **Untested (as far as read):** non-CIC networks, low-FPR operating points |
| Unresolved questions | Does it hold up against NetMasquerade-style benign mimicry? What is the base rate inside the LOFO folds? |

**KnowML: Improving Generalization of ML-NIDS with Attack Knowledge Graphs** — verification: **ABSTRACT** (arXiv) plus web summary ([arXiv 2506.19802](https://arxiv.org/abs/2506.19802); [UCL Discovery](https://discovery.ucl.ac.uk/id/eprint/10225498))

| Field | Extraction |
|---|---|
| Authors / venue / year | Xin Fan Guo, Xinran Zheng, Albert Meroño Peñuela, Lorenzo Cavallaro, Sergio Maffeis, Fabio Pierazzi; IEEE EuroS&P 2026 |
| Problem | Anomaly-based NIDS generalize poorly to attack variants |
| Hypothesis | Feature spaces suffer from "Out-of-Dimension Blindness" and "Attack Strategy Aggregation Failure". Incremental and contrastive generalization frameworks cannot compensate |
| Mechanism | LLM-built per-family attack knowledge graphs plus symbolic reasoning produce a knowledge-augmented feature space, trained on benign traffic only |
| Datasets / protocol | Not extracted. A web summary says 28 variants, 10 of them newly collected. Whether leave-family-out splits are used was not verified |
| Key results | Up to 99% detection with **FPR ≤ 0.0137%** across attack variants |
| Stated / unstated limitations | Not extracted |
| Demonstrates / claims / untested | **Claims** (abstract level) variant generalization at very low FPR. Split protocol, drift behaviour and adaptive attackers were not verified in the notes |
| Unresolved questions | Is the reported FPR controlled or only measured empirically? How does it behave under temporal drift? |

**PANDORA: Lightweight Adversarial Defense for Edge IoT using Uncertainty-Aware Metric Learning** — verification: **ABSTRACT** (NDSS page) ([NDSS](https://www.ndss-symposium.org/ndss-paper/pandora-lightweight-adversarial-defense-for-edge-iot-using-uncertainty-aware-metric-learning/))

| Field | Extraction |
|---|---|
| Authors / venue / year | Avinash Awasthi, Pritam Vediya, Hemant Miranka, Ramesh Babu Battula, Manoj Singh Gaur; NDSS 2026 |
| Mechanism | Probabilistic, uncertainty-aware embeddings, a new PMSD loss, and a Mamba-MoE architecture aimed at zero-day IoT attack detection |
| Datasets | Introduces TTDFIOTIDS2025. Also uses CICIDS2017 |
| Key results | F1 0.971 with 10-shot adaptation on CICIDS2017. Up to 99% zero-shot accuracy under domain shift. Runs on a Raspberry Pi |
| Everything else | Threat model, protocol (whether LOFO is used) and limitations: **not extracted** |
| Demonstrates / claims / untested | Abstract-level **claims** only |

**RAPIER: Low-Quality Training Data Only? A Robust Framework for Detecting Encrypted Malicious Network Traffic** — verification: **PARTIAL TEXT** (first pages) / ABSTRACT ([NDSS](https://www.ndss-symposium.org/ndss-paper/low-quality-training-data-only-a-robust-framework-for-detecting-encrypted-malicious-network-traffic/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2024-81-paper.pdf))

| Field | Extraction |
|---|---|
| Authors / venue / year | Yuqi Qing, Qilei Yin, Xinhao Deng, Yihao Chen, Zhuotao Liu, Kun Sun, Ke Xu, Jia Zhang, Qi Li; NDSS 2024; DOI 10.14722/ndss.2024.23081. The arXiv preprint dates from Sep 2023 ([arXiv 2309.04798](https://arxiv.org/abs/2309.04798)), so treat it as borderline 2023/2024 |
| Problem / threat model | Detect encrypted malicious traffic from "continuously evolving malware" when training data is scarce, mislabelled or noisy. A formal threat model was not verified |
| Hypothesis | "Normal data is tightly distributed… malicious data is scattered over the entire feature space" |
| Mechanism | Distribution-aware data augmentation, a feature-vector module, and a label-noise-correction module |
| Datasets | Two public datasets, one combined dataset, one real enterprise dataset |
| Key results | With 1,000 samples at 45% label noise, F1 0.770 / 0.776 / 0.855 (average gains of 352.6% / 284.3% / 214.9%). Enterprise best F1 0.773 |
| Unstated limitations (note-writer) | An absolute F1 near 0.77 leaves many errors. The large relative gains reflect weak baselines under 45% noise. Leave-family-out use, compute cost and stated limitations were not verified |

### Tier 1B — Adversarial robustness and certification

**NetMasquerade: A Hard-Label Black-Box Evasion Attack against ML-based Malicious Traffic Detection Systems** — verification: zero-day notes say **PARTIAL TEXT** (first pages plus targeted searches); adversarial notes say extracted from the **primary PDF** ([NDSS page](https://www.ndss-symposium.org/ndss-paper/a-hard-label-black-box-evasion-attack-against-ml-based-malicious-traffic-detection-systems/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf); [arXiv 2510.14906](https://arxiv.org/abs/2510.14906))

| Field | Extraction |
|---|---|
| Authors / venue / year | Zixuan Liu, Yi Zhao (BIT), Zhuotao Liu, Qi Li, Chuanpu Fu, Guangmeng Zhou, Ke Xu (Tsinghua / Zhongguancun Lab); NDSS 2026 (San Diego, 23–27 Feb 2026); DOI 10.14722/ndss.2026.230916 |
| Problem | Can ML traffic detectors be evaded with only drop/no-drop feedback? |
| Threat model | An external botnet adversary sends attack flows through an in-line detector at the victim's ingress. The detector uses flow- or packet-level statistics and no payload. The attacker knows nothing about the model, features, extractor or training data, and sees only whether traffic was dropped (strict hard-label; Kitsune is attacked gray-box). It may use public benign traffic and probe the detector |
| Mechanism | Stage 1: Traffic-BERT pretrained on public benign traffic, with a network-specific tokenizer and a new attention block. Stage 2: an RL agent over a finite-horizon MDP picks the location and type of each packet edit. The reward has dissimilarity and effectiveness penalties, with Q-value threshold ξ′ and step threshold τ |
| Targets / data | Whisper, FlowLens, NetBeacon; Vanilla+RNN, CICFlowMeter+MLP, Kitsune; 12 attacks, 80 scenarios; real backbone traces such as MAWI. Baselines include GAN+PSO mimicry and Amoeba-style splitting |
| Key results | ASR **> 96.65%** overall. Per detector: Whisper 0.9878, FlowLens 0.9717, NetBeacon 0.9809, Vanilla+RNN 0.9782, CICFlowMeter+MLP 0.9626, Kitsune 0.991. At most 10 edits per flow. Bandwidth KL divergence 0.013. 4.239K adversarial packets/s. Evades Whisper (empirically robust) and **BARS** (certified, NDSS 2023) |
| Stated limitations | Needs a probing phase; smaller probing budgets reach 35.6%, 70.4% and 88.9% of final ASR. Degrades gracefully under 5%, 15% and 30% feedback noise. Suggested defences: traffic-space adversarial training, traffic-space certification (e.g., bounding inserted packets), inference-time randomization |
| Unstated limitations (note-writer) | Assumes a static decision boundary, so interaction with periodic retraining is unstudied. **Not evaluated against CertTA** as far as the extracted text shows. Not evaluated against PANTS-hardened models |
| Demonstrates / claims / untested | **Demonstrates** high ASR against six detectors, including certified BARS. **Claims** that feature-space defences "fail to counter" it. **Untested:** CertTA, retraining dynamics, randomized inference |
| Unresolved questions | Do ≤ 10-step edits fall inside CertTA's certified budget? |

**CertTA: Certified Robustness Made Practical for Learning-Based Traffic Analysis** — verification: zero-day notes say **PARTIAL TEXT** (first pages); adversarial notes say extracted from the **primary PDF**; encrypted notes marked the venue UNVERIFIED, but the venue was later confirmed on the official USENIX program ([USENIX page](https://www.usenix.org/conference/usenixsecurity25/presentation/yan-jinzhu); [PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf); [Zenodo](https://zenodo.org/records/15594865))

| Field | Extraction |
|---|---|
| Authors / venue / year | Jinzhu Yan, Zhuotao Liu, Yuyang Xie, Ke Xu (Tsinghua/ZGC Lab), Shiyu Liang (SJTU), Lin Liu (NUDT); USENIX Security 2025, pp. 7349–7368 |
| Threat model | Adversarial flows built from packet insertion, substitution and deletion, length padding and timing delay, alone or combined (Blanket, Amoeba, Prism), within protocol feasibility constraints |
| Mechanism | Multi-modal randomized smoothing. Each sample picks d packets (order kept) and adds i.i.d. Exponential noise to length (β_l) and inter-arrival time (β_t). Theorem 1 bounds the probability ratio jointly over additive and edit perturbations (n_ins, n_sub, n_del), combining a binomial term with exp(Σ δ_l/β_l + δ_t/β_t) |
| Models / datasets / baselines | kFP, Kitsune, Whisper, DF, YaTC, TrafficFormer, plus three unsupervised models in the artifact. Datasets CICDOH20 and TIISSRC23. Baselines VRS, BARS, RS-Del |
| Key results | Where baselines certify nothing, **99%** certified accuracy for the two Transformer models and **> 80%** for the other four. Proposes pairing with an anomaly detector to create an attacker dilemma |
| Stated assumptions | Guarantees hold only within the certified edit/δ budget, are probabilistic (Monte-Carlo), and use per-dataset tuned hyperparameters (e.g., β_l = 100, β_t = 20 ms, d = ⌈0.2n⌉) |
| Unstated limitations (note-writer) | Per-flow only, so multi-flow and campaign attacks are not covered. Feature-extractor state (e.g., Kitsune damped windows across flows) is not covered |
| Demonstrates / claims / untested | **Demonstrates** certified accuracy on two datasets. **Untested:** NetMasquerade-style adaptive attack, CertTA-aware attacks |

**PANTS: Robustifying ML-powered Network Classifiers with PANTS** — verification: **primary PDF** (adversarial notes); USENIX abstract (sweep) ([USENIX](https://www.usenix.org/conference/usenixsecurity25/presentation/jin-minhao); [PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf))

| Field | Extraction |
|---|---|
| Authors / venue / year | Minhao Jin, Maria Apostolaki (Princeton); USENIX Security 2025, pp. 7291–7310 |
| Problem | ML network classifiers contain non-differentiable components, and their adversarial inputs must be realizable and semantics-preserving |
| Threat model | White-box, with full access to implementation and training data. Operator-configured domain rules (e.g., TCP never ACKs a packet before it is sent). End-host attacker: delay ≤ 20% of flow duration and modify ≤ 20% of packets. In-path attacker: one-direction delay ≤ 20% |
| Mechanism | Adversarial ML (e.g., PGD) proposes feature-space targets on vulnerable features. An SMT solver finds a realizable packet sequence. This runs inside iterative adversarial training (about 180 samples per benign sample) at about 1.7 samples/s |
| Datasets | VPN detection (ISCXVPN2016, 8,577 flows), QoE inference (VCAML), and a third application (UNVERIFIED). Models MLP, CNN, Transformer, RF |
| Key results | Median ASR 35.31% vs 19.57% (Amoeba) and 10.31% (BAP). One case deceives MLP / CNN / Transformer at 81.12% / 94.25% / 99.80%. Robustified models **52.7%** more robust, including against out-of-scope attackers, without accuracy loss. Non-realizable training is far less effective (e.g., 92% less for RF) |
| Unstated limitations (note-writer) | Not adapted to a defence-aware attacker. Not tested against NetMasquerade |

**"What is the Problem Space?" Defining Host-space Adversarial Perturbations against NIDS** — verification: arXiv full text / abstract ([arXiv 2605.25822](https://arxiv.org/abs/2605.25822); [PDF](https://arxiv.org/pdf/2605.25822))

| Field | Extraction |
|---|---|
| Authors / venue / year | Miel Verkerken, Laurens D'hooge, Bruno Volckaert, Filip De Turck, Giovanni Apruzzese; ACM AsiaCCS 2026 |
| Problem / hypothesis | A review of 316 papers finds prior work perturbs pre-collected packets or flows, which may be beyond an attacker who controls only unprivileged hosts |
| Mechanism | Defines host-space perturbations (HsP): executing a different set of operations (𝒪′ ≠ 𝒪) to reach the same goal. HsP satisfies Pierazzi et al.'s problem-space properties |
| Datasets | Models trained on CICIDS17/18. Confirmed on benchmarks and on a real network |
| Key results | Changing one character of a `patator` SSH brute-force command evades detection; the sweep notes say detectors miss every attempt. Switching tools (Hydra, Medusa) evades some models (e.g., SVM) |
| Untested (note-writer) | No defences against HsP were evaluated. Which character was changed is UNVERIFIED |

### Tier 1C — Evaluation critiques that set reviewer expectations

**Bad Design Smells in Benchmark NIDS Datasets** — verification: **[VERIFIED-primary]** author final draft (full text partly extracted; §8 limitations not extracted) ([final draft](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf); [DBLP](https://dblp.org/rec/conf/eurosp/FloodEAD24.html); [IEEE Xplore](https://ieeexplore.ieee.org/document/10629000))

| Field | Extraction |
|---|---|
| Authors / venue / year | Robert Flood, Gints Engelen, David Aspinall, Lieven Desmet; IEEE EuroS&P 2024, pp. 658–675 |
| Problem | Synthetic NIDS benchmarks are rarely audited, and the design choices behind them bias experiments |
| Datasets | ISCX 2012, CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15, CTU-13, Bot-IoT, ToN-IoT (65+ attack classes). The program-page abstract says "six highly cited" benchmarks, which conflicts with this list of seven |
| Mechanism | Manual analysis plus six heuristics. Review of 38 papers (2015–2023); 4 re-run in detail |
| Key results | On UNSW-NB15, Protocol and TTL alone separate the classes with 98% accuracy. A gradient-free TTL/protocol perturbation "achieves identical performance to AJSMA". ADA's reported advantage shrinks to a 1.5% gap. CIC-IDS2017 train and test sets overlap almost entirely under the standard pipeline. CSE-CIC-IDS2018 Infiltration contains duplicated benign flows. Regenerating DoS Hulk with DetGen raised diversity to 0.89 and 0.62 |
| Recommendations | Define generalization. Avoid same-class, same-dataset train/test. Do not use provided features blindly. Tie features to attack mechanism. Run fragility tests. Dataset creators should provide TESSERACT-style space/time-distinct test sets and BPF filters |
| Unstated limitations (note-writer) | Synthetic datasets only. No replacement benchmark. Heuristics not validated against ground truth. Award status conflicting (Best vs Distinguished Paper, unconfirmed) |

**SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers** — verification: **ABSTRACT** (arXiv) ([arXiv 2503.20093](https://arxiv.org/abs/2503.20093))

| Field | Extraction |
|---|---|
| Authors / venue / year | Nimesha Wickramasinghe, Arash Shaghaghi, Gene Tsudik, Sanjay Jha; IEEE S&P 2025, pp. 1825–1843 |
| Key results | "The majority of proposed encrypted traffic classifiers have mistakenly utilized unencrypted traffic due to the use of legacy datasets". 348 feature-occlusion experiments show design oversights cause overfitting. Releases CipherSpectrum, a TLS 1.3-era dataset ([HTML v4](https://arxiv.org/html/2503.20093v4)) |
| Not extracted | Number of papers surveyed, classifiers tested, per-model numbers |
| Relevance note | The same first and last authors wrote the IMC 2026 PQ-TLS measurement ([arXiv 2607.29005](https://arxiv.org/abs/2607.29005)) |

**True Attacks, Attack Attempts, or Benign Triggers? An Empirical Measurement of Network Alerts in a SOC** — verification: **ABSTRACT** (USENIX page) ([USENIX](https://www.usenix.org/conference/usenixsecurity24/presentation/yang-limin))

| Field | Extraction |
|---|---|
| Authors / venue / year | Limin Yang, Zhi Chen, Chenkai Wang, Zhenning Zhang, Sushruth Booma, Phuong Cao, Constantin Adam, Alexander Withers, Zbigniew Kalbarczyk, Ravishankar K. Iyer, Gang Wang; USENIX Security 2024 |
| Data / protocol | 4 years of real SOC network alerts (115M, 2018–2022) checked against ground truth for 227 successful attacks |
| Key results | 24K–134K alerts/day. Only **0.01%** tied to true attacks; 27% are "attack attempts" and 49% "benign triggers". Rare or abnormal alert patterns could help isolate true attacks |

**On the Cross-Dataset Generalization of ML for Network Intrusion Detection** — verification: **ABSTRACT** ([arXiv 2402.10974](https://arxiv.org/abs/2402.10974))

| Field | Extraction |
|---|---|
| Authors / venue / year | Marco Cantone, Claudio Marrocco, Alessandro Bria; IEEE Access 12:144489–144508, 2024 (not a top security venue) |
| Datasets | CIC-IDS2017, CSE-CIC-IDS2018, LycoS-IDS2017, and the new LycoS-Unicas-IDS2018; four classifiers (names not checked) |
| Key results | Within a dataset: "nearly perfect". Across datasets: "largely commensurate with random chance", except a few combinations, attributed partly to data anomalies. Per-pair tables were not extracted |

### Tier 1D — Drift, calibration and update-loop papers that bound a guarantee claim

**Revisiting Concept Drift in Windows Malware Detection** — verification: **PARTIAL TEXT** (NDSS slides plus pages 1–2) ([NDSS page](https://www.ndss-symposium.org/ndss-paper/revisiting-concept-drift-in-windows-malware-detection-adaptation-to-real-drifted-malware-with-minimal-samples/); [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2025-830-paper.pdf))

| Field | Extraction |
|---|---|
| Authors / venue / year | Adrian Shuai Li, Arun Iyengar, Ashish Kundu, Elisa Bertino; NDSS 2025 |
| Mechanism | CFG plus PalmTree instruction embeddings, then a GNN with DANN-style adversarial domain adaptation. Includes an outlier module for new families |
| Data / protocol | Microsoft Big-15, and 2024 real daily malware with monthly tasks (source Mar–May 2024; targets Jul/Aug and Aug/Sep) |
| Key results | Smallest accuracy drop on Big-15 (0.5% average). 200 labels/month match labelling 75% of the data (warm-start needs 500). Family classification +9–14% with 10 samples per family. Evasion rate for new families < 5% |
| Stated caveat | Big-15 families "exhibit highly similar characteristics", which likely overestimates accuracy |
| Untested | No calibration or conformal guarantee. Formal threat model not checked |

**DREAM: Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification** — verification: **ABSTRACT** ([arXiv 2405.04095](https://arxiv.org/abs/2405.04095)). Yiling He, Junchi Lei, Zhan Qin, Kui Ren, Chun Chen; ACM CCS 2025. Concepts are embedded in a contrastive-autoencoder latent space, and drift is detected without training data. Reaches the same accuracy with **76.6% fewer new labels** when updating Drebin. Datasets, baselines and limitations were not checked.

**EnCP: Ensemble Conformal Predictor with Robustness Guarantees against Data Poisoning Attacks** — verification: **TITLE ONLY / UNVERIFIED** (official S&P 2026 list plus researchr record) ([researchr](https://researchr.org/publication/YangLFSW26/authors); [S&P 2026 list](https://sp2026.ieee-security.org/accepted-papers.html)). Yuxin Yang, Qiang Li, Runyang Feng, Liren Shan, Binghui Wang; S&P 2026, pp. 156–174. A conformal predictor with provable robustness to training or calibration poisoning. The certificate form is UNVERIFIED, and it does not appear to be detector-specific or to address drift.

**Robust Conformal Intrusion Detection via Traffic-Aware Calibration and Attack-Orbit Invariance** — verification: **ABSTRACT** ([arXiv 2609.19241](https://arxiv.org/abs/2609.19241)). Zhenpeng Li; arXiv (submitted to IEEE TDSC; the submission date shown does not match the 2609 ID). Shows that clean-traffic conformal thresholds lose coverage under adversarial feature changes on three IDS benchmarks. Traffic-aware calibration restores coverage only when the perturbation mechanism is known and can be sampled. Excluding attacker-controllable features and their descendants gives an "exact, pathwise" coverage guarantee at a cost of **7–14 points** of clean accuracy. Benchmark names are NOT VERIFIED.

**Candidate Comparability Before Promotion: Conditional Validation in Adaptive NIDS** — verification: **ABSTRACT** ([arXiv 2609.04388](https://arxiv.org/abs/2609.04388)). Fernández-Barrios, Pastor-López, Pikatza-Huerga, García Bringas; arXiv Sep 2026, not peer reviewed. Data: CICIDS2017, UNSW-NB15, ToN-IoT, plus 13 real time-ordered replays. Reusing the incumbent's frozen preprocessing inflated apparent promotion harm. Raising evidence from 512 to 2,000 samples per class improved promotion by +0.53, +1.67 and +0.38 balanced-accuracy points, mostly through fewer false positives. No policy among nine dominated, and "always deploy" caused no net harm in the real replays.

**Test-Time Poisoning Attacks Against Test-Time Adaptation Models** — verification: **ABSTRACT** ([arXiv 2308.08505](http://arxiv.org/abs/2308.08505)). Tianshuo Cong, Xinlei He, Yun Shen, Yang Zhang; IEEE S&P 2024. The first test-time poisoning attacks on TTA methods (TTT, DUA, TENT, RPL). Generic ML, not NIDS.

**Persistent Backdoor Attacks in Continual Learning** — verification: **ABSTRACT** ([USENIX](https://www.usenix.org/conference/usenixsecurity25/presentation/guo-zhen)). Zhen Guo, Abhinav Kumar, Reza Tourani; USENIX Security 2025. Blind Task and Latent Task backdoors persist through continual updates and evade SentiNet and I-BAU. Vision-style triggers, not security data.

### Tier 1E — Encrypted traffic and post-quantum TLS

**The Colossus with Feet of Clay: Debunking Encrypted Traffic Classifiers under PQC Evolution** — verification: **ABSTRACT** ([arXiv 2608.22683](https://arxiv.org/abs/2608.22683)). Bingzhen Li et al.; arXiv Aug 2026, not peer reviewed, with code at an anonymous 4open.science repository. Hypothesis: "PQC-induced protocol drift". The setting is closed-world HTTPS website fingerprinting over TLS 1.3 with X25519MLKEM768, testing 5 classifiers in matched-domain, cross-domain and deployment-ratio settings. Website information stays learnable, but configurations that work in-domain lose reliability across cryptographic domains. The segmentation-shift mechanism is SNIPPET-ONLY, and exact accuracy drops were not extracted. It covers website fingerprinting, not NIDS.

**Extending C2 Traffic Detection Methodologies: From TLS 1.2 to TLS 1.3-enabled Malware** — verification: **ABSTRACT** (RAID PDF first page) ([PDF](https://raid2024.github.io/papers/raid2024-31.pdf)). Diogo Barradas, Carlos Novo, Bernardo Portela, Sofia Romeiro, Nuno Santos; RAID 2024. TLS 1.3's encrypted handshake degrades C2 classifiers trained on TLS 1.2. The paper infers certificate size within 1.0% error, giving 100% detection from certificate size and over 93% on TLS 1.3 behaviour when trained only on TLS 1.2. The sweep treats it as the closest analogue to a protocol-evolution-versus-detector study.

**Classifying Implementations of Cryptographic Primitives and Protocols that Use PQ Algorithms** — verification: **ABSTRACT** ([arXiv 2503.17830](https://arxiv.org/abs/2503.17830)). Mallick, Nita-Rotaru, Kundu, Kompella; arXiv 2025–2026. Distinguishes classical vs PQ key exchange at **98%**, signatures at 100%, the specific KEM at 97%, the specific PQ signature at 86%, and liboqs vs CIRCL at up to 100%. Integrated into Cisco's QUARTZ analyzer.

**Mind the Gap: Policy vs Reality in Post-Quantum TLS Deployment** — verification: **ABSTRACT** ([arXiv 2607.29005](https://arxiv.org/abs/2607.29005)). Wickramasinghe, Li, Jha, Shaghaghi; accepted to ACM IMC 2026. Over 2 billion handshakes, 1 million domains, 11 vantage points. Deployment converges on a single hybrid, is driven by CDNs, and adds no meaningful latency. The abstract does not mention middleboxes or IDS.

### Tier 2 — Important adjacent papers (compact extraction)

| Paper (venue, year) | Verification | Problem → mechanism | Key result | Untested / caveat recorded in notes |
|---|---|---|---|---|
| Detecting and Mitigating Sampling Bias with Unlabeled Data (USENIX Sec 2024) ([link](https://www.usenix.org/conference/usenixsecurity24/presentation/thirumuruganathan)) | ABSTRACT | Train/production shift → domain-discrimination detection and adaptation-inspired mitigation using unlabeled data | F-score +10–16 points (AndroZoo 0.83→0.937); includes intrusion-detection data | No FPR guarantee claimed |
| Facade (USENIX Sec 2026) ([link](https://www.usenix.org/conference/usenixsecurity26/presentation/kantchelian)) | ABSTRACT | Benign-only contrastive contextual anomaly detection on insider logs, deployed at Google since 2018 | FPR < 0.01% (0.0003% for single rogue events) | Empirical, not a guarantee; not network flows |
| Retrofit (USENIX Sec 2026) ([link](https://www.usenix.org/conference/usenixsecurity26/presentation/he-yiling)) | ABSTRACT | Continual learning with controlled forgetting via two-teacher aggregation | Retention 20.2%→38.6% under temporal malware drift | Not NIDS |
| LogInject (USENIX Sec 2026) ([link](https://www.usenix.org/conference/usenixsecurity26/presentation/karanjai)) | ABSTRACT | Prompt injection planted in log fields against SOC LLM triage | 76.4% success for fragmented payloads; defences cut attacks 90.4%, leaving 8.4% residual | — |
| AIOpsDoom/AIOpsShield (USENIX Sec 2026) ([link](https://www.usenix.org/conference/usenixsecurity26/presentation/pasquini)) | ABSTRACT | Telemetry injection misleads autonomous LLM remediation agents | AIOpsShield blocks the attacks | — |
| You Know Why, but Still Rely (USENIX Sec 2026) ([link](https://www.usenix.org/conference/usenixsecurity26/presentation/roch)) | ABSTRACT | XAI user study (N=139) on malicious-domain blocking | XAI did not raise trust or performance; experts trusted less after it | Not NIDS |
| Tracegram (USENIX Sec 2026) ([link](https://www.usenix.org/conference/usenixsecurity26/presentation/qu)) | ABSTRACT | Trace-level multiple-instance learning for traffic | Better than or comparable to SOTA on 4 datasets; key-flow attribution aligns with APT phases | Split protocol unknown |
| ISDC (USENIX Sec 2024) ([link](https://www.usenix.org/conference/usenixsecurity24/presentation/mirnajafizadeh)) | ABSTRACT | In-network serverless flow-data collection | Fixes "model self-poisoning" caused by duplicated or fragmented flow measurements | — |
| BEAM routing anomaly detection (USENIX Sec 2024) ([link](https://www.usenix.org/conference/usenixsecurity24/presentation/chen-yihao)) | ABSTRACT | Semantics-aware BGP anomaly detection | ≤ 5 false alarms per 180M announcements; 1.65 false alarms/day in an ISP deployment | Routing, not flows |
| AMIDES (USENIX Sec 2024) ([link](https://www.usenix.org/conference/usenixsecurity24/presentation/uetz)) | ABSTRACT | Detects evasions of SIEM rules | Most of 500+ evasions detected "without any false alerts" | — |
| MAGIC (USENIX Sec 2024) ([link](https://www.usenix.org/conference/usenixsecurity24/presentation/jia-zian)) | ABSTRACT | Masked graph learning for provenance APT detection, with concept-drift adaptation | 3 datasets | Host IDS |
| Sometimes Simpler is Better (USENIX Sec 2025) ([link](https://www.usenix.org/conference/usenixsecurity25/presentation/bilot)) | ABSTRACT | Reimplementation of 8 provenance IDSs | 9 shortcomings; a simple NN matches SOTA on 5 of 7 DARPA datasets | Host IDS |
| ORTHRUS (USENIX Sec 2025) ([link](https://www.usenix.org/conference/usenixsecurity25/presentation/jiang-baoxiang)) | ABSTRACT | Quality of Attribution in provenance IDS | Orders-of-magnitude fewer nodes to inspect | Host IDS; criticizes evaluations that ignore class imbalance |
| GeCo (USENIX Sec 2025) ([PDF](https://www.usenix.org/system/files/usenixsecurity25-wolsing.pdf)) | PARTIAL TEXT (first pages) / ABSTRACT | Comprehensible state-space models of benign industrial process behaviour | On par with expert rules | Process data, not packet/flow |
| GEAD, Rules Refine the Riddle (CCS 2024) ([SCU](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368)) | SECONDARY (portal abstract / DBLP record) | Global rule extraction from DL anomaly detectors, including NIDS | SCADA deployment; CCS Distinguished Artifact Award | Fidelity numbers UNVERIFIED |
| Ano2Rule (IEEE TDSC 2026) ([Lancaster](https://eprints.lancs.ac.uk/id/eprint/236142)) | ABSTRACT | Rule-based global interpretation of unsupervised anomaly detection | "High fidelity" on NIDS and IoT data | Numbers NOT VERIFIED |
| KnowGraph (CCS 2024) ([arXiv 2410.08390](http://arxiv.org/abs/2410.08390)) | ABSTRACT | GNN plus logical reasoning for anomaly detection under shift; network-traffic intrusion detection as one application | — | — |
| tFusion, Training with Only 1.0‰ Samples (CCS 2025) ([secrss](https://www.secrss.com/articles/89823)) | SECONDARY | Cross-modality fusion plus topology-driven contrastive pre-training | 99.82% accuracy in a real deployment with 1.0‰ labels; 11 datasets | Secondary source only |
| CoLD (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/cold-collaborative-label-denoising-framework-for-network-intrusion-detection/)) | PARTIAL TEXT (first pages) / ABSTRACT | Label noise in NIDS → feature-subset joint learning plus causal denoising | Not extracted | — |
| Entente (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/entente-cross-silo-intrusion-detection-on-network-log-graphs-with-federated-learning/)) | ABSTRACT | Federated graph NIDS (LANL, OpTC, Pivoting) | Bounds the success of FL poisoning | — |
| MineShark (NDSS 2025) ([NDSS](https://www.ndss-symposium.org/ndss-paper/mineshark-cryptomining-traffic-detection-at-scale/)) | ABSTRACT | Line-rate mining detection; active probing confirms alarms and drives self-updates | Filtered > 99.3% of false alarms over 10 months at 10 Gbps | Attacks on its update loop not studied |
| On Precisely Detecting Censorship Circumvention (NDSS 2024) ([NDSS](https://www.ndss-symposium.org/ndss-paper/on-precisely-detecting-censorship-circumvention-in-real-world-networks/)) | ABSTRACT | Base-rate fallacy in DL flow classifiers | > 94% false positives at realistic base rates; host-level accumulation over 60M flows reaches perfect recall with no FPs | — |
| Indicator of Benignity (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/indicator-of-benignity-an-industry-view-of-false-positive-in-malicious-domain-detection-and-its-mitigation/)) | ABSTRACT | Six years of vendor FP reports; LLM-based IOBHunter | 99.22% precision, 68.6% recall; 4,338 confirmed FPs found | Domains, not flows |
| Proteus, WF against traffic drift (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/enhancing-website-fingerprinting-attacks-against-traffic-drift/)) | ABSTRACT | Label-free drift adaptation (MMD, entropy, GMM pseudo-labels) | +94.24% F1 on average across 6 drift scenarios | WF attack, not NIDS |
| Beyond RTT (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/beyond-rtt-an-adversarially-robust-two-tiered-approach-for-residential-proxy-detection/)) | ABSTRACT | Robust residential-proxy detection | RTT detectors fall from 99% to 8% recall under scheduling; CorrTransform keeps > 92% F1; 15 months, 900 GB | — |
| Strategic Games and Zero-Shot Attacks on Heavy-Hitter Monitoring (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/strategic-games-and-zero-shot-attacks-on-heavy-hitter-network-flow-monitoring/)) | ABSTRACT | RL adversaries against flow monitors | Up to 299% over bandwidth caps; succeeds against 8 of 9 systems | — |
| Incident Response Planning with a Lightweight LLM (NDSS 2026) ([NDSS](https://www.ndss-symposium.org/ndss-paper/incident-response-planning-using-a-lightweight-large-language-model-with-reduced-hallucination/)) | ABSTRACT | Fine-tuning, retrieval and lookahead planning | Proven bound on hallucination probability; recovery up to 22% shorter | Bound is on hallucination, not FPR |
| SketchFeature (NDSS 2025) ([NDSS](https://www.ndss-symposium.org/ndss-paper/sketchfeature-high-quality-per-flow-feature-extractor-towards-security-aware-data-plane/)) | ABSTRACT | Approximate data-plane extractors open an evasion avenue → sketch-based extractor | Near-optimal detection | — |
| Density Boosts Everything (NDSS 2025) ([NDSS](https://www.ndss-symposium.org/ndss-paper/density-boosts-everything-a-one-stop-strategy-for-improving-performance-robustness-and-sustainability-of-malware-detectors/)) | ABSTRACT | Feature sparsity as a shared root of poisoning, evasion and drift | Improves robustness over time | Malware |
| Evaluating ML-based IoT Device Identification (NDSS 2025) ([NDSS](https://www.ndss-symposium.org/ndss-paper/evaluating-machine-learning-based-iot-device-identification-models-for-security-applications/)) | ABSTRACT | Degradation under operating modes, spatio-temporal variation and sampling | — | — |
| 5G-Spector (NDSS 2024) ([NDSS](https://www.ndss-symposium.org/ndss-paper/5g-spector-an-o-ran-compliant-layer-3-cellular-attack-detection-service/)) | ABSTRACT | Cellular L3 detection as an O-RAN xApp | Generalizes to 11 unknown attacks; no false alarms on 31 traces | Cellular |
| No Need for Details (RAID 2024) ([PDF](https://raid2024.github.io/papers/raid2024-41.pdf)) | ABSTRACT | Protocol-agnostic one-class ICS traffic detection | Tests transfer to foreign scenarios | ICS |
| Cross-Regional Malware Detection (RAID 2024) ([PDF](https://raid2024.github.io/papers/raid2024-3.pdf)) | ABSTRACT | Temporally ordered AV data from USA, Brazil, Japan | Only the FL global model increases detection | Malware |
| ADAPT (RAID 2025 per sweep; arXiv) ([arXiv 2507.08597](https://arxiv.org/abs/2507.08597)) | ABSTRACT / SECONDARY | Drift-aware pseudo-labelling, model-agnostic | Gains on 5 malware datasets; "catastrophic self-poisoning" framing is snippet-level | Drift notes listed no venue; the sweep places it at RAID 2025 |
| Carbon Filter (RAID 2025) ([UIUC](https://sts.cs.illinois.edu/papers/paper/CarbonFilterScalable20251019.html)) | SECONDARY | EDR alert triage from command-line context | > 82% fewer false alerts; AUC 0.94 | EDR |
| Ruling the Unruly (AsiaCCS 2025) ([arXiv 2501.09808](https://arxiv.org/abs/2501.09808)) | ABSTRACT | Suricata rule design at a managed SOC | Six design principles; specificity vs coverage trade-off | — |
| R+R: From Claims to Crashes (ACSAC 2025) ([papers](https://www.acsac.org/2025/program/papers/); [arXiv 2503.20281](https://arxiv.org/abs/2503.20281)) | ABSTRACT of probable preprint; link INFERRED | Re-evaluation of graph NIDS | "Significant performance discrepancies"; FPR and robustness hard to reproduce | Preprint-to-paper link not verified |
| LLMs in the SOC (S&P 2026) ([arXiv 2508.18947](http://arxiv.org/abs/2508.18947)) | ABSTRACT | 3,090 queries from 45 analysts over 10 months | Analysts use LLMs for sensemaking, not high-stakes decisions | — |
| Contorter, A Context is Worth a Thousand Lies (S&P 2026) ([PDF](https://azadeht.github.io/papers/Contorter_sp26.pdf)) | SECONDARY (search summary of author PDF) | Context-distortion evasion of node-level provenance IDS | — | Authors unverified; host, not flows |
| TrafficFormer (S&P 2025) ([group page](https://liuzhuotao.github.io/publications/secure_networking_and_systems_infrastructure/encrypted_traffic_analysis/1-2-7)) | SECONDARY (group page); venue confirmed on [S&P 2025 list](https://sp2025.ieee-security.org/accepted-papers.html) by sweep, UNVERIFIED in the encrypted notes | Traffic pre-training model | Up to +10% F1 on 6 datasets | No zero-day or open-set evaluation found |
| The Sweet Danger of Sugar (SIGCOMM 2025) ([arXiv 2507.16438](https://arxiv.org/abs/2507.16438)) | ABSTRACT; detailed numbers SNIPPET-ONLY | Representation-learning traffic classifiers inflated by shortcuts; proposes Pcap-Encoder | Performance collapses without shortcuts (~80% drop and same-flow leakage are snippet-only) | Not a target security venue |
| netFound (arXiv, v5 2026) ([arXiv 2310.17025](https://arxiv.org/abs/2310.17025)) | ABSTRACT | Principled NFM design; 4.2B-flow pretraining corpus | Exogenous-context F1 0.95 vs < 0.62 | No zero-day breakdown |
| Demystifying NFMs (arXiv 2025) ([arXiv 2509.23089](https://arxiv.org/abs/2509.23089)) | ABSTRACT | Anisotropy, shortcut and payload dependence in 4 NFMs | Up to +0.35 F1 from fixes | — |
| NetVAD (arXiv; IEEE ISI) ([arXiv 2606.01452](https://arxiv.org/abs/2606.01452)) | ABSTRACT | VAE on NFM embeddings, benign-only, identifier-free | 98% micro-F1 on ToN-IoT "at an operational FPR" | Threshold calibrated with attack labels; misses single-packet reconnaissance |
| Aurora (arXiv 2025–26) ([arXiv 2505.22843](https://arxiv.org/abs/2505.22843)) | ABSTRACT | Reliability and stability of selective malware classifiers under drift (AURC) | SOTA frameworks fragile | No numbers or venue |
| Li, Akil, Bertino, drift-adaptive robustness (arXiv 2026) ([arXiv 2604.06599](https://arxiv.org/abs/2604.06599)) | ABSTRACT | PGD and MalGuise against AdvDA over 5 monthly windows, 3 FPR points | 100% PGD / 13% MalGuise undefended → 3.2% / 5.1% after robustification; no transfer between threat models | Evasion, not update-loop poisoning |
| PCAP-Backdoor (arXiv 2025) ([arXiv PDF](https://arxiv.org/pdf/2501.15563)) | arXiv full text | PCAP-level triggers before feature extraction | 0.97 ASR at 2% poisoning vs 35% for label flipping | Venue UNVERIFIED |
| ALERT-BENCH / AIDA (arXiv 2026) ([arXiv 2610.10608](https://arxiv.org/abs/2610.10608)) | ABSTRACT | 1,247 alerts from one scenario through a live SIEM | All baselines miss ≥ 40.4% of attack alerts; AIDA F1 0.958, FNR 3.1%, 18.4% escalated | Single scenario |
| OpenSec (arXiv 2026) ([arXiv 2601.21083](https://arxiv.org/abs/2601.21083)) | ABSTRACT | IR agent calibration under prompt injection, 40 episodes per model | GPT-5.2: 100% containment, 82.5% FP; Sonnet 4.5: 62.5% containment, 45% FP | Conflicting secondary "90–97%" figure rejected |

---

## Master table of all 2024–2026 papers recorded in the notes

**Verification codes:**
- **F** = full text
- **P** = partial text (first pages, slides or targeted sections)
- **A** = abstract (official page or arXiv)
- **S** = secondary or snippet only
- **T** = title only / UNVERIFIED

**Topic tags:**
- ZD = zero-day / unseen
- DR = drift / continual / shift
- XD = cross-dataset
- ADV = evasion
- POI = poisoning / backdoor
- CERT = certified
- FP = false-positive control / calibration / conformal
- XAI = explainability
- LLM = LLM triage / response
- ENC = encrypted traffic
- PQ = post-quantum
- EVAL = dataset / evaluation pitfalls
- FM = foundation model
- HOST = provenance / host IDS (adjacent)
- PER = peripheral

Venue and paper membership come from official lists in the two sweeps ([USENIX/S&P sweep sources](https://www.usenix.org/conference/usenixsecurity25/technical-sessions); [CCS 2025 JSON](https://www.sigsac.org/ccs/CCS2025/assets/accepted-papers.json); [NDSS 2026 list](https://www.ndss-symposium.org/ndss2026/accepted-papers/)).

| # | Paper (short title) | Venue | Year | Tag | Ver. |
|---|---|---|---|---|---|
| 1 | True Attacks, Attack Attempts, or Benign Triggers? (SOC alerts) | USENIX Sec | 2024 | FP, EVAL | A |
| 2 | Detecting and Mitigating Sampling Bias with Unlabeled Data | USENIX Sec | 2024 | DR, EVAL | A |
| 3 | Learning with Semantics (BEAM routing anomaly) | USENIX Sec | 2024 | FP, XAI | A |
| 4 | You Cannot Escape Me (AMIDES) | USENIX Sec | 2024 | ADV, FP | A |
| 5 | ISDC in-network data collection | USENIX Sec | 2024 | POI (self-poisoning) | A |
| 6 | MAGIC | USENIX Sec | 2024 | HOST, ZD, DR | A |
| 7 | Fingerprinting Obfuscated Proxy Traffic (encapsulated TLS) | USENIX Sec | 2024 | ENC | A |
| 8 | How does Endpoint Detection use MITRE ATT&CK? | USENIX Sec | 2024 | EVAL | A |
| 9 | A Wolf in Sheep's Clothing (MalGuise) | USENIX Sec | 2024 | ADV | A |
| 10 | SAIN (ICS invariants) | USENIX Sec | 2024 | PER | A |
| 11 | ChainPatrol | USENIX Sec | 2024 | PER | A |
| 12 | Uncovering the Limits of ML for Vulnerability Detection | USENIX Sec | 2024 | EVAL | A |
| 13 | Unveiling the Hunter-Gatherers; DHS threat hunting; WF subpages; Verify your Labels!; CalcuLatency | USENIX Sec | 2024 | PER (Verify your Labels: POI/label noise) | A |
| 14 | Robustifying ML Network Classifiers (PANTS) | USENIX Sec | 2025 | ADV | F (primary PDF) / A |
| 15 | CertTA | USENIX Sec | 2025 | CERT, ADV | P / F (notes differ) |
| 16 | Sometimes Simpler is Better | USENIX Sec | 2025 | HOST, EVAL | A |
| 17 | ORTHRUS | USENIX Sec | 2025 | HOST, FP | A |
| 18 | TAPAS | USENIX Sec | 2025 | HOST | A |
| 19 | GeCos Replacing Experts (GeCo) | USENIX Sec | 2025 | ZD, XAI (ICS) | P / A |
| 20 | AutoLabel | USENIX Sec | 2025 | EVAL (labelling) | A |
| 21 | Persistent Backdoor Attacks in Continual Learning | USENIX Sec | 2025 | POI, DR | A |
| 22 | Fighting Fire with Fire (HagDe) | USENIX Sec | 2025 | ADV | A |
| 23 | VAPD | USENIX Sec | 2025 | ADV, ZD | A |
| 24 | Gotta Detect 'Em All (FBSDetector) | USENIX Sec | 2025 | NIDS (cellular) | A |
| 25 | Lemon | USENIX Sec | 2025 | PER | A |
| 26 | Preventing Artificially Inflated SMS Attacks | USENIX Sec | 2025 | FP (PER) | A |
| 27 | Ares | USENIX Sec | 2025 | FP (routing) | A |
| 28 | UPGen | USENIX Sec | 2025 | ADV, ENC | A |
| 29 | Predictive Response Optimization | USENIX Sec | 2025 | LLM/response (PER) | A |
| 30 | Expert Insights into APTs; SoK TTP Extraction; Ransomware Decade; IoC attribution | USENIX Sec | 2025 | PER | A/T |
| 31 | Retrofit | USENIX Sec | 2026 | DR | A |
| 32 | Tracegram | USENIX Sec | 2026 | ENC, XAI | A |
| 33 | Context Contamination (LogInject) | USENIX Sec | 2026 | LLM, ADV | A |
| 34 | When AIOps Become "AI Oops" | USENIX Sec | 2026 | LLM, ADV | A |
| 35 | Cutting the Fuse (ProvX) | USENIX Sec | 2026 | HOST, XAI, response | A |
| 36 | DUPIN | USENIX Sec | 2026 | HOST, FM, FP | A |
| 37 | Facade | USENIX Sec | 2026 | FP (low-FPR) | A |
| 38 | SoK: Pitfalls of DRL for Cybersecurity | USENIX Sec | 2026 | EVAL | A |
| 39 | You Know Why, but Still Rely | USENIX Sec | 2026 | XAI | A |
| 40 | Credible Threat Detection? (Sigma) | USENIX Sec | 2026 | FP, update risk | A |
| 41 | From Texts to Rules (SIGMERGE) | USENIX Sec | 2026 | LLM | A |
| 42 | Practical Few-shot Multi-tab WF (MMF) | USENIX Sec | 2026 | ENC, ZD | A |
| 43 | Estimating Script-generated Traffic | USENIX Sec | 2026 | PER | A |
| 44 | Security Tools Don't Detect Attacks; Cryptography at Scale (PQ inventory) | USENIX Sec | 2026 | Invited talks, not refereed (PQ) | A |
| 45 | KAIROS | IEEE S&P | 2024 | HOST, ZD | A (arXiv) |
| 46 | FLASH | IEEE S&P | 2024 | HOST | T |
| 47 | R-CAID | IEEE S&P | 2024 | HOST, XAI | T |
| 48 | Jbeil | IEEE S&P | 2024 | DR (lateral movement) | S |
| 49 | Multi-Instance Adversarial Attack on GNN Domain Detection | IEEE S&P | 2024 | ADV | A (arXiv) |
| 50 | Test-Time Poisoning against TTA | IEEE S&P | 2024 | POI, DR | A (arXiv) |
| 51 | DrSec; Unsupervised Network Representation Learning gap; DNS Reputation attacks; Prefix DDoS; Cerberus; SoK XAI in Adversarial Environments; CaFA; WF defense; Pryde; WAF evasion; IR Playbooks; eAUDIT | IEEE S&P | 2024 | mixed (ADV/XAI/EVAL/PER) | T |
| 52 | SoK: Decoding the Enigma of Encrypted Traffic Classifiers | IEEE S&P | 2025 | ENC, EVAL | A |
| 53 | MANTIS | IEEE S&P | 2025 | ZD, FP (domains) | A |
| 54 | TrafficFormer | IEEE S&P | 2025 | FM, ENC | S (venue on official list) |
| 55 | What We Talk About When We Talk About Logs; CountMamba; PQ Analysis of SSH; Resolution Without Dissent | IEEE S&P | 2025 | EVAL / ENC / PQ (protocol) / PER | T |
| 56 | Contorter (A Context is Worth a Thousand Lies) | IEEE S&P | 2026 | ADV, HOST | S |
| 57 | EnCP | IEEE S&P | 2026 | FP (conformal), POI | T |
| 58 | LLMs in the SOC | IEEE S&P | 2026 | LLM | A (arXiv) |
| 59 | PROVFUSION | IEEE S&P | 2026 | HOST, FP | A (arXiv) |
| 60 | Incalmo | IEEE S&P | 2026 | LLM (offense) | A (arXiv) |
| 61 | Catch Me If You Can; APIEcho; Guardians of the Air; APT to Disagree; Sealing the Window; Kernel auditing; LLM-GNN poisoning; PQ WireGuard | IEEE S&P | 2026 | mixed (ADV/ZD/POI/PQ-protocol) | T |
| 62 | Detecting Tunneled Flooding Traffic | ACM CCS | 2024 | ENC | T |
| 63 | Rules Refine the Riddle (GEAD) | ACM CCS | 2024 | XAI | S |
| 64 | Training Robust Raw-Binary Malware Detectors | ACM CCS | 2024 | ADV | T |
| 65 | TREC | ACM CCS | 2024 | HOST | A |
| 66 | KnowGraph | ACM CCS | 2024 | DR, XAI | A |
| 67 | CanCal; Inbox Invasion; Early-Stage WF | ACM CCS | 2024 | PER | T |
| 68 | Training with Only 1.0‰ Samples (tFusion) | ACM CCS | 2025 | ENC, label efficiency | S |
| 69 | MM4flow | ACM CCS | 2025 | FM | T |
| 70 | Training Robust Classifiers for Encrypted Traffic under Dynamic Network Conditions | ACM CCS | 2025 | ENC, DR | T |
| 71 | FlowSentry; SISTAR | ACM CCS | 2025 | PER (DDoS) | T |
| 72 | DREAM | ACM CCS | 2025 | DR, XAI | A |
| 73 | Deep Learning from Imperfectly Labeled Malware Data | ACM CCS | 2025 | label noise | T |
| 74 | Robustness of a Production Malware Detector to Transferable Attacks | ACM CCS | 2025 | ADV | T |
| 75 | ForeDroid | ACM CCS | 2025 | XAI | T |
| 76 | Analyzing PDFs like Binaries; Pack-ALM | ACM CCS | 2025 | ADV | A |
| 77 | Slot; OCR-APT | ACM CCS | 2025 | HOST, LLM | A |
| 78 | RAPIER (Low-Quality Training Data Only?) | NDSS | 2024 | ENC, label noise | P / A |
| 79 | Attributions for ML-based ICS Anomaly Detection | NDSS | 2024 | XAI | A |
| 80 | NODLINK | NDSS | 2024 | HOST | A |
| 81 | REPLICAWATCHER | NDSS | 2024 | DR | A |
| 82 | Information-Based Heavy Hitters (DNS exfiltration) | NDSS | 2024 | FP | A |
| 83 | On Precisely Detecting Censorship Circumvention | NDSS | 2024 | FP, EVAL (base rate) | A |
| 84 | 5G-Spector | NDSS | 2024 | ZD (cellular) | A |
| 85 | Revisiting Concept Drift in Windows Malware | NDSS | 2025 | DR | P |
| 86 | Density Boosts Everything | NDSS | 2025 | DR, POI, ADV | A |
| 87 | PBP backdoor purification | NDSS | 2025 | POI | A |
| 88 | Automated Mass Malware Factory | NDSS | 2025 | ADV | A |
| 89 | Evaluating ML IoT Device Identification | NDSS | 2025 | EVAL, DR | A |
| 90 | MineShark | NDSS | 2025 | ENC, FP, update loop | A |
| 91 | SketchFeature | NDSS | 2025 | ADV (extractor) | A |
| 92 | CAPTAIN (Incorporating Gradients to Rules) | NDSS | 2025 | HOST, FP | A |
| 93 | ERW-Radar; IMSI-Catchers; Cross-layer RTTs | NDSS | 2025 | PER / ENC | A |
| 94 | PQConnect | NDSS | 2025 | PQ (protocol, not detection) | A |
| 95 | NetMasquerade | NDSS | 2026 | ADV, CERT-bypass | P / F (notes differ) |
| 96 | CoLD | NDSS | 2026 | label noise | P / A |
| 97 | TIPSO-GAN | NDSS | 2026 | ZD, XD | P |
| 98 | PANDORA | NDSS | 2026 | ZD, DR, uncertainty | A |
| 99 | Entente | NDSS | 2026 | POI (FL), NIDS | A |
| 100 | NetRadar | NDSS | 2026 | DR (feature mismatch) | A |
| 101 | Strategic Games on Heavy-Hitter Monitoring | NDSS | 2026 | ADV | A |
| 102 | Indicator of Benignity | NDSS | 2026 | FP, LLM | A |
| 103 | Incident Response Planning with Lightweight LLM | NDSS | 2026 | LLM | A |
| 104 | WebSpotter | NDSS | 2026 | XAI | A |
| 105 | Beyond RTT | NDSS | 2026 | ADV, ENC | A |
| 106 | Enhancing WF against Traffic Drift (Proteus) | NDSS | 2026 | DR, ENC | A |
| 107 | Beyond Raw Bytes (malware LMs) | NDSS | 2026 | FM | A |
| 108 | Chasing Shadows (LLM pitfalls) | NDSS | 2026 | EVAL | A |
| 109 | KnowHow | NDSS | 2026 | HOST, FP | A |
| 110 | Chimera | NDSS | 2026 | EVAL (dataset) | A |
| 111 | Phishing in Wonderland | NDSS | 2026 | EVAL | A |
| 112 | WiFinger; Unknown Target (TCAS) | NDSS | 2026 | PER | A |
| 113 | Bad Design Smells in Benchmark NIDS Datasets | EuroS&P | 2024 | EVAL | F (final draft, partial) |
| 114 | Can Allowlists Capture IoT Variability? | EuroS&P | 2024 | DR | T |
| 115 | DNS Exfiltration Guided by GANs (DOLOS) | EuroS&P | 2024 | ADV | A (partial) |
| 116 | PASA | EuroS&P | 2024 | ADV (detection) | A |
| 117 | MalMixer | EuroS&P | 2025 | ZD (few-shot) | A |
| 118 | O'MINE; LLMPot | EuroS&P | 2025 | PER | T |
| 119 | KnowML | EuroS&P | 2026 | ZD, FP | A |
| 120 | GRAAL | EuroS&P | 2026 | AI-IDS | T |
| 121 | QUIC-Aware Lateral Movement Detection | EuroS&P | 2026 | ENC | T |
| 122 | Agility for Steganalysis (drift) | EuroS&P | 2026 | DR | T |
| 123 | Delayed Rendering vs Visual Phishing; SoK Honeypots & LLMs; SoK IR Influence Factors | EuroS&P | 2026 | ADV / LLM / PER | T |
| 124 | Mateen | RAID | 2024 | DR, FP | F |
| 125 | Extending C2 Detection: TLS 1.2 → TLS 1.3 | RAID | 2024 | ENC, protocol evolution | A |
| 126 | No Need for Details | RAID | 2024 | ZD (ICS) | A |
| 127 | Down to Earth! DGA Guidelines | RAID | 2024 | EVAL | A |
| 128 | How to Train your Antivirus | RAID | 2024 | ADV | A |
| 129 | Cross-Regional Malware Detection | RAID | 2024 | DR | A |
| 130 | AudiTrim | RAID | 2024 | PER | T |
| 131 | Context-Aware Anomaly Detection (vehicles); What do malware analysts want? | RAID | 2024 | PER | A |
| 132 | NIDP (neural pruning for shift) | RAID | 2025 | DR (NIDS) | T |
| 133 | Stealthy Label-Inversion Drifts | RAID | 2025 | DR, possible POI | T |
| 134 | ADAPT | RAID | 2025 | DR, self-poisoning | A / S |
| 135 | Carbon Filter | RAID | 2025 | FP, triage | S |
| 136 | CasinoLimit; PYROLYSE; API-call features; DGA botnets; Adaptive Arms Race; STGraph; MuSAR; CPS defender | RAID | 2025 | EVAL / ADV / PER | T |
| 137 | Security Alert Investigation Tool (Tier 1) | ACSAC | 2024 | LLM/triage | T |
| 138 | Madeline; IoC Stalker; DEEPCAPA | ACSAC | 2024 | PER | T |
| 139 | Model-Manipulation Attacks against Black-Box Explanations | ACSAC | 2024 | XAI, ADV | T |
| 140 | Impact of Active Learning on Availability Poisoning (McFadden et al.) | ACSAC Workshops | 2024 | POI, DR | S (PARTIALLY VERIFIED; 403) |
| 141 | R+R: From Claims to Crashes (graph NIDS) | ACSAC | 2025 | EVAL | A (preprint; link inferred) |
| 142 | R+R Android; One Detector Fits All; TempoNet; Clouesau; CarDS; Smart home; Splash | ACSAC | 2025 | EVAL / DR / LLM / PER | T |
| 143 | Towards Robust DGA Classification | AsiaCCS | 2024 | ADV | S (not from official list) |
| 144 | Unmasking the Veiled (Android evasive) | AsiaCCS | 2024 | PER | S |
| 145 | Ruling the Unruly | AsiaCCS | 2025 | FP | A |
| 146 | OMAD5G; SigN; SCADA triage; Minerva; CryptoGuard; Phishing-detector robustness | AsiaCCS | 2025 | PER | T |
| 147 | "What is the Problem Space?" (host-space perturbations) | AsiaCCS | 2026 | ADV, EVAL | F / A (arXiv) |
| 148 | StealthCup | AsiaCCS | 2026 | EVAL (IDS benchmark) | T |
| 149 | LotBoNC | AsiaCCS | 2026 | ENC/malicious traffic | T |
| 150 | ALPHA (PAC-Bayesian active learning) | AsiaCCS | 2026 | DR, possible guarantee | T |
| 151 | Taming Data Challenges with GenAI; macOS features; PQ DNSSEC | AsiaCCS | 2026 | PER / PQ (protocol) | T |
| 152 | Ano2Rule | IEEE TDSC | 2026 | XAI | A |
| 153 | Calibrated Uncertainty for IoT Attack Detection (Pal et al.) | IEEE TDSC | 2025 | FP (calibration) | S |
| 154 | Lightweight Dynamic Open-Set IDS for IIoT | IEEE TIFS | 2025 | ZD | S (listing; mostly UNVERIFIED) |
| 155 | SmartDetector | IEEE TIFS | 2025 | ENC, ADV | S |
| 156 | Zero-X (TIFS venue UNVERIFIED) | arXiv / ?TIFS | 2024 | ZD | A (venue UNVERIFIED) |
| 157 | Cross-Dataset Generalization of ML for NIDS (Cantone) | IEEE Access | 2024 | XD, EVAL | A |
| 158 | The Sweet Danger of Sugar | SIGCOMM | 2025 | FM, ENC, EVAL | A (+S details) |
| 159 | Bias in the Shadows (BiasSeeker) | arXiv / IWQoS | 2026 | ENC, EVAL | A (venue partial) |
| 160 | Pitfalls in ML for Computer Security | CACM | 2024 | EVAL | A (record) |
| 161 | Expectations Versus Reality (IDS in practice) | DSN-S | 2025 | EVAL | A (record) |
| 162 | Network Intrusion Datasets survey (Goldschmidt & Chudá) | Computers & Security | 2025 | EVAL | A |
| 163 | Temporal Analysis of NetFlow Datasets (Luay et al.) | arXiv / IEEE Access | 2025–26 | EVAL, DR | A |
| 164 | CLOSR | IEEE TNSM | 2026 | ZD | A |
| 165 | NetVAD | arXiv / IEEE ISI | 2026 | ZD, FM | A |
| 166 | CND-IDS | DAC | 2025 | ZD, DR | A |
| 167 | Self-Supervised Transformer Contrastive IDS | IFIP Networking | 2025 | ZD, XD | A |
| 168 | SSF continual learning | arXiv (INFOCOM 2025 per citation) | 2024–25 | DR | A (venue S) |
| 169 | NetGuard | ACM (venue UNVERIFIED) | 2025 | DR | S |
| 170 | PLAA packet-level attacks | TrustCom / arXiv | 2025–26 | ADV | A |
| 171 | GraphIDS | NeurIPS | 2025 | ZD | A |
| 172 | Enhancing Trustworthiness with UQ (Talpini et al.) | JRIE | 2024 | FP (UQ) | S |
| 173 | Deployment-oriented evaluation of DL-NIDS (mini-review) | Frontiers | 2026 | FP, EVAL | A |
| 174 | FIRCE | arXiv / IEEE SmartNets | 2026 | FP (conformal), response | A |
| 175 | ConFID | Internet of Things (journal) | 2026 | FP (conformal), ZD | S |
| 176 | netFound | arXiv | 2023–26 | FM | A |
| 177 | Demystifying Network Foundation Models | arXiv | 2025 | FM, EVAL | A |
| 178 | Lens | arXiv | 2024 | FM | A |
| 179 | Learning to Detect Cyber Attacks (Zhou et al.) | arXiv | 2024 | ZD (theory) | A |
| 180 | Zero Day Attacks: Novel Behaviour or Novel Vulnerability? | arXiv | 2026 | ZD, EVAL | A |
| 181 | Illusion of Model Efficacy | arXiv | 2026 | EVAL, ZD | A |
| 182 | Aurora | arXiv | 2025–26 | FP (selective), DR | A |
| 183 | Can Drift-Adaptive Malware Detectors Be Made Robust? | arXiv | 2026 | DR, ADV | A |
| 184 | Candidate Comparability Before Promotion | arXiv | 2026 | DR, update gating | A |
| 185 | PCAP-Backdoor | arXiv (ACM venue UNVERIFIED) | 2025 | POI | F (arXiv) |
| 186 | Constrained Network Adversarial Attacks | arXiv | 2025 | ADV | A |
| 187 | Robust Conformal Intrusion Detection | arXiv (to TDSC) | 2026 | FP (conformal), ADV | A |
| 188 | C-PP-COAD | arXiv | 2025 | FP (online FDR) | S |
| 189 | XSec self-explainable architecture | arXiv | 2026 | XAI | A |
| 190 | CORTEX | arXiv | 2025 | LLM | A |
| 191 | ALERT-BENCH / AIDA | arXiv | 2026 | LLM | A |
| 192 | OpenSec | arXiv | 2026 | LLM, response | A |
| 193 | The Colossus with Feet of Clay (PQC drift) | arXiv | 2026 | PQ, ENC | A |
| 194 | Classifying PQ Implementations | arXiv | 2025–26 | PQ | A |
| 195 | Mind the Gap: PQ-TLS deployment | ACM IMC (accepted) | 2026 | PQ | A |
| 196 | Measurement of PQ Readiness 2026 | arXiv | 2026 | PQ | A |
| 197 | SoK: Where Do Flow Labels Come From? | arXiv | 2026 | ENC, EVAL | A |
| 198 | Unmasking Shortcut Learning in IoT IDS (Roy & Minu) | arXiv | 2026 | EVAL | A |
| 199 | Do Transformers Actually Help ID? (CIC-IDS2017 temporal) | arXiv | 2026 | EVAL | S |
| 200 | Contextualized NetFlow DL survey (El Mahdaouy et al.) | arXiv | 2026 | EVAL | A |
| 201 | Leakage-safe RPL IoT re-evaluation | ScienceDirect | 2026 | EVAL | S |
| 202 | ConCap traffic generation | arXiv | 2025 | EVAL (dataset) | S |
| 203 | First-Principles Evaluation of Graph NIDS | arXiv | 2026 | EVAL | S |
| 204 | Detecting Adversarial Evasion against AE-NIDS; Robustness under Resource Constraints; Vulnerability Disclosure via Black-Box Attacks; GNN problem-space attacks | arXiv | 2024–26 | ADV | A/S |
| 205 | Further title-only foundation-model, encrypted and PQ items (FlowletFormer, Traffic-MoE, MambaNetBurst, FlowCLIP, UniAlign, MalMoE, MalRAG, UK PQ-TLS, financial PQ-TLS) | arXiv | 2025–26 | FM / ENC / PQ | S/T |
| 206 | Cloudflare "State of the PQ Internet in 2025" (industry) | Blog | 2025 | PQ | Primary blog |

---

## USENIX Security 2027 Cycle 2 rules that bind the project

The 2027 CFP is published, and the latest PDF is revision 11/09/26. The symposium (36th) runs **August 11–13, 2027, in Denver** ([CFP](https://www.usenix.org/conference/usenixsecurity27/call-for-papers); [CFP PDF](https://www.usenix.org/sites/default/files/sec27_cfp_110926.pdf)). Today is 2026-11-16, so Cycle 1 has passed and Cycle 2 is the only remaining 2027 option. The notes checked all seven Cycle 2 dates in the project's plan against the official CFP and found no mismatch. They also found three Cycle 2 deadlines the plan omitted: shepherded approval, embargo requests, and the artifact-availability deadline.

| Cycle 2 milestone (all AoE) | Date | Source |
|---|---|---|
| Registration (title, authors, abstract, topics; all authors need ORCID) | Tue, Jan 19, 2027 | [CFP](https://www.usenix.org/conference/usenixsecurity27/call-for-papers) |
| Paper submission | Tue, Jan 26, 2027 | CFP |
| Submission artifacts due (3-day grace; paper frozen meanwhile) | Fri, Jan 29, 2027 | CFP |
| Early reject notification | Tue, Mar 9, 2027 | CFP |
| Rebuttal | Thu, Apr 8–15, 2027 | CFP |
| Notification | Thu, May 6, 2027 | CFP |
| **Shepherded approval due** (additional date) | Tue, May 18, 2027 | CFP |
| Final papers | Thu, Jun 3, 2027 | CFP |
| **Embargo requests** (additional date) | Thu, Jul 1, 2027 | CFP |
| **AE: artifacts due for availability check** (additional date) | May 17, 2027 | [Call for Artifacts](https://www.usenix.org/conference/usenixsecurity27/call-for-artifacts) |
| AE: shepherding notification / Available decision / Functional–Reproduced submission | May 18 / Jun 1 / Jun 10, 2027 | Call for Artifacts |
| AE: author discussion / F–R decision / final appendix files | Jun 18–Jul 14 / Jul 21 / Jul 28, 2027 | Call for Artifacts |

**Format.** The main body is limited to **13 pages** at submission. References and appendices do not count and have no limit, but reviewers "are not required to read any optional appendices". After acceptance the paper must fit **20 pages in total**, including the Open Science and any ethics appendices and the bibliography. The mandatory USENIX 2027 LaTeX template uses two columns, 10-pt Times on 12-pt leading, a 7"×9" text block, and must be legible in grayscale. Space-saving tricks (negative vspace, savetrees, titlesec) may lead to rejection. Review is strictly double-blind: self-citation in the third person, and anonymized artifact links that do not track reviewers. Each author may submit at most seven papers per cycle. SoK titles must start with "SoK:" ([CFP](https://www.usenix.org/conference/usenixsecurity27/call-for-papers); [CFP PDF](https://www.usenix.org/sites/default/files/sec27_cfp_110926.pdf)).

**Open Science.** "All USENIX Security '27 submissions must include an Open Science Appendix" that describes the artifacts or explains why they cannot be provided. Artifacts go through anonymous, non-tracking links; anonymous.4open.science with ID "SEC27" is recommended. URLs are final at the deadline, and artifacts freeze after the 3-day grace period. Acceptance "is conditional on their public availability" for artifacts declared public. Availability checking on a permanent archive (Zenodo, FigShare, Dryad, Software Heritage, institutional) is mandatory, and GitHub or personal sites are not accepted. Functional and Reproduced badges are optional. Withholding an artifact needs a "detailed" justification that reviewers validate; if they disagree, the paper is rejected unless the artifact is supplied. Code must still be released ([CFP PDF](https://www.usenix.org/sites/default/files/sec27_cfp_110926.pdf); [Call for Artifacts](https://www.usenix.org/conference/usenixsecurity27/call-for-artifacts)).

**Ethics.** The ethics appendix is **no longer mandatory but "strongly encouraged"**. It was mandatory in 2026. Reviewers still evaluate ethics, and "papers may be rejected on ethical grounds". For details on stakeholder analysis, the Menlo principles, IRB ("not a substitute for ethical analysis") and prompt vulnerability disclosure, the CFP points to the 2026 guidelines ([2026 ethics](https://www.usenix.org/conference/usenixsecurity26/call-for-papers#ethics)).

**Topic rule for ML-for-NIDS.** "Intrusion and anomaly detection and prevention" is a Network Security subtopic. The Submitting-ML-Work page says a new ML method for intrusion detection takes **Network Security as its primary field**, not Security of ML, which "is not meant for papers that propose/evaluate/improve ML-based techniques for a security task". Out-of-scope papers are desk-rejected. All papers need a threat model covering attacker(s), threat surfaces, generality and practicality ([Submitting ML Work](https://www.usenix.org/conference/usenixsecurity27/submitting-ml-work-usenix-security)).

**AI-use policy and outcomes.** AI tools are permitted, and authors remain responsible for all content. "Fabrications or hallucinations, including non-existing references or incorrect authors… is considered academic misconduct" and can lead to desk rejection. Authors are encouraged to use the hallucinator tool that the chairs use. Outcomes are Accept, **Accept on Shepherd Approval**, or Reject. There is **no major-revision outcome**. Papers rejected in Cycle 1 '27 cannot go to Cycle 2 '27, while papers rejected from '26 may be submitted. Review criteria are originality, relevance, scientific rigor, correctness and clarity. A new USENIX Authorship Policy applies; the notes did not fetch it ([CFP PDF](https://www.usenix.org/sites/default/files/sec27_cfp_110926.pdf)).

**Gaps the CFP leaves open:**
- No early-reject criteria.
- No page cap stated for the Open Science Appendix.
- No 2027-specific IRB rules.
- No 2027 guidance on where appendices sit relative to references.

---

## Coverage: 20 of 21 venue-years scanned, most papers read only at the surface

The two title-level sweeps loaded every official accepted-paper list except one. Lists covered:
- **USENIX Security:** 2024 (417 pages), 2025 (455 entries), 2026 (378 pages; the Cycle 2 accepted page was an empty shell, so the technical-sessions page was used instead).
- **IEEE S&P:** 2024 (261 titles), 2025 (255), 2026 (254).
- **ACM CCS:** 2024, and 2025 (316 papers via JSON).
- **NDSS:** 2024, 2025, 2026.
- **IEEE EuroS&P:** 2024, 2025, 2026.
- **RAID:** 2024, 2025.
- **ACSAC:** 2024 (83 papers from the final program because the papers URL returned 404), 2025.
- **AsiaCCS:** 2025, 2026.

Sources: [USENIX '26 sessions](https://www.usenix.org/conference/usenixsecurity26/technical-sessions), [S&P 2026 list](https://sp2026.ieee-security.org/accepted-papers.html), [RAID 2025 list](https://raid2025.github.io/accepted_open.html), [ACSAC 2024 program](https://www.acsac.org/2024/program/final/).

**AsiaCCS 2024 was not scanned.** The site returned a proxy 502, DBLP served an "Access Denied" bot check, and Wayback requests were reset. Targeted searches surfaced only two AsiaCCS '24 papers (robust DGA classification; Android evasive malware), confirmed through ACM DL DOIs rather than the official list ([ACM DL](https://dl.acm.org/doi/10.1145/3634737.3656287)). The sweep names this 65-paper venue as the main residual risk of a missed competitor.

**Coverage limitations that bound every conclusion:**

| # | Limitation |
|---|---|
| 1 | DBLP was blocked on all mirrors, so no list was cross-checked against DBLP. |
| 2 | OpenAlex and Semantic Scholar were rate-limited, and a web-search quota ran out partway through. |
| 3 | S&P pages list titles and authors only. More than 20 S&P papers remain title-level, including FLASH, R-CAID, DrSec, CaFA, the SoK on XAI in adversarial environments, "What We Talk About When We Talk About Logs", Catch Me If You Can, APIEcho and EnCP. |
| 4 | RAID 2025 PDFs were not linked, which leaves NIDP and the label-inversion drift paper title-only. |
| 5 | CCS 2024 author lists are concatenated, so only first authors are reliable. |
| 6 | Several CCS 2025 traffic papers (MM4flow, the robust encrypted-traffic classifier) are title-only. |
| 7 | The ACM DL returned 403, and so did some publisher pages (ConFID, the McFadden workshop paper). |
| 8 | Full texts were read for only a handful of papers: Mateen; NetMasquerade, CertTA, PANTS and PCAP-Backdoor at varying depth; Bad Smells (partial); host-space perturbations. TIPSO-GAN, RAPIER, CoLD, GeCo and Li et al. were read partially. Everything else is abstract-level or lower. |
| 9 | Threat models, compute costs, stated limitations and operating points are therefore missing for most papers. |
| 10 | The topic notes, written before the sweeps, did not browse several proceedings directly. The sweeps later covered them at title level. |
| 11 | No specific search was run for ECH- or DoH-specific malicious-traffic detection, test-time adaptation for NIDS, or PAC-style FPR bounds. |
| 12 | CESNET, UWF-ZeekData, LUFlow, 5G-NIDD and the CIC 2024–2026 datasets were not checked. |

The notes contain several conflicts and unconfirmed items, recorded here as-is:
- **CertTA and NetMasquerade** depth of reading: "first pages" in one note, "primary PDF" in another.
- **TrafficFormer and CertTA** venues: UNVERIFIED in the encrypted-traffic note, later confirmed on official lists by the sweep.
- **Bad Smells** dataset count: seven in the final draft, "six" in the program abstract.
- **Bad Smells** award: Best Paper vs Distinguished Paper.
- **Zero-X** venue: unconfirmed TIFS DOI, and conflicting secondary detection rates of 98.36% vs 77.32% that must not be cited.
- **OpenSec** false-positive figures: a secondary "90–97%" against the abstract's 82.5%.
- **ACSAC 2025 "R+R" graph-NIDS paper:** identification with the arXiv "Are We There Yet?" preprint is an inference from matching authors.

---

## What the literature demonstrates versus what it only claims

Across the extracted papers, demonstrated evidence is concentrated in four areas.

**First, lab corpora inflate NIDS results, and the critiques show this directly rather than by argument:**
- Single features such as TTL and protocol separate UNSW-NB15 at 98% ([Bad Smells](https://detlearsom.github.io/pubs/BadSmells-EuroSP24-finaldraft.pdf)).
- CIC-2017 → CIC-2018 transfer falls to roughly chance ([Cantone](https://arxiv.org/abs/2402.10974)).
- Random flow splits inflate attack recall by up to 14 points ([Roy & Minu](https://arxiv.org/abs/2609.28725)).
- In the snippet-level CIC-IDS2017 temporal study, leakage-free splits expose a 67× rise in false alarms ([arXiv 2606.11098](https://arxiv.org/abs/2606.11098)).
- Encrypted-traffic and foundation-model results depend on legacy unencrypted data and on shortcuts ([SoK](https://arxiv.org/abs/2503.20093); [Sweet Danger](https://arxiv.org/abs/2507.16438); [Demystifying NFMs](https://arxiv.org/abs/2509.23089)).

**Second, traffic-space attacks beat feature-space defences.** NetMasquerade breaks the certified BARS. PANTS shows that only adversarial training on realizable samples transfers. A one-character change in an attack tool's command evades CICIDS-trained detectors ([NetMasquerade](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf); [PANTS](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf); [host-space](https://arxiv.org/abs/2605.25822)).

**Third, real operations work at base rates that lab F1 hides:**
- 0.01% true-attack alerts in a real SOC ([SOC alerts](https://www.usenix.org/conference/usenixsecurity24/presentation/yang-limin)).
- More than 94% false positives for circumvention classifiers at realistic base rates ([NDSS 2024](https://www.ndss-symposium.org/ndss-paper/on-precisely-detecting-censorship-circumvention-in-real-world-networks/)).
- Deployed systems that report FPR at or below 10⁻⁴ (Facade, BEAM).

**Fourth, LLM triage and response agents fail in measurable ways.** All baseline strategies miss ≥ 40.4% of attack alerts in ALERT-BENCH. GPT-5.2 contains with an 82.5% FP rate in OpenSec. Log-field prompt injection succeeds 76.4% of the time ([AIDA](https://arxiv.org/abs/2610.10608); [OpenSec](https://arxiv.org/abs/2601.21083); [LogInject](https://www.usenix.org/conference/usenixsecurity26/presentation/karanjai)). The external validity of these figures is weak: one scenario, and 40 episodes per model.

Several claims run ahead of their verified evidence:
- **TIPSO-GAN's** robustness to adaptive, mimicry and poisoning attacks.
- **KnowML's** FPR ≤ 0.0137% across variants, abstract-level and of unknown protocol.
- **PANDORA's** "up to 99%" zero-shot accuracy under shift.
- **tFusion's** 99.82% deployment accuracy (secondary source).
- **NetVAD's** "operational FPR", which depends on supervised threshold calibration.

The 2026 incident review argues that behaviour-based IDS "may overstate zero-day detection capabilities" because real zero-days arise from undisclosed vulnerabilities rather than novel behaviour ([arXiv 2605.03138](https://arxiv.org/abs/2605.03138)). That challenges the construct validity of every leave-family-out protocol, including TIPSO-GAN's.

The untested space recurs across papers: adaptive attackers tuned to a specific defence, TPR at very low FPR under realistic base rates, and adversarial (rather than random) label noise in update loops. Further gaps the notes record:
- Multi-flow and campaign-level certification, and certification of flow-meter or threshold layers.
- Joint evaluation of cross-dataset shift, unknown attacks and reliability. A 29-paper mini-review found no study doing all three ([Frontiers](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full)).
- Analyst-outcome evidence for NIDS explanations. The one controlled USENIX 2026 study (N=139, domains, not NIDS) found XAI did not improve performance ([Roch et al.](https://www.usenix.org/conference/usenixsecurity26/presentation/roch)).

---

## Stage 1 close-out

**Established, within the stated coverage.**
- **Network-flow NIDS is a small share of top-venue detection work.** Provenance host IDS is crowded, with about a dozen papers at USENIX and S&P alone. Flow NIDS appears mainly as PANTS, CertTA, ISDC, Tracegram, TrafficFormer, the encrypted-traffic SoK, the sampling-bias paper, and NDSS/RAID/EuroS&P entries such as Mateen, TIPSO-GAN, PANDORA, KnowML, CoLD and NetMasquerade.
- **Reviewers at these venues now expect** temporal and session-disjoint splits, cross-dataset tests, shortcut ablations, base-rate-aware metrics (FPR ≤ 10⁻³/10⁻⁴, alerts/day), comparison with simple baselines, adaptive attackers in traffic or host space, and released artifacts.
- **Certified robustness for traffic models** is per-flow, edit-bounded and probabilistic (CertTA).
- **The Tsinghua group** (Ke Xu, Qi Li, Zhuotao Liu and colleagues) and **the Imperial/UCL group** (Maffeis, Pierazzi, Cavallaro) publish repeatedly on exactly these problems.
- **The CFP's binding rules are known precisely:** dates, 13/20 pages, mandatory Open Science Appendix, Network Security as primary topic, no major revision, AI hallucination treated as misconduct.

**Still uncertain.** The full-text content of nearly every competitor beyond Mateen and the adversarial trio is unread. Specific open points:
- Whether KnowML, PANDORA and NIDP use leave-family-out or temporal splits.
- Whether KnowML's FPR is controlled or merely measured.
- What EnCP's certificate actually covers.
- Whether ALPHA (AsiaCCS 2026) gives PAC-Bayesian guarantees under drift.
- Whether "Stealthy Label-Inversion Drifts" (RAID 2025) models an adversary in the update loop.
- What TIPSO-GAN's §VI-G attackers look like.
- What AsiaCCS 2024 contains.

**Evidence still needed before Stage 2:**
- Full-text reads of KnowML, PANDORA, NIDP, Label-Inversion Drifts, EnCP, ALPHA, TIPSO-GAN §VI-G, CoLD, MM4flow, the CCS 2025 robust encrypted-traffic paper, DREAM and Li et al. (NDSS 2025).
- A manual check of the AsiaCCS 2024 ACM DL table of contents (10.1145/3634737).
- A DBLP cross-check once access returns.
- Targeted searches for conformal or PAC FPR bounds for security detectors, test-time adaptation for NIDS, and ECH/DoH-specific detection.
- Primary-source verification of the snippet-level numbers listed in this report (Sweet Danger's ~80% drop, Zero-X rates, McFadden et al., tFusion).
- Dataset checks on CESNET-TLS/QUIC, UWF-ZeekData, MAWIFlow and the CIC 2024–2026 releases.

**Early signals for Stage 3. These are preliminary signals, NOT established gaps.** Each could fall to a full-text read or to AsiaCCS 2024.

- **(a) FPR guarantees under drift.** No paper at any scanned venue-year gives a formal FPR guarantee under drift for NIDS. Both sweeps report this independently; the nearest S&P item is EnCP ([researchr](https://researchr.org/publication/YangLFSW26/authors)) and the nearest NIDS item is KnowML's empirical FPR ([arXiv 2506.19802](https://arxiv.org/abs/2506.19802)). Nearest work:
  - EnCP: conformal plus poisoning, generic, certificate UNVERIFIED.
  - Li's arXiv robust conformal IDS: coverage under manipulation at a cost of 7–14 accuracy points.
  - ConFID and FIRCE at minor venues.
  - Empirical low-FPR systems: KnowML, Facade, BEAM.
  - Aurora's evidence that selective-classifier confidence is fragile under drift.
  
  The notes record that exchangeability assumptions break under both drift and adaptive attack ([arXiv 2609.19241](https://arxiv.org/abs/2609.19241)).
- **(b) Attacks on NIDS update and retraining loops.** No direct NIDS paper was found. Adjacent work:
  - Generic attacks: Test-Time Poisoning (S&P 2024), Persistent Backdoors in CL (USENIX 2025).
  - Mitigations: ADAPT's self-poisoning (RAID 2025), Entente's FL poisoning bound (NDSS 2026).
  - Measurement-induced self-poisoning: ISDC.
  - Loops that are attackable but unstudied: MineShark's self-update and Mateen's labelling channel.
  - The title-only "Stealthy Label-Inversion Drifts".
  
  Chen et al. (USENIX 2023, background) and Mateen both name poisoning of the active-learning loop as open ([Mateen](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf); [Test-time poisoning](http://arxiv.org/abs/2308.08505)).
- **(c) PQ-TLS effects on NIDS.** No peer-reviewed measurement of PQ-induced feature shift or IDS breakage was found. Evidence so far:
  - The only direct study is a non-peer-reviewed website-fingerprinting preprint ([Colossus](https://arxiv.org/abs/2608.22683)).
  - The closest peer-reviewed analogue is the TLS 1.2 → 1.3 C2 study ([RAID 2024](https://raid2024.github.io/papers/raid2024-31.pdf)).
  - Middlebox breakage evidence is industry-sourced. Over 50% of human Cloudflare traffic used PQ key agreement by late 2025 ([Cloudflare](https://blog.cloudflare.com/pq-2025/)).
  - PQ use itself is classifiable at 98% ([arXiv 2503.17830](https://arxiv.org/abs/2503.17830)).
  
  The possibility of a "PQ key share ⇒ benign browser" shortcut is an untested hypothesis from the notes. The Wickramasinghe/Shaghaghi/Jha team (S&P 2025 SoK, IMC 2026 PQ-TLS) is flagged as the likeliest competitor here.
- **(d) Closest competitors to differentiate against in any later stage:**
  - KnowML (variant generalization at low FPR).
  - PANDORA (zero-shot under domain shift).
  - TIPSO-GAN (LOFO and cross-dataset).
  - EnCP (conformal plus poisoning).
  - Mateen (benign-drift adaptation).
  - CertTA (traffic-space certification).
  - PANTS (realizable adversarial training).
  - NetMasquerade (hard-label mimicry that evades certified defences).
  - Also relevant: NIDP, Label-Inversion Drifts, ALPHA, Retrofit, DREAM, Proteus and the host-space perturbation paper.

One further signal from the adversarial notes: NetMasquerade was not evaluated against CertTA, and no paper adapts an attacker to CertTA or to PANTS-hardened models ([NetMasquerade PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)).

## Conclusion

The 2024–2026 record reads less like a race toward better NIDS accuracy and more like a slow recalibration of what counts as evidence. Each strong detection claim at a top venue (TIPSO-GAN's LOFO, KnowML's 0.0137% FPR, PANDORA's zero-shot accuracy) now sits beside a peer-reviewed critique or attack that would undercut it under a stricter protocol: shortcut audits, cross-dataset collapse, base-rate reality, hard-label mimicry and host-space perturbations. A Cycle 2 paper will be judged against both the detectors and their critics, under a 13-page body, a mandatory Open Science Appendix and no revision path.

The three preliminary absences that recur across independent notes are drift-time FPR guarantees, attacks on NIDS update loops, and PQ-TLS effects on detectors. They are the most decision-relevant output of Stage 1. They rest mostly on titles and abstracts, with AsiaCCS 2024 unscanned. Converting them from signals to established gaps is the immediate job before any Stage 2 ideation, and it requires full-text reads of about a dozen named papers and the AsiaCCS 2024 table of contents.
