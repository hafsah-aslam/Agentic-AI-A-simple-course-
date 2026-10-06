# InvariantGuard — Supplementary Material

Artifacts for the EDBT 2027 research paper
**"InvariantGuard: Admission Control for Agentic Database Writes Using Certified Cardinality Bounds"**.

This package contains the implementation, the data and benchmark, the result file behind every
number in the paper, and the scripts that regenerate the paper's numbers and data figures.

## Contents

```
InvariantGuard_artifacts/
├── README.md
├── reproduce.sh              runs everything (or --figures-only, no database needed)
├── requirements.txt          Python dependencies
├── scripts_start_postgres.sh starts a throw-away PostgreSQL 16 cluster on port 5433
├── code/
│   ├── invariantguard/       the system (modules listed below)
│   ├── experiments/          one script per experiment (run_*.py) + make_numbers.py
│   ├── figures/              one script per paper figure (fig3..fig9) + make_paper_figures.py
│   └── tests/                unit tests (no database needed)
├── data/
│   ├── fixtures/             5 database fixtures (schema.sql, seed.sql)
│   ├── invariants/           declared invariant sets (YAML)
│   └── ig_bench/             IG-Bench v3, 470 records (JSONL)
├── results/                  output of every experiment (JSON/JSONL) and numbers.tex
└── figures/                  Figures 3–9 of the paper as vector PDF + 300 dpi PNG
```

## Quick start (about one minute, no database)

```bash
pip install -r requirements.txt
./reproduce.sh --figures-only
```

This regenerates `results/numbers.tex` (every measured number quoted in the paper, as LaTeX
macros) and Figures 3–9 in `figures/` from the shipped `results/`. Each figure script also
prints a self-check (no overlapping labels, no label covering data).

## Full reproduction

Requirements: Python 3.11, PostgreSQL 16, and SQLite through Python's built-in `sqlite3` (the paper used SQLite 3.45).

```bash
pip install -r requirements.txt
./scripts_start_postgres.sh        # or set IG_PG to any PostgreSQL 16, e.g. IG_PG="host=localhost port=5432 user=postgres"
./reproduce.sh                     # unit tests, all experiments, numbers.tex, figures
```

Each experiment works on disposable clones of per-fixture template databases and never
modifies the fixtures. Decisions, labels, and bounds are deterministic (fixed seeds, fixed
benchmark release). Latencies depend on the host; the ratios between disciplines and between
the static and shadow paths are the reproducible quantities.

## Where each result in the paper comes from

| Paper | Experiment script | Result file(s) | Figure script |
|---|---|---|---|
| RQ1, Table 3, Figure 3 (bound quality, property and cascade tests, sweeps) | `run_bounds.py` | `bound_quality.json`, `bound_quality_rows.jsonl` | `fig3_bound_quality.py` |
| RQ2, Figure 4 (admission outcomes, evidence) | `run_admission.py` | `admission.json`, `admission_records.jsonl` | `fig4_admission.py` |
| RQ2, Figure 5 (baselines, F1 with 95% CI) | `run_admission.py` | `admission.json` | `fig5_baselines.py` |
| RQ2, Figure 6, Table 4 (ablation, defects, τ_b sweep, estimate provider) | `run_admission.py` | `admission.json` | `fig6_ablation_heatmap.py` |
| RQ3, Figure 7 (static discharge, cross-check) | `run_admission.py` | `admission.json` | `fig7_static_discharge.py` |
| RQ4 (oracle, release criteria, boundary oracle, selection completeness) | `run_benchmark.py` | `benchmark_validation.json` | — |
| RQ5, Figure 8 (concurrency: latency and containment) | `run_concurrency.py` | `concurrency.json` | `fig8_latency.py` |
| RQ5, Figure 9 (scale up to 4.1M rows) | `run_scale.py` | `scale.json` | `fig9_scale.py` |
| RQ5 (coverage tooling) | `run_coverage.py` | `coverage.json`, `coverage_invariants/*.yaml` | — |
| RQ5 (SQLite portability) | `run_sqlite.py` | `sqlite_portability.json` | — |
| All numbers in the text | `make_numbers.py` | `numbers.tex` | — |

Experiment scripts are in `code/experiments/`, figure scripts in `code/figures/`, result files in
`results/`. Figure file names match the names used in the paper's LaTeX source
(e.g. Figure 3 is `fig06_bound_quality.pdf`). Figures 1 and 2 are hand-drawn diagrams and are
not generated from data.

## The system (`code/invariantguard/`)

| Module | Paper section | Role |
|---|---|---|
| `compiler.py` | 3.2 | pglast parse tree → IR, supported predicate grammar, invariant read sets |
| `invariants.py` | 3.1 | invariant tuple, statement/action scope, metric relation |
| `db.py` | 3.1 | fixture templates, disposable clones, write-watermark triggers |
| `snapshot.py` | 3.1 | certificate snapshot: \|T\|, mf, per-value frequency certificates, keys, FKs, watermarks; validity |
| `bounds.py` | 3.3 | rules R1–R8′, sum-merged cascade vectors, certified lower bounds |
| `verifier.py` | 3.3–3.5 | selection and vacuity rule, static analyzer (original / extended), frame rule, shadow verification, aggregation, decision |
| `proxy.py` | 3.6 | connection proxy; separate / serializable-through-commit / witness-and-revalidate |
| `oracle.py` | 3.7 | independent commit oracle (final-state and boundary-matched) |
| `baselines.py` | 4.3 | no verification, keyword guardrail, ABAC, estimate admission |
| `coverage.py` | 4.6 | suggested invariants over uncovered cascade relations |
| `sqlite_backend.py` | 4.6 | SQLite port (snapshot, watermarks, shadow, oracle) |

## Data

All data were built for this study; none is proprietary or personal.

* `data/fixtures/`: `chinook_derived` and `northwind_derived` adapt the schemas of the public
  Chinook and Northwind sample databases, re-seeded by hand; `hr_payroll`, `banking_heldout`, and
  `healthcare_heldout` were written from scratch (the latter two after thresholds were frozen).
* `data/invariants/`: the declared invariant set of each fixture.
* `data/ig_bench/ig_bench_v3.jsonl`: IG-Bench v3, 470 scenarios (341 safe, 114 unsafe, 15 rejected
  by PostgreSQL), each with its fixture, invariant set, action sequence, provenance, seed, and ground-truth label.
* The correlated relation, property-test relations, random foreign-key schemas, and scaled
  `banking` instances are generated by the experiment scripts with fixed seeds.
