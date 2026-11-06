"""Export 3D protein-ligand graphs for the RescueDock pose scorer (experiment 3, data prep).

For every complex, write a compact .npz holding the pocket atoms (once) and each Vina pose's ligand atoms, with
the oracle RMSD labels. The learned scorer reads these to rank poses by predicted closeness to native. All inputs
already exist from docking (poses.pdbqt, receptor.pdbqt, oracle.json); CPU only, restart-safe.

Per-complex arrays:
  poc_xyz   (M,3) pocket heavy-atom coords (protein atoms near the ligand, capped)
  poc_elem  (M,)  element index per pocket atom
  lig_xyz   (P,L,3) ligand heavy-atom coords for each of P poses (L atoms, shared molecule)
  lig_elem  (L,)  element index per ligand atom
  rmsd      (P,)  symmetry-corrected heavy-atom RMSD to native (oracle label)
  meta: pdb, split

Usage:
  python3 src/export_graphs.py --manifest manifests/manifest.csv --dock DPC_WORK/docked \
      --out DPC_WORK/graphs [--pocket-radius 10.0 --max-pocket 350]
"""
import argparse, json, os, csv
import numpy as np
from rdkit import Chem, RDLogger
from meeko import PDBQTMolecule, RDKitMolCreate

RDLogger.DisableLog("rdApp.*")

ELEMENTS = ["C", "N", "O", "S", "P", "F", "Cl", "Br", "I"]          # + "other" bucket at index len(ELEMENTS)
ELEM_IDX = {e: i for i, e in enumerate(ELEMENTS)}
OTHER = len(ELEMENTS)                                                # 9
NELEM = len(ELEMENTS) + 1                                            # 10
AD2EL = {"A": "C", "C": "C", "N": "N", "NA": "N", "NS": "N", "OA": "O", "OS": "O", "O": "O",
         "SA": "S", "S": "S", "P": "P", "F": "F", "Cl": "Cl", "Br": "Br", "I": "I"}


def elem_index(sym):
    return ELEM_IDX.get(sym, OTHER)


def receptor_atoms(pdbqt_path):
    xyz, el = [], []
    for line in open(pdbqt_path):
        if line.startswith(("ATOM", "HETATM")):
            ad = line[77:79].strip()
            if ad in ("H", "HD", "HS"):
                continue
            try:
                xyz.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
            el.append(elem_index(AD2EL.get(ad, ad)))   # map AutoDock type to element; unknown -> OTHER bucket
    return np.asarray(xyz, float), np.asarray(el, int)


def ligand_poses(pdbqt_path):
    pm = PDBQTMolecule(open(pdbqt_path).read(), skip_typing=True)
    dock = RDKitMolCreate.from_pdbqt_mol(pm)[0]
    heavy0 = Chem.RemoveHs(dock)
    elems = np.array([elem_index(a.GetSymbol()) for a in heavy0.GetAtoms()], int)
    poses = []
    for cid in range(dock.GetNumConformers()):
        one = Chem.Mol(dock); one.RemoveAllConformers()
        one.AddConformer(dock.GetConformer(cid), assignId=True)
        poses.append(Chem.RemoveHs(one).GetConformer().GetPositions())
    return np.stack(poses), elems           # (P,L,3), (L,)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dock", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pocket-radius", type=float, default=10.0)
    ap.add_argument("--max-pocket", type=int, default=350)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = list(csv.DictReader(open(a.manifest)))
    done = skipped = 0
    for i, row in enumerate(rows):
        pdb = row["pdb"]
        dst = os.path.join(a.out, f"{pdb}.npz")
        if os.path.exists(dst):
            done += 1; continue
        d = os.path.join(a.dock, pdb)
        pf, rf, oj = os.path.join(d, "poses.pdbqt"), os.path.join(d, "receptor.pdbqt"), os.path.join(d, "oracle.json")
        if not all(os.path.exists(p) for p in (pf, rf, oj)):
            skipped += 1; continue
        orc = json.load(open(oj))
        if orc.get("status") != "ok":
            skipped += 1; continue
        try:
            lig_xyz, lig_elem = ligand_poses(pf)
            poc_xyz, poc_elem = receptor_atoms(rf)
        except Exception:
            skipped += 1; continue
        rmsd = np.array([r if r is not None else np.nan for r in orc["per_pose_rmsd"]], float)
        if len(rmsd) != lig_xyz.shape[0]:
            skipped += 1; continue
        # pocket = protein atoms near the ligand (any pose), capped to nearest max_pocket by centroid distance
        centroid = lig_xyz.reshape(-1, 3).mean(0)
        if poc_xyz.shape[0]:
            dmin = np.linalg.norm(poc_xyz[None, :, :] - lig_xyz.reshape(-1, 3)[:, None, :], axis=2).min(0)
            near = dmin < a.pocket_radius
            poc_xyz, poc_elem = poc_xyz[near], poc_elem[near]
            if poc_xyz.shape[0] > a.max_pocket:
                order = np.argsort(np.linalg.norm(poc_xyz - centroid, axis=1))[:a.max_pocket]
                poc_xyz, poc_elem = poc_xyz[order], poc_elem[order]
        np.savez_compressed(dst, poc_xyz=poc_xyz.astype(np.float32), poc_elem=poc_elem.astype(np.int16),
                            lig_xyz=lig_xyz.astype(np.float32), lig_elem=lig_elem.astype(np.int16),
                            rmsd=rmsd.astype(np.float32), pdb=pdb, split=row["split"])
        done += 1
        if (i + 1) % 100 == 0:
            print(f"  ...{i + 1}/{len(rows)}  (written {done}, skipped {skipped})")
    print(f"done: wrote {done} graphs to {a.out}, skipped {skipped}. NELEM={NELEM}")


if __name__ == "__main__":
    main()
