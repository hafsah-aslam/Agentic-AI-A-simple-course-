# Drift, distribution shift, cross-dataset generalization and continual learning for ML security detectors (NIDS and malware), 2024–2026

Scope note from the researcher: I had a budget of about 20 tool calls. I verified 12 works from 2024–2026 on primary pages (arXiv abstract pages, the NDSS paper page and slides, the full RAID 2024 PDF). They differ in how much I could extract. Mateen (RAID 2024) and Li et al. (NDSS 2025) were extracted in depth from full text or slides. For the others I read only the abstract page, so fields such as datasets, baselines and limitations are marked "not checked". I list known foundational works only as background and did not re-verify them in this session. Several venue papers I expected to find (e.g., at EuroS&P, ACSAC main track, or USENIX Security 2024–2026 on NIDS drift) were not surfaced by my searches. That is a coverage gap, not evidence that such papers do not exist.

## Q1. Which 2024–2026 papers study drift or shift for NIDS and security classifiers? (paper-by-paper extraction)

### Takeaway
The verified 2024–2026 core is: Li et al. NDSS 2025 (Windows malware, domain adaptation), He et al. CCS 2025 (DREAM, drift explanation plus adaptation, Android), and Alotaibi and Maffeis RAID 2024 (Mateen, NIDS benign-shift adaptation). Around them sit a cluster of arXiv preprints from 2025–2026 on reliability of selective classification (Aurora), pseudo-labelling (ADAPT), robustness of drift-adaptive detectors (Li et al. 2026), and gating model promotion in adaptive NIDS (Fernández-Barrios et al. 2026). The NIDS-specific literature at top-4 venues is thin compared with the malware drift line.

### Cited Findings

