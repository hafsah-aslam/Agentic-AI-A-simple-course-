#!/usr/bin/env python3
"""Record pinned source, model, configuration, and runtime metadata."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from common import atomic_json, environment_metadata, sha256


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tool", choices=("equibind", "diffdock"), required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--model-dir", type=Path, default=None)
    parser.add_argument("--model-archive", type=Path, default=None)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--raw-output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260827)
    parser.add_argument("--inference-steps", type=int, default=None)
    parser.add_argument("--samples-per-complex", type=int, default=None)
    return parser.parse_args()


def git_value(source: Path, *arguments: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(source), *arguments], text=True).strip()
    except Exception as error:
        return f"unavailable:{type(error).__name__}:{error}"


def main() -> int:
    args = parse_args()
    source = args.source_dir.resolve()
    payload = {
        "metadata_version": "external-baseline-inference-metadata-v1",
        "tool": args.tool,
        "manifest_sha256": args.manifest_sha256,
        "source_dir": str(source),
        "source_commit": git_value(source, "rev-parse", "HEAD"),
        "source_status_porcelain": git_value(source, "status", "--porcelain"),
        "checkpoint": str(args.checkpoint.resolve()) if args.checkpoint else None,
        "checkpoint_sha256": sha256(args.checkpoint.resolve()) if args.checkpoint and args.checkpoint.is_file() else None,
        "model_dir": str(args.model_dir.resolve()) if args.model_dir else None,
        "model_archive": str(args.model_archive.resolve()) if args.model_archive else None,
        "model_archive_sha256": sha256(args.model_archive.resolve()) if args.model_archive and args.model_archive.is_file() else None,
        "configuration": {
            "seed": args.seed,
            "inference_steps": args.inference_steps,
            "samples_per_complex": args.samples_per_complex,
            "inputs_dir": str(args.inputs_dir.resolve()),
            "raw_output_dir": str(args.raw_output_dir.resolve()),
        },
        "environment": environment_metadata(),
    }
    atomic_json(args.output.resolve(), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
