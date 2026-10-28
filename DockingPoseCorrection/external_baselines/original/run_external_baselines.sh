#!/usr/bin/env bash
# Restart-safe inference driver.  It never changes frozen Milestone outputs.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_external_baselines.sh --stage prepare|equibind|diffdock|collect|progress \
    --manifest PATH --m2-output-dir PATH --workspace PATH [options]

Required for GPU stages:
  --equibind-python PATH     Python from the compatible EquiBind environment
  --diffdock-python PATH     Python from the compatible DiffDock environment

Options:
  --bundle-root PATH         Defaults to this script's parent directory
  --shards N                 Defaults to 20; changing it requires --force-inputs
  --force-inputs             Rebuild only generated input files
  --protein-mode symlink|copy  Defaults to symlink
  --vendor-root PATH         Defaults to WORKSPACE/vendor
  --diffdock-model-zip URL_OR_FILE  Defaults to the pinned official release URL
EOF
}

stage=""
bundle_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest=""
m2_output=""
workspace=""
equibind_python=""
diffdock_python=""
vendor_root=""
shards=20
force_inputs=0
protein_mode=symlink
model_zip="https://github.com/gcorso/DiffDock/releases/download/v1.1/diffdock_models.zip"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage) stage="$2"; shift 2;;
    --bundle-root) bundle_root="$2"; shift 2;;
    --manifest) manifest="$2"; shift 2;;
    --m2-output-dir) m2_output="$2"; shift 2;;
    --workspace) workspace="$2"; shift 2;;
    --equibind-python) equibind_python="$2"; shift 2;;
    --diffdock-python) diffdock_python="$2"; shift 2;;
    --vendor-root) vendor_root="$2"; shift 2;;
    --shards) shards="$2"; shift 2;;
    --force-inputs) force_inputs=1; shift;;
    --protein-mode) protein_mode="$2"; shift 2;;
    --diffdock-model-zip) model_zip="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2;;
  esac
done

[[ -n "$stage" && -n "$manifest" && -n "$m2_output" && -n "$workspace" ]] || { usage >&2; exit 2; }
[[ "$stage" =~ ^(prepare|equibind|diffdock|collect|progress)$ ]] || { echo "Invalid --stage: $stage" >&2; exit 2; }
[[ "$protein_mode" =~ ^(symlink|copy)$ ]] || { echo "Invalid --protein-mode: $protein_mode" >&2; exit 2; }

bundle_root="$(cd "$bundle_root" && pwd)"
workspace="$(mkdir -p "$workspace" && cd "$workspace" && pwd)"
manifest="$(cd "$(dirname "$manifest")" && pwd)/$(basename "$manifest")"
m2_output="$(cd "$m2_output" && pwd)"
vendor_root="${vendor_root:-$workspace/vendor}"
inputs="$workspace/inputs"
raw="$workspace/raw_inference"
predictions="$workspace/predictions"
logs="$workspace/logs"
runner_python="${RUNNER_PYTHON:-python3}"
export PYTHONPATH="$bundle_root/scripts${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

prepare_inputs() {
  local extra=()
  [[ "$force_inputs" -eq 1 ]] && extra+=(--force)
  "$runner_python" "$bundle_root/scripts/prepare_external_baseline_inputs.py" \
    --manifest "$manifest" --m2-output-dir "$m2_output" --output-dir "$inputs" \
    --shards "$shards" --protein-mode "$protein_mode" "${extra[@]}"
}

ensure_repository() {
  local name="$1" url="$2" commit="$3" target="$4"
  if [[ ! -d "$target/.git" ]]; then
    mkdir -p "$(dirname "$target")"
    git clone "$url" "$target"
  fi
  git -C "$target" fetch --tags origin
  git -C "$target" checkout --detach "$commit"
  [[ "$(git -C "$target" rev-parse HEAD)" == "$commit" ]] || { echo "$name commit verification failed" >&2; exit 1; }
}

