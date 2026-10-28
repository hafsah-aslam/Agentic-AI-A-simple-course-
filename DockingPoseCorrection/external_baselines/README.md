# External docking baselines (EquiBind, DiffDock) with the original study's code

The original study compared Vina, the ungated and gated corrections against EquiBind and DiffDock on the internal
test and PoseBusters cohorts. This folder runs that comparison on the reproduction's cohorts. It uses the original
bundle's own scripts, the same pinned tool versions and the same seeds and settings:

| | Setting |
|---|---|
| EquiBind | commit `4cb1b4c`, checkpoint `runs/flexible_self_docking/best_checkpoint.pt` (SHA-256 checked), `--use_rdkit_coords`, seed 20260827 |
| DiffDock | commit `85c49b6`, v1.1 models, 20 inference steps, 40 samples per complex, rank-1 pose, seed 20260827 |
| Input ligand | graph only: a fresh ETKDGv3 + MMFF conformer (seed 20260827) carrying atom-map numbers, never crystal coordinates |
| Scoring | heavy-atom atom-map match (graph-isomorphism fallback), RMSD without superposition, success < 2 Å, 22 PoseBusters dock checks |
| Statistics | complex-level percentile bootstrap, 10,000 resamples, seed 0 |

## Run it (on the computer that made the run)

```bash
cd ~/DockingPoseCorrection && source ~/dpc/bin/activate
bash external_baselines/setup_envs.sh                       # once: two conda environments, about 6-8 GB of downloads
bash external_baselines/run_baselines.sh --work ~/dpc_work  # restart-safe: rerun the same command after any stop
```

The result table is printed at the end and copied to `results/external_baselines/`. On an i9-13900 with an
RTX 4080, expect EquiBind (CPU) to take well under an hour and DiffDock (GPU) a few hours for the 828 complexes.

## Folder layout

| Path | What it is |
|---|---|
| `original/` | the original bundle files, byte for byte, for reference |
| `scripts/`, `bin/` | the same files with the minimal changes listed below |
| `scripts/bridge_from_dpc.py` | new: writes the reproduction's cohort, reference poses, per-complex evaluation and PoseBusters results in the layout the original scripts read |
| `compare_with_original.py` | new: per-complex comparison of a run with the original study's frozen `manifest.csv` and `per_complex_evaluation.csv` |
| `patches/`, `diffdock_external_inference.yaml` | reconstructed (see below) |
| `envs/` | conda environments for EquiBind (CPU) and DiffDock (GPU) |

## Changes to the original scripts

The change that adapts the scripts to the reproduction:

- `common.py`: if `DPC_BRIDGE` is set, the frozen manifest hash, exclusion-list hash and cohort counts come from
  `bridge.json` instead of the original constants. Nothing else in the module changed.
- `aggregate_external_baselines.py`: the gate threshold, hard-coded as 1.3671 (the original model's τ), is read
  from `DPC_GATE_TAU`; the driver sets it to the reproduction's τ. The default is unchanged.

Seven defects in the original bundle were fixed, each with a one-line change. Six of them stop a stage before it
finishes, so the scripts could not have run to the end as supplied:

| File | Defect | Effect | Fix |
|---|---|---|---|
| `run_external_baselines.sh` (DiffDock stage) | `local shard=… output=…/$shard` on one line | `set -u` aborts with "shard: unbound variable" on the first shard (already fixed for EquiBind in one of the two supplied copies) | split into separate lines |
| `collect_predictions.py` | metadata counts keyed by `(tool, split)` tuples | `json.dumps` fails after the inventory is written, so the stage exits with an error | keys written as `"tool/split"` |
| `score_external_baselines.py` | graph-isomorphism fallback unpacks 3 values; `match_reference_pose` returns 4 | every pose without atom-map labels is excluded | unpack 4 values |
| `score_external_baselines.py` | exclusion list selects `scoring_exclusion_reason`, which exists only if something was excluded | a run with no exclusions crashes at the last step | `reindex` the columns |
| `aggregate_external_baselines.py` | placeholder `posebusters_valid` column kept before merging the real one | pandas renames both (`_x`/`_y`) and the Vina row raises `KeyError` whenever PoseBusters results are supplied | drop the placeholder before the merge |
| `sanity_check_external_baselines.py` | same 3-value unpack | fallback matching always reported as failed | unpack 4 values |
| `validate_external_baselines.py` | two `check()` calls without their name argument | the validator crashes with `TypeError` | add the names |

Two files referenced by the runner were not in the bundle and are reconstructed:

- `patches/equibind_deterministic_listing.patch`: the one-line change the runner checks for
  (`names = sorted(os.listdir(args.inference_path))`).
- `diffdock_external_inference.yaml`: DiffDock's own `default_inference_args.yaml` at the pinned commit, with
  `samples_per_complex: 40`. The runner also passes steps, samples and batch size on the command line.

## Checks done without the GPU

The full chain (prepare, collect, score, aggregate, sanity check, validate) was run on the reported reproduction
with Vina poses and generated conformers standing in for EquiBind and DiffDock outputs:

- The original scorer gives RMSDs identical to the reproduction's own baseline RMSD (largest difference 3e-7 Å).
- The original aggregator reproduces the reproduction's Vina, ungated and gated success and PoseBusters pass rates exactly.

EquiBind and DiffDock themselves were not run here (no GPU), so the environment setup has not been tested on the
target computer.
