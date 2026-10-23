"""Stage 2b: docked/reference atom matching and baseline RMSD.

Meeko's PDBQT->RDKit export does not preserve the input atom order, so correspondence is established by
element-labelled heavy-atom graph isomorphism between the docked and reference ligands. Among all isomorphisms
(graph automorphisms make several valid), the one with the smallest in-place RMSD is used (symmetry-corrected
RMSD, no superposition). Complexes whose graphs are not isomorphic fail atom matching and are excluded.

Usage: python3 match.py MANIFEST DATA_DIR PB_DIR DOCK_DIR
Writes DOCK_DIR/{pdb}/match.json.
"""
import sys, os, json
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import isomorphism
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")


def graph(mol):
    G = nx.Graph()
    for a in mol.GetAtoms():
        G.add_node(a.GetIdx(), z=a.GetAtomicNum())
    for b in mol.GetBonds():
        G.add_edge(b.GetBeginAtomIdx(), b.GetEndAtomIdx())
    return G


def heavy_mapping(dock_heavy, ref, max_iso=20000):
    """Return (msd, m) with m[k] = docked atom index matched to reference atom k."""
    dx = dock_heavy.GetConformer().GetPositions()
    rx = ref.GetConformer().GetPositions()
    if dock_heavy.GetNumAtoms() != ref.GetNumAtoms():
        return None
    gm = isomorphism.GraphMatcher(graph(ref), graph(dock_heavy), node_match=lambda a, b: a["z"] == b["z"])
    best = None
    for n, iso in enumerate(gm.isomorphisms_iter()):
        m = [iso[k] for k in range(len(rx))]
        msd = float(((dx[m] - rx) ** 2).sum(1).mean())
        if best is None or msd < best[0]:
            best = (msd, m)
        if n >= max_iso:
            break
    return best


def ref_path(row, data, pb):
    if row["split"] == "external":
        return f"{pb}/posebusters_benchmark_set/{row['pdb']}/{row['pdb']}_ligand.sdf"
    return f"{data}/internal/{row['pdb']}/ligand_ref.sdf"


def main():
    man, data, pb, dockdir = sys.argv[1:5]
    df = pd.read_csv(man)
    for row in df.to_dict("records"):
        d = f"{dockdir}/{row['pdb']}"
        if not os.path.exists(f"{d}/dock.json") or os.path.exists(f"{d}/match.json"):
            continue
        info = json.load(open(f"{d}/dock.json"))
        res = {"pdb": row["pdb"], "split": row["split"]}
        if info["status"] != "ok":
            res.update(status="dock_failed", error=info.get("error"))
        else:
            dock = Chem.RemoveHs(Chem.MolFromMolFile(f"{d}/docked.sdf", removeHs=False))
            ref = Chem.MolFromMolFile(ref_path(row, data, pb))
            best = heavy_mapping(dock, ref) if dock is not None and ref is not None else None
            if best is None:
                res.update(status="atom_matching_failed")
            else:
                res.update(status="ok", baseline_rmsd=best[0] ** 0.5, mapping=list(map(int, best[1])), n_atoms=ref.GetNumAtoms(),
                           vina_energy=info["vina_energies"][0])
        json.dump(res, open(f"{d}/match.json", "w"))


if __name__ == "__main__":
    main()
