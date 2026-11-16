# NIDS full-text investigation — working directory

Central hypothesis under test (NOT an established gap):
> Can an adaptive NIDS maintain reliable detection of unseen attacks and controlled
> false alarms under temporal distribution shift when an adversary can manipulate the
> observations or the model-update process?

## Stages (strict order)
1. Corpus discovery — register 100–200 papers (2024–2026), verify full-text availability  <- CURRENT
2. Full-text reading — Level A extractions in `extractions/`
3. Claim verification — audit of the "second report" claims
4. Mathematical foundations — conformal prediction under shift / adversarial contamination
5. Existing methods — online learning, adaptive calibration, poisoning resistance
6. Competitor analysis
7. Threat-model investigation
8. Research gap identification
9. Research direction selection
10. Reviewer simulation

## Evidence levels
- **A** — full text examined (all sections incl. method, splits, results, limitations, appendices where available). Only A counts toward the 100–200 target.
- **B** — partial text examined.
- **C** — metadata only (title / abstract / listing).
At Stage 1 every register row is C by definition; levels are upgraded only in Stage 2.

## Files
- `register/parts/*.csv` — per-category discovery registers (Stage 1)
- `register/corpus_register.csv` — merged, de-duplicated register
- `extractions/<paper_id>.md` — Level A/B paper records (Stage 2)
- `stage_reports/` — end-of-stage reports
- `pdfs/` — downloaded full texts (git-ignored; re-downloadable from `fulltext_url`)

## Register CSV schema (RFC 4180, header row, all fields quoted)
paper_id,title,authors,year,venue,venue_type,peer_reviewed,doi_or_url,fulltext_url,fulltext_status,local_pdf,supplementary,categories,priority,closest_competitors,notes,evidence_level

- venue_type: conference | journal | preprint | tech_report | workshop
- peer_reviewed: Y | N
- fulltext_status: DOWNLOADED | ACCESSIBLE_NOT_DOWNLOADED | PAYWALLED | NOT_FOUND
- supplementary: Y | N | UNKNOWN
- categories: semicolon-separated from {zero_day, generalization, drift, continual, conformal, calibration, adversarial, poisoning, update_security, guarantees, encrypted, evaluation}
- priority: 1 (core to the hypothesis) | 2 (important) | 3 (context)
- evidence_level: C at Stage 1
