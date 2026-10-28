#!/usr/bin/env bash
# EquiBind and DiffDock baselines on the reproduction's test and PoseBusters cohorts, with the original study's
# pinned tools, seeds, settings and scoring code. Restart-safe: rerun the same command after any interruption.
#
#   bash external_baselines/run_baselines.sh --work ~/dpc_work [--posebusters DIR] [--results DIR] [--stages bridge,equibind,diffdock,score]
#
# Run it from the DockingPoseCorrection folder with the main environment active (the one used for run_all.py).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/.." && pwd)"
work="" posebusters="" results="" stages="bridge,equibind,diffdock,score"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --work) work="$2"; shift 2;;
    --posebusters) posebusters="$2"; shift 2;;
    --stages) stages="$2"; shift 2;;
    --results) results="$2"; shift 2;;
    -h|--help) sed -n 2,8p "$0"; exit 0;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
[[ -n "$work" ]] || { echo "--work is required" >&2; exit 2; }
work="$(cd "$work" && pwd)"
posebusters="${posebusters:-$work/sources}"
[[ -d "$posebusters/posebusters_benchmark_set" ]] || posebusters="$posebusters/posebusters_paper_data"
base="$( (command -v mamba >/dev/null && mamba info --base) || conda info --base 2>/dev/null || echo "$HOME/miniconda3")"
equibind_python="${EQUIBIND_PYTHON:-$base/envs/dpc-equibind/bin/python}"
diffdock_python="${DIFFDOCK_PYTHON:-$base/envs/dpc-diffdock/bin/python}"
ws="$work/external_baselines"
bridge="$ws/bridge"
log() { echo "[$(date +%H:%M:%S)] $*"; }
has() { [[ ",$stages," == *",$1,"* ]]; }

if has bridge || [[ ! -f "$bridge/bridge.json" ]]; then
  log "bridge: exposing this run in the original bundle's input layout"
  python3 "$here/scripts/bridge_from_dpc.py" --repo "$repo" --work "$work" --posebusters "$posebusters" --results "${results:-$repo/results}" --out "$bridge"
fi
export DPC_BRIDGE="$bridge/bridge.json" PYTHONPATH="$here/scripts${PYTHONPATH:+:$PYTHONPATH}"
export DPC_GATE_TAU="$(python3 -c "import json; print(json.load(open('$DPC_BRIDGE'))['gate_tau'])")"
common=(--manifest "$bridge/manifest.csv" --m2-output-dir "$bridge/m2" --workspace "$ws")

has equibind && { log "EquiBind (CPU)"; bash "$here/bin/run_external_baselines.sh" --stage equibind "${common[@]}" --equibind-python "$equibind_python"; }
has diffdock && { log "DiffDock (GPU, 40 samples x 20 steps per complex)"; bash "$here/bin/run_external_baselines.sh" --stage diffdock "${common[@]}" --diffdock-python "$diffdock_python"; }

if has score; then
  log "collect, score (22 PoseBusters checks), aggregate, validate"
  bash "$here/bin/run_external_baselines.sh" --stage collect "${common[@]}"
  python3 "$here/scripts/score_external_baselines.py" --manifest "$bridge/manifest.csv" --m2-output-dir "$bridge/m2" \
      --predictions-dir "$ws/predictions" --output-dir "$ws/scores" ${DPC_SCORE_LIMIT:+--limit-per-split $DPC_SCORE_LIMIT} || log "scoring finished with exclusions (listed in scores/external_baseline_scoring_exclusions.csv)"
  python3 "$here/scripts/aggregate_external_baselines.py" --manifest "$bridge/manifest.csv" \
      --scores-csv "$ws/scores/external_baseline_scores.csv" --m6-evaluation "$bridge/per_complex_evaluation.csv" \
      --frozen-posebusters-results "$bridge/posebusters_results.csv" --output-dir "$ws/summary"
  python3 "$here/scripts/sanity_check_external_baselines.py" --scores-csv "$ws/scores/external_baseline_scores.csv" \
      --m2-output-dir "$bridge/m2" --output "$ws/summary/sanity_check.json" >/dev/null
  python3 "$here/scripts/validate_external_baselines.py" --manifest "$bridge/manifest.csv" --inputs-dir "$ws/inputs" \
      --predictions-dir "$ws/predictions" --scores-csv "$ws/scores/external_baseline_scores.csv" \
      --summary-csv "$ws/summary/external_baseline_summary.csv" --output "$ws/summary/validation.json" --allow-exclusions >/dev/null \
      || log "validation reported failures: see $ws/summary/validation.json"
  mkdir -p "$repo/results/external_baselines"
  cp "$ws/summary/"*.csv "$ws/summary/"*.json "$repo/results/external_baselines/"
  python3 - "$ws/summary/external_baseline_summary.csv" <<'EOF'
import sys, pandas as pd
s = pd.read_csv(sys.argv[1])
cols = ["cohort", "tool", "n_complexes", "n_excluded", "success_pct", "success_ci95_lower", "success_ci95_upper", "posebusters_pass_pct", "mean_rmsd"]
s[["success_ci95_lower", "success_ci95_upper"]] *= 100
print(s[cols].round(1).to_string(index=False))
EOF
  log "done: results/external_baselines/"
fi
