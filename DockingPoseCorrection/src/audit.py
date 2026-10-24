"""Stage 6: full-cohort PoseBusters chemical-validity audit (dock configuration, 22 checks).

For every internal-test and external complex the following ligand poses are audited against the receptor:
  baseline           Vina rank-1 pose (heavy atoms)
  corrected_s{seed}  ungated learned correction, one per seed (gated poses are baseline or corrected, so their
                     validity follows from these rows and the gate decision)
  rigid_s{seed}      NEW: rigid-body projection of the corrected pose (Kabsch fit of the docked pose onto the
                     corrected coordinates), which preserves the docked internal geometry exactly
  ensemble           NEW: mean of the five seeds' corrections
  ensemble_rigid     NEW: rigid projection of the ensemble correction
A pose is valid only if every check is True; a check not computed after an upstream failure counts as failed.
Also records whether the Open Babel PDBQT->SDF conversion of the same pose fails RDKit sanitisation (the
conversion artifact reported in the original study).

Usage: python3 audit.py FEATS.pkl RUNS_DIR ARCH DOCK_DIR DATA_DIR PB_DIR OUT_CSV WORKER NWORKERS
"""
import sys, os, pickle, json
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdmolops
from posebusters import PoseBusters

RDLogger.DisableLog("rdApp.*")
SEEDS = [0, 42, 123, 999, 2026]


def kabsch_apply(P, Q):
    """Rigidly move P to best fit Q (both N x 3) and return the moved P."""
    pc, qc = P.mean(0), Q.mean(0)
    Hm = (P - pc).T @ (Q - qc)
    U, S, Vt = np.linalg.svd(Hm)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return (P - pc) @ R + qc


def with_coords(mol, xyz):
    m = Chem.Mol(mol)
    conf = m.GetConformer()
    for i, p in enumerate(xyz):
        conf.SetAtomPosition(i, p.tolist())
    return m


def obabel_artifact(path):
    """Count N atoms with explicit valence 4 and formal charge 0 in the Open Babel conversion; report whether
    strict RDKit sanitisation fails."""
    m = Chem.MolFromMolFile(path, sanitize=False, removeHs=False)
    if m is None:
        return {"obabel_parse": False}
    m.UpdatePropertyCache(strict=False)
    bad = sum(1 for a in m.GetAtoms() if a.GetSymbol() == "N" and a.GetExplicitValence() == 4 and a.GetFormalCharge() == 0)
    try:
        Chem.SanitizeMol(Chem.Mol(m)); ok = True
    except Exception:
        ok = False
    return {"obabel_parse": True, "obabel_sanitizes": ok, "obabel_n_valence4_uncharged": bad}


def main():
    feats_p, runs, arch, dockdir, data, pbdir, out, wid, nw = sys.argv[1:8] + [int(sys.argv[8]), int(sys.argv[9])]
    keep = ("test",) if os.environ.get("ONLY_TEST") else ("test", "external")
    only = set(os.environ["ONLY_PDBS"].split(",")) if os.environ.get("ONLY_PDBS") else None
    feats = {d["pdb"]: d for d in pickle.load(open(feats_p, "rb")) if d["split"] in keep and (only is None or d["pdb"] in only)}
    preds = {s: pickle.load(open(f"{runs}/{arch}_s{s}.pkl", "rb"))["predictions"] for s in SEEDS}
    bust = PoseBusters(config="dock")
    rows = []
    for pdb in sorted(feats)[wid::nw]:
        d = feats[pdb]
        prot = (f"{pbdir}/posebusters_benchmark_set/{pdb}/{pdb}_protein.pdb" if d["split"] == "external"
                else f"{data}/internal/{pdb}/protein.pdb")
        if os.path.exists(prot.replace("protein.pdb", "protein_pb.pdb")):
            prot = prot.replace("protein.pdb", "protein_pb.pdb")   # polymer-only copy for receptors RDKit cannot parse
        base = Chem.RemoveHs(Chem.MolFromMolFile(f"{dockdir}/{pdb}/docked.sdf", removeHs=False))
        X = base.GetConformer().GetPositions()
        poses = [("baseline", None, base)]
        ens = np.mean([preds[s][pdb]["pred"] for s in SEEDS], 0)
        for s in SEEDS:
            corr = X + preds[s][pdb]["pred"]
            poses.append(("corrected", s, with_coords(base, corr)))
            poses.append(("rigid", s, with_coords(base, kabsch_apply(X, corr))))
        poses.append(("ensemble", None, with_coords(base, X + ens)))
        poses.append(("ensemble_rigid", None, with_coords(base, kabsch_apply(X, X + ens))))
        try:
            df = bust.bust([p[2] for p in poses], None, prot)
            df = df.reset_index(drop=True)
        except Exception as e:
            print(pdb, "posebusters error", e, flush=True)
            continue
        art = obabel_artifact(f"{dockdir}/{pdb}/docked_obabel.sdf")
        checks = [c for c in df.columns]
        for (variant, seed, m), (_, r) in zip(poses, df.iterrows()):
            vals = {c: bool(r[c]) if pd.notna(r[c]) else False for c in checks}
            rows.append({"pdb": pdb, "cohort": d["split"], "variant": variant, "seed": seed, **vals,
                         "valid": all(vals.values()), **art})
        print(pdb, "done", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)


if __name__ == "__main__":
    main()
