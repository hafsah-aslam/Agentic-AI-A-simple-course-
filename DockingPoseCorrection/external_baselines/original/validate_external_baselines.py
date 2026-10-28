#!/usr/bin/env python3
"""Strict contract validation for external-baseline inference and reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common import EXPECTED_COMPLEX_COUNTS, MANIFEST_SHA256, atomic_json, require, sha256


VALIDATOR_VERSION = "external-baseline-validator-v1"
TOOLS = ("equibind", "diffdock")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--scores-csv", type=Path, required=True)
    parser.add_argument("--summary-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-exclusions", action="store_true", help="diagnostic only; final publication validation should omit this")
    return parser.parse_args()


def check(condition: bool, name: str, details: Any, failures: list[dict[str, Any]]) -> None:
    if not condition:
        failures.append({"name": name, "details": details})


def main() -> int:
    args = parse_args()
    failures: list[dict[str, Any]] = []
    manifest = args.manifest.resolve()
    check(manifest.is_file(), "manifest_exists", str(manifest), failures)
    if manifest.is_file():
        check(sha256(manifest) == MANIFEST_SHA256, "manifest_sha256", sha256(manifest), failures)
    inputs = args.inputs_dir.resolve()
    inventory_path = inputs / "cohort_inventory.csv"
    check(inventory_path.is_file(), "input_inventory_exists", str(inventory_path), failures)
    inventory = pd.read_csv(inventory_path, dtype={"split": str, "complex_id": str}) if inventory_path.is_file() else pd.DataFrame()
    if len(inventory):
        observed = inventory.groupby("split")["complex_id"].nunique().to_dict()
        check(observed == EXPECTED_COMPLEX_COUNTS, "input_cohort_counts", observed, failures)
        check(not inventory.duplicated(["split", "complex_id"]).any(), "input_membership_unique", "duplicate split/complex_id", failures)
        check(inventory["heavy_atom_maps_bijective"].astype(bool).all(), "input_atom_maps_bijective", "at least one false", failures)
    predictions = args.predictions_dir.resolve()
    prediction_inventory_path = predictions / "prediction_inventory.csv"
    check(prediction_inventory_path.is_file(), "prediction_inventory_exists", str(prediction_inventory_path), failures)
    prediction_inventory = pd.read_csv(prediction_inventory_path, dtype={"tool": str, "split": str, "complex_id": str}) if prediction_inventory_path.is_file() else pd.DataFrame()
    if len(prediction_inventory):
        check(len(prediction_inventory) == 2 * sum(EXPECTED_COMPLEX_COUNTS.values()), "prediction_inventory_row_count", len(prediction_inventory), failures)
        for tool in TOOLS:
            for split, expected in EXPECTED_COMPLEX_COUNTS.items():
                subset = prediction_inventory.loc[(prediction_inventory["tool"] == tool) & (prediction_inventory["split"] == split)]
                check(len(subset) == expected, f"prediction_inventory_count_{tool}_{split}", len(subset), failures)
                check((subset["status"] == "collected").all(), f"prediction_inventory_complete_{tool}_{split}", subset["status"].value_counts().to_dict(), failures)
                for path in subset["rank1_prediction"].tolist():
                    check(Path(path).is_file() and Path(path).stat().st_size > 0, f"prediction_file_{tool}_{split}", path, failures)
    scores_path = args.scores_csv.resolve()
    check(scores_path.is_file(), "scores_exists", str(scores_path), failures)
    scores = pd.read_csv(scores_path, dtype={"tool": str, "split": str, "complex_id": str}) if scores_path.is_file() else pd.DataFrame()
    if len(scores):
        check(len(scores) == 2 * sum(EXPECTED_COMPLEX_COUNTS.values()), "scores_row_count", len(scores), failures)
        check(not scores.duplicated(["tool", "split", "complex_id"]).any(), "scores_unique_keys", "duplicate key", failures)
        check(set(scores["tool"]) == set(TOOLS), "scores_tools", sorted(scores["tool"].unique()), failures)
        completed = scores.loc[scores["status"] == "completed"]
        check(len(completed) == len(scores) or args.allow_exclusions, "scores_no_exclusions", int(len(scores) - len(completed)), failures)
        check(completed["mapping_bijective"].astype(bool).all(), "scores_mapping_bijective", "at least one false", failures)
        check(set(completed["mapping_method"]).issubset({"atom_map", "topology_graph_isomorphism"}), "scores_mapping_method", sorted(completed["mapping_method"].dropna().unique()), failures)
        check((completed["n_atoms"].to_numpy(dtype=float) > 0).all(), "scores_positive_atom_counts", "non-positive value", failures)
        for column in ("msd", "rmsd"):
            check(np.isfinite(completed[column].to_numpy(dtype=float)).all(), f"scores_finite_{column}", "non-finite value", failures)
            check((completed[column].to_numpy(dtype=float) >= 0).all(), f"scores_nonnegative_{column}", "negative value", failures)
        check((completed["posebusters_check_count"].astype(int) == 22).all(), "scores_posebusters_check_count", completed["posebusters_check_count"].value_counts().to_dict(), failures)
        check(completed["posebusters_checks_reported"].astype(int).between(0, 22).all(), "scores_reported_check_range", "out of range", failures)
    summary_path = args.summary_csv.resolve()
    check(summary_path.is_file(), "summary_exists", str(summary_path), failures)
    summary = pd.read_csv(summary_path) if summary_path.is_file() else pd.DataFrame()
    if len(summary):
        check(len(summary) == 10, "summary_row_count", len(summary), failures)
        check(set(summary["cohort"]) == set(EXPECTED_COMPLEX_COUNTS), sorted(summary["cohort"].unique()), failures)
        check(set(summary["tool"]) == {"vina_baseline", "equibind", "diffdock", "ungated_corrected", "gated_corrected"}, sorted(summary["tool"].unique()), failures)
        for row in summary.itertuples(index=False):
            expected = EXPECTED_COMPLEX_COUNTS.get(row.cohort)
            if expected is not None and row.tool in {"equibind", "diffdock"}:
                check(int(row.n_complexes) == expected or args.allow_exclusions, f"summary_count_{row.tool}_{row.cohort}", int(row.n_complexes), failures)
        for column in ("mean_msd", "mean_rmsd", "success_pct", "success_ci95_lower", "success_ci95_upper"):
            if column in summary:
                check(np.isfinite(summary[column].dropna().to_numpy(dtype=float)).all(), f"summary_finite_{column}", "non-finite value", failures)
    report = {
        "validator_version": VALIDATOR_VERSION,
        "manifest_sha256": MANIFEST_SHA256,
        "scores_sha256": sha256(scores_path) if scores_path.is_file() else None,
        "summary_sha256": sha256(summary_path) if summary_path.is_file() else None,
        "allow_exclusions": bool(args.allow_exclusions),
        "checks_passed": len(failures) == 0,
        "failures": failures,
    }
    atomic_json(args.output.resolve(), report)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 3


if __name__ == "__main__":
    raise SystemExit(main())
