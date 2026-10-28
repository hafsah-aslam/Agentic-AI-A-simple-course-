#!/usr/bin/env python3
"""Expose a DockingPoseCorrection run in the input layout of the original external-baseline bundle.

The original scripts read a frozen manifest, a Milestone 2 directory (complexes/<split>/<id>/protein.pdb and
reference_pose.sdf, plus artifact_exclusions.csv), the per-complex correction evaluation (one row per complex and
seed) and the frozen PoseBusters results of the Vina, ungated and gated poses. This script writes those files from
the reproduction's own outputs, plus bridge.json, which common.py reads when DPC_BRIDGE is set. Nothing in the run
is modified; reference ligands and proteins are linked, not copied.

Usage: python3 bridge_from_dpc.py --repo DockingPoseCorrection --work DPC_WORK --posebusters DIR --out BRIDGE_DIR
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import pandas as pd


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def link(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.exists():
        if destination.resolve() == source.resolve():
            return
        destination.unlink()
    destination.symlink_to(source.resolve())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True, help="DockingPoseCorrection folder (results/, manifests/)")
    ap.add_argument("--work", type=Path, required=True, help="the run's work folder (data/internal, docked/)")
    ap.add_argument("--posebusters", type=Path, required=True, help="folder that contains posebusters_benchmark_set/")
    ap.add_argument("--results", type=Path, default=None, help="results folder (default: REPO/results)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    res = (a.results or a.repo / "results").resolve()
    out = a.out.resolve()
    pb = a.posebusters.resolve() / "posebusters_benchmark_set"
    ev = json.load(open(res / "eval.json"))
    arch, tau = ev["selection"]["selected"], float(ev["gate"]["tau"])
    rows = pd.read_csv(res / "rows_selected.csv")
    rows = rows[rows.cohort.isin(["test", "external"])].rename(columns={"cohort": "split", "pdb": "complex_id"})
    man = pd.read_csv(a.repo / "manifests" / "manifest.csv")
    man = man[man.split.isin(["test", "external"])]
    evaluated = set(zip(rows.split, rows.complex_id))

    # frozen manifest and Milestone 2 layout
    records, exclusions = [], []
    for r in man.itertuples(index=False):
        cid = str(r.pdb)
        if (r.split, cid) not in evaluated:
            dj = a.work / "docked" / cid / "dock.json"
            reason = json.load(open(dj)).get("error", "docking failed") if dj.exists() else "not docked"
            exclusions.append({"complex_id": cid, "split": r.split, "reason": reason if dj.exists() and json.load(open(dj)).get("status") != "ok" else "not featurized"})
        if r.split == "external":
            protein, ligand, source = pb / cid / f"{cid}_protein.pdb", pb / cid / f"{cid}_ligand.sdf", "posebusters"
        else:
            d = a.work / "data" / "internal" / cid
            protein = d / "protein_pb.pdb" if (d / "protein_pb.pdb").exists() else d / "protein.pdb"
            ligand, source = d / "ligand_ref.sdf", "lp_pdbbind"
        if (r.split, cid) in evaluated:
            target = out / "m2" / "complexes" / r.split / cid
            link(protein, target / "protein.pdb")
            link(ligand, target / "reference_pose.sdf")
        records.append({"complex_id": cid, "split": r.split, "eligible": True, "source": source,
                        "pdb_id": cid[:4].lower(), "group_id": r.group_id})
    (out / "m2").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(out / "manifest.csv", index=False)
    pd.DataFrame(exclusions, columns=["complex_id", "split", "reason"]).to_csv(out / "m2" / "artifact_exclusions.csv", index=False)

    # per-complex correction evaluation (one row per complex and seed), Equation 4 units
    m6 = pd.DataFrame({
        "complex_id": rows.complex_id, "split": rows.split, "seed": rows.seed, "n_atoms": rows.n,
        "baseline_msd": rows.base_se / rows.n, "baseline_rmsd": rows.base_rmsd, "baseline_success": rows.base_rmsd < 2.0,
        "corrected_msd": rows.corr_se / rows.n, "corrected_rmsd": rows.corr_rmsd, "corrected_success": rows.corr_rmsd < 2.0,
        "mean_predicted_sigma": rows.sigma})
    m6.to_csv(out / "per_complex_evaluation.csv", index=False)

    # frozen PoseBusters validity of the Vina, ungated and gated poses (same 22 dock checks)
    audit = pd.read_csv(res / "audit.csv")
    audit = audit[audit.cohort.isin(["test", "external"])]
    valid = audit.valid.astype(str).str.lower().eq("true")
    base = dict(zip(audit[audit.variant == "baseline"].pdb.astype(str), valid[audit.variant == "baseline"]))
    corr = {(p, int(s)): v for p, s, v in zip(audit[audit.variant == "corrected"].pdb.astype(str),
                                              audit[audit.variant == "corrected"].seed, valid[audit.variant == "corrected"])}
    pbr = m6[["complex_id", "split", "seed"]].copy()
    pbr["baseline_valid"] = [base[c] for c in pbr.complex_id]
    pbr["ungated_corrected_valid"] = [corr[(c, int(s))] for c, s in zip(pbr.complex_id, pbr.seed)]
    applied = m6.mean_predicted_sigma <= tau
    pbr["gated_valid"] = pbr.ungated_corrected_valid.where(applied, pbr.baseline_valid)
    pbr.to_csv(out / "posebusters_results.csv", index=False)

    counts = {s: int(rows[rows.split == s].complex_id.nunique()) for s in ("test", "external")}
    json.dump({"manifest_sha256": sha256(out / "manifest.csv"),
               "m2_exclusions_sha256": sha256(out / "m2" / "artifact_exclusions.csv"),
               "counts": counts, "selected_architecture": arch, "gate_tau": tau,
               "source_results": str(res), "source_work": str(a.work.resolve())},
              open(out / "bridge.json", "w"), indent=2)
    print(f"bridge: {counts} evaluated complexes, {len(exclusions)} prior exclusions, gate tau {tau:.4f} ({arch})")


if __name__ == "__main__":
    main()
