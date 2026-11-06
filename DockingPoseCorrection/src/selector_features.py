"""Per-pose feature extraction for the RescueDock selector (experiment 2).

For every Vina pose of every complex, compute REFERENCE-FREE features (usable at inference, when no crystal pose
is known) and attach the RMSD label computed by the oracle study. The output is the training table for a learned
selector whose job is to pick the near-native pose out of Vina's five — beating Vina's own energy ranking, which
the oracle study showed leaves +17-20 points of success on the table.

Features per pose (all reference-free):
  vina_energy        Vina total score for this pose (from dock.json)
  vina_rank          0..4, Vina's own ranking (0 = Vina's pick today)
  energy_gap         vina_energy - best vina_energy in this complex
  n_contacts         ligand heavy atoms with a receptor heavy atom within 4.0 A
  n_clash            ligand-receptor heavy-atom pairs closer than 2.2 A (bad)
  min_contact_dist   closest ligand-receptor heavy-atom distance
  buried_frac        fraction of ligand heavy atoms within 4.5 A of the receptor
  rgyr               ligand radius of gyration (compactness)
Label:
  rmsd               symmetry-corrected heavy-atom RMSD to the reference (from oracle.json); is_best within complex

Reads only files the pipeline already produced (poses.pdbqt, receptor.pdbqt, dock.json, oracle.json). No GPU.
Run selector trains on split=train only; evaluation is on test/external (no leakage).

Usage:
  python3 src/selector_features.py --manifest manifests/manifest.csv --data DPC_WORK/data \
      --posebusters DPC_WORK/sources --dock DPC_WORK/docked --out DPC_WORK/selector_features.csv
"""
import argparse
import csv
import json
import os
import sys

import numpy as np
from rdkit import Chem, RDLogger
from meeko import PDBQTMolecule, RDKitMolCreate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RDLogger.DisableLog("rdApp.*")


def receptor_heavy_coords(pdbqt_path):
    """Heavy-atom XYZ of the receptor from its PDBQT (fixed columns; element in 77:79)."""
    xs = []
    for line in open(pdbqt_path):
        if line.startswith(("ATOM", "HETATM")):
            el = line[77:79].strip()
            if el in ("H", "HD", "HS"):
                continue
            try:
                xs.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    return np.asarray(xs, dtype=float) if xs else np.zeros((0, 3))


def pose_heavy_coords(pdbqt_path):
    """List (per pose, in Vina rank order) of ligand heavy-atom XYZ arrays."""
    pm = PDBQTMolecule(open(pdbqt_path).read(), skip_typing=True)
    dock = RDKitMolCreate.from_pdbqt_mol(pm)[0]
    out = []
    for cid in range(dock.GetNumConformers()):
        one = Chem.Mol(dock)
        one.RemoveAllConformers()
        one.AddConformer(dock.GetConformer(cid), assignId=True)
        heavy = Chem.RemoveHs(one)
        out.append(heavy.GetConformer().GetPositions())
    return out


def pose_features(lig_xyz, rec_xyz):
    f = {}
    if rec_xyz.shape[0] and lig_xyz.shape[0]:
        d = np.linalg.norm(lig_xyz[:, None, :] - rec_xyz[None, :, :], axis=2)  # (n_lig, n_rec)
        per_lig_min = d.min(1)
        f["n_contacts"] = int((d < 4.0).any(1).sum())
        f["n_clash"] = int((d < 2.2).sum())
        f["min_contact_dist"] = round(float(d.min()), 4)
        f["buried_frac"] = round(float((per_lig_min < 4.5).mean()), 4)
    else:
        f.update(n_contacts=0, n_clash=0, min_contact_dist=-1.0, buried_frac=0.0)
    c = lig_xyz - lig_xyz.mean(0)
    f["rgyr"] = round(float(np.sqrt((c ** 2).sum(1).mean())), 4)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--posebusters", required=True)
    ap.add_argument("--dock", required=True)
    ap.add_argument("--out", default="selector_features.csv")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.manifest)))
    cols = ["pdb", "split", "pose_index", "rmsd", "is_best", "vina_energy", "vina_rank", "energy_gap",
            "n_contacts", "n_clash", "min_contact_dist", "buried_frac", "rgyr"]
    out_rows, skipped = [], {}
    for i, row in enumerate(rows):
        d = os.path.join(a.dock, row["pdb"])
        pf, rf = os.path.join(d, "poses.pdbqt"), os.path.join(d, "receptor.pdbqt")
        dj, oj = os.path.join(d, "dock.json"), os.path.join(d, "oracle.json")
        if not all(os.path.exists(p) for p in (pf, rf, dj, oj)):
            skipped["missing_files"] = skipped.get("missing_files", 0) + 1
            continue
        orc = json.load(open(oj))
        if orc.get("status") != "ok":
            skipped[orc.get("status", "oracle_bad")] = skipped.get(orc.get("status", "oracle_bad"), 0) + 1
            continue
        energies = json.load(open(dj)).get("vina_energies") or []
        rmsds = orc["per_pose_rmsd"]
        try:
            lig_poses = pose_heavy_coords(pf)
            rec = receptor_heavy_coords(rf)
        except Exception as e:  # noqa: BLE001
            skipped[f"read_error:{type(e).__name__}"] = skipped.get(f"read_error:{type(e).__name__}", 0) + 1
            continue
        best_rmsd = min(r for r in rmsds if r is not None)
        best_e = min(energies) if energies else 0.0
        for idx, lig_xyz in enumerate(lig_poses):
            if idx >= len(rmsds) or rmsds[idx] is None:
                continue
            feat = pose_features(np.asarray(lig_xyz), rec)
            e = energies[idx] if idx < len(energies) else None
            out_rows.append({"pdb": row["pdb"], "split": row["split"], "pose_index": idx,
                             "rmsd": rmsds[idx], "is_best": int(rmsds[idx] == best_rmsd),
                             "vina_energy": e, "vina_rank": idx,
                             "energy_gap": round(e - best_e, 4) if e is not None else None, **feat})
        if (i + 1) % 50 == 0:
            print(f"  ...{i + 1}/{len(rows)} complexes")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nwrote {a.out}: {len(out_rows)} pose rows")
    if skipped:
        print("skipped:", skipped)
    for coh in ["train", "val", "test", "external"]:
        n = len({r["pdb"] for r in out_rows if r["split"] == coh})
        if n:
            print(f"  {coh}: {n} complexes")


if __name__ == "__main__":
    main()
