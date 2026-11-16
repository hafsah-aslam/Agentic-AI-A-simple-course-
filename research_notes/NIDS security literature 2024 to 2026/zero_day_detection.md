# Zero-Day / Unseen-Attack Detection in AI-Based NIDS (2024–2026)

Scope note on how deeply each source was read (this matters for every claim below):
- **Full PDF text read and searched:** Mateen (RAID 2024), RAPIER (NDSS 2024, first pages only), NetMasquerade (NDSS 2026, first pages plus targeted searches), TIPSO-GAN (NDSS 2026, abstract, research questions and the zero-day results table), CoLD (NDSS 2026, first pages only), GeCo (USENIX Sec 2025, first pages only), CertTA (USENIX Sec 2025, first pages only).
- **arXiv abstract and metadata only (API record):** netFound, "Demystifying Network Foundation Models", Lens, NetVAD, CLOSR contrastive loss (TNSM 2026), CND-IDS (DAC 2025), the self-supervised transformer contrastive IDS (IFIP Networking 2025), Zhou/Lau/Lee/Huo neural anomaly detection, Zero-X, the S&P 2025 encrypted-traffic SoK, "Are We There Yet?" (graph NIDS), GraphIDS (NeurIPS 2025), "Zero Day Attacks: Novel Behaviour or Novel Vulnerability?", "Illusion of Model Efficacy", and the dual-tier OCC IDS.
- **Search snippets or proceedings listings only (no abstract or PDF read by me):** "Rules Refine the Riddle" (CCS 2024), TrafficFormer (S&P 2025), the TIFS 2025 IIoT open-set IDS, the ACSAC 2025 "R+R: From Claims to Crashes" paper, and the CCS 2024 tunneled-flooding paper.
- DBLP and OpenAlex APIs were rate-limited or returned nothing during this session, so venues were verified through proceedings pages (ndss-symposium.org, usenix.org, sigsac.org, acsac.org), arXiv journal-ref and comment fields, or publisher listings. Each entry says which.

## Q1. Which 2024–2026 papers address zero-day / unseen-attack detection in network traffic, and what does each one contain?

### Takeaway
Top-tier security venues in 2024–2026 have few papers whose main goal is zero-day NIDS detection. The closest are NDSS 2026's TIPSO-GAN (the only one I found with an explicit leave-one-family-out (LOFO) plus cross-dataset protocol), RAID 2024's Mateen (one-class autoencoder (DAE) ensemble under distribution shift), NDSS 2024's RAPIER (malware that keeps evolving, trained on noisy low-quality data), and S&P 2025's TrafficFormer and SoK, which deal with traffic foundation models and encrypted traffic classification. Most work that explicitly claims "zero-day" detection appears in journals, DAC or IFIP venues, or arXiv. The strongest security-venue signal is negative: evaluation critiques (S&P 2025 SoK, ACSAC 2025 R+R) and a hard-label black-box evasion attack (NDSS 2026) that defeats Kitsune and other anomaly or ML detectors.

### Cited Findings

