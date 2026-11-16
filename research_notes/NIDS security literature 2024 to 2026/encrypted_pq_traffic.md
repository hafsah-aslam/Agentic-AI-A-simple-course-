# ML on Encrypted Traffic for Security & the Impact of Post-Quantum TLS/QUIC/ECH (2024–2026)

Scope note: research was done on 2026-11-16 with a budget of about 20 tool calls. Each entry below says how it was verified. "VERIFIED (arXiv/primary)" means I fetched the paper's primary landing page (arXiv abstract page, NDSS page, or vendor blog). "SNIPPET-ONLY" means the information comes only from search-result snippets or aggregators. "UNVERIFIED" means the claim comes from background knowledge or a secondary source and needs checking. Abstract pages generally did not include threat model, baselines, costs, or exact results. Where a field could not be extracted it is marked "not extracted", not inferred.

## Q1. Which 2024–2026 papers cover (a) malicious encrypted traffic detection, (b) traffic foundation models and critiques of them, (c) PQ effects on detectors/fingerprinting, and (d) PQ-TLS deployment measurement? Paper-by-paper extraction

### Takeaway
The verified core set is 11 papers plus one industry source. It contains one top-4 SoK critique (IEEE S&P 2025) and one SIGCOMM 2025 critique showing that pre-trained traffic classifiers rely on shortcuts. NDSS 2024 has a malicious-encrypted-traffic detector (RAPIER). One 2026 arXiv preprint directly studies PQC-induced drift in encrypted-traffic classifiers. An IMC 2026 paper gives the first longitudinal PQ-TLS deployment measurement. Many 2025–2026 foundation-model and malicious-traffic preprints exist but are unvetted.

### Cited Findings

#### (b) Critiques of encrypted traffic classifiers and foundation models

