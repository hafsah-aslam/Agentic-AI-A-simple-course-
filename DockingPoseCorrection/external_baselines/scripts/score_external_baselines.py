#!/usr/bin/env python3
"""Score rank-1 EquiBind/DiffDock poses against the frozen reference poses.

The script is deliberately restart-safe.  Each complex is scored into a JSON
cache before the aggregate CSV is written, so an interrupted PoseBusters run
can be resumed without repeating completed complexes.  It never writes into a
Milestone 1/2 directory.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

from canonical_matching import ArtifactError, match_reference_pose
from canonical_metrics import mean_squared_displacement, pose_rmsd
from common import (
    EXPECTED_COMPLEX_COUNTS,
    MANIFEST_SHA256,
    atomic_csv,
    atomic_json,
    environment_metadata,
    read_frozen_cohorts,
    require,
    sha256,
)


SCORER_VERSION = "external-baseline-scorer-v1"
TOOLS = {"equibind": "lig_equibind_corrected.sdf", "diffdock": "rank1.sdf"}
MAPPING_TOLERANCE_ANGSTROM = 0.002
REPAIR_MAX_N_VALENCE = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--m2-output-dir", type=Path, required=True)
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--posebusters-vendor", type=Path, default=None)
    parser.add_argument("--limit-per-split", type=int, default=None, help="diagnostic smoke run only")
    parser.add_argument("--force", action="store_true", help="ignore score cache and rescore")
    return parser.parse_args()


def load_posebusters(vendor: Path | None):
    if vendor is not None:
        vendor = vendor.resolve()
        if (vendor / "posebusters" / "__init__.py").is_file():
            sys.path.insert(0, str(vendor))
        elif (vendor / "__init__.py").is_file() and vendor.name == "posebusters":
            sys.path.insert(0, str(vendor.parent))
        else:
            raise RuntimeError(f"PoseBusters vendor is not a package root: {vendor}")
    import posebusters
    from posebusters import PoseBusters

    return posebusters, PoseBusters


def configured_check_columns(posebusters_module) -> list[str]:
    import yaml

    config_path = Path(posebusters_module.__file__).resolve().parent / "config" / "dock.yml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    columns: list[str] = []
    for module in config["modules"]:
        rename = module.get("rename_outputs", {})
        suffix = module.get("rename_suffix", "")
        for output in module.get("chosen_binary_test_output", []):
            columns.append(rename.get(output, output + suffix).lower().replace(" ", "_"))
    require(len(columns) == len(set(columns)), "PoseBusters check names are not unique")
    require(len(columns) == 22, f"unexpected PoseBusters dock check count: {len(columns)}")
    return columns


def tri_bool(value: Any) -> bool | None:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"", "nan", "na", "none", "<na>"}:
            return None
        if text == "true":
            return True
        if text == "false":
            return False
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        if float(value) == 1.0:
            return True
        if float(value) == 0.0:
            return False
    return None


def read_one_molecule(path: Path, *, sanitize: bool) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), sanitize=sanitize, removeHs=False)
    molecules = [molecule for molecule in supplier if molecule is not None]
    require(len(molecules) == 1, f"expected one molecule in {path}, found {len(molecules)}")
    molecule = molecules[0]
    require(molecule.GetNumConformers() == 1, f"prediction must contain one conformer: {path}")
    return molecule


def neutral_n_repair(path: Path, output_path: Path) -> tuple[Path, dict[str, Any]]:
    """Repair only the previously observed lost-charge representation.

    A repair is permitted only when every detected chemistry problem is a
    neutral nitrogen with explicit valence four.  Ambiguous failures remain
    exclusions and are never coerced through a permissive sanitizer.
    """

    try:
        read_one_molecule(path, sanitize=True)
        return path, {"repair_applied": False, "repair_type": "none", "repair_atoms": []}
    except Exception as original_error:
        raw = read_one_molecule(path, sanitize=False)
        raw.UpdatePropertyCache(strict=False)
        problems = Chem.DetectChemistryProblems(raw)
        repairs: list[int] = []
        for problem in problems:
            if problem.GetType() != "AtomValenceException":
                return path, {
                    "repair_applied": False,
                    "repair_type": "excluded_non_neutral_n_valence",
                    "repair_atoms": [],
                    "original_exception": repr(original_error),
                    "chemistry_problem_types": [item.GetType() for item in problems],
                }
            index = int(problem.GetAtomIdx())
            atom = raw.GetAtomWithIdx(index)
            if atom.GetAtomicNum() != 7 or atom.GetFormalCharge() != 0 or atom.GetExplicitValence() != REPAIR_MAX_N_VALENCE:
                return path, {
                    "repair_applied": False,
                    "repair_type": "excluded_ambiguous_valence",
                    "repair_atoms": [],
                    "original_exception": repr(original_error),
                    "chemistry_problem_types": [item.GetType() for item in problems],
                }
            repairs.append(index)
        require(repairs, f"sanitization failed without a repairable chemistry problem: {path}")
        for index in repairs:
            raw.GetAtomWithIdx(index).SetFormalCharge(1)
        raw.UpdatePropertyCache(strict=False)
        try:
            Chem.SanitizeMol(raw)
        except Exception as repair_error:
            return path, {
                "repair_applied": False,
                "repair_type": "excluded_repair_sanitization_failed",
                "repair_atoms": repairs,
                "original_exception": repr(original_error),
                "repair_exception": repr(repair_error),
            }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".sdf", dir=output_path.parent)
        os.close(fd)
        temporary = Path(name)
        try:
            writer = Chem.SDWriter(str(temporary))
            writer.write(raw)
            writer.close()
            os.replace(temporary, output_path)
        finally:
            temporary.unlink(missing_ok=True)
        return output_path, {
            "repair_applied": True,
            "repair_type": "neutral_n_formal_charge_plus_one",
            "repair_atoms": repairs,
            "original_exception": repr(original_error),
        }


def atom_map_match(reference: Chem.Mol, prediction: Chem.Mol) -> tuple[np.ndarray, np.ndarray, dict[str, Any]] | None:
    ref_heavy = [atom for atom in reference.GetAtoms() if atom.GetAtomicNum() > 1]
    pred_heavy = [atom for atom in prediction.GetAtoms() if atom.GetAtomicNum() > 1]
    expected_maps = {atom.GetIdx() + 1: atom for atom in ref_heavy}
    observed_maps = [atom.GetAtomMapNum() for atom in pred_heavy]
    if len(observed_maps) != len(set(observed_maps)) or set(observed_maps) != set(expected_maps):
        return None
    conformer_ref = reference.GetConformer()
    conformer_pred = prediction.GetConformer()
    ordered_pred: list[np.ndarray] = []
    ordered_ref: list[np.ndarray] = []
    for map_number in sorted(expected_maps):
        ref_atom = expected_maps[map_number]
        pred_atom = next(atom for atom in pred_heavy if atom.GetAtomMapNum() == map_number)
        require(pred_atom.GetAtomicNum() == ref_atom.GetAtomicNum(), f"atom-map element mismatch at map {map_number}")
        rp = conformer_ref.GetAtomPosition(ref_atom.GetIdx())
        pp = conformer_pred.GetAtomPosition(pred_atom.GetIdx())
        ordered_ref.append(np.array([rp.x, rp.y, rp.z], dtype=np.float64))
        ordered_pred.append(np.array([pp.x, pp.y, pp.z], dtype=np.float64))
    return np.vstack(ordered_pred), np.vstack(ordered_ref), {
        "mapping_method": "atom_map",
        "mapping_bijective": True,
        "isomorphisms_considered": 1,
        "mapping_max_distance_angstrom": float(np.max(np.linalg.norm(np.vstack(ordered_pred) - np.vstack(ordered_ref), axis=1))),
    }


def map_coordinates(reference: Chem.Mol, prediction: Chem.Mol) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    mapped = atom_map_match(reference, prediction)
    if mapped is not None:
        return mapped
    predicted, target, _rmsd, details = match_reference_pose(reference, prediction)
    details = dict(details)
    details.update({"mapping_method": "topology_graph_isomorphism", "mapping_bijective": True, "mapping_max_distance_angstrom": float(np.max(np.linalg.norm(predicted - target, axis=1)))})
    return predicted, target, details


def score_one(
    tool: str,
    split: str,
    complex_id: str,
    complex_dir: Path,
    prediction_path: Path,
    checks: list[str],
    buster,
    repaired_dir: Path,
    cache_path: Path,
    force: bool,
) -> dict[str, Any]:
    prediction_hash = sha256(prediction_path)
    if cache_path.is_file() and not force:
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("scorer_version") == SCORER_VERSION and cached.get("prediction_sha256") == prediction_hash:
                return cached
        except (OSError, ValueError):
            pass
    row: dict[str, Any] = {
        "scorer_version": SCORER_VERSION,
        "tool": tool,
        "split": split,
        "complex_id": complex_id,
        "prediction_path": str(prediction_path),
        "prediction_sha256": prediction_hash,
        "reference_pose_sha256": sha256(complex_dir / "reference_pose.sdf"),
        "protein_sha256": sha256(complex_dir / "protein.pdb"),
        "status": "completed",
        "mapping_bijective": False,
        "posebusters_check_count": len(checks),
    }
    try:
        reference = read_one_molecule(complex_dir / "reference_pose.sdf", sanitize=True)
        raw_prediction = read_one_molecule(prediction_path, sanitize=False)
        predicted_coords, reference_coords, mapping = map_coordinates(reference, raw_prediction)
        row.update(mapping)
        row["n_heavy_atoms"] = int(len(reference_coords))
        row["n_atoms"] = int(len(reference_coords))
        row["msd"] = mean_squared_displacement(predicted_coords, reference_coords)
        row["rmsd"] = pose_rmsd(predicted_coords, reference_coords)
        row["success"] = bool(row["rmsd"] < 2.0)
        pb_path, repair = neutral_n_repair(prediction_path, repaired_dir / f"{complex_id}.sdf")
        row.update(repair)
        row["posebusters_input_path"] = str(pb_path)
        report = buster.bust(mol_pred=[pb_path], mol_true=None, mol_cond=complex_dir / "protein.pdb", full_report=True).reset_index(drop=True)
        require(len(report) == 1, f"PoseBusters returned {len(report)} rows for {tool}/{split}/{complex_id}")
        pb_row = report.iloc[0]
        reported = 0
        values: list[bool] = []
        for check in checks:
            value = tri_bool(pb_row.get(check))
            is_reported = value is not None
            row[f"pb_{check}"] = bool(value is True)
            row[f"pb_{check}_reported"] = is_reported
            reported += int(is_reported)
            values.append(value is True)
        row["posebusters_checks_reported"] = reported
        row["posebusters_valid"] = bool(reported == len(checks) and all(values))
        row["posebusters_error"] = ""
    except Exception as error:
        row.update({"status": "excluded", "scoring_exclusion_reason": f"{type(error).__name__}: {error}", "posebusters_valid": False, "posebusters_checks_reported": 0, "posebusters_error": repr(error)})
        for check in checks:
            row[f"pb_{check}"] = False
            row[f"pb_{check}_reported"] = False
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(cache_path, row)
    return row


def main() -> int:
    args = parse_args()
    require(args.limit_per_split is None or args.limit_per_split > 0, "--limit-per-split must be positive")
    manifest = args.manifest.resolve()
    m2_output = args.m2_output_dir.resolve()
    predictions = args.predictions_dir.resolve()
    output = args.output_dir.resolve()
    cohorts = read_frozen_cohorts(manifest, m2_output)
    if args.limit_per_split is not None:
        cohorts = pd.concat([frame.sort_values("complex_id").head(args.limit_per_split) for _, frame in cohorts.groupby("split")], ignore_index=True)
    posebusters_module, PoseBusters = load_posebusters(args.posebusters_vendor)
    checks = configured_check_columns(posebusters_module)
    RDLogger.DisableLog("rdApp.*")
    buster = PoseBusters(config="dock", max_workers=0)
    rows: list[dict[str, Any]] = []
    started = time.time()
    for ordinal, record in enumerate(cohorts.itertuples(index=False), start=1):
        for tool in TOOLS:
            prediction_path = predictions / tool / record.split / record.complex_id / "rank1.sdf"
            require(prediction_path.is_file() and prediction_path.stat().st_size > 0, f"missing collected prediction: {prediction_path}")
            complex_dir = m2_output / "complexes" / record.split / record.complex_id
            cache = output / "score_cache" / tool / record.split / f"{record.complex_id}.json"
            repaired_dir = output / "repaired_sdf" / tool / record.split
            scored = score_one(tool, record.split, record.complex_id, complex_dir, prediction_path, checks, buster, repaired_dir, cache, args.force)
            scored.update({"source": record.source, "pdb_id": record.pdb_id, "group_id": record.group_id})
            rows.append(scored)
        if ordinal % 10 == 0 or ordinal == len(cohorts):
            partial = pd.DataFrame(rows)
            atomic_csv(output / "external_baseline_scores_partial.csv", partial)
            print(f"SCORE {ordinal}/{len(cohorts)} complexes ({2 * ordinal} poses, {time.time() - started:.1f}s)", flush=True)
    scores = pd.DataFrame(rows).sort_values(["tool", "split", "complex_id"]).reset_index(drop=True)
    atomic_csv(output / "external_baseline_scores.csv", scores)
    exclusions = scores.reindex(columns=["tool", "split", "complex_id", "status", "scoring_exclusion_reason"]).loc[scores["status"] != "completed"]
    atomic_csv(output / "external_baseline_scoring_exclusions.csv", exclusions)
    atomic_json(output / "scoring_metadata.json", {
        "scorer_version": SCORER_VERSION,
        "manifest_sha256": MANIFEST_SHA256,
        "manifest_observed_sha256": sha256(manifest),
        "predictions_dir": str(predictions),
        "m2_output_dir": str(m2_output),
        "configuration": {
            "posebusters_config": "dock",
            "posebusters_check_count": len(checks),
            "missing_check_policy": "not a pass",
            "mapping_contract": "atom-map heavy-atom bijection first; frozen topology graph matcher fallback; no coordinate nearest-neighbor for de-novo poses",
            "mapping_tolerance_angstrom": MAPPING_TOLERANCE_ANGSTROM,
            "rmsd_definition": "sqrt(mean_i(||pred_i-target_i||^2)); no rigid-body alignment",
            "success_threshold_angstrom": 2.0,
            "neutral_n_repair": "only neutral N, formal charge 0, explicit valence 4; otherwise exclusion",
        },
        "checks": checks,
        "counts": {"input_complexes": int(len(cohorts)), "scored_rows": int(len(scores)), "completed": int((scores.status == "completed").sum()), "excluded": int((scores.status != "completed").sum())},
        "prediction_inventory_sha256": sha256(predictions / "prediction_inventory.csv"),
        "scores_sha256": sha256(output / "external_baseline_scores.csv"),
        "environment": environment_metadata(),
    })
    print(f"Scoring complete: {len(scores)} rows; exclusions={len(exclusions)}", flush=True)
    return 0 if len(exclusions) == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
