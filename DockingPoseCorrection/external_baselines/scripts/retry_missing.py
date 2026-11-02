#!/usr/bin/env python3
"""List the complexes a tool left without a prediction and prepare single-complex inputs for a retry.

EquiBind and DiffDock process a shard in one call, so one complex that crashes the tool (for example an RDKit
conformer failure inside EquiBind) leaves every later complex of that shard undone. This script finds those
complexes and writes, for each, an input that contains only that complex, in the same form the runner uses for a
shard (a folder of complex links for EquiBind, a one-row protein_ligand_csv for DiffDock). It prints one
tab-separated line per complex: split, shard, complex_id, input path, raw output folder of the shard.

A complex whose single retry also produced nothing has a <complex_id>.failed marker next to its shard output and
is skipped, so reruns do not repeat it; it is scored as a docking failure.

Usage: python3 retry_missing.py --tool equibind|diffdock --workspace WS
"""
import argparse
import csv
import os
from pathlib import Path

OUTPUT_NAMES = {"equibind": "lig_equibind_corrected.sdf", "diffdock": "rank1.sdf"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tool", choices=sorted(OUTPUT_NAMES), required=True)
    ap.add_argument("--workspace", type=Path, required=True)
    a = ap.parse_args()
    ws = a.workspace.resolve()
    name = OUTPUT_NAMES[a.tool]
    for shard_dir in sorted((ws / "inputs" / "shards").glob("*/shard_*")):
        split, shard = shard_dir.parent.name, shard_dir.name
        raw = ws / "raw_inference" / a.tool / split / shard
        rows = list(csv.DictReader(open(shard_dir / "diffdock_inputs.csv", encoding="utf-8", newline="")))
        for row in rows:
            cid = row["complex_name"]
            out = raw / cid / name
            if (out.is_file() and out.stat().st_size > 0) or (raw / f"{cid}.failed").exists():
                continue
            single = ws / "inputs" / "single" / a.tool / split / cid
            single.mkdir(parents=True, exist_ok=True)
            if a.tool == "equibind":
                link = single / cid
                if not link.is_symlink():
                    os.symlink((ws / "inputs" / "input_data" / split / cid).resolve(), link, target_is_directory=True)
                target = single
            else:
                target = single / "diffdock_inputs.csv"
                with open(target, "w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(row)
            print("\t".join([split, shard, cid, str(target), str(raw)]))


if __name__ == "__main__":
    main()
