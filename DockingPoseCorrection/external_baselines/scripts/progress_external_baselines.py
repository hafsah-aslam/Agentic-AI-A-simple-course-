#!/usr/bin/env python3
"""Print and persist full-cohort external-baseline inference progress."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from common import atomic_csv, atomic_json, sha256


OUTPUT_NAMES = {"equibind": "lig_equibind_corrected.sdf", "diffdock": "rank1.sdf"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--raw-output-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = args.inputs_dir.resolve()
    raw = args.raw_output_dir.resolve()
    output = args.output_dir.resolve()
    inventory = list(csv.DictReader((inputs / "cohort_inventory.csv").open(encoding="utf-8", newline="")))
    if not inventory:
        raise RuntimeError("prepared cohort inventory is missing or empty")
    records: list[dict[str, object]] = []
    for tool, filename in OUTPUT_NAMES.items():
        for record in inventory:
            split, complex_id = record["split"], record["complex_id"]
            path = raw / tool / split
            matches = list(path.glob(f"shard_*/{complex_id}/{filename}")) if path.is_dir() else []
            if len(matches) > 1:
                raise RuntimeError(f"duplicate raw output for {tool}/{split}/{complex_id}: {matches}")
            prediction = matches[0] if matches else None
            records.append(
                {
                    "tool": tool,
                    "split": split,
                    "complex_id": complex_id,
                    "completed": prediction is not None and prediction.stat().st_size > 0,
                    "prediction_path": str(prediction) if prediction else "",
                    "prediction_sha256": sha256(prediction) if prediction and prediction.stat().st_size > 0 else "",
                }
            )
    frame_rows = records
    atomic_csv(output / "inference_progress.csv", __import__("pandas").DataFrame(frame_rows))
    summary: dict[str, object] = {"prepared_input_inventory_sha256": sha256(inputs / "cohort_inventory.csv"), "progress": {}}
    for tool in OUTPUT_NAMES:
        summary["progress"][tool] = {}
        for split in ("test", "external"):
            selected = [row for row in records if row["tool"] == tool and row["split"] == split]
            complete = sum(bool(row["completed"]) for row in selected)
            summary["progress"][tool][split] = {
                "completed": complete,
                "expected": len(selected),
                "percent": 100.0 * complete / len(selected),
                "complete": complete == len(selected),
            }
            print(f"{tool:9s} {split:8s} {complete:3d}/{len(selected):3d} ({100.0 * complete / len(selected):5.1f}%)")
    atomic_json(output / "inference_progress.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
