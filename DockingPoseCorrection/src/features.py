"""Stage 3b: ligand and pocket-geometry features.

Ligand: heavy atoms of the rank-1 docked pose (docked atom order), 18 chemistry features, coordinates relative to
the docked-ligand centroid. Target: reference coordinates in the same order (symmetry-aware mapping from dock.py).
Pocket: residues with any heavy atom within 8 A of any docked ligand heavy atom (defined from the docked pose only).
28 residue-node features: 20 amino-acid one-hot, C-alpha position (3), side-chain-centroid offset (3), local
degree (1), MISATO flexibility (1). Graph edges: C-alpha pairs within 10 A. Hyperedges: chain segments of
consecutive residue numbers. Flexibility for residues without a mapped MISATO atom is imputed later with the
frozen training mean (see build_dataset).

Usage: python3 features.py MANIFEST DATA_DIR PB_DIR DOCK_DIR OUT_PICKLE
"""
import sys, os, json, pickle
import numpy as np
import pandas as pd
import gemmi
from scipy.spatial import cKDTree
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
AA = "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split()
ALIAS = {"MSE": "MET", "SEP": "SER", "TPO": "THR", "PTR": "TYR", "HYP": "PRO", "CSO": "CYS", "HID": "HIS", "HIE": "HIS", "HIP": "HIS"}
ELEM = ["C", "N", "O", "S", "P", "F", "Cl", "Br", "I"]
HYB = [Chem.HybridizationType.SP, Chem.HybridizationType.SP2, Chem.HybridizationType.SP3]
POCKET_CUTOFF, EDGE_CUTOFF, MAP_TOL = 8.0, 10.0, 1.5
MISATO_LIG_RMSD, MISATO_MEDIAN_NN = 2.0, 2.5   # registration acceptance (A)


def atom_features(a):
    e = [0.0] * 10
    s = a.GetSymbol()
    e[ELEM.index(s) if s in ELEM else 9] = 1.0
    return e + [min(a.GetDegree(), 4) / 4, float(a.GetIsAromatic()), float(a.IsInRing()), float(a.GetFormalCharge()),
                min(a.GetTotalNumHs(), 3) / 3] + [float(a.GetHybridization() == h) for h in HYB]


def protein_residues(path):
    st = gemmi.read_structure(path)
    st.remove_alternative_conformations()
    out = []
    for ch in st[0]:
        for r in ch:
            name = ALIAS.get(r.name, r.name)
            if name not in AA:
                continue
            heavy = np.array([[a.pos.x, a.pos.y, a.pos.z] for a in r if a.element.name != "H"])
            ca = r.find_atom("CA", "*")
            if ca is None or len(heavy) == 0:
                continue
            side = [[a.pos.x, a.pos.y, a.pos.z] for a in r if a.element.name != "H" and a.name not in ("N", "CA", "C", "O")]
            out.append({"chain": ch.name, "num": r.seqid.num, "aa": AA.index(name),
                        "ca": np.array([ca.pos.x, ca.pos.y, ca.pos.z]),
                        "sc": np.mean(side, 0) if side else np.array([ca.pos.x, ca.pos.y, ca.pos.z]), "heavy": heavy})
    return out


def featurize(row, data, pb, dockdir):
    pdb, split = row["pdb"], row["split"]
    info = json.load(open(f"{dockdir}/{pdb}/match.json"))
    if info["status"] != "ok":
        return None
    dock = Chem.MolFromMolFile(f"{dockdir}/{pdb}/docked.sdf", removeHs=False)
    heavy = Chem.RemoveHs(dock)
    dxyz = heavy.GetConformer().GetPositions()
    if split == "external":
        prot = f"{pb}/posebusters_benchmark_set/{pdb}/{pdb}_protein.pdb"
        ref = Chem.MolFromMolFile(f"{pb}/posebusters_benchmark_set/{pdb}/{pdb}_ligand.sdf")
    else:
        prot = f"{data}/internal/{pdb}/protein.pdb"
        ref = Chem.MolFromMolFile(f"{data}/internal/{pdb}/ligand_ref.sdf")
    rxyz = ref.GetConformer().GetPositions()
    m = info["mapping"]
    target = np.zeros_like(dxyz)
    target[m] = rxyz                       # reference coordinates in docked atom order
    centre = dxyz.mean(0)
    res = protein_residues(prot)
    tree = cKDTree(dxyz)
    pocket = [r for r in res if tree.query(r["heavy"])[0].min() <= POCKET_CUTOFF]
    if len(pocket) < 3:
        return None
    ca = np.array([r["ca"] for r in pocket])
    flex = np.full(len(pocket), np.nan)
    misato_qc = "absent"
    if split != "external" and os.path.exists(f"{data}/misato/{pdb}.npz"):
        mz = np.load(f"{data}/misato/{pdb}.npz")
        # registration quality gate: ligand fit and protein agreement after the rigid transform
        misato_qc = "ok" if float(mz["lig_rmsd"]) <= MISATO_LIG_RMSD and float(mz["median_nn"]) <= MISATO_MEDIAN_NN else "failed_registration"
    if misato_qc == "ok":
        mt = cKDTree(mz["xyz"])
        for i, r in enumerate(pocket):
            hits = sorted({j for lst in mt.query_ball_point(r["heavy"], MAP_TOL) for j in lst})
            if hits:
                flex[i] = float(mz["rmsf"][hits].mean())
    d_ca = np.linalg.norm(ca[:, None] - ca[None], axis=2)
    deg = ((d_ca < EDGE_CUTOFF).sum(1) - 1) / 20.0
    onehot = np.eye(20)[[r["aa"] for r in pocket]]
    edges = np.argwhere((d_ca < EDGE_CUTOFF) & ~np.eye(len(pocket), dtype=bool))
    seg, sid = [], -1
    for i, r in enumerate(pocket):
        if i == 0 or r["chain"] != pocket[i - 1]["chain"] or r["num"] != pocket[i - 1]["num"] + 1:
            sid += 1
        seg.append(sid)
    return {"pdb": pdb, "split": split,
            "lig_feat": np.array([atom_features(a) for a in heavy.GetAtoms()], np.float32),
            "lig_xyz": (dxyz - centre).astype(np.float32), "target": (target - dxyz).astype(np.float32),
            "res_aa": onehot.astype(np.float32), "res_xyz": (ca - centre).astype(np.float32),
            "res_sc": np.array([r["sc"] - r["ca"] for r in pocket], np.float32), "res_deg": deg.astype(np.float32),
            "res_flex_raw": flex.astype(np.float32), "edges": edges.astype(np.int64), "segments": np.array(seg, np.int64),
            "misato_qc": misato_qc, "baseline_rmsd": info["baseline_rmsd"], "vina": info["vina_energy"], "centre": centre}


def main():
    man, data, pb, dockdir, outp = sys.argv[1:6]
    df = pd.read_csv(man)
    out, skipped = [], {}
    for row in df.to_dict("records"):
        if not os.path.exists(f"{dockdir}/{row['pdb']}/match.json"):
            skipped["not_docked"] = skipped.get("not_docked", 0) + 1
            continue
        try:
            f = featurize(row, data, pb, dockdir)
        except Exception as e:
            f = None; print(row["pdb"], "feature error", e)
        if f is None:
            skipped[row["split"]] = skipped.get(row["split"], 0) + 1
        else:
            out.append(f)
    pickle.dump(out, open(outp, "wb"))
    print("featurized", pd.Series([o["split"] for o in out]).value_counts().to_dict(), "skipped", skipped)


if __name__ == "__main__":
    main()
