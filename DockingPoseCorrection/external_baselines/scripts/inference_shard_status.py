#!/usr/bin/env python3
"""Check one restart-safe external-docking inference shard."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from common import atomic_json, sha256


OUTPUT_NAMES = {"equibind": "lig_equibind_corrected.sdf", "diffdock": "rank1.sdf"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=sorted(OUTPUT_NAMES), required=True)
    parser.add_argument("--input-shard", type=Path, required=True)
    parser.add_argument("--raw-output-shard", type=Path, required=True)
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_shard = args.input_shard.resolve()
    raw_output = args.raw_output_shard.resolve()
    rows = list(csv.DictReader((input_shard / "complexes.csv").open(encoding="utf-8", newline="")))
    if not rows:
        raise RuntimeError(f"shard membership is missing or empty: {input_shard / 'complexes.csv'}")
    complex_ids = [row["complex_id"] for row in rows]
    if len(complex_ids) != len(set(complex_ids)):
        raise RuntimeError(f"shard has duplicate complex IDs: {input_shard}")
    output_name = OUTPUT_NAMES[args.tool]
    completed: list[dict[str, str]] = []
    missing: list[str] = []
    for complex_id in complex_ids:
        path = raw_output / complex_id / output_name
        if path.is_file() and path.stat().st_size > 0:
            completed.append({"complex_id": complex_id, "path": str(path), "sha256": sha256(path)})
        else:
            missing.append(complex_id)
    report = {
        "tool": args.tool,
        "input_shard": str(input_shard),
        "raw_output_shard": str(raw_output),
        "expected_complexes": len(complex_ids),
        "completed_complexes": len(completed),
        "missing_complexes": len(missing),
        "complete": not missing,
        "completed_outputs": completed,
        "missing_ids": missing,
    }
    if args.status_file is not None:
        atomic_json(args.status_file.resolve(), report)
    if not args.quiet:
        print(json.dumps(report, sort_keys=True))
    return 0 if not missing else 3


if __name__ == "__main__":
    raise SystemExit(main())
