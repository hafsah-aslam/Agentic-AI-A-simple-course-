#!/usr/bin/env python3
"""Standardize pinned external-tool outputs without modifying raw results."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

from common import EXPECTED_COMPLEX_COUNTS, atomic_csv, atomic_json, require, sha256


OUTPUT_NAMES = {"equibind": "lig_equibind_corrected.sdf", "diffdock": "rank1.sdf"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--raw-output-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true", help="diagnostic only; final scoring remains strict")
    return parser.parse_args()


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    shutil.copy2(source, temporary)
    temporary.replace(destination)


def main() -> int:
    args = parse_args()
    inputs, raw, output = args.inputs_dir.resolve(), args.raw_output_dir.resolve(), args.output_dir.resolve()
    inventory_path = inputs / "cohort_inventory.csv"
    require(inventory_path.is_file(), f"prepared cohort inventory is missing: {inventory_path}")
    inventory = pd.read_csv(inventory_path, dtype={"complex_id": str, "split": str})
    counts = inventory.groupby("split")["complex_id"].nunique().to_dict()
    require(counts == EXPECTED_COMPLEX_COUNTS, f"prepared cohort differs from frozen counts: {counts}")
    rows: list[dict[str, object]] = []
    for tool, raw_name in OUTPUT_NAMES.items():
        for record in inventory.itertuples(index=False):
            candidates = sorted((raw / tool / record.split).glob(f"shard_*/{record.complex_id}/{raw_name}"))
            require(len(candidates) <= 1, f"multiple raw predictions for {tool}/{record.split}/{record.complex_id}")
            source = candidates[0] if candidates else None
            destination = output / tool / record.split / record.complex_id / "rank1.sdf"
            if source is None or source.stat().st_size == 0:
                rows.append({
                    "tool": tool, "split": record.split, "complex_id": record.complex_id,
                    "status": "missing_raw_prediction", "source_prediction": "", "source_sha256": "",
                    "rank1_prediction": "", "rank1_sha256": "",
                })
                continue
            if not destination.is_file() or sha256(destination) != sha256(source):
                atomic_copy(source, destination)
            rows.append({
                "tool": tool, "split": record.split, "complex_id": record.complex_id,
                "status": "collected", "source_prediction": str(source), "source_sha256": sha256(source),
                "rank1_prediction": str(destination), "rank1_sha256": sha256(destination),
            })
    result = pd.DataFrame(rows).sort_values(["tool", "split", "complex_id"]).reset_index(drop=True)
    missing = result.loc[result["status"] != "collected"]
    atomic_csv(output / "prediction_inventory.csv", result)
    atomic_json(output / "collection_metadata.json", {
        "input_inventory_sha256": sha256(inventory_path),
        "counts": {f"{key[0]}/{key[1]}": int(value) for key, value in result.loc[result.status == "collected"].groupby(["tool", "split"]).size().to_dict().items()},
        "missing_predictions": int(len(missing)),
        "allow_incomplete": bool(args.allow_incomplete),
    })
    if len(missing) and not args.allow_incomplete:
        raise RuntimeError(f"{len(missing)} required rank-1 prediction(s) are missing; rerun the listed shard(s) before scoring")
    print(f"Collected {int((result.status == 'collected').sum())}/{len(result)} rank-1 outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
