# Adversarial Attacks on and Defenses for ML-based NIDS / Traffic Classification (2024–2026)

Scope note: about 16 tool calls. Seven papers were extracted from full text: four from the primary PDF (CertTA, PANTS, NetMasquerade, host-space perturbations) and three from the arXiv full text or abstract (PCAP-Backdoor, Constrained Network Adversarial Attacks, PLAA). The rest are leads checked only through an abstract page or a search snippet, and are labelled as such. Missing fields are marked UNVERIFIED. Several top-venue proceedings (IEEE S&P 2024–2026, CCS 2024–2025, USENIX Sec 2024/2026, RAID, ACSAC, EuroS&P) were **not** systematically browsed. Treat this as a non-exhaustive list.

## Which 2024–2026 papers address these topics, and what does each one contribute? (paper-by-paper extraction)

### Takeaway
The strongest verified 2024–2026 top-venue work is a cluster from Tsinghua (Ke Xu, Zhuotao Liu and colleagues) and Princeton:
- **CertTA** (USENIX Sec 2025): certification.
- **PANTS** (USENIX Sec 2025): realizable white-box attack plus adversarial training.
- **NetMasquerade** (NDSS 2026): hard-label black-box traffic-space evasion that beats BARS.

Alongside these:
- **Host-space perturbations** (AsiaCCS 2026) argues that most prior "problem-space" NIDS work is still unrealistic.
- Backdoor and poisoning work on traffic NIDS is mostly at lower venues or arXiv (PCAP-Backdoor).

### Cited Findings

**P1. NetMasquerade: "A Hard-Label Black-Box Evasion Attack against ML-based Malicious Traffic Detection Systems"**
- **Venue and authors:** NDSS 2026 (23–27 Feb 2026, San Diego), DOI 10.14722/ndss.2026.230916. Authors are Zixuan Liu, Yi Zhao (BIT), Zhuotao Liu, Qi Li, Chuanpu Fu, Guangmeng Zhou and Ke Xu (Tsinghua / Zhongguancun Lab). — [NDSS page](https://www.ndss-symposium.org/ndss-paper/a-hard-label-black-box-evasion-attack-against-ml-based-malicious-traffic-detection-systems/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- **Threat model:**
  - An external adversary drives botnets whose attack flows come from the Internet and must cross an in-line ML detector at the victim's ingress.
  - The detector uses flow- or packet-level statistical patterns (sizes, delays) and does not inspect payload.
  - The attacker has no knowledge of the model, features, feature extractor or training data. Its only feedback is whether the detector blocked or dropped the traffic (strict hard-label).
  - The attacker can use public benign traffic that differs from the detector's training data, and can probe the detector to train the agent. — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- **Mechanism:**
  - **Stage 1:** "Traffic-BERT" is pre-trained on benign traffic from public datasets, using a network-specific tokenizer and a new attention block.
  - **Stage 2:** an RL agent, formulated as a finite-horizon MDP, picks the location and type of each packet modification step by step, guided by Traffic-BERT.
  - **Reward:** includes dissimilarity and effectiveness penalties, so the traffic keeps its stealth and attack function. The agent uses Q-values with a Q-value threshold ξ′ and a step threshold τ. — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- **Targets:**
  - Traditional ML detectors: Whisper, FlowLens, NetBeacon.
  - DL detectors: Vanilla features + RNN, CICFlowMeter + MLP, Kitsune.
  - 12 attacks drawn from multiple datasets, 80 attack scenarios in total, plus real backbone traces such as MAWI.
  - Baselines include a GAN + particle-swarm traffic-mimicry method and Amoeba-style packet splitting. Some baselines get ASR < 0.01 on some targets. — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- **Results:**
  - Over 96.65% attack success rate (ASR) across 80 scenarios.
  - Average ASR by detector: Whisper 0.9878, FlowLens 0.9717, NetBeacon 0.9809, Vanilla+RNN 0.9782, CICFlowMeter+MLP 0.9626, Kitsune 0.991.
  - At most 10 modification steps per flow; KL divergence of 0.013 between the original and modified bandwidth distributions.
  - Generates 4.239K adversarial packets per second. — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- **Against robust detectors:** it evades both Whisper (empirically robust) and **BARS** (certified, NDSS 2023). The authors' explanation: BARS certifies a bounded region in feature space, but small traffic-space changes become large feature-space distances. They state that feature-space defenses (adversarial training, randomized smoothing) "fail to counter NetMasquerade". — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- **Costs and limitations:**
  - Needs a probing phase. With smaller probing budgets the attack reaches 35.6%, 70.4% and 88.9% of its final ASR (as reported).
  - Under 5%, 15% and 30% feedback-noise levels, ASR degrades gracefully rather than collapsing.
  - **Defenses the authors suggest:** traffic-space adversarial training; traffic-space certification (e.g., bounding the number of inserted packets); and inference-time randomization of architecture or parameters, which breaks the attack's assumption of a static decision boundary. — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)

**P2. CertTA: "Certified Robustness Made Practical for Learning-Based Traffic Analysis"**
- **Venue and authors:** USENIX Security 2025, pp. 7349–7368. Authors are Jinzhu Yan, Zhuotao Liu, Yuyang Xie, Ke Xu (Tsinghua / Zhongguancun Lab), Shiyu Liang (SJTU) and Lin Liu (NUDT). Code is at InspiringGroup-Lab/CertTA and the artifact is on Zenodo. — [USENIX page](https://www.usenix.org/conference/usenixsecurity25/presentation/yan-jinzhu); [Zenodo](https://zenodo.org/records/15594865)
- **Threat model:**
  - The adversary crafts adversarial flows using packet insertion, substitution, deletion, length padding and timing delays, alone or combined.
  - It may use advanced attacks (e.g., Blanket, Amoeba, Prism), but must respect network-protocol feasibility constraints. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)
- **Mechanism (multi-modal randomized smoothing):**
  - For a flow with n packets, each smoothing sample randomly selects d packets (keeping their order) and adds i.i.d. Exponential noise to the length (scale β_l) and the inter-arrival time (scale β_t) of each selected packet.
  - The base model f is evaluated on these samples, and the majority prediction defines g.
  - **Theorem 1** bounds the ratio of sample probabilities between x and x̃. Here x̃ is x with non-negative length/time noise vectors δ_l, δ_t added, plus n_ins inserted, n_sub substituted and n_del deleted packets.
  - The bound combines a binomial-coefficient term from the packet selection with an exponential term exp(Σ δ_l/β_l + δ_t/β_t). This yields certified regions jointly over additive (length/time) and edit (insert/delete/substitute) perturbations. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)
