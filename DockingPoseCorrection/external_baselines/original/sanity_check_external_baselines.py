#!/usr/bin/env python3
"""Spot-check flagged external poses and persist geometry diagnostics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rdkit import Chem

from canonical_matching import match_reference_pose
from common import atomic_json, require, sha256


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores-csv", type=Path, required=True)
    parser.add_argument("--m2-output-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-flagged", type=int, default=10)
    return parser.parse_args()


def molecule(path: Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), sanitize=False, removeHs=False)
    values = [item for item in supplier if item is not None]
    require(len(values) == 1, f"expected one molecule in {path}")
    return values[0]


def geometry(mol: Chem.Mol) -> dict[str, Any]:
    conf = mol.GetConformer()
    coordinates = np.asarray(conf.GetPositions(), dtype=np.float64)
    bond_lengths: list[float] = []
    for bond in mol.GetBonds():
        a, b = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        bond_lengths.append(float(np.linalg.norm(coordinates[a] - coordinates[b])))
    angles: list[float] = []
    for center in mol.GetAtoms():
        c = center.GetIdx()
        neighbors = [neighbor.GetIdx() for neighbor in center.GetNeighbors()]
        for i, left in enumerate(neighbors):
            for right in neighbors[i + 1:]:
                first = coordinates[left] - coordinates[c]
                second = coordinates[right] - coordinates[c]
                denominator = np.linalg.norm(first) * np.linalg.norm(second)
                if denominator == 0:
                    continue
                cosine = float(np.clip(np.dot(first, second) / denominator, -1.0, 1.0))
                angles.append(float(math.degrees(math.acos(cosine))))
    def summary(values: list[float]) -> dict[str, Any]:
        if not values:
            return {"count": 0, "min": None, "median": None, "max": None}
        return {"count": len(values), "min": float(np.min(values)), "median": float(np.median(values)), "max": float(np.max(values))}
    return {"bond_lengths_angstrom": summary(bond_lengths), "bond_angles_degrees": summary(angles)}


def main() -> int:
    args = parse_args()
    require(args.n_flagged > 0, "--n-flagged must be positive")
    scores_path = args.scores_csv.resolve()
    scores = pd.read_csv(scores_path, dtype={"tool": str, "split": str, "complex_id": str})
    require({"tool", "split", "complex_id", "status", "posebusters_valid", "mapping_bijective"} <= set(scores.columns), "scores CSV lacks sanity-check columns")
    flagged = scores.loc[(scores["status"] == "completed") & (~scores["posebusters_valid"].astype(str).str.lower().isin({"true", "1"}))].sort_values(["tool", "split", "complex_id"]).head(args.n_flagged)
    records: list[dict[str, Any]] = []
    for row in flagged.itertuples(index=False):
        prediction = Path(row.prediction_path)
        complex_dir = args.m2_output_dir.resolve() / "complexes" / row.split / row.complex_id
        predicted = molecule(prediction)
        reference = molecule(complex_dir / "reference_pose.sdf")
        try:
            _predicted, _reference, matching = match_reference_pose(reference, predicted)
            fallback_match = {"fallback_mapping_bijective": True, "fallback_isomorphisms_considered": matching.get("isomorphisms_considered", 0)}
        except Exception as error:
            fallback_match = {"fallback_mapping_bijective": False, "fallback_mapping_error": f"{type(error).__name__}: {error}"}
        record = {"tool": row.tool, "split": row.split, "complex_id": row.complex_id, "prediction_sha256": sha256(prediction), "mapping_bijective": bool(row.mapping_bijective), "geometry": geometry(predicted), **fallback_match}
        print(f"{row.tool}/{row.split}/{row.complex_id}: bonds={record['geometry']['bond_lengths_angstrom']} angles={record['geometry']['bond_angles_degrees']}", flush=True)
        records.append(record)
    report = {
        "sanity_check_version": "external-baseline-sanity-v1",
        "scores_sha256": sha256(scores_path),
        "requested_flagged": args.n_flagged,
        "flagged_records": records,
        "all_scored_mappings_bijective": bool(scores.loc[scores["status"] == "completed", "mapping_bijective"].astype(str).str.lower().isin({"true", "1"}).all()),
        "interpretation": "Geometry ranges are diagnostic spot-checks of de-novo outputs flagged by PoseBusters; they do not alter validity labels or force repairs.",
    }
    atomic_json(args.output.resolve(), report)
    print(f"Wrote {len(records)} flagged-pose diagnostics to {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