**P1. SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers.** VERIFIED (arXiv abstract page)
- Authors: Nimesha Wickramasinghe, Arash Shaghaghi, Gene Tsudik, Sanjay Jha. Venue: IEEE S&P 2025, pp. 1825–1843, DOI 10.1109/SP61157.2025.00165. arXiv 2503.20093, v1 25 Mar 2025, v4 16 May 2025. — [arXiv](https://arxiv.org/abs/2503.20093); [NSF PAR](https://par.nsf.gov/biblio/10617400)
- Problem: ML encrypted-traffic classifiers are evaluated on outdated datasets and unverified assumptions. — [arXiv](https://arxiv.org/abs/2503.20093)
- Mechanism and evaluation: a systematic review and taxonomy covering design choices, benchmarking suites, and assumptions, plus **348 feature-occlusion experiments** on state-of-the-art classifiers. — [arXiv](https://arxiv.org/abs/2503.20093)
- Key result: **most proposed "encrypted" traffic classifiers actually trained on unencrypted traffic** because they used legacy datasets. Design oversights cause overfitting. — [arXiv](https://arxiv.org/abs/2503.20093)
- Dataset contribution: CipherSpectrum, a contemporary TLS 1.3-era dataset. — [arXiv HTML v4](https://arxiv.org/html/2503.20093v4)
- An aggregator says pre-2018 datasets do not reflect TLS 1.3 traffic. — [alphaxiv](https://alphaxiv.org/abs/2503.20093)
- Not extracted: the number of papers surveyed, the specific classifiers tested, and per-model numbers.

**P2. The Sweet Danger of Sugar: Debunking Representation Learning for Encrypted Traffic Classification.** VERIFIED (arXiv abstract page)
- Authors: Yuqi Zhao, Giovanni Dettori, Matteo Boffa, Luca Vassio, Marco Mellia. Venue: ACM SIGCOMM 2025, DOI 10.1145/3718958.3750498. arXiv 2507.16438, 22 Jul 2025. — [arXiv](https://arxiv.org/abs/2507.16438)
- Problem and hypothesis: BERT-style representation-learning traffic classifiers claim "up to 98% accuracy". The authors argue these results are inflated by data-preparation flaws that create shortcuts, meaning spurious feature–label correlations. — [arXiv](https://arxiv.org/abs/2507.16438)
- Key result: when shortcuts are removed, as in realistic settings, the models perform poorly. The authors propose **Pcap-Encoder**, a language-model encoder over protocol headers. It is the only evaluated model that gives a useful representation, but its complexity may limit practical use. The paper proposes a more rigorous evaluation and benchmarking methodology. — [arXiv](https://arxiv.org/abs/2507.16438)
- SNIPPET-ONLY: performance drops about 80% once shortcuts are removed. Randomly initialised ET-BERT matches the pre-trained model. ET-BERT's preprocessing leaks packets of the same flow across the train/test split. — [arXiv PDF via search](https://arxiv.org/pdf/2507.16438); [ResearchGate](https://www.researchgate.net/publication/393923523_The_Sweet_Danger_of_Sugar_Debunking_Representation_Learning_for_Encrypted_Traffic_Classification). These three points are not on the abstract page. Confirm them in the full text before quoting.

**P3. Bias in the Shadows: Explore Shortcuts in Encrypted Network Traffic Classification.** VERIFIED (arXiv abstract page); venue PARTIAL
- Authors: Chuyi Wang, Xiaohui Xie, Tongze Wang, Yong Cui. arXiv 2601.10180, 15 Jan 2026. The page lists a related DOI, 10.1109/IWQoS70441.2026.11661209, which suggests IWQoS 2026. That is not a target venue. — [arXiv](https://arxiv.org/abs/2601.10180)
- Mechanism: **BiasSeeker** is a model-agnostic, semi-automated framework that runs statistical correlation analysis on raw bytes. It finds dataset-specific spurious or environment-entangled features before any training, and it includes a taxonomy of shortcut types. Evaluation covers **19 public datasets and 3 NTC tasks**. No metrics appear on the abstract page. — [arXiv](https://arxiv.org/abs/2601.10180)

**P4. SoK: Where Do Flow Labels Come From? Auditing Label Provenance in Encrypted Traffic Benchmarks.** VERIFIED (arXiv); no venue
- Authors: Sizhe Huang, Shujie Yang. arXiv 2609.02140, 2 Sep 2026. — [arXiv](https://arxiv.org/abs/2609.02140)
- Findings:
  - It audits **14 benchmark entries** and identifies two labelling strategies: coarse inheritance and overstrict filtering.
  - Downstream papers' task objects disagree with the recovered label record in **8 of 23** cells.
  - For strict side-channel features, the balanced-accuracy ceiling on label-inheriting public benchmarks is **0.56–0.76**.
  - Only **24.95%** of connections carry their own observable SNI.
  - Discarded connections raise macro accuracy from **0.44 to 0.65** through same-run co-occurrence features, which is a leakage path.
  - Source: [arXiv](https://arxiv.org/abs/2609.02140)

#### (b) Traffic foundation and pre-trained models

**P5. TrafficFormer: An Efficient Pre-trained Model for Traffic Data.** Authors VERIFIED (lab page); venue UNVERIFIED
- Authors: Guangmeng Zhou, Xiongwen Guo, Zhuotao Liu, Tong Li, Qi Li, Ke Xu. — [Liu lab page](https://liuzhuotao.github.io/publications/secure_networking_and_systems_infrastructure/encrypted_traffic_analysis/1-2-7)
- Mechanism: a fine-grained multi-classification pre-training task, plus field-randomization augmentation during fine-tuning. Reports up to 10% F1 improvement across 6 traffic classification datasets. — [Liu lab page](https://liuzhuotao.github.io/publications/secure_networking_and_systems_infrastructure/encrypted_traffic_analysis/1-2-7)
- Venue: I believe it is IEEE S&P 2025, but I could not confirm this. DBLP was blocked by bot protection. Mark it UNVERIFIED.
- Cost (third-party): a FlowletFormer comparison reports 45 h pre-training for TrafficFormer versus 41 h for ET-BERT, and similar inference throughput (150.45 vs 148.92 samples/s). — [FlowletFormer arXiv 2508.19924](https://arxiv.org/html/2508.19924v1)
- The field-randomization augmentation is effectively a shortcut mitigation, since it randomizes header fields such as IP and port. Interpretation: inference.

**Other foundation-model papers found but not deeply extracted (SNIPPET-ONLY, venues unverified):**
- FlowletFormer (arXiv 2508.19924). — [arXiv](https://arxiv.org/html/2508.19924v1)
- Traffic-MoE: A Sparse Foundation Model for Network Traffic Analysis (arXiv 2601.00357). — [arXiv](https://arxiv.org/html/2601.00357)
- Offloading a network foundation model to SmartNIC (arXiv 2508.02001). — [arXiv](https://arxiv.org/pdf/2508.02001)
- MambaNetBurst, a byte-level classifier "without tokenization or pretraining" (arXiv 2605.11034). — [arXiv](https://arxiv.org/pdf/2605.11034)
- FlowCLIP, contrastive pre-training with domain names (arXiv 2606.17746). — [arXiv](https://arxiv.org/pdf/2606.17746)
- UniAlign, for distribution shift (arXiv 2605.17575). — [arXiv](https://arxiv.org/pdf/2605.17575)
- An evaluation paper uses ET-BERT, YaTC, NetMamba, netFound, TrafficFormer, and Pcap-Encoder as baselines. This shows the standard 2025–26 baseline set. — [search snippet](https://arxiv.org/pdf/2601.22494)
- Background (pre-2024 or not re-verified): ET-BERT (WWW 2022, arXiv 2202.06335) — [arXiv](https://arxiv.org/pdf/2202.06335). netFound, YaTC, and NetMamba details are UNVERIFIED in this pass.

#### (a) Malicious encrypted traffic detection

**P6. Low-Quality Training Data Only? A Robust Framework for Detecting Encrypted Malicious Network Traffic (RAPIER).** VERIFIED (NDSS page)
- Authors: Yuqi Qing, Qilei Yin, Xinhao Deng, Yihao Chen, Zhuotao Liu, Kun Sun, Ke Xu, Jia Zhang, Qi Li (Tsinghua, Zhongguancun Lab, George Mason University). Venue: NDSS 2024, DOI 10.14722/ndss.2024.23081 (DOI from search snippet). — [NDSS](https://www.ndss-symposium.org/ndss-paper/low-quality-training-data-only-a-robust-framework-for-detecting-encrypted-malicious-network-traffic/)
- Problem and threat model: evolving malware, with training data that is scarce, mislabeled, or noisy.
- Hypothesis: normal traffic clusters tightly in feature space, while malicious traffic is dispersed.
- Mechanism: distribution-aware data augmentation, a feature-vector module, and a label-noise-correction module.
- Data: two public datasets, a combined dataset, and a real enterprise dataset.
- Results:
  - With 1,000 samples at 45% label noise, F1 is **0.770 / 0.776 / 0.855** on the three public settings.
  - Average F1 improvement over existing methods is **352.6% / 284.3% / 214.9%**.
  - On the enterprise data, the best F1 is **0.773**, a 272.5% average improvement.
  - Source: [NDSS](https://www.ndss-symposium.org/ndss-paper/low-quality-training-data-only-a-robust-framework-for-detecting-encrypted-malicious-network-traffic/)
- Unstated limitation (inference): an absolute F1 near 0.77 means many errors remain. The large relative gains reflect weak baselines under 45% noise.

**P7. Training with Only 1.0‰ Samples: Malicious Traffic Detection via Cross-Modality Feature Fusion.** Title and venue SNIPPET-ONLY
- Listed in the ACM CCS '25 proceedings, DOI 10.1145/3719027.3765143. The ACM page returned HTTP 403, so authors and results were not extracted. — [ACM DL](https://dl.acm.org/doi/10.1145/3719027.3765143)

**Further 2025–26 candidates (SNIPPET-ONLY; titles only, venues not verified):**
- MalMoE: Mixture-of-Experts Enhanced Encrypted Malicious Traffic Detection Under Graph Drift (arXiv 2602.10157). — [arXiv](https://arxiv.org/pdf/2602.10157)
- MalRAG: A Retrieval-Augmented LLM Framework for Open-set Malicious Traffic Identification (arXiv 2511.14129). — [arXiv](https://arxiv.org/pdf/2511.14129)
- A Hard-Label Black-Box Evasion Attack against ML-based Malicious Traffic Detection Systems (arXiv 2510.14906). — [arXiv](https://arxiv.org/pdf/2510.14906)
- CertTA: Certified Robustness Made Practical for Learning-Based Traffic Analysis. A curated list places it at USENIX Security 2025, but the listing is ambiguous, so it is UNVERIFIED. — [Awesome-ML-SP-Papers](https://github.com/gnipping/Awesome-ML-SP-Papers)
- Background: HyperVision, "Detecting Unknown Encrypted Malicious Traffic in Real Time via Flow Interaction Graph Analysis" (NDSS 2023, arXiv 2301.13686). — [arXiv](https://arxiv.org/pdf/2301.13686)
- Curated index of encrypted-traffic-analysis papers (venue labels need checking). — [ETA-Resource](https://github.com/linwhitehat/ETA-Resource)

#### (c) PQ effects on classifiers and fingerprinting

**P8. The Colossus with Feet of Clay: Debunking Encrypted Traffic Classifiers under PQC Evolution.** VERIFIED (arXiv); no venue
- Authors: Bingzhen Li, Lingjia Meng, Runhan Song, Chuanzhou Pan, Tongjun Pu, Ziqiang Ma, Yupeng Jiang, Lei Cui, Zhiyu Hao. arXiv 2608.22683, 24 Aug 2026. Code is in an anonymous 4open.science repository (PQ-WF-Eval). — [arXiv](https://arxiv.org/abs/2608.22683)
- Hypothesis: "PQC-induced protocol drift". Hybrid PQ key exchange changes observable traffic but not the labels.
- Setting: closed-world HTTPS website fingerprinting over TLS 1.3 with X25519MLKEM768.
- Method: a benchmark that pairs traditional and hybrid-PQC traffic. It tests **5 classifiers** and several side-channel representations in matched-domain, cross-domain, and deployment-ratio settings.
- Result: website information remains learnable, but configurations that work in-domain lose reliability across cryptographic domains. The authors recommend protocol-aware, cross-domain evaluation. — [arXiv](https://arxiv.org/abs/2608.22683)
- SNIPPET-ONLY mechanism text: larger hybrid key shares "may shift ... TCP segmentation and packet positions". Under fixed or truncated observation windows, classifiers capture different parts of the handshake. — [arXiv HTML](https://arxiv.org/html/2608.22683)
- Not extracted: exact accuracy drops and dataset sizes.
- Limitation (inference): the paper covers website fingerprinting, which is a privacy attack, not NIDS or malware detection. It is not peer reviewed.

**P9. Classifying Implementations of Cryptographic Primitives and Protocols that Use Post-Quantum Algorithms.** VERIFIED (arXiv); no venue
- Authors: Tushin Mallick, Cristina Nita-Rotaru, Ashish Kundu, Ramana Kompella. arXiv 2503.17830, v1 22 Mar 2025, v4 10 Jan 2026. An earlier version was titled "Fingerprinting Implementations of ...". — [arXiv](https://arxiv.org/abs/2503.17830); [v1 HTML](https://arxiv.org/html/2503.17830v1)
- Scope: liboqs and CIRCL, PQ use in TLS, SSH, QUIC, OpenVPN, and OIDC on Windows, Ubuntu, and macOS, and a Tranco scan for PQ-enabled TLS domains. The method is integrated into Cisco's QUARTZ analyzer. — [arXiv](https://arxiv.org/abs/2503.17830)
- Results:
  - Classical vs PQ key exchange is distinguished with **98%** accuracy.
  - Classical vs PQ signatures: **100%**.
  - The specific PQ KEM algorithm: **97%**.
  - The specific PQ signature algorithm: **86%**.
  - The same algorithm in liboqs vs CIRCL: up to **100%**.
  - Within CIRCL, PQ vs hybrid KEM: **97%**.
  - Source: [arXiv](https://arxiv.org/abs/2503.17830)
- Threat model: an on-path or same-network observer reads key shares in the plaintext ClientHello and ServerHello. — [search snippet of v1](https://arxiv.org/html/2503.17830v1)

#### (d) PQ-TLS deployment measurement

**P10. Mind the Gap: Policy vs Reality in Post-Quantum TLS Deployment.** VERIFIED (arXiv)
- Authors: Nimesha Wickramasinghe, Frank Li, Sanjay Jha, Arash Shaghaghi. Accepted to ACM IMC 2026. arXiv 2607.29005, 31 Jul 2026. — [arXiv](https://arxiv.org/abs/2607.29005)
- Scale: described as the first longitudinal PQ-TLS adoption study, with **more than 2 billion TLS handshakes, 1 million domains, and 11 vantage points**. — [arXiv](https://arxiv.org/abs/2607.29005)
- Findings:
  - Deployment converges on a single hybrid construction.
  - Most progress comes from managed infrastructure providers such as CDNs.
  - National roadmaps correspond poorly to observed deployment.
  - On the Internet, PQ-TLS adds no meaningful latency, which contradicts earlier lab studies.
  - PQ-TLS is often deployed alongside legacy TLS configurations.
  - The abstract does not mention middleboxes or IDS.
  - Source: [arXiv](https://arxiv.org/abs/2607.29005)
- This is the same first and last author team as P1, the S&P 2025 SoK.

**P11. Measurement Study of Post-Quantum Readiness of Internet: 2026.** VERIFIED (arXiv); no venue
- Authors: Vanishka Mohan Dubey, Gaurav Varshney. arXiv 2606.16473, 15 Jun 2026. — [arXiv](https://arxiv.org/abs/2606.16473)
- Results across **32,011 domains**:
  - **49.3%** support hybrid PQ key exchange (e.g., X25519MLKEM768).
  - **50.7%** use only classical key exchange.
  - **15.70%** still use TLS 1.2.
  - **0%** use hybrid PQ certificates.
  - Banking and government domains lag.
  - Source: [arXiv](https://arxiv.org/abs/2606.16473)

**Other 2026 arXiv measurement items (titles only, not extracted):**
- "Measuring Post-Quantum TLS Deployment Across UK Internet Sectors" (arXiv 2608.02147). — [arXiv](https://arxiv.org/pdf/2608.02147)
- "Operationalising Post Quantum TLS ... Financial Infrastructure" (arXiv 2605.17955). — [arXiv](https://arxiv.org/pdf/2605.17955)

**I1 (INDUSTRY SOURCE). Cloudflare, "State of the post-quantum Internet in 2025".** Bas Westerbaan, 28 Oct 2025. VERIFIED (primary blog)
- Usage: in late Oct 2025 the "majority" of human traffic to Cloudflare used PQ key agreement, described as "over 50% (and rising!)". — [Cloudflare](https://blog.cloudflare.com/pq-2025/)
- Origin support was about 0.5% in 2023 and 3.7% in 2025. — [Cloudflare](https://blog.cloudflare.com/pq-2025/)
- Default-enable timeline:
  - Chrome Desktop: Mar 2024.
  - Go: Aug 2024.
  - Chrome Android and Firefox Desktop: Nov 2024.
  - OpenSSL: Apr 2025.
  - Apple OS 26: Oct 2025.
  - Source: [Cloudflare](https://blog.cloudflare.com/pq-2025/)
- Ossification: earlier NTRU-HRSS experiments broke connections because middleboxes and load balancers assumed the ClientHello fits in one packet. The "fast" method of sending PQ shares to origins immediately would break **0.05%** of connections, so Cloudflare defaults to HelloRetryRequest for non-enterprise customers. — [Cloudflare](https://blog.cloudflare.com/pq-2025/); [Cloudflare origins post](https://blog.cloudflare.com/post-quantum-to-origins)
- Secondary and unconfirmed: "more than two-thirds of human TLS traffic to Cloudflare" was hybrid ML-KEM by April 2026, reported via a search summary. I did not reach the primary source. — [InfoQ (search result)](https://www.infoq.com/news/2026/03/cloudflare-post-quantum-ipsec/). A scraping vendor's figure of "57.4% of browser traffic" has no methodology. Do not use it. — [Scrapfly](https://scrapfly.io/blog/posts/post-quantum-tls-bot-detection)

### Inferences
- The two top-venue critiques (P1 at S&P 2025, P2 at SIGCOMM 2025) and the follow-ups (P3, P4) together make a strong 2025–26 case that published encrypted-traffic results, especially for pre-trained models, are inflated by legacy unencrypted data, shortcuts, flow leakage, and label provenance problems.
- Only one paper (P8) directly tests PQ drift on encrypted-traffic classifiers, and it covers website fingerprinting, not malicious-traffic detection.
- Wickramasinghe/Shaghaghi/Jha appear on both P1 and P10. That team is the likely closest competitor for a USENIX Security 2027 paper on PQ × NIDS.

### Gaps
- Not extracted for most papers: threat models, baselines, costs, and exact numbers. The ACM DL returned 403 and DBLP was bot-blocked.
- TrafficFormer's venue (believed to be S&P 2025) and CertTA's venue (USENIX Security 2025) are UNVERIFIED.
- netFound, NetMamba, and YaTC were not verified in this pass.
- I found no verified 2024–26 papers on ECH-specific or DoH-specific malicious-traffic detection at top venues, but I did not search them specifically. This is a search gap, not evidence that they don't exist.
- No USENIX Security 2024/2025/2026 encrypted-malware-detection paper was verified.

## Q2. Is there published work measuring how PQ-TLS adoption shifts NIDS / encrypted-classifier feature distributions, or middlebox/IDS breakage from PQ handshakes?

### Takeaway
I found no peer-reviewed work that measures PQ-induced feature shift for NIDS or malicious-traffic detectors. The closest is one non-peer-reviewed arXiv preprint (P8, Aug 2026). It shows PQ-induced drift breaks cross-domain *website-fingerprinting* classifiers. Evidence on middlebox breakage comes from industry sources (Cloudflare, tldr.fail, Chrome 124 reports), not academic measurement.

### Cited Findings
- P8 defines "PQC-induced protocol drift" and shows that in-domain-reliable classifiers lose reliability across classical vs X25519MLKEM768 traffic. — [arXiv 2608.22683](https://arxiv.org/abs/2608.22683)
- PQ use is itself detectable: 98% accuracy for classical vs PQ KEM, and 97% for identifying the algorithm. This means PQ status is a strong, confounding feature for any classifier. — [arXiv 2503.17830](https://arxiv.org/abs/2503.17830)
- Hybrid ML-KEM key share sizes:
  - Per a secondary blog relaying Cloudflare: about 1216 bytes for the hybrid key share versus 36 for X25519. This splits the ClientHello across packets. — [crawlex blog](https://blog.crawlex.net/blog/post-quantum-tls-ml-kem/)
  - Background (FIPS 203): an ML-KEM-768 encapsulation key is 1184 bytes, and 1184 + 32 = 1216, which matches. This arithmetic is mine, not from a fetched source.
- Middlebox and server breakage:
  - After Chrome/Edge 124 shipped Kyber768 hybrid (2024), some servers, firewalls, and middleboxes dropped connections after the ClientHello. tldr.fail was created to document this. — [BleepingComputer](https://www.bleepingcomputer.com/news/security/google-chromes-new-post-quantum-cryptography-may-break-tls-connections/); [itwiz](https://www.itwiz.io/post/secure-but-disconnected-quantum-resistant-chrome-124-and-how-to-fix-it)
  - A 2019 middlebox vendor dropped split ClientHellos. — [Cloudflare origins post](https://blog.cloudflare.com/post-quantum-to-origins)
  - Cloudflare measured 0.05% breakage for the "fast" method toward origins. — [Cloudflare](https://blog.cloudflare.com/pq-2025/)
- A 2026 deployment guide says the most common production issue with X25519MLKEM768 is TLS-inspection, firewall, DLP, or SSL-offload appliances rejecting an unknown group codepoint. This is a vendor or consultancy source. — [Encryption Consulting](https://www.encryptionconsulting.com/x25519mlkem768-tls-deployment-guide/)
- Fingerprinting practice (editorial, not measurement): PQ-capable ClientHellos change JA3/JA4 fingerprints, and ClientHello size becomes a coarse signal. — [BrowserInsight](https://browserinsight.net/blog/post-quantum-tls-fingerprinting)
- The IMC 2026 longitudinal study (P10) does not mention middleboxes or IDS in its abstract. — [arXiv 2607.29005](https://arxiv.org/abs/2607.29005)

### Inferences
- Packet-length, segmentation, and first-N-packets features are exposed to a clear mechanism of shift. Raw-byte foundation models that tokenize the first packets or bytes (the ET-BERT family) are too. That mechanism is the roughly 1.2 KB larger ClientHello spanning two TCP segments and QUIC Initial packets. This is plausible but untested for NIDS.
- Legacy datasets predate PQ deployment (2024–2025). Given P1's finding that most classifiers trained on legacy, often unencrypted, data, essentially every published detector was trained on pre-PQ traffic. Today, more than 50% of human Cloudflare traffic is PQ.
- PQ status correlates with the client stack. Browsers adopted PQ early, while malware and older libraries may not. So PQ can become a *new shortcut*: "PQ key share ⇒ benign browser". This is an untested hypothesis and a clear research opportunity.

### Gaps
- No academic measurement of IDS or NIDS signature or ML breakage under PQ handshakes. No study of Suricata/Zeek parsing of split ClientHellos with ML-KEM. No PQ-aware malicious-traffic dataset found.
- I did not open tldr.fail directly, so its specifics are unverified.
- QUIC-specific PQ effects were not found in academic work. A large ClientHello can span multiple QUIC Initial packets; this is background knowledge, not verified here. ECH interaction with PQ was not found either.

## Q3. Do traffic foundation models actually generalize? Evidence of leakage and shortcuts

### Takeaway
No, not under rigorous evaluation. Peer-reviewed evidence (P1 at S&P 2025, P2 at SIGCOMM 2025) and 2026 preprints (P3, P4, P8) consistently show that reported near-perfect accuracy depends on shortcuts, legacy unencrypted data, flow-level leakage, label artifacts, or matched train/test protocol conditions.

### Cited Findings
- Up to 98% claimed accuracy collapses once shortcuts are removed. Only a header-focused Pcap-Encoder yields useful representations. — [arXiv 2507.16438](https://arxiv.org/abs/2507.16438)
- SNIPPET-ONLY, to confirm in the full text: about an 80% drop, a randomly initialized ET-BERT matching the pre-trained one, and same-flow packet leakage across splits. — [arXiv PDF](https://arxiv.org/pdf/2507.16438)
- Most "encrypted" classifiers used unencrypted traffic, and 348 occlusion experiments show overfitting from design oversights. — [arXiv 2503.20093](https://arxiv.org/abs/2503.20093)
- Raw-byte pre-trained models exploit dataset-specific spurious features, analyzed across 19 datasets. — [arXiv 2601.10180](https://arxiv.org/abs/2601.10180)
- Label provenance limits achievable balanced accuracy to 0.56–0.76 on inheriting benchmarks. — [arXiv 2609.02140](https://arxiv.org/abs/2609.02140)
- Classifiers fail across classical vs PQ cryptographic domains. — [arXiv 2608.22683](https://arxiv.org/abs/2608.22683)
- The ET-BERT authors themselves attributed performance to the "imperfect randomness" of ciphertext. — [ET-BERT arXiv](https://arxiv.org/pdf/2202.06335)

### Inferences
- A USENIX Security 2027 evaluation should include several controls:
  - TLS 1.3 / QUIC-era data such as CipherSpectrum.
  - Flow- and session-level splits.
  - Masking of IP, port, TTL, and checksum fields.
  - A random-init ablation.
  - Label-provenance documentation.
  - Classical-vs-PQ cross-domain tests.

### Gaps
- No verified 2024–26 critique specific to *malicious*-traffic foundation models, as opposed to app or website classification.
- Exact quantitative results of P2, P3, and P8 were not extracted from the full texts.
