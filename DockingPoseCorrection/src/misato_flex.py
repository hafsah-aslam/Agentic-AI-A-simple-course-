"""Stage 3a: MISATO trajectory flexibility (per-residue RMSF over the 100-frame MD trajectory).

MISATO MD.hdf5 (133 GB) is read remotely with HTTP range requests; only the group of each internal complex is
fetched. MISATO coordinates are translated relative to the crystal frame, so the offset is estimated from the
ligand centroid and verified on protein heavy atoms (median nearest-neighbour distance). Frames are Kabsch-
aligned on protein heavy atoms before RMSF.

Output per complex: DATA/misato/{pdb}.npz with heavy-atom coordinates (crystal frame), residue index per atom,
per-residue RMSF, and the verification distance.

Usage: python3 misato_flex.py MANIFEST DATA_DIR WORKER NWORKERS
"""
import sys, os, json, time
import numpy as np
import pandas as pd
import fsspec, h5py
from scipy.spatial import cKDTree
import networkx as nx
from networkx.algorithms import isomorphism
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
URL = "https://zenodo.org/records/7711953/files/MD.hdf5?download=1"


def kabsch(P, Q):
    """Rotation R and translation t minimising |(P R + t) - Q|."""
    pc, qc = P.mean(0), Q.mean(0)
    H = (P - pc).T @ (Q - qc)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1, 1, d])
    R = U @ D @ Vt
    return R, qc - pc @ R


def ligand_graph(xyz, z):
    """Heavy-atom connectivity graph from coordinates (covalent-radius rule)."""
    rad = {6: 0.76, 7: 0.71, 8: 0.66, 9: 0.57, 15: 1.07, 16: 1.05, 17: 1.02, 35: 1.20, 53: 1.39, 5: 0.84, 14: 1.11, 34: 1.20}
    G = nx.Graph()
    for i, zi in enumerate(z):
        G.add_node(i, z=int(zi))
    d = np.linalg.norm(xyz[:, None] - xyz[None], axis=2)
    for i in range(len(z)):
        for j in range(i + 1, len(z)):
            if d[i, j] < rad.get(int(z[i]), 0.8) + rad.get(int(z[j]), 0.8) + 0.45:
                G.add_edge(i, j)
    return G


def register(mis_xyz, mis_z, ref):
    """Rigid transform taking MISATO ligand heavy atoms onto the crystal ligand (graph isomorphism + Kabsch)."""
    rx = ref.GetConformer().GetPositions()
    Gr = nx.Graph()
    for a in ref.GetAtoms():
        Gr.add_node(a.GetIdx(), z=a.GetAtomicNum())
    for b in ref.GetBonds():
        Gr.add_edge(b.GetBeginAtomIdx(), b.GetEndAtomIdx())
    Gm = ligand_graph(mis_xyz, mis_z)
    gm = isomorphism.GraphMatcher(Gr, Gm, node_match=lambda a, b: a["z"] == b["z"])
    best = None
    for k, m in enumerate(gm.isomorphisms_iter()):
        idx = [m[i] for i in range(len(rx))]
        R, t = kabsch(mis_xyz[idx], rx)
        rmsd = float(np.sqrt((((mis_xyz[idx] @ R + t) - rx) ** 2).sum(1).mean()))
        if best is None or rmsd < best[0]:
            best = (rmsd, R, t)
        if k >= 200:
            break
    if best is None:
        raise RuntimeError("ligand graph mismatch between MISATO and crystal")
    return best


def process(h, pdb, data):
    g = h[pdb.upper()]
    z = g["atoms_number"][:]
    mb = g["molecules_begin_atom_index"][:]
    traj = g["trajectory_coordinates"][:]            # (100, natoms, 3)
    lig_start = int(mb[-1])
    heavy = z > 1
    ph = heavy.copy(); ph[lig_start:] = False
    lh = heavy.copy(); lh[:lig_start] = False
    ref = Chem.MolFromMolFile(f"{data}/internal/{pdb}/ligand_ref.sdf")
    lig_rmsd, R, t = register(traj[0][lh], z[lh], ref)
    crystal = []
    for line in open(f"{data}/internal/{pdb}/protein.pdb"):
        if line.startswith(("ATOM", "HETATM")):
            crystal.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    crystal = np.array(crystal)
    x0 = traj[0][ph] @ R + t
    near = cKDTree(crystal).query(x0)[0]
    P0 = traj[0][ph]
    aligned = np.empty((traj.shape[0], ph.sum(), 3))
    for k in range(traj.shape[0]):
        Rk, tk = kabsch(traj[k][ph], P0)
        aligned[k] = traj[k][ph] @ Rk + tk
    rmsf_atom = np.sqrt(((aligned - aligned.mean(0)) ** 2).sum(2).mean(0))
    np.savez_compressed(f"{data}/misato/{pdb}.npz", xyz=x0.astype(np.float32), rmsf=rmsf_atom.astype(np.float32),
                        median_nn=np.float32(np.median(near)), lig_rmsd=np.float32(lig_rmsd))
    return float(np.median(near))


def main():
    man, data, wid, nw = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    os.makedirs(f"{data}/misato", exist_ok=True)
    df = pd.read_csv(man)
    pdbs = [p for p, s in zip(df.pdb, df.split) if s in ("train", "val", "test")][wid::nw]
    h = None
    for pdb in pdbs:
        out = f"{data}/misato/{pdb}.npz"
        if os.path.exists(out) or os.path.exists(out + ".fail"):
            continue
        for attempt in range(5):
            try:
                if h is None:
                    f = fsspec.open(URL, block_size=4 * 2 ** 20, cache_type="blockcache").open()
                    h = h5py.File(f, "r")
                t = time.time()
                d = process(h, pdb, data)
                print(pdb, "ok", round(d, 3), round(time.time() - t, 1), flush=True)
                break
            except KeyError:
                open(out + ".fail", "w").write("not in MD.hdf5"); print(pdb, "missing", flush=True); break
            except Exception as e:
                msg = f"{type(e).__name__}: {e}"[:200]
                print(pdb, "retry", attempt, msg, flush=True)
                h = None
                time.sleep(30 * (attempt + 1))
        else:
            open(out + ".fail", "w").write(msg)


if __name__ == "__main__":
    main()
