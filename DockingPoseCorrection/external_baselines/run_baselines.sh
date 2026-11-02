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

# One complex that crashes a tool stops its whole shard, and the original runner then stops the stage. Here a
# stage with failures continues; afterwards every complex left without a prediction is retried on its own, and a
# complex that fails again is recorded as a docking failure (a .failed marker; it is scored as a failure).
retry_missing() {
  local tool="$1" n=0 failed=0
  while IFS=$'\t' read -r split shard cid input raw; do
    n=$((n + 1))
    mkdir -p "$raw" "$ws/logs/$tool/retry"
    if [[ "$tool" == equibind ]]; then
      (cd "$ws/vendor/EquiBind" && "$equibind_python" inference.py --config configs_clean/inference.yml \
          --inference_path "$input" --output_directory "$raw" --use_rdkit_coords --seed 20260827) \
          > "$ws/logs/$tool/retry/$cid.log" 2>&1 || true
      out="$raw/$cid/lig_equibind_corrected.sdf"
    else
      local dd="$ws/vendor/DiffDock"
      (cd "$dd" && "$diffdock_python" "$here/scripts/run_diffdock_seeded.py" --diffdock-root "$dd" --seed 20260827 \
          --config "$here/diffdock_external_inference.yaml" --protein_ligand_csv "$input" --out_dir "$raw" \
          --model_dir "$dd/workdir/v1.1/score_model" --confidence_model_dir "$dd/workdir/v1.1/confidence_model" \
          --inference_steps 20 --samples_per_complex 40 --batch_size 10 --loglevel INFO) \
          > "$ws/logs/$tool/retry/$cid.log" 2>&1 || true
      out="$raw/$cid/rank1.sdf"
    fi
    if [[ -s "$out" ]]; then
      log "   $tool $split/$cid: done on retry"
    else
      touch "$raw/$cid.failed"; failed=$((failed + 1))
      log "   $tool $split/$cid: $tool cannot dock this complex (log: logs/$tool/retry/$cid.log); recorded as a failure"
    fi
  done < <(python3 "$here/scripts/retry_missing.py" --tool "$tool" --workspace "$ws")
  [[ $n -gt 0 ]] && log "   $tool retries: $((n - failed)) of $n complexes docked on their own, $failed recorded as failures"
  return 0
}

if has equibind; then
  log "EquiBind (CPU)"
  bash "$here/bin/run_external_baselines.sh" --stage equibind "${common[@]}" --equibind-python "$equibind_python" \
    || log "   some EquiBind shards are incomplete; retrying their missing complexes one at a time"
  retry_missing equibind
fi
if has diffdock; then
  log "DiffDock (GPU, 40 samples x 20 steps per complex)"
  bash "$here/bin/run_external_baselines.sh" --stage diffdock "${common[@]}" --diffdock-python "$diffdock_python" \
    || log "   some DiffDock shards are incomplete; retrying their missing complexes one at a time"
  retry_missing diffdock
fi

if has score; then
  log "collect, score (22 PoseBusters checks), aggregate, validate"
  # complexes a tool could not dock have no prediction; they are scored as failures, not dropped silently
  python3 "$here/scripts/collect_predictions.py" --inputs-dir "$ws/inputs" --raw-output-dir "$ws/raw_inference" \
      --output-dir "$ws/predictions" --allow-incomplete
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
