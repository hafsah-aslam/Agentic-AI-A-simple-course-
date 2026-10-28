"""Shared immutable-input and provenance helpers for external docking baselines."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


MANIFEST_SHA256 = "fd3428a7bf322cc1e5cd2c23a385544adec7c03c56ee9d2fcedf370455ffb78e"
M2_EXCLUSIONS_SHA256 = "d6a016b4fb88be43292223243512008c99032515efc7983d39287408b380450a"
EXPECTED_COMPLEX_COUNTS = {"test": 394, "external": 428}
# Reproduction adapter (the only change to this module): when DPC_BRIDGE points to the bridge.json written by
# bridge_from_dpc.py, the frozen identity of the reproduction cohort replaces the original study's constants.
if os.environ.get("DPC_BRIDGE"):
    with open(os.environ["DPC_BRIDGE"], encoding="utf-8") as _handle:
        _bridge = json.load(_handle)
    MANIFEST_SHA256 = _bridge["manifest_sha256"]
    M2_EXCLUSIONS_SHA256 = _bridge["m2_exclusions_sha256"]
    EXPECTED_COMPLEX_COUNTS = {split: int(_bridge["counts"][split]) for split in ("test", "external")}
SPLITS = tuple(EXPECTED_COMPLEX_COUNTS)
SUCCESS_THRESHOLD_ANGSTROM = 2.0
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 0

EQUIBIND_REPOSITORY = "https://github.com/HannesStark/EquiBind.git"
EQUIBIND_COMMIT = "4cb1b4c562dae914780154518a6b915bb4cba658"
EQUIBIND_CHECKPOINT_RELATIVE = "runs/flexible_self_docking/best_checkpoint.pt"
EQUIBIND_CHECKPOINT_SHA256 = "eedf3daf1479244e00a1f5c6951cda8d874482c676cb2e21311557ab72d93559"

DIFFDOCK_REPOSITORY = "https://github.com/gcorso/DiffDock.git"
DIFFDOCK_COMMIT = "85c49b60d3e0b0182a59ee43a34a6d7036981284"
DIFFDOCK_MODELS_URL = "https://github.com/gcorso/DiffDock/releases/download/v1.1/diffdock_models.zip"


class BaselineError(RuntimeError):
    """An external baseline result violates the frozen scientific contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BaselineError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n")


def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".csv", dir=path.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        frame.to_csv(temporary, index=False, lineterminator="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot JSON encode {type(value).__name__}")


def verify_manifest(path: Path) -> str:
    resolved = path.resolve()
    require(resolved.is_file(), f"manifest is missing: {resolved}")
    observed = sha256(resolved)
    require(observed == MANIFEST_SHA256, f"frozen manifest hash differs: {observed}")
    return observed


def read_frozen_cohorts(manifest: Path, m2_output_dir: Path) -> pd.DataFrame:
    """Return precisely the M2-evaluable test/external membership in frozen order.

    The manifest defines candidate membership.  The Milestone 2 exclusions are
    immutable prior exclusions, so they are subtracted before any external-tool
    work begins.  Directory existence is then checked as an integrity check,
    never used to add or remove membership.
    """

    verify_manifest(manifest)
    exclusions_path = m2_output_dir / "artifact_exclusions.csv"
    require(exclusions_path.is_file(), f"M2 exclusions are missing: {exclusions_path}")
    require(sha256(exclusions_path) == M2_EXCLUSIONS_SHA256, f"protected M2 exclusions hash differs: {sha256(exclusions_path)}")
    frame = pd.read_csv(manifest, dtype={"complex_id": str, "split": str})
    exclusions = pd.read_csv(exclusions_path, dtype={"complex_id": str, "split": str})
    required = {"complex_id", "split", "eligible"}
    require(required <= set(frame.columns), f"manifest lacks columns: {sorted(required - set(frame.columns))}")
    require({"complex_id", "split", "reason"} <= set(exclusions.columns), "M2 exclusions schema differs")
    eligible_values = frame["eligible"].astype(str).str.strip().str.lower()
    require(eligible_values.isin({"true", "false", "1", "0"}).all(), "manifest eligible column is not boolean")
    eligible_mask = eligible_values.isin({"true", "1"})
    eligible = frame.loc[
        frame["split"].isin(SPLITS) & eligible_mask,
        ["split", "complex_id", "source", "pdb_id", "group_id"],
    ].copy()
    prior_exclusions = set(
        map(tuple, exclusions.loc[exclusions["split"].isin(SPLITS), ["split", "complex_id"]].to_records(index=False))
    )
    eligible = eligible.loc[
        [(row.split, row.complex_id) not in prior_exclusions for row in eligible.itertuples(index=False)]
    ].copy()
    require(not eligible.duplicated(["split", "complex_id"]).any(), "frozen cohort has duplicate complex IDs")
    observed = eligible.groupby("split")["complex_id"].nunique().to_dict()
    require(observed == EXPECTED_COMPLEX_COUNTS, f"frozen cohort counts differ: {observed}")
    for row in eligible.itertuples(index=False):
        directory = m2_output_dir / "complexes" / row.split / row.complex_id
        required_files = (directory / "protein.pdb", directory / "reference_pose.sdf")
        require(all(path.is_file() for path in required_files), f"frozen complex artifacts missing: {directory}")
    return eligible.sort_values(["split", "complex_id"]).reset_index(drop=True)


def environment_metadata() -> dict[str, str]:
    versions: dict[str, str] = {
        "python": sys.version,
        "platform": platform.platform(),
    }
    for module_name in ("numpy", "pandas", "rdkit", "torch", "scipy", "posebusters"):
        try:
            module = __import__(module_name)
            versions[module_name] = str(getattr(module, "__version__", "unknown"))
        except ImportError:
            versions[module_name] = "not_installed"
    return versions


def write_rows_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".csv", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
