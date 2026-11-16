# False-Alarm Control, Calibration, Uncertainty, Conformal Guarantees, Explainability and Automated Response for ML Security Detectors (2024–2026)

Scope note: about 17 tool calls; I checked primary pages (arXiv abstract pages, the ACM/SCU portal, the Lancaster eprint, the NDSS PDF and the Frontiers full text). Most entries rest on abstract-level extraction. Where a field (threat model, datasets, numbers) was not on a page I read, it is marked **NOT VERIFIED**. I did not read any full PDF except the first pages of the NDSS 2025 paper. Today is 2026-11-16, so arXiv IDs 26xx.xxxxx are real 2026 identifiers. Rows marked "background" are pre-2024.

## Q1. Which 2024–2026 papers cover these topics (paper-by-paper extraction)?

### Takeaway
At top security venues (CCS, NDSS, TDSC), 2024–2026 work on these topics is mostly about **global or rule-based explanation of anomaly detectors** (GEAD at CCS'24, Ano2Rule in TDSC'26) and **drift handling for malware** (DREAM at CCS'25, Li et al. at NDSS'25). Work on **conformal FPR control for NIDS**, **calibration of NIDS** and **LLM triage or containment** sits almost entirely in arXiv preprints, workshops and journals outside the core security venues. That makes the field thin, and a USENIX'27 contribution there would face little prior work.

### Cited Findings

**A. Explainability for security anomaly detection / NIDS**

