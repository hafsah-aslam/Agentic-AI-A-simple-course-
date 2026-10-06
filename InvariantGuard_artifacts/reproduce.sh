#!/usr/bin/env bash
# Reproduce every number and data figure of the paper.
#
#   ./reproduce.sh                 unit tests, all experiments (PostgreSQL 16 + SQLite), numbers.tex, figures
#   ./reproduce.sh --figures-only  numbers.tex and Figures 3-9 from the shipped results/ (no database needed)
#
# Requires Python 3.11 with requirements.txt installed. Full runs also need PostgreSQL 16 reachable
# via $IG_PG (default "host=/tmp port=5433 user=postgres"; ./scripts_start_postgres.sh starts one).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/code"

if [[ "${1:-}" != "--figures-only" ]]; then
  python3 -m pytest -q code/tests
  python3 code/experiments/run_admission.py     # RQ2/RQ3: admission, baselines, ablation, defects, tau sweep
  python3 code/experiments/run_bounds.py        # RQ1: bound quality, property tests, sweeps
  python3 code/experiments/run_benchmark.py     # RQ4: oracle, release criteria, boundary oracle, selection
  python3 code/experiments/run_concurrency.py   # RQ5: transaction disciplines under concurrency
  python3 code/experiments/run_scale.py         # RQ5: snapshot and latency up to 4.1M rows
  python3 code/experiments/run_coverage.py      # RQ5: coverage tooling
  python3 code/experiments/run_sqlite.py        # RQ5: SQLite portability
fi
python3 code/experiments/make_numbers.py        # results/numbers.tex (every number quoted in the paper)
python3 code/figures/make_paper_figures.py      # figures/fig*.pdf|png (Figures 3-9 of the paper)
