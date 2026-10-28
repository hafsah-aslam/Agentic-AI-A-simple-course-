#!/usr/bin/env python3
"""Aggregate external-baseline scores with deterministic complex bootstrap CIs."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    EXPECTED_COMPLEX_COUNTS,
    MANIFEST_SHA256,
    atomic_csv,
    atomic_json,
    environment_metadata,
    require,
    sha256,
)


AGGREGATOR_VERSION = "external-baseline-aggregator-v1"
TOOLS = ("vina_baseline", "equibind", "diffdock")
CHECK_PREFIX = "pb_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--scores-csv", type=Path, required=True)
    parser.add_argument("--m6-evaluation", type=Path, required=True, help="frozen per_complex_evaluation.csv for the Vina comparison row")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frozen-posebusters-results", type=Path, default=None, help="optional repaired/frozen PoseBusters full-results CSV (baseline, ungated, gated)")
    parser.add_argument("--baseline-posebusters-results", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--bootstrap-resamples", type=int, default=BOOTSTRAP_RESAMPLES)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    return parser.parse_args()


def bootstrap(values: np.ndarray, n: int, seed: int) -> tuple[float, float, float]:
    require(values.ndim == 1 and len(values) > 0 and np.isfinite(values).all(), "bootstrap values must be finite and non-empty")
    rng = np.random.default_rng(seed)
    draws = np.empty(n, dtype=np.float64)
    for index in range(n):
        draws[index] = float(np.mean(values[rng.integers(0, len(values), size=len(values))]))
    return float(np.mean(values)), float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def parse_bool_series(series: pd.Series, name: str) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    require(normalized.isin({"true", "false", "1", "0"}).all(), f"{name} contains non-boolean values")
    return normalized.isin({"true", "1"})


def read_m6(path: Path) -> pd.DataFrame:
    require(path.is_file(), f"frozen M6 evaluation is missing: {path}")
    frame = pd.read_csv(path, dtype={"complex_id": str, "split": str})
    required = {"complex_id", "split", "baseline_msd", "baseline_rmsd", "baseline_success"}
    require(required <= set(frame.columns), f"M6 evaluation lacks columns: {sorted(required - set(frame.columns))}")
    frame = frame.loc[frame["split"].isin(EXPECTED_COMPLEX_COUNTS)].copy()
    # The baseline is identical across the five model seeds.  Verify that
    # invariant before collapsing to one row per complex.
    collapsed = frame.sort_values(["split", "complex_id", "seed"]).drop_duplicates(["split", "complex_id"]).copy()
    for column in ("baseline_msd", "baseline_rmsd", "baseline_success"):
        counts = frame.groupby(["split", "complex_id"])[column].nunique(dropna=False)
        require((counts <= 1).all(), f"M6 baseline column varies across seeds: {column}")
    require(collapsed.groupby("split")["complex_id"].nunique().to_dict() == EXPECTED_COMPLEX_COUNTS, "M6 baseline cohort counts differ")
    return collapsed


def optional_posebusters(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    require(path.is_file(), f"Vina PoseBusters results are missing: {path}")
    frame = pd.read_csv(path, dtype={"complex_id": str, "split": str})
    require({"complex_id", "split", "baseline_valid"} <= set(frame.columns), "PoseBusters results lack baseline_valid")
    return frame


def summary_row(tool: str, split: str, frame: pd.DataFrame, n_excluded: int, n_bootstrap: int, seed: int, pb_column: str | None, *, seed_count: int = 1, aggregation_unit: str = "complex") -> dict[str, Any]:
    values = frame
    row: dict[str, Any] = {
        "cohort": split,
        "tool": tool,
        "method": tool,
        "condition": "baseline" if tool == "vina_baseline" else "de_novo_docking",
        "n_complexes": int(len(values)),
        "n_seed_rows": int(values.attrs.get("n_seed_rows", len(values))),
        "seed_count": int(seed_count),
        "aggregation_unit": aggregation_unit,
        "n_excluded": int(n_excluded),
        "bootstrap_resamples": int(n_bootstrap),
        "bootstrap_seed": int(seed),
        "ci_method": "complex_level_percentile_bootstrap",
        "metric_version": "metrics-v1",
    }
    for metric in ("msd", "rmsd"):
        array = values[metric].to_numpy(dtype=np.float64)
        estimate, lower, upper = bootstrap(array, n_bootstrap, seed + (11 if metric == "msd" else 17))
        row[f"mean_{metric}"] = estimate
        row[f"median_{metric}"] = float(np.median(array))
        row[f"sd_{metric}"] = float(np.std(array, ddof=1)) if len(array) > 1 else 0.0
        row[f"{metric}_ci95_lower"] = lower
        row[f"{metric}_ci95_upper"] = upper
    if "n_atoms" in values.columns:
        weights = values["n_atoms"].to_numpy(dtype=np.float64)
        require(np.isfinite(weights).all() and (weights > 0).all(), "n_atoms must be finite and positive")
        pooled_msd = float(np.average(values["msd"].to_numpy(dtype=np.float64), weights=weights))
        row["pooled_msd"] = pooled_msd
        row["pooled_rmsd"] = math.sqrt(pooled_msd)
    else:
        row["pooled_msd"] = np.nan
        row["pooled_rmsd"] = np.nan
    # ``success`` is boolean for single-run tools and a per-complex fraction
    # for the five-seed correction comparison.  Preserve fractional values;
    # coercing them to bool would turn any partial success into a false 100%.
    success = values["success"].to_numpy(dtype=np.float64)
    estimate, lower, upper = bootstrap(success, n_bootstrap, seed + 23)
    row.update({"success_rate": estimate, "success_pct": 100.0 * estimate, "success_ci95_lower": lower, "success_ci95_upper": upper})
    if pb_column is None:
        row.update({"posebusters_pass_rate": np.nan, "posebusters_pass_pct": np.nan, "posebusters_ci95_lower": np.nan, "posebusters_ci95_upper": np.nan})
    else:
        valid = values[pb_column].to_numpy(dtype=np.float64)
        estimate, lower, upper = bootstrap(valid, n_bootstrap, seed + 29)
        row.update({"posebusters_pass_rate": estimate, "posebusters_pass_pct": 100.0 * estimate, "posebusters_ci95_lower": lower, "posebusters_ci95_upper": upper})
    return row


def main() -> int:
    args = parse_args()
    require(args.bootstrap_resamples > 0, "--bootstrap-resamples must be positive")
    manifest = args.manifest.resolve()
    require(sha256(manifest) == MANIFEST_SHA256, "frozen manifest hash differs")
    score_path = args.scores_csv.resolve()
    scores = pd.read_csv(score_path, dtype={"complex_id": str, "split": str, "tool": str})
    required = {"tool", "split", "complex_id", "status", "msd", "rmsd", "success", "posebusters_valid"}
    require(required <= set(scores.columns), f"score CSV lacks columns: {sorted(required - set(scores.columns))}")
    score_complete = scores.loc[scores["status"] == "completed"].copy()
    score_complete["success"] = parse_bool_series(score_complete["success"], "score success")
    score_complete["posebusters_valid"] = parse_bool_series(score_complete["posebusters_valid"], "score PoseBusters validity")
    m6 = read_m6(args.m6_evaluation.resolve())
    pb_path = args.frozen_posebusters_results or args.baseline_posebusters_results
    vina_pb = optional_posebusters(pb_path.resolve() if pb_path else None)
    summary: list[dict[str, Any]] = []
    for split_index, split in enumerate(EXPECTED_COMPLEX_COUNTS):
        expected_ids = set(m6.loc[m6["split"] == split, "complex_id"])
        for tool_index, tool in enumerate(("equibind", "diffdock")):
            subset = score_complete.loc[(score_complete["split"] == split) & (score_complete["tool"] == tool)].copy()
            require(not subset["complex_id"].duplicated().any(), f"duplicate completed score rows for {tool}/{split}")
            require(set(subset["complex_id"]) <= expected_ids, f"score contains non-frozen IDs for {tool}/{split}")
            excluded = int(len(expected_ids) - len(subset))
            pb_column = "posebusters_valid"
            if len(subset):
                subset.attrs["n_seed_rows"] = len(subset)
                summary.append(summary_row(tool, split, subset, excluded, args.bootstrap_resamples, args.seed + 100 * split_index + tool_index, pb_column))

        # Add the already-frozen Vina, ungated, and gated correction rows.  A
        # complex-level summary first averages the five immutable seed rows;
        # this keeps the external single-run bootstrap and the correction
        # comparison on the same complex denominator.
        m6_split = m6.loc[m6["split"] == split].copy()
        all_m6 = pd.read_csv(args.m6_evaluation.resolve(), dtype={"complex_id": str, "split": str})
        all_m6 = all_m6.loc[all_m6["split"] == split].copy()
        all_m6["gate_applied"] = all_m6["mean_predicted_sigma"].astype(float) <= float(os.environ.get("DPC_GATE_TAU", 1.367134928703308))
        all_m6["gated_msd"] = np.where(all_m6["gate_applied"], all_m6["corrected_msd"], all_m6["baseline_msd"])
        all_m6["gated_rmsd"] = np.where(all_m6["gate_applied"], all_m6["corrected_rmsd"], all_m6["baseline_rmsd"])
        all_m6["gated_success"] = np.where(all_m6["gate_applied"], all_m6["corrected_success"], all_m6["baseline_success"])
        baseline = m6_split[["complex_id", "n_atoms", "baseline_msd", "baseline_rmsd", "baseline_success"]].rename(columns={"baseline_msd": "msd", "baseline_rmsd": "rmsd", "baseline_success": "success"}).copy()
        baseline["success"] = parse_bool_series(baseline["success"], "M6 baseline success")
        baseline["posebusters_valid"] = False
        pb_column = None
        if vina_pb is not None:
            pb_split = vina_pb.loc[vina_pb["split"] == split].copy()
            base_variation = pb_split.groupby("complex_id")["baseline_valid"].nunique(dropna=False)
            require((base_variation <= 1).all(), f"Vina baseline validity varies across seed rows for {split}")
            pb_base = pb_split[["complex_id", "baseline_valid"]].drop_duplicates("complex_id")
            baseline = baseline.drop(columns="posebusters_valid").merge(pb_base.rename(columns={"baseline_valid": "posebusters_valid"}), on="complex_id", how="left")
            require(baseline["posebusters_valid"].notna().all(), f"Vina PoseBusters baseline rows missing for {split}")
            baseline["posebusters_valid"] = parse_bool_series(baseline["posebusters_valid"], "Vina baseline PoseBusters validity")
            pb_column = "posebusters_valid"
        baseline.attrs["n_seed_rows"] = len(all_m6)
        summary.append(summary_row("vina_baseline", split, baseline, 0, args.bootstrap_resamples, args.seed + 300 + split_index, pb_column, seed_count=1))
        for condition, metric_column, rmsd_column, success_column in (("ungated_corrected", "corrected_msd", "corrected_rmsd", "corrected_success"), ("gated_corrected", "gated_msd", "gated_rmsd", "gated_success")):
            grouped = all_m6.groupby("complex_id", as_index=False).agg(n_atoms=("n_atoms", "first"), msd=(metric_column, "mean"), rmsd=(rmsd_column, "mean"), success=(success_column, "mean"))
            grouped["success"] = grouped["success"].astype(float)
            grouped["posebusters_valid"] = False
            pb_column = None
            if vina_pb is not None:
                valid_column = "ungated_corrected_valid" if condition == "ungated_corrected" else "gated_valid"
                require(valid_column in vina_pb.columns, f"frozen PoseBusters results lack {valid_column}")
                pb_split = vina_pb.loc[vina_pb["split"] == split].copy()
                pb_split[valid_column] = parse_bool_series(pb_split[valid_column], f"Vina {valid_column}")
                pb_group = pb_split.groupby("complex_id", as_index=False)[valid_column].mean()
                grouped = grouped.merge(pb_group, on="complex_id", how="left")
                require(grouped[valid_column].notna().all(), f"frozen PoseBusters rows missing for {condition}/{split}")
                grouped["posebusters_valid"] = grouped[valid_column].astype(float)
                pb_column = "posebusters_valid"
            grouped.attrs["n_seed_rows"] = len(all_m6)
            summary.append(summary_row(condition, split, grouped, 0, args.bootstrap_resamples, args.seed + 400 + split_index, pb_column, seed_count=5, aggregation_unit="complex_mean_across_five_seeds"))
    summary_frame = pd.DataFrame(summary).sort_values(["cohort", "tool"]).reset_index(drop=True)
    atomic_csv(args.output_dir / "external_baseline_summary.csv", summary_frame)
    atomic_csv(args.output_dir / "external_baseline_comparison_table.csv", summary_frame)

    failure_rows: list[dict[str, Any]] = []
    # Derive check names from the paired ``pb_<name>_reported`` columns.
    check_columns = sorted(column[3:-len("_reported")] for column in scores.columns if column.startswith("pb_") and column.endswith("_reported"))
    for (tool, split), subset in score_complete.groupby(["tool", "split"], sort=True):
        for check in check_columns:
            value_column = f"pb_{check}"
            if value_column not in subset:
                continue
            failed = int((~subset[value_column].astype(bool)).sum())
            failure_rows.append({"tool": tool, "cohort": split, "failure_mode": check, "n_complexes": int(len(subset)), "n_failed_or_not_evaluated": failed, "failed_or_not_evaluated_pct": 100.0 * failed / len(subset) if len(subset) else np.nan, "n_not_evaluated": int((~subset[f"{value_column}_reported"].astype(bool)).sum())})
    atomic_csv(args.output_dir / "external_baseline_posebusters_failure_modes.csv", pd.DataFrame(failure_rows))
    atomic_json(args.output_dir / "aggregation_metadata.json", {
        "aggregator_version": AGGREGATOR_VERSION,
        "manifest_sha256": MANIFEST_SHA256,
        "scores_sha256": sha256(score_path),
        "m6_evaluation_sha256": sha256(args.m6_evaluation.resolve()),
        "baseline_posebusters_results_sha256": sha256(pb_path.resolve()) if pb_path else None,
        "bootstrap_resamples": args.bootstrap_resamples,
        "bootstrap_seed": args.seed,
        "ci_method": "complex-level percentile bootstrap; seed-level Student-t is not applicable to single-run external baselines",
        "environment": environment_metadata(),
    })
    print(f"Wrote {len(summary_frame)} cohort/tool summary rows and {len(failure_rows)} PoseBusters failure-mode rows", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