#### P1. Mateen: Adaptive Ensemble Learning for Network Anomaly Detection (RAID 2024). Full text read.
- Authors and venue: Fahad Alotaibi and Sergio Maffeis (Imperial College London), RAID 2024, Padua, Sep 30–Oct 2 2024, DOI 10.1145/3678890.3678901 — [Paper PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf); [OpenAlex DOI record](https://api.openalex.org/works/doi:10.1145%2F3678890.3678901)
- Problem: offline one-class DAE NIDS assume benign behaviour is static. As benign traffic evolves, false alarms rise, so the question is how to adapt "while avoiding false alarms caused by benign behavior changes" — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Mechanism: an ensemble of DAEs trained only on benign data, with an MSE anomaly score per sample. Shift is detected with a two-sample Kolmogorov–Smirnov test (sup over r of |F_Dc(r) − F_Bi(r)|) between ECDFs of MSE scores on a reference set and each incoming batch, at p < 0.05. Shifted batches trigger representative-sample selection, ranked by informativeness and representativeness, for human labelling. The model is then updated in a minor (incremental) or major (new model) way, and high-F1 members are merged while underperformers are discarded — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Datasets and protocol: CICIDS2017, CSE-CICIDS2018, Kitsune, plus two synthetic variants (mKitsune with a constant malicious ratio, and rKitsune with a recurring concept). Splits are "time-aware… to mitigate bias". Kitsune has no timestamps, so file order was used. The authors acknowledge the data is synthetic: "Our use of synthetic datasets is consistent with recent work on NIDS" — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Baselines: No-Update DAE, OWAD (NDSS 2023), INSOMNIA (supervised), and CADE (sample selection only) — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Results: AUC-ROC of 96.79% on IDS17, 98.17% on IDS18 and 94.76% on mKitsune, beating the best baseline by 2.23, 4.36 and 14.78 points. F1 rises 4.13% on IDS17 ("light change") and 72.6% on Kitsune ("heavy change"), labelling only 1% of incoming samples. Across hyperparameters on IDS17 the mean AUC-ROC was 96.19 (std 0.64) — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Untested (my reading of the text): no TPR at low FPR is reported (only AUC-ROC, F1 and accuracy), and there is no adaptive attacker such as poisoning through the 1% human-labelled update channel. "Unseen attack" is not the main variable; benign drift is.

#### P2. RAPIER: "Low-Quality Training Data Only? A Robust Framework for Detecting Encrypted Malicious Network Traffic" (NDSS 2024). First pages read.
- Authors: Yuqi Qing, Qilei Yin, Xinhao Deng, Yihao Chen, Zhuotao Liu, Kun Sun, Ke Xu, Jia Zhang, Qi Li (Tsinghua, Zhongguancun Lab, GMU). NDSS 2024, DOI 10.14722/ndss.2024.23081 — [NDSS paper page](https://www.ndss-symposium.org/ndss-paper/low-quality-training-data-only-a-robust-framework-for-detecting-encrypted-malicious-network-traffic/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2024-81-paper.pdf). An arXiv preprint dates from Sep 2023 ([arXiv 2309.04798](https://arxiv.org/abs/2309.04798)), so treat this as borderline 2023/2024.
- Problem and hypothesis: detect encrypted malicious traffic from "continuously evolving malware" when training data is small and noisily labelled. The hypothesis is that "normal data is tightly distributed in a certain area and the malicious data is scattered over the entire feature space", which RAPIER uses to augment training data and correct label noise — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2024-81-paper.pdf)
- Results: with 1,000 samples and 45% label noise, F1 is 0.770, 0.776 and 0.855 on two public datasets and one combined dataset (average gains of 352.6%, 284.3% and 214.9% over existing methods). On a real enterprise dataset the best F1 is 0.773 — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2024-81-paper.pdf)
- Not verified: the threat model, whether a leave-family-out split was used, compute cost, and stated limitations, because only the first pages were read.

