#!/usr/bin/env python3
"""Prepare topology-only, atom-mapped inputs for EquiBind and DiffDock.

This script never writes into the frozen Milestone 1/2 directories.  It uses
the reference ligand only for its chemical graph, not for its crystallographic
coordinates: every input conformer is generated deterministically with RDKit.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

from common import (
    EXPECTED_COMPLEX_COUNTS,
    MANIFEST_SHA256,
    M2_EXCLUSIONS_SHA256,
    atomic_csv,
    atomic_json,
    read_frozen_cohorts,
    require,
    sha256,
)


INPUT_VERSION = "external-baseline-inputs-v1"
RDKIT_CONFORMER_SEED = 20260827


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--m2-output-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=20, help="Resumable shards per cohort")
    parser.add_argument("--protein-mode", choices=("symlink", "copy"), default="symlink")
    parser.add_argument("--force", action="store_true", help="Rebuild generated inputs, never frozen files")
    return parser.parse_args()


def read_one_sdf(path: Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), sanitize=True, removeHs=False)
    molecules = [molecule for molecule in supplier if molecule is not None]
    require(len(molecules) == 1, f"expected exactly one valid reference ligand in {path}, found {len(molecules)}")
    require(molecules[0].GetNumAtoms() > 0, f"reference ligand contains no atoms: {path}")
    return molecules[0]


def deterministic_ligand(reference_path: Path) -> tuple[Chem.Mol, str]:
    """Create a topology-preserving conformer without retaining native coordinates."""

    source = read_one_sdf(reference_path)
    ligand = Chem.Mol(source)
    ligand.RemoveAllConformers()
    # Original atom indexes are the cross-tool identity contract.  Hydrogens
    # introduced later deliberately retain map zero and are ignored in scoring.
    for atom in ligand.GetAtoms():
        atom.SetAtomMapNum(atom.GetIdx() + 1)
    ligand = Chem.AddHs(ligand, addCoords=False)
    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = RDKIT_CONFORMER_SEED
    parameters.useRandomCoords = False
    parameters.enforceChirality = True
    status = AllChem.EmbedMolecule(ligand, parameters)
    method = "ETKDGv3"
    if status != 0:
        ligand.RemoveAllConformers()
        parameters.useRandomCoords = True
        status = AllChem.EmbedMolecule(ligand, parameters)
        method = "ETKDGv3_random_coordinate_fallback"
    require(status == 0 and ligand.GetNumConformers() == 1, f"RDKit conformer generation failed: {reference_path}")
    try:
        optimized = AllChem.MMFFOptimizeMolecule(ligand, confId=0, maxIters=500)
        method += f"+MMFF({optimized})"
    except Exception:
        try:
            optimized = AllChem.UFFOptimizeMolecule(ligand, confId=0, maxIters=500)
            method += f"+UFF({optimized})"
        except Exception:
            method += "+unoptimized"
    positions = np.asarray(ligand.GetConformer().GetPositions(), dtype=np.float64)
    require(np.isfinite(positions).all(), f"generated ligand coordinates are non-finite: {reference_path}")
    return ligand, method


def write_sdf(path: Path, molecule: Chem.Mol) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    writer = Chem.SDWriter(str(temporary))
    try:
        writer.write(molecule)
    finally:
        writer.close()
    os.replace(temporary, path)


def link_or_copy(source: Path, destination: Path, mode: str, force: bool) -> None:
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() and destination.resolve() == source.resolve() and not force:
            return
        if destination.is_file() and mode == "copy" and sha256(destination) == sha256(source) and not force:
            return
        destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if mode == "symlink":
        destination.symlink_to(source.resolve())
    else:
        shutil.copy2(source, destination)


def build_shards(cohorts: pd.DataFrame, output: Path, shards: int) -> pd.DataFrame:
    require(shards > 0, "--shards must be positive")
    rows: list[dict[str, object]] = []
    for split, split_frame in cohorts.groupby("split", sort=True):
        ids = split_frame.sort_values("complex_id")["complex_id"].tolist()
        for ordinal, complex_id in enumerate(ids):
            shard = ordinal % shards
            destination = output / "shards" / split / f"shard_{shard:03d}" / complex_id
            source = output / "input_data" / split / complex_id
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() or destination.is_symlink():
                require(destination.is_symlink() and destination.resolve() == source.resolve(), f"unexpected shard target: {destination}")
            else:
                destination.symlink_to(source.resolve(), target_is_directory=True)
            rows.append({"split": split, "complex_id": complex_id, "shard": shard})
    assignment = pd.DataFrame(rows).sort_values(["split", "shard", "complex_id"]).reset_index(drop=True)
    for (split, shard), frame in assignment.groupby(["split", "shard"], sort=True):
        shard_dir = output / "shards" / split / f"shard_{int(shard):03d}"
        atomic_csv(shard_dir / "complexes.csv", frame[["split", "complex_id", "shard"]])
        diffdock = frame.copy()
        diffdock["complex_name"] = diffdock["complex_id"]
        diffdock["protein_path"] = [str((output / "input_data" / split / cid / "protein.pdb").resolve()) for cid in diffdock["complex_id"]]
        diffdock["ligand_description"] = [str((output / "input_data" / split / cid / "ligand.sdf").resolve()) for cid in diffdock["complex_id"]]
        diffdock["protein_sequence"] = ""
        atomic_csv(shard_dir / "diffdock_inputs.csv", diffdock[["complex_name", "protein_path", "ligand_description", "protein_sequence"]])
    return assignment


def main() -> int:
    args = parse_args()
    manifest = args.manifest.resolve()
    m2_output = args.m2_output_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cohorts = read_frozen_cohorts(manifest, m2_output)
    existing_metadata = output / "input_metadata.json"
    if existing_metadata.is_file() and not args.force:
        previous = json.loads(existing_metadata.read_text(encoding="utf-8"))
        require(previous.get("configuration", {}).get("shards") == args.shards, "existing inputs use a different --shards value; use the original value or --force")
        require(previous.get("configuration", {}).get("protein_mode") == args.protein_mode, "existing inputs use a different --protein-mode; use the original value or --force")

    records: list[dict[str, object]] = []
    for ordinal, row in enumerate(cohorts.itertuples(index=False), start=1):
        source_dir = m2_output / "complexes" / row.split / row.complex_id
        destination = output / "input_data" / row.split / row.complex_id
        ligand_path = destination / "ligand.sdf"
        protein_path = destination / "protein.pdb"
        if args.force or not ligand_path.is_file():
            ligand, conformer_method = deterministic_ligand(source_dir / "reference_pose.sdf")
            write_sdf(ligand_path, ligand)
        else:
            # The only allowed reuse condition is a valid atom-map contract.
            ligand = read_one_sdf(ligand_path)
            conformer_method = "reused_verified"
        heavy = [atom for atom in ligand.GetAtoms() if atom.GetAtomicNum() > 1]
        maps = [atom.GetAtomMapNum() for atom in heavy]
        require(all(value > 0 for value in maps) and len(maps) == len(set(maps)), f"heavy-atom map contract failed: {ligand_path}")
        link_or_copy(source_dir / "protein.pdb", protein_path, args.protein_mode, args.force)
        records.append(
            {
                "split": row.split,
                "complex_id": row.complex_id,
                "source": row.source,
                "pdb_id": row.pdb_id,
                "group_id": row.group_id,
                "reference_pose_sha256": sha256(source_dir / "reference_pose.sdf"),
                "protein_sha256": sha256(source_dir / "protein.pdb"),
                "prepared_ligand_sha256": sha256(ligand_path),
                "n_atoms_input": ligand.GetNumAtoms(),
                "n_heavy_atoms_input": len(heavy),
                "heavy_atom_maps_bijective": True,
                "conformer_method": conformer_method,
                "prepared_ligand": str(ligand_path.resolve()),
                "prepared_protein": str(protein_path.resolve()),
            }
        )
        if ordinal % 25 == 0 or ordinal == len(cohorts):
            print(f"PREPARE {ordinal}/{len(cohorts)} complexes", flush=True)

    inventory = pd.DataFrame(records).sort_values(["split", "complex_id"]).reset_index(drop=True)
    observed = inventory.groupby("split")["complex_id"].nunique().to_dict()
    require(observed == EXPECTED_COMPLEX_COUNTS, f"prepared cohort counts differ: {observed}")
    assignments = build_shards(cohorts, output, args.shards)
    atomic_csv(output / "cohort_inventory.csv", inventory)
    atomic_csv(output / "shard_assignment.csv", assignments)
    metadata = {
        "input_version": INPUT_VERSION,
        "manifest_sha256": MANIFEST_SHA256,
        "m2_artifact_exclusions_sha256": sha256(m2_output / "artifact_exclusions.csv"),
        "m2_artifact_exclusions_expected_sha256": M2_EXCLUSIONS_SHA256,
        "configuration": {
            "shards": args.shards,
            "protein_mode": args.protein_mode,
            "rdkit_conformer_seed": RDKIT_CONFORMER_SEED,
            "reference_coordinates_used": False,
            "atom_identity": "reference SDF original atom index + 1 stored as atom-map number; heavy atoms must be bijective",
        },
        "counts": {key: int(value) for key, value in observed.items()},
        "input_inventory_sha256": sha256(output / "cohort_inventory.csv"),
        "shard_assignment_sha256": sha256(output / "shard_assignment.csv"),
    }
    atomic_json(output / "input_metadata.json", metadata)
    print(f"Prepared {len(inventory)} frozen-cohort inputs in {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