ensure_equibind() {
  [[ -n "$equibind_python" && -x "$equibind_python" ]] || { echo "--equibind-python is required for EquiBind" >&2; exit 2; }
  local dir="$vendor_root/EquiBind"
  ensure_repository EquiBind https://github.com/HannesStark/EquiBind.git 4cb1b4c562dae914780154518a6b915bb4cba658 "$dir"
  local patch="$bundle_root/patches/equibind_deterministic_listing.patch"
  if grep -Fq 'names = os.listdir(args.inference_path)' "$dir/inference.py"; then
    git -C "$dir" apply "$patch"
  fi
  grep -Fq 'names = sorted(os.listdir(args.inference_path))' "$dir/inference.py" || { echo "EquiBind ordering patch is absent" >&2; exit 1; }
  [[ "$("$runner_python" -c "import hashlib; p='$dir/runs/flexible_self_docking/best_checkpoint.pt'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())")" == "eedf3daf1479244e00a1f5c6951cda8d874482c676cb2e21311557ab72d93559" ]] || { echo "EquiBind checkpoint hash verification failed" >&2; exit 1; }
}

ensure_diffdock() {
  [[ -n "$diffdock_python" && -x "$diffdock_python" ]] || { echo "--diffdock-python is required for DiffDock" >&2; exit 2; }
  local dir="$vendor_root/DiffDock"
  ensure_repository DiffDock https://github.com/gcorso/DiffDock.git 85c49b60d3e0b0182a59ee43a34a6d7036981284 "$dir"
  if [[ ! -d "$dir/workdir/v1.1/score_model" || ! -d "$dir/workdir/v1.1/confidence_model" ]]; then
    local archive="$workspace/models/diffdock_models.zip"
    mkdir -p "$(dirname "$archive")"
    if [[ -f "$model_zip" ]]; then cp -f "$model_zip" "$archive"; fi
    if [[ ! -s "$archive" ]]; then curl --fail --location --retry 3 --progress-bar --output "$archive" "$model_zip"; fi
    unzip -q -o "$archive" -d "$dir"
  fi
  [[ -d "$dir/workdir/v1.1/score_model" && -d "$dir/workdir/v1.1/confidence_model" ]] || { echo "DiffDock model extraction did not create expected workdir/v1.1 models" >&2; exit 1; }
}

record_inference_metadata() {
  local tool="$1" source_dir="$2" checkpoint="$3" model_dir="$4" model_archive="$5" steps="$6" samples="$7"
  local metadata="$workspace/${tool}_inference_metadata.json"
  local checkpoint_arg=()
  local model_arg=()
  local archive_arg=()
  local steps_arg=()
  local samples_arg=()
  [[ -n "$checkpoint" ]] && checkpoint_arg=(--checkpoint "$checkpoint")
  [[ -n "$model_dir" ]] && model_arg=(--model-dir "$model_dir")
  [[ -n "$model_archive" ]] && archive_arg=(--model-archive "$model_archive")
  [[ -n "$steps" ]] && steps_arg=(--inference-steps "$steps")
  [[ -n "$samples" ]] && samples_arg=(--samples-per-complex "$samples")
  "$runner_python" "$bundle_root/scripts/write_inference_metadata.py" \
    --output "$metadata" --tool "$tool" --source-dir "$source_dir" \
    "${checkpoint_arg[@]}" "${model_arg[@]}" "${archive_arg[@]}" --manifest-sha256 "$("$runner_python" -c "from common import verify_manifest; from pathlib import Path; print(verify_manifest(Path('$manifest')))" )" \
    --inputs-dir "$inputs" --raw-output-dir "$raw" --seed 20260827 \
    "${steps_arg[@]}" "${samples_arg[@]}"
}