#### P3. TIPSO-GAN: Malicious Network Traffic Detection Using a Novel Optimized GAN (NDSS 2026). Abstract, research questions and zero-day table read.
- Authors: Ernest Akpaku, Jinfu Chen (Jiangsu University), Joshua Ofoeda (UPS Ghana). NDSS 2026, DOI 10.14722/ndss.2026.243241 — [NDSS page](https://www.ndss-symposium.org/ndss-paper/tipso-gan-malicious-network-traffic-detection-using-a-novel-optimized-generative-adversarial-network/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- Mechanism: GAN training framed as particle swarm optimization, with adaptive inertia, diversity preservation and reinitialization of stagnant particles. It adds transfer learning and Temporal-Decaying Multi-Head Self-Attention, and its loss is reconstruction plus focal loss. The authors attribute zero-day capability to "unsupervised fine-tuning on normal traffic, where deviations from the learned [benign manifold]" are flagged — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- Datasets: CIC-IDS2018, CICAPT-IIoT2024 and CIC-DDoS2019. In-distribution F1 is 99.1, 98.9 and 98.7 respectively, and macro PR-AUC on CICAPT-IIoT2024 is 0.999 — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- Zero-day protocol: LOFO on CIC-IDS2018 with six held-out families (DoS, Brute Force, Botnet, Infiltration, Web Attacks, Heartbleed). Mean F1 across families is 92.3 ± 0.6 over five seeds. Cross-dataset train→test runs on the three corpora give 79–83 F1, with recall above 0.80. The authors also list mimicry, poisoning, black-box transfer and adaptive attacks as evaluated (Section VI-G) — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- Cost: 0.42 ms latency, about 2,400 flows/s, 2.1 GB footprint — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- Caveats (my reading): every dataset is a CIC lab corpus, and Heartbleed and Infiltration have very few flows in CIC-IDS2018, yet the reported per-family F1 is about 90–93. The base rate in the held-out folds, and TPR at fixed low FPR, were not found in the parts I read. I did not verify how the attacker in Section VI-G was parameterized.

#### P4. NetMasquerade: "A Hard-Label Black-Box Evasion Attack against ML-based Malicious Traffic Detection Systems" (NDSS 2026). Attack paper, included because it sets the adaptive-attacker bar.
- Authors: Zixuan Liu, Yi Zhao, Zhuotao Liu, Qi Li, Chuanpu Fu, Guangmeng Zhou, Ke Xu (Tsinghua, BIT, Zhongguancun Lab). DOI 10.14722/ndss.2026.230916 — [NDSS page](https://www.ndss-symposium.org/ndss-paper/a-hard-label-black-box-evasion-attack-against-ml-based-malicious-traffic-detection-systems/); [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf); [arXiv 2510.14906](https://arxiv.org/abs/2510.14906)
- Threat model: a strict hard-label black box, where the only feedback is "whether the target system drops malicious packets". Mechanism: a pretrained Traffic-BERT with a network-specialized tokenizer learns benign patterns, and RL then edits malicious packet sequences to mimic them with minimal changes — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- Targets: Whisper, FlowLens, NetBeacon, a vanilla model, CICFlowMeter+MLP, and Kitsune (gray-box for Kitsune). Over 80 attack scenarios the success rate is above 96.65%, and the attack "can evade the methods that are either empirically or certifiably robust" — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)

#### P5. TrafficFormer: An Efficient Pre-trained Model for Traffic Data (IEEE S&P 2025). Not read; secondary sources only.
- Authors: Guangmeng Zhou, Xiongwen Guo, Zhuotao Liu, et al. IEEE S&P 2025, pp. 1844–1860, DOI 10.1109/sp61157.2025.00102. This rests on a reference list in a Chinese journal and on the author's publication page. Some sources date it 2024 — [Zhuotao Liu publication page](https://liuzhuotao.github.io/publications/secure_networking_and_systems_infrastructure/encrypted_traffic_analysis/1-2-7); [Citing journal page](https://www.ejournal.org.cn/zh/article/doi/10.12263/DZXB.20251032/)
- Content: a fine-grained multi-classification pre-training task and a traffic augmentation method used in fine-tuning. It was evaluated on six traffic classification datasets, with up to 10% F1 improvement — [Author page](https://liuzhuotao.github.io/publications/secure_networking_and_systems_infrastructure/encrypted_traffic_analysis/1-2-7)
- **UNVERIFIED for zero-day relevance:** I found no evidence that TrafficFormer evaluates unseen-attack or open-set detection. It is a closed-set classification foundation model, and the full author list is incomplete ("et al.").

#### P6. netFound (arXiv, versions 2023–2026). Abstract only.
- Title in the current version: "netFound: Principled Design for Network Foundation Models". Authors: Sylee Beltiukov, Satyandra Guthula, Haarika Manda, Jaber Daneshamooz, Wenbo Guo, Walter Willinger, Arpit Gupta, Inder Monga. Versions v1 (Oct 2023), v3 (Oct 2024), v4 (Jan 2025) and v5 (May 2026). The arXiv page gives no venue — [arXiv 2310.17025](https://arxiv.org/abs/2310.17025)
- v5 claims: prior network foundation models (NFMs) "exploit dataset shortcuts, produce collapsed embedding spaces, and miss exogenous network conditions". The proposed design uses protocol-aware tokenization, operational-context embedding, burst-flow hierarchical attention and payload-free, IP-free inputs. Pretraining took 5,000 GPU hours on a billion-token-scale corpus, and the release includes a 4.2-billion-flow pretraining dataset. Exogenous-context F1 is 0.95, against below 0.62 for prior models — [arXiv 2310.17025](https://arxiv.org/abs/2310.17025)
- netFound's evaluation covers encrypted traffic classification, malware detection, intrusion detection and application fingerprinting, with ET-BERT, YaTC, NetMamba, TrafficFormer and Pcap-Encoder as baselines. No zero-day breakdown was found — [arXiv v5 HTML](https://arxiv.org/html/2310.17025v5)

#### P7. Demystifying Network Foundation Models (arXiv, Sep 2025). Abstract only.
- Authors: Sylee Beltiukov, Satyandra Guthula, Wenbo Guo, Walter Willinger, Arpit Gupta. Preprint with no venue listed — [arXiv 2509.23089](https://arxiv.org/abs/2509.23089)
- Findings across four NFMs and five datasets: "significant anisotropy", "inconsistent feature sensitivity", "inability to separate high-level context" and "payload dependency". Fixing these gave up to +0.35 F1 without architecture changes. The abstract does not address zero-day detection — [arXiv 2509.23089](https://arxiv.org/abs/2509.23089)

#### P8. Lens: A Knowledge-Guided Foundation Model for Network Traffic (arXiv, Feb 2024). Abstract only.
- Authors: Xiaochang Li, Chen Qian, Qineng Wang, Jiangtao Kong, Yuchen Wang, Ziyu Yao, Bo Ji, Long Cheng, Gang Zhou, Huajie Shao. arXiv v5, no venue listed — [arXiv 2402.03646](https://arxiv.org/abs/2402.03646)
- Relevance: the authors say prior traffic pretrained models "struggle to extend classification to new classes during fine-tuning due to the distribution shift". Lens recasts classification as closed-ended generation and claims it "extends to novel classes with significantly better performance". Average accuracy is 96.33%, and it beats baselines on 8 of 12 tasks. "Novel classes" here means new labelled classes added at fine-tuning, not zero-shot unseen-attack detection — [arXiv 2402.03646](https://arxiv.org/abs/2402.03646)

#### P9. NetVAD: Foundation-Model Representation Learning for Identifier-Free Unsupervised Intrusion Detection (arXiv May 2026; accepted at IEEE ISI). Abstract only.
- Authors: Darren Fürst, Patrick Levi, Sebastian Steindl — [arXiv 2606.01452](https://arxiv.org/abs/2606.01452)
- Mechanism: a variational autoencoder on frozen netFound-style NFM embeddings, trained only on benign traffic and identifier-free (no IPs), with "supervised calibration" of the threshold. Datasets are ToN-IoT and IoT-23. On ToN-IoT it reports 98% micro-F1 and 96% macro-F1 "at an operational false positive rate", and 99.6% F1 on Okiru. It reports results per attack class and admits that flow-based NFMs miss "single-packet reconnaissance events" — [arXiv 2606.01452](https://arxiv.org/abs/2606.01452)
- It notes that NFM research "primarily evaluates representations in supervised settings", leaving benign-only detection underexplored — [arXiv 2606.01452 PDF](https://arxiv.org/pdf/2606.01452)

#### P10. CLOSR: A Novel Contrastive Loss for Zero-Day Network Intrusion Detection (IEEE TNSM 2026). Abstract only.
- Authors: Jack Wilkie, Hanan Hindy, Craig Michie, Christos Tachtatzis, James Irvine, Robert Atkinson. Published in IEEE TNSM 2026 (IEEE doc 11340750), with code at github.com/jackwilkie/CLOSR — [arXiv 2601.09902](https://arxiv.org/abs/2601.09902)
- Hypothesis: learn the benign distribution using both benign and known-malicious samples, holding out the zero-day class, to avoid the "prohibitively high false positive rate" of benign-only anomaly detectors. On the Lycos2017 dataset (a relabelled CIC-IDS2017 derivative) AUROC improves by 0.000065 (known attacks) and 0.060883 (zero-day), and OpenAUC by 0.170883 in the open-set extension — [arXiv 2601.09902](https://arxiv.org/abs/2601.09902)
- Venue tier: TNSM is a networking journal, not a top-tier security venue.

#### P11. Self-Supervised Transformer-based Contrastive Learning for Intrusion Detection Systems (IFIP Networking 2025). Abstract only.
- Authors: Ippokratis Koukoulis, Ilias Syrigos, Thanasis Korakis — [arXiv 2505.08816](https://arxiv.org/abs/2505.08816)
- Method: packet-level augmentation plus a transformer encoder over raw packet sequences, rather than NetFlow features. Anomaly-detection AUC is up to 3% higher intra-dataset and up to 20% higher inter-dataset than NetFlow self-supervised baselines. Fine-tuning still works "even when lacking benign data from the target domain" — [arXiv 2505.08816](https://arxiv.org/abs/2505.08816)

#### P12. CND-IDS: Continual Novelty Detection for Intrusion Detection Systems (DAC 2025). Abstract only.
- Authors: Sean Fuhrman, Onat Gungor, Tajana Rosing. Accepted at the 62nd DAC — [arXiv 2502.14094](https://arxiv.org/abs/2502.14094)
- Mechanism: a continually updated learned feature extractor feeding a PCA-reconstruction novelty detector, with no attack labels. Claims are up to 6.1x F-score and 6.5x forward transfer over the state-of-the-art unsupervised continual-learning algorithm. A 2026 follow-up, ACORN-IDS, exists — [arXiv 2502.14094](https://arxiv.org/abs/2502.14094); [arXiv 2602.07291](https://arxiv.org/abs/2602.07291)

#### P13. Learning to Detect Cyber Attacks: Neural Anomaly Detection for Cybersecurity with Theoretical Insights (arXiv 2024). Abstract only.
- Authors: Tian-Yi Zhou, Matthew Lau, Jizhou Chen, Wenke Lee, Xiaoming Huo. No venue in the arXiv record — [arXiv 2409.08521](https://arxiv.org/abs/2409.08521)
- Mathematical basis: a classifier trained on normal samples plus synthetic anomalies is "proven to attain minimax excess risk" and "guaranteed to learn the boundary of the normal region". The paper claims it "significantly enhances the detection of difficult and previously unseen cyberattacks" in NIDS experiments — [arXiv 2409.08521](https://arxiv.org/abs/2409.08521)

#### P14. Zero-X: Blockchain-Enabled Open-Set Federated Learning for Zero-Day Attack Detection in IoV (arXiv Jul 2024). Abstract only.
- Authors: Abdelaziz Amara Korba, Abdelwahab Boualouache, Yacine Ghamri-Doudane — [arXiv 2407.02969](https://arxiv.org/abs/2407.02969)
- Method: DNN plus open-set recognition, trained with blockchain-coordinated federated learning between vehicles and SOCs. It is evaluated on "two recent network traffic datasets" — [arXiv 2407.02969](https://arxiv.org/abs/2407.02969)
- **Venue UNVERIFIED:** a search snippet linked a TIFS DOI (10.1109/TIFS.2025.3539100) to "Zero-X", but neither the arXiv record nor any primary page I saw confirms a TIFS publication. Secondary summaries also give conflicting numbers: 98.36% zero-day detection rate versus 77.32% average zero-day detection rate — [search aggregator summary](https://www.themoonlight.io/review/zero-x-a-blockchain-enabled-open-set-federated-learning-framework-for-zero-day-attack-detection-in-iov). Do not cite those numbers without checking the PDF.

#### P15. A Lightweight and Dynamic Open-Set Intrusion Detection for Industrial Internet of Things (IEEE TIFS 2025). Listing only.
- DOI 10.1109/TIFS.2025.3546849. Authors per the search listing: Yang, Tong, Jiang, Cheng (full names not verified). The design is open-set IDS for IIoT using an Extreme Value Machine (EVM) plus a DQN that solves a discrete-time Markov decision process for self-updating. It was evaluated on four datasets against four open-set IDS baselines — [ACM DL listing](https://dl.acm.org/doi/abs/10.1109/TIFS.2025.3546849); [ResearchGate](https://www.researchgate.net/publication/389445004_A_Lightweight_and_Dynamic_Open-Set_Intrusion_Detection_for_Industrial_Internet_of_Things)
- **Mostly UNVERIFIED:** the full author names, datasets, numbers and split protocol were not retrieved.

#### P16. Rules Refine the Riddle: Global Explanation for Deep Learning-Based Anomaly Detection in Security Applications (ACM CCS 2024). Search snippet and DBLP record only.
- Authors: Dongqi Han, Zhiliang Wang, Ruitao Feng, Minghui Jin, Wenqi Chen, Kai Wang, Su Wang, Jiahai Yang, Xingang Shi, Xia Yin, Yang Liu. CCS 2024, pp. 4509–4523 — [DBLP](https://dblp.org/rec/conf/ccs/HanWFJCWW0SYL24.html); [SCU portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368); [CCS 2024 accepted papers](https://www.sigsac.org/ccs/CCS2024/program/accepted-papers.html)
- GEAD extracts high-fidelity rules from deep-learning anomaly detectors, including NIDS. It is used to compare model knowledge with expert knowledge and to combine the two, and it was deployed in a real SCADA system — [SCU portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368)
- Relevance: this is about explainability and trust in benign-trained anomaly detection, not a new zero-day detector. Its quantitative results are UNVERIFIED.

#### P17. GeCo: Generalizable and Comprehensible Industrial Intrusion Detection (USENIX Security 2025). First pages read.
- Authors: Konrad Wolsing, Eric Wagner, Luisa Lux, Klaus Wehrle, Martin Henze (Fraunhofer FKIE, RWTH Aachen) — [USENIX PDF](https://www.usenix.org/system/files/usenixsecurity25-wolsing.pdf)
- GeCo learns comprehensible state-space models of benign process behaviour from historical industrial data, which makes it a benign-model anomaly detector for industrial control systems. The authors claim it beats state-of-the-art industrial IDSs and performs "on par with expert-derived rules". Note that it is process-data based, not packet or flow NIDS — [USENIX PDF](https://www.usenix.org/system/files/usenixsecurity25-wolsing.pdf)

#### Evaluation-critique and benchmark papers (2024–2026)
- **SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers** (IEEE S&P 2025, pp. 1825–1843). Authors: Nimesha Wickramasinghe, Arash Shaghaghi, Gene Tsudik, Sanjay Jha. "The majority of proposed encrypted traffic classifiers have mistakenly utilized unencrypted traffic due to the use of legacy datasets". 348 feature-occlusion experiments show that design oversights cause overfitting — [arXiv 2503.20093](https://arxiv.org/abs/2503.20093)
- **ACSAC 2025: "R+R: From Claims to Crashes: A Systematic Re-evaluation of Graph-Based Network Intrusion Detection Systems"**. Authors: Chenglong Wang, Pujia Zheng, Jiaping Gui, Cunqing Hua, and others (SJTU) — [ACSAC 2025 papers page](https://www.acsac.org/2025/program/papers/). It appears to be the published form of the arXiv preprint "Are We There Yet? Unraveling the State-of-the-Art Graph Network Intrusion Detection Systems" (same first four authors plus Wajih Ul Hassan). That preprint reports "significant performance discrepancies" and "difficulties in reproducing and replicating results, particularly concerning false positive rates and robustness against adversarial attacks". It evaluated three public datasets plus a new large-scale enterprise dataset — [arXiv 2503.20281](https://arxiv.org/abs/2503.20281). The link between the two is my INFERENCE from matching authors and topic, not verified.
- **"Zero Day Attacks: Novel Behaviour or Novel Vulnerability?"** (arXiv May 2026). Authors: Nnamdi Jibunoh, Sara Khanchi, Adetokunbo Makanju. A review of 20 years of documented zero-day incidents finds they "arise from the exploitation of undisclosed vulnerabilities rather than novel attack behavior". The authors warn that behaviour-based ML IDS "may overstate zero-day detection capabilities" — [arXiv 2605.03138](https://arxiv.org/abs/2605.03138)
- **"Evaluating ML-based Intrusion Detection Systems: The Illusion of Model Efficacy"** (arXiv Sep 2026). Authors: Spanos, Kantzavelou. It tests generalization to unseen attacks and proposes seven evaluation criteria — [arXiv 2609.02469](https://arxiv.org/abs/2609.02469)
- **USENIX Security 2025, provenance-based (host) IDS:** ORTHRUS argues that prior evaluations "fail to account for the significant class imbalance" and proposes a more conservative protocol. "Sometimes Simpler is Better" finds that state-of-the-art provenance IDS reporting near-perfect detection are "not viable for practical deployment". Both are host-level background, not NIDS — [USENIX Sec '25 sessions](https://www.usenix.org/conference/usenixsecurity25/technical-sessions); [ORTHRUS PDF](https://www.usenix.org/system/files/usenixsecurity25-jiang-baoxiang.pdf)

#### Adjacent top-venue work found in proceedings lists (titles verified, content not extracted)
- CCS 2024: "Detecting Tunneled Flooding Traffic via Deep Semantic Analysis of Packet Length Patterns" (Chuanpu Fu et al., Tsinghua) — [CCS 2024 accepted papers](https://www.sigsac.org/ccs/CCS2024/program/accepted-papers.html)
- NDSS 2026: "CoLD: Collaborative Label Denoising Framework for Network Intrusion Detection" (Shuo Yang, Xinran Zheng, Jinze Li, Jinfeng Xu, Edith C. H. Ngai). This is supervised label-noise work, not zero-day — [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s1950-paper.pdf)
- USENIX Security 2025: "CertTA: Certified Robustness Made Practical for Learning-Based Traffic Analysis" (Jinzhu Yan, Zhuotao Liu, Yuyang Xie, Shiyu Liang, Lin Liu, Ke Xu). It provides multi-modal randomized smoothing against padding, delay and dummy-packet insertion — [USENIX PDF](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf). NetMasquerade (P4) claims to evade "certifiably robust" methods — [NDSS 2026 PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- NeurIPS 2025: GraphIDS, a self-supervised masked-autoencoder graph NIDS trained on normal flows. It reports up to 99.98% PR-AUC and 99.61% macro-F1 on NetFlow benchmarks — [arXiv 2509.16625](https://arxiv.org/abs/2509.16625)

### Inferences
- Among the 2024–2026 proceedings lists I scanned (NDSS 2024/2025/2026, USENIX Sec 2024/2025, CCS 2024, ACSAC 2025), I found no paper whose primary contribution is a zero-day NIDS detector with leave-attack-family-out evaluation, apart from TIPSO-GAN (NDSS 2026). Top-tier security venues have mostly published adjacent work: drift adaptation, label noise, explanation, robustness and evaluation critiques. This leaves room for a USENIX 2027 paper.
- The Tsinghua group (Zhuotao Liu, Qi Li, Ke Xu) appears across RAPIER, TrafficFormer, CertTA and NetMasquerade, which makes it a central cluster for ML traffic-detection work at top venues.
- In the foundation-model line (netFound, Lens, TrafficFormer), "new classes" means labelled fine-tuning, not detection of unseen attacks. Only NetVAD (a lower-tier venue) evaluates an NFM backbone as a benign-only zero-day detector.

### Gaps
- The CCS 2025, USENIX Security 2026, IEEE S&P 2024/2026, EuroS&P, RAID 2025, AsiaCCS and ACSAC 2024 programs were not scanned. The CCS 2025 page returned no parsable titles, the RAID 2024 page failed, and the ACSAC 2024 URL returned 404. NIDS zero-day papers there may be missing.
- IEEE TDSC: no 2024–2026 zero-day NIDS paper was confirmed. TIFS: only P15, and only as a listing.
- ET-BERT follow-ups and YaTC (AAAI 2023) are pre-2024 background. NetMamba (reportedly ICNP 2024) was not verified in this session.
- Full texts were not read for P5–P16, so threat models, compute, stated limitations and operating points are unavailable for those papers.

## Q2. What does each paper demonstrate, versus claim, versus leave untested?

### Takeaway
Demonstrated results are mostly AUC or F1 on lab CIC/Kitsune/ToN-IoT corpora. Claims of generalization to "zero-day" in the wild, deployment readiness and robustness go beyond what the evaluations show. Adaptive attackers, realistic base rates and TPR at very low FPR are largely untested, except in the attack paper NetMasquerade, which shows these detectors are evadable.

### Cited Findings
- Mateen **demonstrates** better AUC and F1 under benign drift with 1% labelling on IDS17, IDS18 and Kitsune variants. It **acknowledges** synthetic datasets. It **leaves untested** human-label poisoning, low-FPR operating points and real enterprise traffic — [RAID 2024 PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- TIPSO-GAN **demonstrates** LOFO mean F1 of 92.3 on CIC-IDS2018 and 79–83 F1 cross-dataset. It **claims** robustness to adaptive, mimicry and poisoning attacks (Section VI-G, not verified by me). All data is CIC-generated, so the cross-dataset tests share a generator lineage — [NDSS 2026 PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- NetMasquerade **demonstrates** a success rate above 96.65% against six detectors, including Kitsune (benign-modelling, anomaly-based) and certifiably robust methods, under a hard-label black box — [NDSS 2026 PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf)
- netFound **claims** principled NFM design and top benchmark rank, but the abstract shows no unseen-attack evaluation — [arXiv 2310.17025](https://arxiv.org/abs/2310.17025). The same group's "Demystifying" paper **demonstrates** shortcut and payload dependence in four NFMs — [arXiv 2509.23089](https://arxiv.org/abs/2509.23089)
- NetVAD **demonstrates** per-class transparency and **acknowledges** a blind spot: flow-based NFMs miss single-packet reconnaissance. Its "supervised calibration" of the threshold uses attack labels, which partially undermines "unsupervised" zero-day framing — [arXiv 2606.01452](https://arxiv.org/abs/2606.01452)
- CLOSR's zero-day AUROC gain is +0.06, and its known-attack gain of +0.000065 is within noise. It was tested on a single dataset (Lycos2017) — [arXiv 2601.09902](https://arxiv.org/abs/2601.09902)
- Zhou et al. **demonstrate** a theoretical guarantee (minimax excess risk, learning the normal-region boundary). Its NIDS claim of "previously unseen cyberattacks" lacks dataset and split details in the abstract — [arXiv 2409.08521](https://arxiv.org/abs/2409.08521)

### Inferences
- The most common unacknowledged gap is the adaptive attacker. Benign-manifold detectors (DAE, VAE, GAN, contrastive) are exactly what NetMasquerade-style benign mimicry targets, yet none of the detection papers I read besides TIPSO-GAN claim to test it.
- "Zero-day" is often equated with "attack class held out from a lab dataset". The 2026 incident review argues real zero-days are new vulnerabilities, not new behaviour, so held-out-family results may not transfer to real zero-days — [arXiv 2605.03138](https://arxiv.org/abs/2605.03138)

### Gaps
- Without full texts for most journal and arXiv papers, I could not check for leakage (for example IP or port identifiers, or flow-ID overlap across splits) or for random versus temporal splitting.

## Q3. Which evaluation protocols are used, and where are they weak?

### Takeaway
Three protocols dominate: (a) benign-only training with all attacks unseen at test time (Mateen, NetVAD, GraphIDS, CND-IDS); (b) LOFO or held-out-class splits (TIPSO-GAN, CLOSR, Zero-X, open-set IDS); (c) cross-dataset transfer (TIPSO-GAN, the IFIP 2025 contrastive transformer). Common weaknesses are reliance on legacy synthetic CIC/Kitsune/ToN-IoT corpora, AUC or F1 at test-set base rates rather than TPR at low FPR, threshold calibration with attack labels, few or no temporal splits, shortcut features in foundation models, and poor reproducibility.

### Cited Findings
- Mateen uses time-aware splits but has to fall back to file order for Kitsune, which has no timestamps, and it builds synthetic shift variants — [RAID 2024 PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- TIPSO-GAN uses LOFO over six CIC-IDS2018 families plus six cross-dataset pairs, five seeds each — [NDSS 2026 PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f3241-paper.pdf)
- The S&P 2025 SoK finds that most "encrypted" classifiers were trained on unencrypted legacy data, and that design choices cause overfitting — [arXiv 2503.20093](https://arxiv.org/abs/2503.20093)
- NFMs show payload dependence and shortcut use — [arXiv 2509.23089](https://arxiv.org/abs/2509.23089); [arXiv 2310.17025](https://arxiv.org/abs/2310.17025)
- Graph NIDS results are hard to reproduce, especially false positive rates and adversarial robustness — [arXiv 2503.20281](https://arxiv.org/abs/2503.20281)
- In host IDS, ORTHRUS criticizes evaluations that ignore class imbalance — [USENIX Sec '25 sessions](https://www.usenix.org/conference/usenixsecurity25/technical-sessions)
- The Dos and Don'ts taxonomy (USENIX Sec 2022, background only) lists sampling bias and inappropriate baselines, with NIDS as a running example — [USENIX 2022 PDF](https://www.usenix.org/system/files/sec22summer_arp.pdf)
- Benign-only anomaly detectors come "at the expense of a prohibitively high false positive rate", according to the CLOSR authors — [arXiv 2601.09902](https://arxiv.org/abs/2601.09902)

### Inferences
- A defensible protocol for USENIX 2027 would combine LOFO with temporal ordering and cross-network (not just cross-CIC) transfer. It should report TPR at FPR ≤ 1e-3/1e-4 under realistic base rates, keep the threshold calibrated on benign data only, and include a NetMasquerade-style hard-label adaptive attacker.

### Gaps
- I did not find a 2024–2026 top-venue paper that reports TPR at a fixed very low FPR for zero-day NIDS. This may reflect the limited full-text access rather than true absence.

## Q4. What open problems recur across papers?

### Takeaway
The recurring problems are: separating benign drift from novel attacks; false positive rates of benign-only detectors; evasion by benign mimicry; foundation-model shortcut learning and lack of unseen-attack evaluation; label scarcity and noise; reliance on stale lab datasets; and a conceptual mismatch between "novel behaviour" detection and real zero-day exploitation.

### Cited Findings
- Benign drift versus attack: Mateen — [RAID 2024 PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf); CND-IDS — [arXiv 2502.14094](https://arxiv.org/abs/2502.14094)
- False positives of anomaly detectors: [arXiv 2601.09902](https://arxiv.org/abs/2601.09902); NetVAD needs supervised calibration to reach an "operational false positive rate" — [arXiv 2606.01452](https://arxiv.org/abs/2606.01452)
- Evasion by mimicking benign traffic, including against certified defences: [NDSS 2026 NetMasquerade](https://www.ndss-symposium.org/wp-content/uploads/2026-s916-paper.pdf); certified robustness remains partial: [CertTA USENIX Sec 2025](https://www.usenix.org/system/files/usenixsecurity25-yan-jinzhu.pdf)
- NFM shortcuts, and the lack of benign-only or zero-day evaluation of NFMs: [arXiv 2509.23089](https://arxiv.org/abs/2509.23089); [arXiv 2606.01452](https://arxiv.org/pdf/2606.01452)
- Low-quality or noisy labels: [RAPIER NDSS 2024](https://www.ndss-symposium.org/wp-content/uploads/2024-81-paper.pdf); [CoLD NDSS 2026](https://www.ndss-symposium.org/wp-content/uploads/2026-s1950-paper.pdf)
- Single-packet or low-volume attacks missed by flow-level models: [arXiv 2606.01452](https://arxiv.org/abs/2606.01452)
- Mismatch with how real zero-days work: [arXiv 2605.03138](https://arxiv.org/abs/2605.03138)
- Explainability of anomaly alarms for operators: [CCS 2024 GEAD via SCU portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368); [GeCo USENIX Sec 2025](https://www.usenix.org/system/files/usenixsecurity25-wolsing.pdf)

### Inferences
- The clearest open slot is a benign-only (or benign plus known-attack) NFM-based detector evaluated with LOFO, temporal and cross-network splits at low FPR, and stress-tested against hard-label mimicry. No paper I found does all of these together.

### Gaps
- No verified 2024–2026 work at a top security venue evaluates few-shot or LLM-based NIDS for unseen attacks. Those I found are arXiv or MDPI and low-tier, for example [arXiv 2605.17530](https://arxiv.org/abs/2605.17530) (few-shot triplet mining, MDPI Applied Sciences 2026) and [arXiv 2602.00219](https://arxiv.org/abs/2602.00219) (zero-shot federated LLM IDS), and were not extracted.
