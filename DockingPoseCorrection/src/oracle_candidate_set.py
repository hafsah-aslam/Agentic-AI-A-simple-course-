"""Candidate-set oracle study (RescueDock, experiment 1).

Research question: how often is a near-native pose ALREADY in Vina's candidate list, even when rank-1 is wrong?
This is the ceiling of any method that selects/refines among Vina's own poses (RescueDock Pillar 1). If the
oracle success rate is well above rank-1, "rescue by selection" is worth building; if not, Pillar 1 is dead.

It re-reads the full pose set the docking stage already saved (docked/<pdb>/poses.pdbqt, five poses per complex)
and, for every pose, computes the SAME symmetry-corrected heavy-atom RMSD to the reference that the pipeline uses
(match.heavy_mapping: graph-isomorphism correspondence, no superposition). No re-docking, no GPU. Per complex it
records the rank-1 RMSD (pose 0, what the pipeline reports today) and the oracle RMSD (best of the five poses).

Restart-safe: writes docked/<pdb>/oracle.json per complex and skips ones already done. Rerun the same command
after any interruption, then rerun with --summary-only to print the table from existing oracle.json files.

Usage:
  python3 src/oracle_candidate_set.py --manifest manifests/manifest.csv --data DPC_WORK/data \
      --posebusters SOURCES_DIR --dock DPC_WORK/docked --out DPC_WORK/oracle_candidate_set.csv
  python3 src/oracle_candidate_set.py ... --summary-only     # just re-print the summary

SOURCES_DIR is the folder that contains posebusters_benchmark_set/ (the same one passed to docking).
"""
import argparse
import csv
import json
import os
import sys

from rdkit import Chem, RDLogger
from meeko import PDBQTMolecule, RDKitMolCreate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from match import heavy_mapping, ref_path  # reuse the pipeline's exact RMSD + reference resolution

RDLogger.DisableLog("rdApp.*")
SUCCESS = 2.0  # A


def poses_from_pdbqt(path):
    """Return a list of heavy-atom RDKit mols, one per Vina pose, in Vina's rank order."""
    text = open(path).read()
    pm = PDBQTMolecule(text, skip_typing=True)
    mols = RDKitMolCreate.from_pdbqt_mol(pm)
    dock = mols[0]  # one multi-conformer mol; conformer i == pose i (rank i)
    out = []
    for cid in range(dock.GetNumConformers()):
        one = Chem.Mol(dock)
        one.RemoveAllConformers()
        one.AddConformer(dock.GetConformer(cid), assignId=True)
        out.append(Chem.RemoveHs(one))
    return out


def rmsds_for_complex(row, args):
    d = os.path.join(args.dock, row["pdb"])
    pf = os.path.join(d, "poses.pdbqt")
    dj = os.path.join(d, "dock.json")
    if not os.path.exists(pf) or not os.path.exists(dj):
        return {"pdb": row["pdb"], "split": row["split"], "status": "no_poses"}
    if json.load(open(dj)).get("status") != "ok":
        return {"pdb": row["pdb"], "split": row["split"], "status": "dock_not_ok"}
    ref = Chem.MolFromMolFile(ref_path(row, args.data, args.posebusters))
    if ref is None:
        return {"pdb": row["pdb"], "split": row["split"], "status": "no_reference"}
    try:
        poses = poses_from_pdbqt(pf)
    except Exception as e:  # noqa: BLE001 - record and move on, one bad file must not stop the study
        return {"pdb": row["pdb"], "split": row["split"], "status": f"pose_read_error:{type(e).__name__}"}
    rmsds = []
    for p in poses:
        best = heavy_mapping(p, ref) if p is not None and p.GetNumAtoms() == ref.GetNumAtoms() else None
        rmsds.append(round(best[0] ** 0.5, 4) if best else None)
    valid = [r for r in rmsds if r is not None]
    if not valid:
        return {"pdb": row["pdb"], "split": row["split"], "status": "atom_matching_failed"}
    oracle = min(valid)
    return {"pdb": row["pdb"], "split": row["split"], "status": "ok", "n_poses": len(rmsds),
            "rank1_rmsd": rmsds[0], "oracle_rmsd": oracle,
            "best_pose_index": rmsds.index(oracle), "per_pose_rmsd": rmsds}


def summarize(records, out_csv):
    cols = ["pdb", "split", "status", "n_poses", "rank1_rmsd", "oracle_rmsd", "best_pose_index"]
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k) for k in cols})
    print(f"\nwrote {out_csv}\n")
    print(f"{'cohort':<10}{'n':>5}{'rank-1 <2A':>13}{'oracle <2A':>13}{'rescued':>10}{'rescue ceiling':>16}")
    for coh in ["test", "external"]:
        ok = [r for r in records if r["split"] == coh and r.get("status") == "ok"]
        n = len(ok)
        if not n:
            continue
        r1 = sum(r["rank1_rmsd"] < SUCCESS for r in ok)
        orc = sum(r["oracle_rmsd"] < SUCCESS for r in ok)
        rescued = sum(r["rank1_rmsd"] >= SUCCESS and r["oracle_rmsd"] < SUCCESS for r in ok)
        print(f"{coh:<10}{n:>5}{100*r1/n:>12.1f}%{100*orc/n:>12.1f}%{rescued:>10}{100*(orc-r1)/n:>15.1f}%")
    bad = [r for r in records if r.get("status") != "ok"]
    if bad:
        from collections import Counter
        print("\nexcluded:", dict(Counter(r["status"] for r in bad)))
    print("\nrank-1 <2A = today's Vina baseline; oracle <2A = best achievable by selecting among the 5 poses;")
    print("rescue ceiling = how many more points a perfect selector could add over rank-1.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--data", required=True, help="DPC_WORK/data (holds internal/<pdb>/ligand_ref.sdf)")
    ap.add_argument("--posebusters", required=True, help="folder containing posebusters_benchmark_set/")
    ap.add_argument("--dock", required=True, help="DPC_WORK/docked (holds <pdb>/poses.pdbqt)")
    ap.add_argument("--out", default="oracle_candidate_set.csv")
    ap.add_argument("--summary-only", action="store_true", help="recompute nothing; summarize existing oracle.json")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.manifest)))
    records = []
    for i, row in enumerate(rows):
        oj = os.path.join(a.dock, row["pdb"], "oracle.json")
        if a.summary_only:
            if os.path.exists(oj):
                records.append(json.load(open(oj)))
            continue
        if os.path.exists(oj):
            records.append(json.load(open(oj)))
            continue
        rec = rmsds_for_complex(row, a)
        json.dump(rec, open(oj, "w"))
        records.append(rec)
        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(rows)} complexes")
    summarize(records, a.out)


if __name__ == "__main__":
    main()