run_equibind() {
  ensure_equibind
  record_inference_metadata equibind "$vendor_root/EquiBind" "$vendor_root/EquiBind/runs/flexible_self_docking/best_checkpoint.pt" "" "" "" "1"
  local dir="$vendor_root/EquiBind" failed=0
  for split in test external; do
    for shard_dir in "$inputs/shards/$split"/shard_*; do
      [[ -d "$shard_dir" ]] || continue
      local shard
      shard="$(basename "$shard_dir")"
      local output="$raw/equibind/$split/$shard"
      local status="$raw/equibind/$split/$shard.status.json"
      if "$runner_python" "$bundle_root/scripts/inference_shard_status.py" --tool equibind --input-shard "$shard_dir" --raw-output-shard "$output" --quiet; then
        echo "EquiBind $split/$shard already complete"
        continue
      fi
      mkdir -p "$(dirname "$output")" "$logs/equibind/$split"
      # EquiBind enumerates every directory entry in --inference_path and
      # therefore cannot receive the CSV metadata files that share the
      # DiffDock shard directory.  Build a clean, symlink-only view.
      local equibind_input="$inputs/equibind_shards/$split/$shard"
      mkdir -p "$equibind_input"
      for complex_dir in "$shard_dir"/*; do
        [[ -d "$complex_dir" ]] || continue
        local complex_name="$(basename "$complex_dir")" link="$equibind_input/$(basename "$complex_dir")"
        if [[ -L "$link" ]]; then
          [[ "$(readlink "$link")" == "$complex_dir" ]] || { echo "unexpected EquiBind shard link: $link" >&2; exit 1; }
        elif [[ -e "$link" ]]; then
          echo "unexpected EquiBind shard entry: $link" >&2; exit 1
        else
          ln -s "$complex_dir" "$link"
        fi
      done
      echo "EquiBind $split/$shard: running $(wc -l < "$shard_dir/complexes.csv") CSV lines"
      if ! (cd "$dir" && CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" "$equibind_python" inference.py \
          --config configs_clean/inference.yml --inference_path "$equibind_input" --output_directory "$output" \
          --use_rdkit_coords --seed 20260827) 2>&1 | tee "$logs/equibind/$split/$shard.log"; then
        failed=1
      fi
      "$runner_python" "$bundle_root/scripts/inference_shard_status.py" --tool equibind --input-shard "$shard_dir" --raw-output-shard "$output" --status-file "$status" || failed=1
    done
  done
  return "$failed"
}

run_diffdock() {
  ensure_diffdock
  record_inference_metadata diffdock "$vendor_root/DiffDock" "" "$vendor_root/DiffDock/workdir/v1.1/score_model" "$workspace/models/diffdock_models.zip" "20" "40"
  local dir="$vendor_root/DiffDock" failed=0
  for split in test external; do
    for shard_dir in "$inputs/shards/$split"/shard_*; do
      [[ -d "$shard_dir" ]] || continue
      local shard="$(basename "$shard_dir")" output="$raw/diffdock/$split/$shard" status="$raw/diffdock/$split/$shard.status.json"
      if "$runner_python" "$bundle_root/scripts/inference_shard_status.py" --tool diffdock --input-shard "$shard_dir" --raw-output-shard "$output" --quiet; then
        echo "DiffDock $split/$shard already complete"
        continue
      fi
      mkdir -p "$(dirname "$output")" "$logs/diffdock/$split"
      echo "DiffDock $split/$shard: running rank-1 selection from 40 generated samples per complex"
      if ! (cd "$dir" && CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" "$diffdock_python" "$bundle_root/scripts/run_diffdock_seeded.py" \
          --diffdock-root "$dir" --seed 20260827 --config "$bundle_root/diffdock_external_inference.yaml" \
          --protein_ligand_csv "$shard_dir/diffdock_inputs.csv" --out_dir "$output" \
          --model_dir "$dir/workdir/v1.1/score_model" --confidence_model_dir "$dir/workdir/v1.1/confidence_model" \
          --inference_steps 20 --samples_per_complex 40 --batch_size 10 --loglevel INFO) 2>&1 | tee "$logs/diffdock/$split/$shard.log"; then
        failed=1
      fi
      "$runner_python" "$bundle_root/scripts/inference_shard_status.py" --tool diffdock --input-shard "$shard_dir" --raw-output-shard "$output" --status-file "$status" || failed=1
    done
  done
  return "$failed"
}

case "$stage" in
  prepare) prepare_inputs ;;
  equibind) prepare_inputs; run_equibind; "$runner_python" "$bundle_root/scripts/progress_external_baselines.py" --inputs-dir "$inputs" --raw-output-dir "$raw" --output-dir "$workspace" ;;
  diffdock) prepare_inputs; run_diffdock; "$runner_python" "$bundle_root/scripts/progress_external_baselines.py" --inputs-dir "$inputs" --raw-output-dir "$raw" --output-dir "$workspace" ;;
  collect) "$runner_python" "$bundle_root/scripts/collect_predictions.py" --inputs-dir "$inputs" --raw-output-dir "$raw" --output-dir "$predictions" ;;
  progress) "$runner_python" "$bundle_root/scripts/progress_external_baselines.py" --inputs-dir "$inputs" --raw-output-dir "$raw" --output-dir "$workspace" ;;
esac
