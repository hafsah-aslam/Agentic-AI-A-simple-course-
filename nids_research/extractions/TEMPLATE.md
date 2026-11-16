---
paper_id:
title:
authors:
year:
venue:
peer_reviewed:            # Y | N
source_used:              # exact file / URL read (e.g. pdfs/AP-024.pdf, arXiv v2)
pages_total:
pages_read:
appendices_read:          # Y | N | NONE_IN_PAPER
status:                   # FULL | PARTIAL
evidence_level:           # A (FULL) | B (PARTIAL)
reader:
date_utc:
relevance:                # SOLVES_PART | COMPETING_MECHANISM | ESTABLISHES_ASSUMPTION | DEMONSTRATES_FAILURE | INDIRECT
---

## Checklist (location in paper, or NOT PRESENT IN PAPER)
- abstract/introduction:
- related work:
- problem formulation:
- threat model / assumptions:
- methodology:
- mathematical formulation:
- experimental methodology:
- datasets & preprocessing:
- train/validation/test splits:
- baselines:
- main results:
- ablations:
- limitations:
- conclusion:
- appendices / supplementary:

## A. Research identity
- Problem addressed:
- Central contribution (authors' words):
- Motivating limitation of prior work:
- What the paper claims is new:

## B. Problem and threat model
- System protected:
- Attacker:
- Attacker can observe / modify / inject / control:
- Can manipulate training data?          (Y/N/NOT STATED — evidence)
- Can influence model updates?           (Y/N/NOT STATED — evidence)
- Can manipulate benign traffic?          (Y/N/NOT STATED — evidence)
- Knows detector / thresholds?            (Y/N/NOT STATED — evidence)
- Explicitly excluded capabilities:

## C. Technical mechanism
- Algorithm / architecture:
- Inputs → outputs:
- Mathematical formulation (key equations, with numbers as in the paper):
- Required assumptions (list each; mark which are stated vs implicit):
- Difference from earlier approaches (authors' claim):
- Guarantee type: FORMAL (theorem #, conditions) | EMPIRICAL ONLY | NONE
- If formal: exact statement, assumptions, what it does NOT cover:

## D. Experimental methodology
- Datasets (public/private, size, class balance, time span):
- Split type (random / chronological / cross-domain / cross-dataset / held-out attack family):
- Attack classes held out? Which:
- Temporal novelty evaluated?:
- Leakage risks noticed (reader's observation, labelled as such):
- Threshold selection rule:
- FPR measured on an independent test set?:
- Seeds / confidence intervals / statistical tests:

## E. Results (each with dataset, split, operating point, baseline, location)
| Metric | Value | Dataset | Split | Operating point / threshold | Baseline (value) | Location |
|---|---|---|---|---|---|---|

- Adaptation performance:
- Latency / overhead / memory:
- Robustness under adversarial manipulation:

## F. Limitations and unresolved questions
- Acknowledged by authors:
- Untested assumptions (reader's analysis, labelled):
- Under temporal shift:
- Under adversarial manipulation:
- Under contaminated update stream:
- When unseen attacks resemble benign traffic:
- Guarantees that disappear when assumptions fail:

## G. Relationship to the investigated NIDS problem
(Adaptive NIDS; unseen attacks; controlled false alarms; temporal shift; adversary manipulates
observations or the update process.)
- Which parts it solves / competes with / assumes / shows failing:
- Evidence that could INVALIDATE the hypothesis or a candidate gap:
- Closest papers to compare against:

## Distinctions check
- [ ] numbers reported as the paper's claims, not independently verified
- [ ] empirical results not described as guarantees
- [ ] calibration targets not described as deployment FPR guarantees
- [ ] proposed attacks not described as demonstrated