1. **"Rules Refine the Riddle: Global Explanation for Deep Learning-Based Anomaly Detection in Security Applications" (GEAD)**. Dongqi Han, Zhiliang Wang, Ruitao Feng, Minghui Jin, Wenqi Chen, Kai Wang, Su Wang, Jiahai Yang, Xingang Shi, Xia Yin, Yang Liu. ACM CCS 2024, pp. 4509–4523, DOI 10.1145/3658644.3670375 — [SCU research portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368); [ACM DL](https://dl.acm.org/doi/pdf/10.1145/3658644.3670375)
   - Problem: most explanation methods are local (one sample at a time), and explainers designed for supervised models do not carry over to anomaly detection — [SCU portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368)
   - Mechanism: extracts high-fidelity global rules from a DL anomaly detector. Applied to NIDS and system-log anomaly detection, with three uses: comparing model knowledge against expert knowledge, finding discrepancies between models, and combining model and expert knowledge. Includes a real-world SCADA deployment — [SCU portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368)
   - Fidelity numbers, datasets, baselines and threat model: **NOT VERIFIED** (the abstract has no numbers).
   - Related work by the same line: NeurIPS 2023 "Interpreting Unsupervised Anomaly Detection in Security via Rule Extraction" (background) — [NeurIPS](https://papers.neurips.cc/paper_files/paper/2023/hash/c43b987f23fd5ea840df2b2be426315c-Abstract-Conference.html)

2. **"Ano2Rule: Rule-Based Global Interpretation for Unsupervised Anomaly Detection in Security"**. Ruoyu Li, Yu Zhang, Qing Li, Nengwu Wu, Yong Jiang, Weizhi Meng, Laizhong Cui. IEEE TDSC vol. 23, no. 3, pp. 6685–6702, 2026 — [Lancaster eprints](https://eprints.lancs.ac.uk/id/eprint/236142)
   - Mechanism: "distribution decomposition rules" come from an unsupervised clustering tree that takes model predictions into account. "Boundary inference rules" come from a Compositional Boundary Exploration algorithm that approximates the decision boundary in each part. Together the rules serve as a human-readable surrogate that can be deployed online — [Lancaster eprints](https://eprints.lancs.ac.uk/id/eprint/236142)
   - Evaluated on NIDS and IoT security datasets, with "high fidelity" claimed. The fidelity figures are **NOT VERIFIED** (not in the abstract) — [Lancaster eprints](https://eprints.lancs.ac.uk/id/eprint/236142)

3. **"A Self-Explainable Deep Architecture for Security Applications" (XSec)**. Ananth Shreekumar, Jyun-Jhu Syu, Muslum Ozgur Ozmen, Dongyan Xu, Z. Berkay Celik. arXiv:2608.05552, Aug 2026, no venue listed — [arXiv](https://arxiv.org/abs/2608.05552)
   - Hypothesis: post-hoc explainers lose faithfulness through local-approximation error, are unstable because they rely on randomness, and cost too much for real-time use — [arXiv](https://arxiv.org/abs/2608.05552)
   - Mechanism: during training, a mask-based method extracts informative sub-features and the model learns per-class prototypes. At test time a similarity layer produces explanations as part of inference. For a fixed model and input the explanations are deterministic — [arXiv](https://arxiv.org/abs/2608.05552)
   - Results: 97.33% average accuracy across five security scenarios, with "substantially lower" explanation latency than post-hoc methods. The names of the scenarios and datasets are **NOT VERIFIED** — [arXiv](https://arxiv.org/abs/2608.05552)

4. Background (2023): **xNIDS** (Wei et al., USENIX Security 2023) builds local explanations of DL-NIDS decisions to drive active intrusion response. Its fidelity is measured by how fast detection accuracy drops when top-ranked features are replaced. The authors report beating LIME/SHAP/LEMNA on fidelity, sparsity, completeness and stability. Global explanation is left as future work — [USENIX](https://usenix.org/conference/usenixsecurity23/presentation/wei)

**B. Calibration / uncertainty for NIDS**

5. **Talpini, J., Sartori, F., & Savi, M. "Enhancing trustworthiness in ML-based network intrusion detection with uncertainty quantification."** Journal of Reliable Intelligent Environments 10, 501–520 (2024); arXiv 2310.10655 — [Frontiers review references](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full); [arXiv PDF](https://arxiv.org/pdf/2310.10655)
   - Mechanism: a Bayesian NN with uncertainty recalibrated so that inputs far from the training data get high uncertainty, which supports OoD (unknown-attack) detection — [search snippet of arXiv 2310.10655](https://arxiv.org/pdf/2310.10655)
   - Result: the review cites AUROC ≈0.92 on ToN-IoT for uncertainty-based OoD/open-set detection and rates the evidence as higher confidence — [Frontiers](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full)
   - Venue and metadata were taken from the review's reference list. I did not open the publisher page.

6. **Pal, B., Islam, M. S., & Liew, A. W.-C. "Calibrated uncertainty estimation for trustworthy deep IoT attack detection."** IEEE TDSC 22, 7571–7584 (2025). It reports 98.4% accuracy on IoT-23, a temperature-scaling T=1.39, and 96.42% retention at the top-F1 operating point — [Frontiers review](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full). This is secondary-source only. Authors and metadata are **NOT VERIFIED** on IEEE Xplore.

7. Other 2024–2025 uncertainty-for-NIDS papers, each from the review only and all **NOT VERIFIED** on primary pages — [Frontiers](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full):
   - Yang, Qiao & Lee (2024, Computers & Security 144, 103909): Bayesian autoencoder uncertainty, AUC-rejection ≈0.986 on UNSW-NB15 and ≈0.846 on CIC-IDS2017.
   - Vij, Tran & Tran (2024, IEEE LCN): near-zero error on accepted samples at about 5–7% rejection, sensitive to the threshold.
   - Medjadba, Drid & Rahouti (2025, Computer Networks 269): 99.93% on InSDN. The review flags leakage because normalization was done before splitting.
   - Xin & Xu (2025): lower ECE, but the source of the calibration data is inconsistent.

8. **"Deployment-oriented evaluation of deep learning network intrusion detection systems"**. Kai Liang Lew, Kok Swee Sim, Hao Xian Cheong. Frontiers in Communications and Networks vol. 7, 2026. A mini-review of 29 empirical works from 2024–2026 — [Frontiers](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full)
   - It found **no study that jointly evaluated cross-dataset shift, withheld unknown attacks and reliability under a single protocol**. It notes that temperature scaling fit on held-out validation data becomes unreliable under shift or new attacks. It recommends ECE, Brier score and risk–coverage curves on shifted and unknown-attack traffic — [Frontiers](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full)

**C. Conformal prediction / selective prediction / drift**

9. **"Robust Conformal Intrusion Detection via Traffic-Aware Calibration and Attack-Orbit Invariance"**. Zhenpeng Li. arXiv:2609.19241 (the page says submitted 22 Jul 2026, which does not match the 2609 ID); submitted to IEEE TDSC — [arXiv](https://arxiv.org/abs/2609.19241)
   - Problem: fine-tuned LLM-based NIDS output point predictions without validity guarantees. Conformal thresholds calibrated on clean traffic fail once an adversary changes controllable features, and the paper shows this on three IDS benchmarks — [arXiv](https://arxiv.org/abs/2609.19241)
   - Threat models and mechanisms:
     - Non-adaptive attacker: "traffic-aware" conformal calibration draws calibration data from the attacker's perturbation mechanism. This restores coverage when that mechanism is known and can be sampled.
     - Adaptive, score-querying attacker: the scored representation excludes attacker-controllable features and their deterministic descendants. The paper claims an *exact, pathwise* coverage guarantee — [arXiv](https://arxiv.org/abs/2609.19241)
   - Cost: clean accuracy drops by 7–14 points. The restricted representation stayed unchanged under every attack the authors evaluated, across three fine-tuned LM architectures. The benchmark names are **NOT VERIFIED** — [arXiv](https://arxiv.org/abs/2609.19241)

10. **"FIRCE: A Framework for Intrusion Response and Conformal Evaluation"**. Seth Barrett, Lin Li, Gokila Dorai, Swarnamugi Rajaganapathy. arXiv:2605.01962, accepted to IEEE SmartNets 2026 — [arXiv](https://arxiv.org/abs/2605.01962)
    - Mechanism: adds conformal evaluators (Inductive, Cross, Approximate Transductive, and a new Approximate Cross-Conformal Evaluator) to a supervised IDS to quantify uncertainty and detect drift. Adaptive chunking sets evaluation granularity according to stream volatility, and detected drift triggers retraining — [arXiv](https://arxiv.org/abs/2605.01962)
    - Data: a custom IoT testbed with 10 commercial devices, plus CICIDS2018 and UNSW-NB15. The abstract states **no formal coverage or FPR guarantee** — [arXiv](https://arxiv.org/abs/2605.01962)

11. **ConFID: "A conformal one-class framework for unsupervised zero-day intrusion detection in IoT networks"** (ScienceDirect journal, Internet of Things, PII S2542660526002088, 2026). According to the search snippet, it adds a conformal module to an unsupervised detector to control FPR at a user-chosen level and claims to be among the first conformal methods for flow-based one-class NIDS. The publisher page returned 403, so **authors, datasets and numbers are NOT VERIFIED** — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S2542660526002088)

12. **C-PP-COAD, "Online Conformal Anomaly Detection with Prediction-Powered Data Acquisition"** (arXiv:2505.01783). According to the search snippet, it controls the online FDR rather than the FPR and was tested on a 5G NIDS dataset. **Authors and venue NOT VERIFIED** — [arXiv](https://arxiv.org/html/2505.01783)

13. **"On the Reliability and Stability of Selective Methods in Malware Classification Tasks" (Aurora)**. Alexander Herzog, Aliai Eusebi, Lorenzo Cavallaro. arXiv:2505.22843, v4 Oct 2026, no venue listed — [arXiv](https://arxiv.org/abs/2505.22843)
    - Hypothesis: drift-adaptive malware classifiers that report good baseline metrics may have confidence that does not track their errors and may be unstable over time.
    - Mechanism: the Aurora framework audits the reliability of a model's confidence profile and adds metrics for stability across evaluation periods.
    - Finding: state-of-the-art frameworks turn out fragile across datasets with different drift severity. Unreliable confidence wastes the active-learning budget and lets error-prone samples through selective classification. No numbers in the abstract — [arXiv](https://arxiv.org/abs/2505.22843)

14. **"Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification" (DREAM)**. Yiling He, Junchi Lei, Zhan Qin, Kui Ren, Chun Chen. ACM CCS 2025, DOI 10.1145/3719027.3744792 — [arXiv](https://arxiv.org/abs/2405.04095)
    - Mechanism: embeds malware explanation concepts in the latent space of a contrastive autoencoder and constrains reconstruction with the classifier's predictions. It detects drift without the training data and includes a behavior-based drift explainer.
    - Result: when updating Drebin, it reaches the same accuracy with **76.6% fewer newly labeled samples** than the best prior method — [arXiv](https://arxiv.org/abs/2405.04095)

15. **"Revisiting Concept Drift in Windows Malware Detection: Adaptation to Real Drifted Malware with Minimal Samples"**. Adrian Shuai Li, Arun Iyengar, Ashish Kundu, Elisa Bertino. NDSS 2025, DOI 10.14722/ndss.2025.240830 — [NDSS PDF](https://www.ndss-symposium.org/wp-content/uploads/2025-830-paper.pdf)
    - Mechanism: a GNN on control-flow graphs with adversarial domain adaptation learns drift-invariant features. Compared against cold-start and warm-start active-learning retraining and against vision domain-adaptation methods. Evaluated on public benchmarks and on 2024 real-world daily malware feeds — [NDSS PDF](https://www.ndss-symposium.org/wp-content/uploads/2025-830-paper.pdf)
    - The authors argue that shortcut features (for example packer-induced db/dw/dd directives) cause false positives on packed benign software — [NDSS PDF](https://www.ndss-symposium.org/wp-content/uploads/2025-830-paper.pdf)
    - Quantitative results: **NOT VERIFIED** (only pages 1–2 were read). The paper offers no calibration or conformal guarantee.

16. Background: Transcend (USENIX Sec 2017) and TRANSCENDENT (IEEE S&P 2022, inductive and cross-conformal evaluators) reject drifting samples with conformal evaluators. Chen et al. (USENIX Sec 2023) use similarity-based uncertainty for continuous learning in Android malware detection — [Continuous Learning, USENIX'23](https://www.usenix.org/system/files/usenixsecurity23-chen-yizheng.pdf); [search summary](https://arxiv.org/pdf/2505.22843)

**D. LLM triage and automated response**

17. **"CORTEX: Collaborative LLM Agents for High-Stakes Alert Triage"**. Bowen Wei, Yuan Shen Tay, Howard Liu, Jinhao Pan, Kun Luo, Ziwei Zhu, Chris Jordan. arXiv:2510.00311 (cs.CL), Sep 2025, no venue listed — [arXiv](https://arxiv.org/abs/2510.00311)
    - Mechanism: a behavior-analysis agent, evidence-gathering agents that query external systems, and a reasoning agent that produces an auditable decision. The authors release a dataset of fine-grained production SOC investigations.
    - The abstract claims "substantially reduces false positives" relative to single-agent LLMs but gives **no numbers** — [arXiv](https://arxiv.org/abs/2510.00311)

18. **"From Investigation Failures to Reliable SOC Agents: Understanding and Improving LLM-Based Alert Triage" (ALERT-BENCH / AIDA)**. Saimon Amanuel Tsegai, Alex Kantchelian, Danfeng (Daphne) Yao, Peng Gao. arXiv:2610.10608, Oct 2026 — [arXiv](https://arxiv.org/abs/2610.10608)
    - Protocol: ALERT-BENCH replays enterprise telemetry through a live SIEM, covering 1,247 alerts from one multi-stage attack scenario. It compares five agent strategies: single-pass, iterative retrieval, sampling, self-review and explicit verification.
    - Finding: every strategy missed **at least 40.4%** of attack alerts. Attack alerts were more likely to be dismissed when searches returned no records. Same-context self-review had *negative* net correction — [arXiv](https://arxiv.org/abs/2610.10608)
    - AIDA mechanism: requires an explicit proposal before an independent challenge in a separate context, keeps an append-only Investigation Ledger, and uses a Judge.
    - AIDA results: F1 0.958 versus 0.371–0.744 for the five strategies. FNR falls from 40.4% to 3.1%, and 18.4% of alerts are escalated to analysts — [arXiv](https://arxiv.org/abs/2610.10608)
    - A search snippet said self-refinement raised false positives from 8 to 65. That number does not appear in the abstract and is **NOT VERIFIED**.

19. **"OpenSec: Measuring Incident Response Agent Calibration Under Adversarial Evidence"**. Jarrod Barnes. arXiv:2601.21083, Jan 2026, 7 pages — [arXiv](https://arxiv.org/abs/2601.21083)
    - Protocol: a dual-control RL environment with prompt-injection scenarios. Metrics are time-to-first-containment (TTFC), evidence-gated action rate (EGAR), blast radius and per-tier injection violation rate. Four frontier models were each run on 40 episodes.
    - Results:
      - GPT-5.2 contained in 100% of episodes with an **82.5% false-positive rate**, usually acting at step 4.
      - Claude Sonnet 4.5 contained in 62.5% of episodes with 45% FP and TTFC 10.6.
      - All models identified the true threat when they acted, so the authors say "the calibration gap is in restraint rather than detection" — [arXiv](https://arxiv.org/abs/2601.21083)
    - Conflict: a search-engine summary claimed "90–97% FP rates" for three of four models. The arXiv abstract (v3) gives 82.5% for GPT-5.2. Use the abstract — [arXiv](https://arxiv.org/abs/2601.21083)

20. Other leads, not extracted:
    - SOCpilot, verifying policy compliance for LLM-assisted incident response — [arXiv 2605.05501](https://arxiv.org/pdf/2605.05501)
    - "LLMs, You Can Evaluate It!", on SOC report evaluation — [arXiv 2601.03013](https://arxiv.org/pdf/2601.03013)
    - An LLM pipeline that reduces IDS false positives (Springer 2025) — [Springer](https://link.springer.com/chapter/10.1007/978-3-031-87772-8_37)
    - A survey of AI alert screening and alert fatigue — [arXiv 2605.08316](https://arxiv.org/pdf/2605.08316)
    - Background: Alahmadi, Axon & Martinovic, "99% false positives", USENIX Security 2022 (search summary only).

### Inferences
- Top-tier security venues in 2024–2026 have **rule/global XAI** (CCS'24, TDSC'26) and **malware drift adaptation** (CCS'25, NDSS'25). I found no top-four security venue paper whose main contribution is conformal FPR control for NIDS. Those papers are arXiv-only, at small venues or in non-security journals.
- The drift literature, at least in its abstracts, optimizes labeling efficiency and accuracy rather than a controlled FPR. FPR at a fixed operating point is seldom the headline metric.

### Gaps
- The full-text quantitative tables (fidelity, FPR at fixed TPR, datasets, baselines, compute cost) for GEAD, Ano2Rule, DREAM, NDSS'25 Li et al. and XSec were not read.
- ConFID and C-PP-COAD could not be verified on primary pages. Their authors are unknown.
- I did not search the USENIX Security 2024/2025/2026, S&P 2025/2026, RAID, ACSAC, AsiaCCS or EuroS&P proceedings directly. Some papers there may be missing, for example in provenance-based IDS false-alarm reduction or alert triage.

## Q2. Does any work give FPR guarantees that hold under temporal drift or adversarial manipulation? What assumptions break?

### Takeaway
No verified 2024–2026 security paper gives a distribution-free FPR guarantee that holds under arbitrary temporal drift. The closest are:
- Li (arXiv 2026): coverage under adversarial feature manipulation, bought by **excluding attacker-controllable features**. This assumes the controllable features and their causal descendants can be identified, and it costs 7–14 points of clean accuracy.
- Online conformal methods such as C-PP-COAD: long-run, average-type FDR control.

Standard split or inductive conformal guarantees rest on **exchangeability**, and drift and adaptive attackers both break it.

### Cited Findings
- Clean-traffic conformal thresholds lose coverage under adversarial feature modification on three IDS benchmarks. Matched "traffic-aware" calibration restores coverage only when the perturbation mechanism is known and can be sampled, and an adaptive attacker can still degrade it. Feature exclusion gives an exact pathwise guarantee at a 7–14 point cost in clean accuracy — [arXiv 2609.19241](https://arxiv.org/abs/2609.19241)
- In general online conformal theory, drift breaks the exchangeability that full conformal coverage depends on. DriftOCP adds drift detection to recover adaptivity (not a security paper) — [arXiv 2602.16537](https://arxiv.org/pdf/2602.16537)
- C-PP-COAD maintains online FDR control on a 5G NIDS dataset (search summary) — [arXiv 2505.01783](https://arxiv.org/html/2505.01783)
- FIRCE uses conformal evaluators for drift detection, not for a stated FPR bound — [arXiv 2605.01962](https://arxiv.org/abs/2605.01962)
- ConFID guarantees FPR at a user-chosen level (snippet). The guarantee presumably assumes exchangeable benign calibration and test traffic, but **the assumptions are NOT VERIFIED** — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S2542660526002088)
- Outside security, a 2026 Reliability Engineering & System Safety paper guarantees false-alarm rates for industrial CPS anomaly detectors via conformal prediction. An ICLR 2026 submission makes the anomaly score directly interpretable as a false-alarm p-value — [RESS/ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0951832026002334); [arXiv 2604.20122](https://arxiv.org/abs/2604.20122)
- Selective or abstaining malware classifiers show unreliable and unstable confidence under drift — [arXiv 2505.22843](https://arxiv.org/abs/2505.22843)
- Temperature scaling fit on validation data degrades under shift or new attacks — [Frontiers](https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2026.1863367/full)
- Background: weighted conformal (Tibshirani et al. 2019, covariate shift with known likelihood ratio) and adaptive conformal inference (Gibbs & Candès 2021, long-run average coverage under arbitrary shift) are the standard tools. I found **no verified 2024–2026 top-venue NIDS paper applying weighted or adaptive conformal**. This background is not re-verified here.

### Inferences
- Which assumptions break, and how:
  1. **Exchangeability between calibration and deployment benign traffic** breaks under temporal drift. Weighted conformal would need density ratios, which are hard to estimate for high-dimensional flows. ACI gives only time-averaged FPR, and that can hide bursts of false alarms.
  2. **A score function that does not depend on attacker-controlled inputs** breaks under evasion and poisoning. Li's restriction trades away detection power.
  3. **FPR control alone says nothing about TPR.** Under shift a valid FPR bound can coexist with collapsed detection, so papers need to report TPR at the controlled FPR together with alerts/day at realistic base rates.
- An open opportunity: label-shift- or attack-prior-aware conformal FPR control evaluated over temporally split NIDS data. Use conditional or Mondrian-by-time calibration and report per-window FPR violations rather than only the marginal rate.

### Gaps
- I could not confirm whether ConFID or C-PP-COAD evaluate on temporally split data, or whether their guarantees survive the shift.
- I found no work that bounds FPR under *poisoning* of the calibration set.

## Q3. Evidence on analyst-facing usefulness of explanations and on automated-response safety

### Takeaway
Evidence that explanations help analysts is **thin, small-sample and mostly non-peer-reviewed**. Top-venue XAI papers (GEAD, Ano2Rule, XSec) measure fidelity, stability and latency, not analyst outcomes. On automated response, the 2026 preprints agree that LLM agents **over-contain**:
- OpenSec: GPT-5.2 had an 82.5% false-positive rate on containment.
- ALERT-BENCH: at least 40.4% of attack alerts were missed under the standard strategies.

Structured adversarial verification (AIDA) brings FNR down to 3.1% on one scenario.

### Cited Findings
- SOC analyst / XAI user studies (2025–2026, mostly preprints or minor venues). From a search summary; details not checked on primary pages:
  - A 64-participant controlled study (32 students, 32 SOC analysts) of SHAP+LIME+counterfactual interfaces (Ex-SOC).
  - A 24-participant within-subjects copilot study (12 analysts), arXiv 2601.22653, on counterfactual and natural-language explanations.
  - An analyst survey finding low adoption of XAI tools and a preference for context-aware alerts that include historical attack information.
  - A TalTech 2025 study finding LIME/SHAP/IG/DeepLIFT top features largely matched what analysts considered important — [arXiv 2601.22653](https://arxiv.org/pdf/2601.22653); [SciTePress 2025](https://www.scitepress.org/Papers/2025/131807/131807.pdf); [ContextBuddy arXiv 2506.09365](https://arxiv.org/pdf/2506.09365)
- Faithfulness and stability critique of post-hoc explainers (local-approximation error, randomness, latency) — [XSec, arXiv 2608.05552](https://arxiv.org/abs/2608.05552)
- GEAD's evidence of usefulness is case studies plus a SCADA deployment, not a controlled user study — [SCU portal](https://researchportal.scu.edu.au/esploro/outputs/conferenceProceeding/Rules-Refine-the-Riddle-Global-Explanation/991013245550902368)
- OpenSec results (GPT-5.2: 100% containment, 82.5% FP, acts at about step 4; Sonnet 4.5: 62.5% containment, 45% FP) — [arXiv 2601.21083](https://arxiv.org/abs/2601.21083)
- ALERT-BENCH and AIDA results (≥40.4% missed for all baselines; empty search results lead to dismissal; same-context review has negative net correction; AIDA F1 0.958, FNR 3.1%, 18.4% escalated) — [arXiv 2610.10608](https://arxiv.org/abs/2610.10608)
- CORTEX claims FP reduction from multi-agent triage with no numbers in its abstract — [arXiv 2510.00311](https://arxiv.org/abs/2510.00311)
- An agentic-AI survey says autonomous incident response lacks formal safety guarantees under distribution shift or adversarial manipulation (search summary) — [arXiv 2601.05293](https://arxiv.org/html/2601.05293v1)

### Inferences
- Faithfulness (fidelity metrics) and usefulness (analyst decision quality) are evaluated in separate literatures. No verified 2024–2026 top-venue paper measures both on NIDS.
- LLM triage and containment results come from single scenarios or from small, synthetic or injected episode sets (n=40 per model in OpenSec; one attack scenario in ALERT-BENCH). External validity is weak.
- None of these response papers ties containment decisions to a statistically controlled error rate. Combining conformal or abstention gates with LLM escalation is an open combination worth targeting.

### Gaps
- I found no peer-reviewed controlled study at a top security venue in 2024–2026 measuring whether NIDS explanations change analyst accuracy or time-to-triage.
- Cost data (tokens, latency, analyst hours) for CORTEX and AIDA is **NOT VERIFIED**.
- I did not check whether xNIDS-style explanation-driven response has been evaluated for collateral damage (blocked benign flows) in 2024–2026 work.