- **Evaluation setup:**
  - **Models:** kFP, Kitsune (supervised), Whisper (supervised), DF, YaTC and TrafficFormer. Three unsupervised models are also in the artifact.
  - **Datasets:** CICDOH20 and TIISSRC23.
  - **Baselines:** VRS, BARS and RS-Del (randomized smoothing for deletion).
  - **Attacks:** three categories of multi-modal attacks (Blanket, Amoeba, Prism). — [PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf); [Zenodo](https://zenodo.org/records/15594865)
- **Results:**
  - Where existing approaches keep no certified accuracy at all, CertTA reaches 99% certified accuracy with the two Transformer models and more than 80% on the other four.
  - It also proposes integrating with an anomaly detector, so the attacker faces a dilemma: perturbations small enough to slip past the anomaly detector are certified away, and large ones get flagged. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)
- **Assumptions:**
  - The guarantees hold only for perturbations within the certified (n_ins, n_del, n_sub, δ) budget and in the smoothed-classifier sense (probabilistic, Monte-Carlo estimated).
  - The smoothing hyper-parameters (e.g., β_l = 100, β_t = 20 ms, d = ⌈0.2n⌉) are tuned per dataset. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)

**P3. PANTS: "Robustifying ML-powered Network Classifiers with PANTS"**
- **Venue and authors:** USENIX Security 2025, pp. 7291–7310. Minhao Jin and Maria Apostolaki (Princeton). — [USENIX page](https://www.usenix.org/conference/usenixsecurity25/presentation/jin-minhao)
- **Problem:** ML-powered network classifiers (MNCs) contain non-differentiable components such as feature extraction and traffic engineering. Their adversarial inputs must also be realizable and semantics-preserving, so plain gradient-based adversarial ML does not apply. — [USENIX page](https://www.usenix.org/conference/usenixsecurity25/presentation/jin-minhao)
- **Threat model:** white-box, with full access to the MNC's implementation and a training dataset. The operator configures the threat model through domain rules; for example, adversarial samples must be valid packet sequences, so TCP never ACKs a packet before it is sent.
  - **End-host attacker:** may delay the flow by up to 20% of its original duration and touch at most 20% of the packets.
  - **In-path attacker:** may delay packets in only one direction, by up to 20% of the flow duration. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf)
- **Mechanism:**
  - Adversarial ML (e.g., PGD on features) proposes feature-space targets, focusing on the most vulnerable features: those that are easy to change under the threat model and important to the model.
  - An SMT solver then finds a realizable packet sequence that meets those targets.
  - This is embedded in iterative adversarial training (about 180 samples per benign sample).
  - Speed: about 1.7 samples per second. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf)