**P1. Revisiting Concept Drift in Windows Malware Detection: Adaptation to Real Drifted Malware with Minimal Samples.** Adrian Shuai Li (Purdue), Arun Iyengar (Intelligent Data Management and Analytics, LLC), Ashish Kundu (Cisco Research), Elisa Bertino (Purdue). NDSS 2025. — [NDSS page](https://www.ndss-symposium.org/ndss-paper/revisiting-concept-drift-in-windows-malware-detection-adaptation-to-real-drifted-malware-with-minimal-samples/); [NDSS slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf); [code](https://github.com/gloryer/malware-detection-concept-drift)
- Problem: active-learning retraining methods for malware classifiers do not force the model to learn features that stay invariant before and after drift, so "the current retraining techniques do not achieve optimal results." — [NDSS page](https://www.ndss-symposium.org/ndss-paper/revisiting-concept-drift-in-windows-malware-detection-adaptation-to-real-drifted-malware-with-minimal-samples/)
- Mechanism and math basis: the pipeline disassembles binaries, builds control-flow graphs (CFGs), embeds each instruction with the pretrained PalmTree assembly language model, and then trains a GNN with adversarial domain adaptation between a labelled source domain and a target domain with few labels. The adversarial domain adaptation is DANN-style alignment. The paper compares this against cold-start retraining (train a fresh model) and warm-start retraining (continue training the existing model). An outlier-detection module flags new families. — [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf)
- Datasets and time spans: Microsoft Big-15 (Kaggle Malware Classification Challenge) as the research dataset, and real-world malware reported daily by security companies in 2024. Monthly tasks used source data from Mar–May 2024 with targets in July/Aug 2024 (task a) and Aug/Sep 2024 (task b). — [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf)
- Protocol: temporal monthly-update splits on the real-world data, plus a multi-family post-drift classification task. — [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf)
- Baselines: cold-start, warm-start, and domain-adaptation methods from computer vision. The paper cites the selection methods of Chen et al. (USENIX Security 2023), Transcending Transcend (S&P 2022) and CADE (USENIX Security 2021) as the active-learning context. — [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf)
- Key results: on Big-15 the method had "the smallest accuracy drop of 0.5% on average". On the real-world data, with 200 labelled samples per month, it matched the accuracy of labelling 75% of the data (1209/1613 in August, 1002/1337 in September). Warm-start needed 500 samples for the same result. With 10 new samples per family, family-level classification improved by 9–14% over the baselines. The evasion rate for new families stayed below 5%. — [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf)
- Stated caveat: the authors found that Big-15 families "exhibit highly similar characteristics". Evaluations that rely on those family labels are therefore likely to overestimate accuracy, so actual drift in research datasets needs to be validated. — [slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf)
- Not checked (full paper not read): formal threat model, compute cost, and the full limitations section.

**P2. Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification (DREAM).** Yiling He, Junchi Lei, Zhan Qin, Kui Ren, Chun Chen. ACM CCS 2025 (arXiv 2405.04095; v1 May 2024, v3 May 2025). — [arXiv](https://arxiv.org/abs/2405.04095)
- Problem: new malware families can drop accuracy to near-random. Prior drift detectors rely on expert label revision, which gives little insight into malware concepts and costs a lot of labelling. — [arXiv](https://arxiv.org/abs/2405.04095)
- Mechanism: malware explanations ("concepts") are embedded in the latent space of a contrastive autoencoder, and sample reconstruction is constrained by the target classifier's predictions. The system detects drift in real time without needing training data. A behaviour-based drift explainer supports expert concept revision, which then guides retraining. — [arXiv](https://arxiv.org/abs/2405.04095)
- Key result: when updating a Drebin classifier, DREAM reaches the same accuracy with 76.6% fewer newly labelled samples than the best existing method. — [arXiv](https://arxiv.org/abs/2405.04095)
- Not checked: dataset names and time spans, named baselines, protocol details, limitations.

**P3. Mateen: Adaptive Ensemble Learning for Network Anomaly Detection.** Fahad Alotaibi, Sergio Maffeis (Imperial College London). RAID 2024, Padua, DOI 10.1145/3678890.3678901. — [full PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf); [code](https://github.com/ICL-ml4csec/Mateen)
- Problem: autoencoder anomaly-based NIDS assume benign traffic stays constant. "Benign shift" makes an offline deep autoencoder (DAE) flag new benign behaviour as malicious, so false positives rise over time. — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Mechanism: an ensemble of DAEs. For each batch, the system detects shift, selects a small representative subset for manual labelling, and adapts. Temporary models within 10% of the best F1 on the labelled subset are merged (with a weight α chosen by grid search over F1), and underperforming ones are discarded. No update is made if F1 on the selected subset exceeds a threshold t (set at 99%). — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Datasets: CICIDS2017 (IDS17), CSE-CIC-IDS2018 (IDS18), Kitsune, and two modified Kitsune variants: mKitsune (constant malicious-to-benign ratio) and rKitsune (recurring concept). Kitsune lacks timestamps, so the authors used file order, and they also built simulated covariate-shift scenarios from IDS18. — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Baselines: No-Update DAE, OWAD (NDSS 2023), INSOMNIA (supervised, AISec 2021) and CADE (USENIX Security 2021, sample selection only). — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Labelling budget: δ = 1% of incoming samples (500 samples per batch). A sensitivity sweep covered δ of 0.5%, 1%, 5% and 10%. — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Key results:
  - F1 rose by 4.13% on IDS17 ("light change") and by 72.6% on Kitsune ("heavy change").
  - AUC-ROC was 96.79% on IDS17, 98.17% on IDS18 and 94.76% on mKitsune, beating the best baseline by 2.23, 4.36 and 14.78 points respectively.
  - In one comparison, OWAD and INSOMNIA used 5,000 labelled samples and reached only 90.01% and 78.98% accuracy.
  - Across hyperparameter settings on IDS17, AUC-ROC averaged 96.19 with a standard deviation of 0.64.
  - [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Label-noise test: 10%, 30% or 50% of the selected labels were flipped at random. Mateen degraded gradually but stayed above OWAD and No-Update on IDS17, while OWAD dropped sharply at 50% noise on mKitsune. — [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Stated limitations:
  - Labelling costs in highly dynamic networks.
  - Labelling latency.
  - Label estimators can cause "self-poisoning".
  - The labelling and update loop "is a potential vector for poisoning the ensemble" through label flipping and backdoors, which is left as future work.
  - Evasive samples disguised as benign.
  - [PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Unstated assumptions (my reading): analysts receive the selected samples and label them correctly. Malicious traffic is assumed to look anomalous relative to benign traffic. The evaluation is offline replay of CIC datasets, which are known to have artefacts.

**P4. On the Cross-Dataset Generalization of Machine Learning for Network Intrusion Detection.** Marco Cantone, Claudio Marrocco, Alessandro Bria. IEEE Access vol. 12, pp. 144489–144508, 2024 (arXiv 2402.10974). Not a top security venue, but it is the most direct NIDS cross-dataset study I found. — [arXiv](https://arxiv.org/abs/2402.10974); [PDF](https://iris.unicas.it/retrieve/a40146bd-61d7-4a77-98c7-cf72f480c839/2024%20-%20Machine%20Learning%20in%20Network%20Intrusion%20Detection%20-%20A%20Cross-Dataset%20Generalization%20Study.pdf)
- Datasets: CIC-IDS2017, CSE-CIC-IDS2018, LycoS-IDS2017, and a new LycoS-Unicas-IDS2018 (LycoS-style corrections applied to CSE-CIC-IDS2018). Four ML classifiers were tested (names not checked). — [arXiv](https://arxiv.org/abs/2402.10974)
- Result: within-dataset performance is "nearly perfect", while cross-dataset accuracy is "largely commensurate with random chance" except for a few attack/dataset combinations. The authors attribute this partly to anomalies in the data. — [arXiv](https://arxiv.org/abs/2402.10974)
- Not checked: per-pair numerical tables.

**P5. Aurora: Are Android Malware Classifiers Reliable (and Stable) under Distribution Shift? / current title: "On the Reliability and Stability of Selective Methods in Malware Classification Tasks."** Alexander Herzog, Aliai Eusebi, Lorenzo Cavallaro (UCL). arXiv 2505.22843: v1 28 May 2025, v4 27 Oct 2026. No venue is listed on the abstract page. — [arXiv](https://arxiv.org/abs/2505.22843)
- Problem: evaluations of drift-adaptive malware classifiers focus on baseline performance. They ignore whether confidence estimates line up with errors and stay stable over time. Poor confidence wastes active-learning budgets and leaves errors undetected in selective classification (rejection). — [arXiv](https://arxiv.org/abs/2505.22843)
- Mechanism: an evaluation framework built on risk–coverage analysis (Area Under the Risk-Coverage Curve, AURC), rejection under a fixed budget, and temporal stability metrics. — [arXiv v1 HTML](https://arxiv.org/html/2505.22843v1)
- Finding: the authors observe fragility in state-of-the-art frameworks across datasets of varying drift severity, which "suggests it may be time to revisit the underlying assumptions." The abstract gives no numbers. — [arXiv](https://arxiv.org/abs/2505.22843)
- Not checked: datasets, which frameworks were evaluated, numerical results, venue.

**P6. ADAPT: A Pseudo-labeling Approach to Combat Concept Drift in Malware Detection.** Md Tanvirul Alam, Aritran Piplai, Nidhi Rastogi. arXiv 2507.08597 (Jul/Aug 2025). No venue listed. — [arXiv](https://arxiv.org/abs/2507.08597)
- Mechanism: model-agnostic semi-supervised pseudo-labelling that works for neural networks and tree models, aimed at reducing the need for ground-truth labels under drift. The authors evaluate five malware datasets across the Android, Windows and PDF domains, and claim consistent gains over baselines. — [arXiv](https://arxiv.org/abs/2507.08597)
- A search snippet says ADAPT targets "catastrophic self-poisoning" through drift-aware pseudo-labelling and extends to active learning. I did not confirm this on the abstract page. — [arXiv HTML v2](https://arxiv.org/html/2507.08597v2)
- Not checked: dataset names and time spans, baselines, numbers.

**P7. Can Drift-Adaptive Malware Detectors Be Made Robust? Attacks and Defenses Under White-Box and Black-Box Threats.** Adrian Shuai Li, Md Ajwad Akil, Elisa Bertino. arXiv 2604.06599 (8 Apr 2026), not peer reviewed. — [arXiv](https://arxiv.org/abs/2604.06599)
- Problem: the adversarial robustness of drift-adaptive detectors has not been studied. The target is AdvDA, an adversarial domain adaptation detector closely related to P1. — [arXiv](https://arxiv.org/abs/2604.06599)
- Threat models: white-box PGD in feature space, and black-box MalGuise, which applies functionality-preserving control-flow mutations to binaries. These are evasion attacks, not poisoning of the update process. — [arXiv](https://arxiv.org/abs/2604.06599)
- Evaluation: Windows malware over five monthly adaptation windows, nine defence configurations, and three FPR operating points. — [arXiv](https://arxiv.org/abs/2604.06599)
- Results:
  - Undefended AdvDA suffers 100% PGD attack success and 13% MalGuise success.
  - The proposed robustification fine-tunes on adversarially transformed inputs and reduces these to 3.2% (PGD) and 5.1% (MalGuise).
  - Source-domain adversarial training is essential against PGD but counterproductive against MalGuise.
  - Robustness does not transfer between the two threat models.
  - [arXiv](https://arxiv.org/abs/2604.06599)

**P8. Candidate Comparability Before Promotion: Conditional Validation in Adaptive Network Intrusion Detection.** Roberto Fernández-Barrios, Iker Pastor-López, Amaia Pikatza-Huerga, Pablo García Bringas. arXiv 2609.04388 (3 Sep 2026), not peer reviewed. — [arXiv](https://arxiv.org/abs/2609.04388)
- Problem: a drift alarm shows that data changed, not that a retrained challenger should replace the deployed incumbent. This is a model-update gating question. — [arXiv](https://arxiv.org/abs/2609.04388)
- Data: CICIDS2017, UNSW-NB15 and ToN-IoT, plus 13 replays of real time-ordered traffic. — [arXiv](https://arxiv.org/abs/2609.04388)
- Results:
  - When the incumbent's frozen preprocessing was reused, it inflated apparent promotion harm. With self-contained challenger pipelines, the mean full-drift harm did not persist.
  - Raising candidate evidence from 512 to 2,000 samples per class improved promotion by +0.53, +1.67 and +0.38 balanced-accuracy points. The gains were driven mainly by fewer false positives.
  - No update policy among the nine compared dominated globally.
  - Validation gating helped only challengers with less evidence.
  - In the 13 real-traffic replays, "always deploy" caused no net harm.
  - [arXiv](https://arxiv.org/abs/2609.04388)

**P9. The Impact of Active Learning on Availability Data Poisoning for Android Malware Classifiers.** Shae McFadden, Zeliang Kan, Lorenzo Cavallaro, Fabio Pierazzi. ACSAC 2024 Workshops (per search result). PARTIALLY VERIFIED: the UCL Discovery record returned HTTP 403. Title, authors and venue come from the search snippet and the [UCL Discovery entry](https://discovery.ucl.ac.uk/id/eprint/10208029) / [PDF](https://discovery.ucl.ac.uk/id/eprint/10208029/1/rpal_artman.pdf). Numbers were not checked.
- Claimed finding (search snippet): active learning, used as a drift mitigation, lets poisoned classifiers recover toward their clean counterparts across three classifiers. Higher poisoning rates delay that recovery. The question studied is whether small poisoning can force defenders into more retraining. — [UCL Discovery](https://discovery.ucl.ac.uk/id/eprint/10208029)

**P10. Continual Learning with Strategic Selection and Forgetting for Network Intrusion Detection (SSF).** arXiv 2412.16264. A citing reference lists it as IEEE INFOCOM 2025. I did not check authors or venue on a primary page. — [arXiv](https://arxiv.org/abs/2412.16264)
- It refreshes a memory buffer through strategic sample selection and forgetting, and is evaluated on NSL-KDD and UNSW-NB15 (from the search summary). Neither dataset has a meaningful temporal structure. — [arXiv](https://arxiv.org/abs/2412.16264)

**P11. Generative Active Adaptation for Drifting and Imbalanced Network Intrusion Detection (NetGuard).** ACM, DOI 10.1145/3830389; arXiv 2503.03022. UNVERIFIED: authors, venue and numbers come from a search snippet only. It combines density-aware active sampling with generative synthesis of minority attack classes. — [ACM DL](https://dl.acm.org/doi/10.1145/3830389)

**P12. A cross-dataset harmonized intrusion detection framework with statistically validated multi-model learning** (2025/26, PMC open access). UNVERIFIED beyond the search snippet: it reportedly pairs NSL-KDD and CICIDS2017 and reports CIC→NSL-KDD at 0.985 in-domain vs 0.570 cross-domain accuracy. It also notes seed variance and within-capture class-prevalence shift in CIC-IDS2017. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13094972/)

**Background (pre-2024; cited by the papers above; not re-verified in this session):**
- TESSERACT (USENIX Security 2019)
- Transcend (USENIX Security 2017) and Transcending Transcend (IEEE S&P 2022, Barbero et al.)
- CADE (Yang et al., USENIX Security 2021)
- INSOMNIA (Andresini et al., AISec 2021)
- OWAD (Han et al., NDSS 2023, normality shift detection, explanation and adaptation)
- Chen, Ding and Wagner, "Continuous Learning for Android Malware Detection" (USENIX Security 2023), whose arXiv version states that defending active learning against poisoning is an open problem — [arXiv 2302.04332](https://arxiv.org/pdf/2302.04332)
- Venue citations for these appear in [NDSS 2025 slides](https://www.ndss-symposium.org/wp-content/uploads/12B-f0830-li.pdf) and the [Mateen paper](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf).

### Inferences
- The malware drift line has moved from detecting drifting samples (CADE, Transcend) toward adaptation with fewer labels: P1 needs about 200 labels per month, and P2 needs 76.6% fewer labels. NIDS work (P3) mostly imports this paradigm for benign shift in one-class detectors.
- Both P1's Big-15 caveat and P4/P12 suggest that benchmark artefacts can inflate drift and adaptation results. Validating that drift actually occurs is a recurring and under-addressed methodological requirement.
- No verified NIDS-drift paper in this set uses a multi-year, timestamped, real enterprise trace as the main benchmark. P8's 13 real replays are the closest.

### Gaps
- I did not search, or did not find, the following candidates; all remain UNVERIFIED:
  - EuroS&P 2024–2026 NIDS dataset-quality work (e.g., on CIC-IDS2017 design flaws)
  - ACSAC 2024/2025 or USENIX Security 2024–2026 NIDS-drift papers
  - TDSC/TIFS 2024–2026 drift papers
  - An extended TESSERACT journal version (2024)
  - Test-time adaptation for NIDS
  - Continual novelty detection for IDS (e.g., "CND-IDS")
- The following fields were not checked for P2, P5, P6, P10 and P11: datasets with time spans, baselines, full numbers, and stated limitations. The full PDFs need reading.

## Q2. What does the evidence show about cross-dataset generalization of NIDS?

### Takeaway
The evidence shows that generalization is poor. Training and testing on one CIC dataset gives near-perfect scores, but transferring to another dataset, even a sibling with similar attack classes (CIC-IDS2017 to CSE-CIC-IDS2018), drops accuracy to around chance for most attack/dataset pairs. Reported in-domain to cross-domain falls include 0.985 to 0.570 accuracy.

### Cited Findings
- Same-dataset evaluation is "nearly perfect", while cross-dataset accuracy is "largely commensurate with random chance" except for a few attack/dataset combinations. This held across CIC-IDS2017, CSE-CIC-IDS2018 and corrected LycoS variants. — [Cantone et al., IEEE Access 2024 / arXiv 2402.10974](https://arxiv.org/abs/2402.10974)
- CIC-IDS2017 and CSE-CIC-IDS2018 were chosen because they share similar attack classes, which makes the near-random transfer more striking. — [Cantone et al. PDF](https://iris.unicas.it/retrieve/a40146bd-61d7-4a77-98c7-cf72f480c839/2024%20-%20Machine%20Learning%20in%20Network%20Intrusion%20Detection%20-%20A%20Cross-Dataset%20Generalization%20Study.pdf)
- CIC→NSL-KDD: 0.985 in-domain vs 0.570 cross-domain accuracy. This is from a snippet and was not verified in the full text. — [PMC harmonized framework](https://pmc.ncbi.nlm.nih.gov/articles/PMC13094972/)
- Few-shot cross-domain (train CICIDS2018, adapt with a few target samples, test CICIDS2017) reports over 95.13% accuracy. Because it uses target labels, it is not zero-shot transfer. — [PLOS ONE 2025](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0327161)
- In time-ordered or batch-shifted settings within one dataset, a non-updated DAE degrades substantially. Mateen's 72.6% F1 gain on Kitsune ("heavy change") gives a lower bound on how much the static model lost. — [Mateen RAID 2024](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- When P8 compared update policies across CICIDS2017, UNSW-NB15 and ToN-IoT, effect sizes differed by benchmark and no policy dominated. — [arXiv 2609.04388](https://arxiv.org/abs/2609.04388)

### Inferences
- A USENIX Security 2027 project should treat "trained on CIC-IDS2017, tested on CIC-IDS2017" as non-evidence of deployability. Cross-dataset and temporal splits should be the primary protocols, and feature-set harmonization (flow extractor differences) should be reported as a confounder.

### Gaps
- I could not extract per-pair F1 tables from Cantone et al. The full PDF is needed.
- I did not find a 2024–2026 top-venue paper that systematically quantifies NIDS cross-network transfer on real (non-synthetic) enterprise traffic.

## Q3. Is there work on certifying or bounding FPR under drift, or on safely gating model updates? What is missing? (Including the security risks of adaptation.)

### Takeaway
I found no verified 2024–2026 work that certifies or provably bounds FPR under drift for NIDS. The closest pieces are: empirical risk–coverage and rejection reliability (Aurora), empirical promotion gating (Fernández-Barrios et al. 2026, which finds no dominant policy and conditional value from validation), and threshold-based no-update rules (Mateen's F1 ≥ 99% skip). Poisoning of the adaptation loop is repeatedly named as an open problem and only lightly studied (McFadden et al. 2024 workshop).

### Cited Findings
- Fernández-Barrios et al. (2026) found:
  - Validation-gated promotion helps only challengers with less evidence.
  - More candidate evidence (512 to 2,000 per class) improves promotion mainly by reducing false positives.
  - "Always deploy" caused no net harm across 13 real-traffic replays.
  - Conclusions depend on whether incumbent preprocessing is reused.
  - [arXiv 2609.04388](https://arxiv.org/abs/2609.04388)
- Aurora argues that confidence estimates of SOTA drift-adaptive malware classifiers are fragile under drift. It uses AURC and budgeted rejection to evaluate selective classification. — [arXiv 2505.22843](https://arxiv.org/abs/2505.22843)
- Mateen skips updates when F1 on the labelled subset is at or above t = 99%, and explicitly flags its labelling loop as a poisoning vector through label flipping and backdoors. — [Mateen PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- Mateen also notes that label estimators "inadvertently lead to self-poisoning". — [Mateen PDF](https://www.doc.ic.ac.uk/~maffeis/papers/raid24.pdf)
- ADAPT positions drift-aware pseudo-labelling against self-poisoning. This is from a snippet and not confirmed. — [arXiv 2507.08597](https://arxiv.org/abs/2507.08597)
- Availability poisoning combined with active learning: poisoned Android classifiers recover toward clean performance under active learning, but higher poisoning rates delay recovery. This is from a snippet; numbers were not checked. — [McFadden et al., ACSAC-W 2024](https://discovery.ucl.ac.uk/id/eprint/10208029)
- Chen, Ding and Wagner (USENIX Security 2023, background) state that defending active learning against poisoning is open. — [arXiv 2302.04332](https://arxiv.org/pdf/2302.04332)
- Drift-adaptive detectors are also highly evadable: 100% PGD success against undefended AdvDA, and robustness does not transfer between threat models. — [arXiv 2604.06599](https://arxiv.org/abs/2604.06599)
- A SECRYPT 2024 paper argues that existing work handles drift detection or poisoning mitigation, but not both together. It evaluates on NIDS and Android data. Title and authors were not verified. — [SciTePress](https://www.scitepress.org/publishedPapers/2024/127616/pdf/index.html)

### Inferences
- What is missing:
  1. Distribution-free or conformal guarantees on FPR for benign traffic after an update, with explicit assumptions on how benign traffic shifts.
  2. Update-gating rules that are robust to an adversary who controls part of the post-drift data or of the samples selected for labelling.
  3. Joint threat models covering drift, poisoning of the labelling and update loop, and evasion. Current papers treat at most two of these.
  4. Evaluations that account for labelling latency and analyst error together with an adversary. Mateen treats random label noise, not adversarial noise.
- Every adaptive method in this set assumes that labels arrive from a trusted analyst, P3 additionally assumes the benign/malicious separation remains anomaly-detectable, and P8 assumes enough candidate evidence per class. These assumptions are the attack surface an adversary would exploit.

### Gaps
- I did not search for conformal prediction or PAC-style FPR bounds specifically for security detectors in 2024–2026, so certification work may exist that I did not surface.
- I did not verify any test-time adaptation papers for NIDS.
- For P9 the primary page was blocked (403), so its quantitative results remain UNVERIFIED.