- **Applications and datasets:** VPN detection (ISCXVPN2016, 8,577 bidirectional flows), QoE inference (VCAML), and a third application that is UNVERIFIED (likely IoT/app classification). Models: MLP, CNN, Transformer and RF. — [PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf)
- **Results:**
  - Median ASR of 35.31%, versus 19.57% for Amoeba and 10.31% for BAP. That is "70% and 2x more likely" to find adversarial inputs.
  - In one case PANTS deceives MLP, CNN and Transformer classifiers at 81.12%, 94.25% and 99.80%.
  - PANTS-robustified models are 52.7% more robust, including against attackers not considered during robustification, without losing accuracy.
  - Training on non-realizable samples degrades accuracy and is far less effective at robustifying the model (e.g., 92% less effective for RF). — [PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf)

**P4. "What is the Problem Space?" Defining Host-space Adversarial Perturbations against Network Intrusion Detection Systems**
- **Venue and authors:** ACM AsiaCCS 2026 (arXiv 2605.25822, May 2026). Miel Verkerken, Laurens D'hooge, Bruno Volckaert, Filip De Turck (Ghent) and Giovanni Apruzzese. — [arXiv](https://arxiv.org/abs/2605.25822)
- **Literature review:** a systematic review of 316 papers finds that prior work perturbs pre-collected data, such as packets captured by a router or flows analysed by the NIDS. That may be beyond an attacker who controls only unprivileged hosts. — [arXiv](https://arxiv.org/html/2605.25822)
- **Definition:** host-space perturbations (HsP) mean executing a different set of operations (𝒪′ ≠ 𝒪) on an attacker-controlled host to achieve the same goal. They satisfy Pierazzi et al.'s problem-space properties, but they are not "problem-space transformations" of an existing sample. — [arXiv PDF](https://arxiv.org/pdf/2605.25822)
- **Results:**
  - Models trained on CICIDS17/CICIDS18 detect SSH brute-force from `patator`, but miss it when one character of the launch command is changed. The baseline models were trained on `patator --persistent=1` traffic; exactly which character was changed is UNVERIFIED in my extraction.
  - Switching to other tools (Hydra, Medusa) also evades some models (e.g., SVM).
  - The findings are confirmed on benchmarks and on a real-world network. The authors conclude that the security of ML-NIDS "should be re-assessed". — [arXiv PDF](https://arxiv.org/pdf/2605.25822)

**P5. PCAP-Backdoor: Backdoor Poisoning Generator for Network Traffic in CPS/IoT Environments**
- **Venue and authors:** arXiv 2501.15563 (v2, Jan 2025). First author Ajesh Koyatan Chathoth (University of Pittsburgh); other authors UNVERIFIED. It appears in the ACM DL as DOI 10.1145/3805033, venue UNVERIFIED. — [arXiv PDF](https://arxiv.org/pdf/2501.15563); [ACM](https://dl.acm.org/doi/10.1145/3805033)
- **Threat model:** the adversary controls a subset of training samples (third-party or public data) by capturing packets from devices it controls. It can manipulate protocols, IPs and ports to embed a trigger. — [arXiv PDF](https://arxiv.org/pdf/2501.15563)
- **Mechanism:**
  - Triggers are inserted at the PCAP level, before feature extraction (a Kitsune-style extractor with 115 features), using realistic packets that keep the device's TCP port and frame length. Packet selection ratio R = 0.2.
  - A naive packet insertion causes protocol anomalies ("TCP ACKed unseen segment", port reuse), which the method avoids. — [arXiv PDF](https://arxiv.org/pdf/2501.15563)
- **Results:**
  - Poisoning about 1% or less of the training data can backdoor the model.
  - Example: CPS ICMP flooding is misclassified as benign with 0.97 ASR at 2% poisoning, versus 35% poisoning needed for label flipping.
  - Datasets: CPS SCADA (Modbus) plus IoT data. — [arXiv PDF](https://arxiv.org/pdf/2501.15563)

**P6. "Constrained Network Adversarial Attacks: Validity, Robustness, and Transferability"**
- **Venue and authors:** arXiv 2505.01328 (May 2025, no venue listed). Anass Grini, Oumaima Taheri, Btissam El Khamlichi and Amal El Fallah-Seghrouchni. — [arXiv](https://arxiv.org/abs/2505.01328)
- **Results:**
  - Up to 80.3% of adversarial examples from standard attacks violate domain constraints in IoT/NIDS data.
  - MLP surrogates produce more valid adversarial examples than CNN or LSTM surrogates.
  - The paper studies how attack severity transfers from the MLP surrogate to other models. — [arXiv](https://arxiv.org/abs/2505.01328)

**P7. PLAA: "Packet-level Adversarial Attacks in Network Traffic Detection"**
- **Venue and authors:** IEEE TrustCom 2025 (DOI 10.1109/Trustcom66490.2025.00153); arXiv 2606.28439 (June 2026). Jinhao You, Zan Zhou, Shujie Yang, Yi Sun, Lei Zhang and Changqiao Xu. — [arXiv](https://arxiv.org/abs/2606.28439)
- **Method and results:**
  - Generates packet-level features incrementally, with semantic-integrity checks at each stage.
  - 92.78% average evasion success on CIC-UNSW-NB15, CIC-DDoS2019 and CIC-IDS-2017.
  - The authors claim the adversarial traffic stays semantically consistent with the original malicious traffic. — [arXiv](https://arxiv.org/abs/2606.28439)

**Leads checked only through an abstract page or search snippet (not deeply extracted)**
- **"Beyond RTT" residential-proxy detection (NDSS 2026):**
  - RTT-discrepancy detectors are fragile: simple traffic-scheduling attacks cut recall from 99% to 8%.
  - The authors propose flow-correlation features and the CorrTransform model.
  - Exact title and authors UNVERIFIED. — [papers.cool NDSS 2026](https://papers.cool/venue/NDSS.2026?group=Fall)
- **CoLD, collaborative label denoising for NIDS (NDSS 2026):** listed in the program. It relates to poisoning and noisy labels, not evasion. Details UNVERIFIED. — [papers.cool NDSS 2026](https://papers.cool/venue/NDSS.2026?group=Summer)
- **SmartDetector, robust malicious encrypted traffic detection via contrastive learning (IEEE TIFS 2025, DOI 10.1109/TIFS.2025.3560560):** reports F1 and AUC above 93% under evasion/obfuscation. Authors and threat model UNVERIFIED. — [ADS](https://ui.adsabs.harvard.edu/abs/2025ITIF...20.4228S/abstract)
- **Catillo et al., "Towards realistic problem-space adversarial attacks against machine learning in network intrusion detection" (ARES 2024):** venue taken from citation snippets only. — [search context via arXiv 2605.25822 refs](https://arxiv.org/html/2605.25822)
- **"Problem space structural adversarial attacks for NIDS based on GNNs" (arXiv 2403.11830, 2024):** claims the first formalization of adversarial attacks tailored to GNN-based NIDS. Venue UNVERIFIED. — [arXiv](https://arxiv.org/html/2403.11830)
- **"Vulnerability Disclosure through Adaptive Black-Box Adversarial Attacks on NIDS" (arXiv 2506.20576, 2025):** contents UNVERIFIED. — [arXiv](https://arxiv.org/pdf/2506.20576)
- **"Detecting Adversarial Evasion Attacks Against Autoencoder-Based NIDS" (arXiv 2607.01194, 2026):** two detectors, one working on packet inter-arrival-time features. — [arXiv](https://arxiv.org/abs/2607.01194)
- **"Adversarial Robustness of Traffic Classification under Resource Constraints: Input Structure Matters" (arXiv 2512.02276, Dec 2025):** input structure significantly affects robustness of small edge/IoT classifiers. — [ResearchGate](https://www.researchgate.net/publication/398268886_Adversarial_Robustness_of_Traffic_Classification_under_Resource_Constraints_Input_Structure_Matters)
- **Implementing problem-space attacks with Scapy packet modification (Hasan et al., IEEE LCN 2025, DOI 10.1109/LCN65610.2025.11146360):** UNVERIFIED beyond a snippet. — [CSU research output](https://researchoutput.csu.edu.au/en/publications/implementing-practical-problem-space-adversarial-attacks-on-moder/)
- **Ma et al., backdoor attack and defense for AI-based IoT IDS (IET Information Security, Sept 2025):** CICIoT2023 dataset; attacks AdaBoost, GBDT, XGBoost, MLP, CNN and RNN. Outside the target venue list. — [Wiley](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/ise2/6664900)
- **Background, pre-2024 (labelled):** BARS (NDSS 2023, feature-space certification); Amoeba (RL censorship evasion, the baseline in PANTS and CertTA); Whisper (CCS 2021 / TNET 2022); Sommer & Paxson (2010); and the 2023 arXiv paper "Evasion Adversarial Attacks Remain Impractical Against ML-based NIDS". — [BARS](https://dev.ndss-symposium.org/ndss-paper/bars-local-robustness-certification-for-deep-learning-based-traffic-analysis-systems); [arXiv 2306.05494](https://arxiv.org/pdf/2306.05494)

### Inferences
- The Tsinghua group published both CertTA (certification) and NetMasquerade (an attack that beats BARS). NetMasquerade's text, as extracted, evaluates against BARS but does **not** appear to evaluate against CertTA, even though CertTA is the "traffic-space certification" it proposes as a countermeasure. Whether NetMasquerade's ≤10-step edits fall inside CertTA's certified budget is an open, testable question for a USENIX 2027 project.
- The papers apply "realism" at four distinct levels:
  1. Feature-space constraint validity (P6).
  2. Packet-level and semantic validity (PLAA, PANTS, CertTA).
  3. In-network or attacker-sender traffic edits (NetMasquerade).
  4. Host-space behavior changes (P4).

  Most work stops at level 2 or 3.

### Gaps
- Not verified: IEEE S&P 2024–2026, ACM CCS 2024–2025, RAID, ACSAC, EuroS&P and TDSC proceedings were not browsed directly. There may be relevant papers there (e.g., on traffic foundation-model robustness) that this pass missed.
- No 2024–2026 top-venue paper was found that attacks a pre-trained traffic foundation model (ET-BERT, YaTC, TrafficFormer, NetMamba) adversarially. CertTA includes YaTC and TrafficFormer only as models to certify.

## What is the state of the art on realistic constraints, and which defenses survive adaptive attacks?

### Takeaway
The state of the art has moved from feature-space perturbations to traffic-space edits, which feature-space defenses do not survive. These edits are packet insertion, padding, delay and splitting, under protocol, semantic and budget constraints: SMT-constrained (PANTS), RL with benign mimicry (NetMasquerade), or packet-incremental (PLAA). Host-space perturbations (P4) raise the bar further. The only defenses with evidence against traffic-space attacks are traffic-space adversarial training with realizable samples (PANTS) and traffic-space certification (CertTA). Neither has been evaluated against the strongest newer adaptive black-box attack (NetMasquerade).

### Cited Findings
- Up to 80.3% of standard adversarial examples on IoT/NIDS data are invalid under domain constraints, which inflates measured vulnerability. — [arXiv 2505.01328](https://arxiv.org/abs/2505.01328)
- Adversarial training on non-realizable or non-semantics-preserving samples degrades accuracy without much robustness gain. PANTS' realizable-sample training gives 52.7% more robustness, including against attackers outside the training threat model. — [PANTS PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf)
- NetMasquerade evades empirically robust Whisper and certified BARS. The authors argue feature-space adversarial training and randomized smoothing cannot counter traffic-space attacks, because small traffic changes become large feature-space shifts. — [NetMasquerade PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- A single-character change to an attack tool's command line (a host-space perturbation) bypasses ML-NIDS trained on CICIDS17/18. — [arXiv 2605.25822](https://arxiv.org/pdf/2605.25822)
- PANTS reports median ASR of 35.31% (PANTS), 19.57% (Amoeba) and 10.31% (BAP) under a 20% delay / 20% packet budget. — [PANTS PDF](https://www.usenix.org/system/files/usenixsecurity25-jin-minhao.pdf)

### Inferences
- "Adaptive attacker" evaluations are thin. PANTS tests transfer to attackers outside the training threat model; NetMasquerade tests against defended models. Neither paper adapts the attacker to the specific defense, for example a CertTA-aware attack or an attack on a PANTS-hardened model with knowledge of the hardening.
- Inference-time randomization is suggested as a defense against hard-label RL attacks. It is untested, and it is open to known EOT-style adaptive attacks from other domains.

### Gaps
- No verified 2024–2026 paper gives a unified, formal constraint language for traffic adversarial examples across protocols, comparable to tabular-constraint work. PANTS' SMT rules come closest.
- No verified evaluation of defenses against host-space perturbations.

## Are there provable/certified guarantees for NIDS robustness, and under what assumptions?

### Takeaway
Yes, but only probabilistic randomized-smoothing guarantees, local to an input and within a bounded edit budget. CertTA (USENIX Sec 2025) is the state of the art: joint certificates over length and timing noise plus packet insertion, deletion and substitution. It supersedes BARS (NDSS 2023), whose feature-space bounds NetMasquerade shows can be circumvented.

### Cited Findings
- CertTA certifies against combined additive (length/IAT) and edit (n_ins, n_sub, n_del) perturbations via Exponential-noise and subset-selection smoothing (Theorem 1). — [CertTA PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)
- In settings where VRS, BARS and RS-Del certify nothing, CertTA certifies 99% (Transformer models) and more than 80% (other four models). — [CertTA PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)
- BARS certifies a bounded region in feature space, which NetMasquerade's traffic-space edits exceed once projected into features. — [NetMasquerade PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)

### Inferences
- What the certificates assume:
  - They are per-flow. Multi-flow, host-level and campaign-level attacks are not covered.
  - They are bounded by edit counts.
  - They hold with Monte-Carlo confidence.
  - They do not cover feature-extractor state, such as Kitsune's damped windows across flows, or the effect of the attacker's other flows on that state.
- No certified guarantees were found for backdoor or poisoning robustness of NIDS in 2024–2026.

### Gaps
- No verified work certifies robustness of flow meters or aggregation (e.g., flow timeouts, sampling).
- No verified work certifies anomaly-detector thresholds.

## Gaps and attack surfaces under-explored (detector updates, explanations, alert thresholds, NIDS pipeline)

### Takeaway
Poisoning work is mostly about data and labels (PCAP-Backdoor; the CoLD noisy-label line). No verified 2024–2026 top-venue paper attacks NIDS retraining or update pipelines, explanation components, or alert-threshold calibration, or the flow-meter / sampling layer as an attack target in its own right.

### Cited Findings
- PCAP-Backdoor shows that PCAP-level trigger injection before feature extraction needs only about 1–2% poisoning, versus 35% for label flipping. That points to public or third-party traffic data as a supply-chain risk. — [arXiv 2501.15563](https://arxiv.org/pdf/2501.15563)
- NetMasquerade says it chose thresholds against those that mainstream IDS products use to raise scan or anomaly alarms. It also assumes a static decision boundary, which implies that periodic retraining is an unstudied interaction. — [NetMasquerade PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- Ten-plus 2024–2026 papers show that the feature extractor (CICFlowMeter, Kitsune AfterImage) shapes evasion outcomes. This is mostly as an evaluation variable, not as the attack target. — [NetMasquerade PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf); [arXiv 2605.25822](https://arxiv.org/pdf/2605.25822)

### Inferences
- These are open directions for a USENIX 2027 project:
  1. Adaptive attacks against CertTA and PANTS-hardened detectors.
  2. Attacks on drift-adaptation or retraining loops, such as poisoning via traffic the attacker knows will be relabelled.
  3. Exploiting flow-meter semantics such as timeouts, sampling and flow-table eviction.
  4. Manipulating explanation components that SOC analysts rely on.
  5. Host-space-perturbation benchmarks.

### Gaps
- Searches for explanation attacks on NIDS and for attacks on traffic foundation models (2024–2026) returned no verified top-venue hits. This is absence of evidence from a limited search, not proof of absence.
