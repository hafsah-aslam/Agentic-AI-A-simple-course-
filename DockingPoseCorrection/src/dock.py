"""Stage 2: AutoDock Vina docking (20 A cubic box, exhaustiveness 8, five poses, rank-1 selection) and
docked/reference atom matching.

The docking input conformer is generated from the ligand graph with ETKDG + MMFF (crystal coordinates are
discarded), so the docked pose carries no crystal information beyond the pocket-informed box centre.
Output per complex: docked.sdf (rank-1, all H), docked_obabel.sdf (same pose converted by Open Babel, used only
for the conversion-artifact analysis), dock.json (energies, timing, atom mapping, baseline RMSD).

Usage: python3 dock.py MANIFEST DATA_DIR PB_DIR OUT_DIR WORKER NWORKERS
"""
import sys, os, json, time, subprocess, tempfile
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from vina import Vina
from meeko import MoleculePreparation, PDBQTWriterLegacy, PDBQTMolecule, RDKitMolCreate

RDLogger.DisableLog("rdApp.*")
MAN, DATA, PB, OUT, WID, NW = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
BOX, EXH, NPOSES, SEED = 20.0, 8, 5, 2026
VINA_TYPES = {"C", "A", "N", "NA", "NS", "OA", "OS", "SA", "S", "H", "HD", "HS", "P", "F", "Cl", "Br", "I", "Mg", "Ca", "Mn", "Fe", "Zn"}


def paths(row):
    if row["split"] == "external":
        d = f"{PB}/posebusters_benchmark_set/{row['pdb']}"
        return f"{d}/{row['pdb']}_protein.pdb", f"{d}/{row['pdb']}_ligand.sdf"
    d = f"{DATA}/internal/{row['pdb']}"
    return f"{d}/protein.pdb", f"{d}/ligand_ref.sdf"


def best_mapping(ref, dock_xyz):
    """Symmetry-aware heavy-atom correspondence: the automorphism of the reference graph that minimises RMSD
    between docked and reference coordinates (no superposition)."""
    ref_xyz = ref.GetConformer().GetPositions()
    autos = ref.GetSubstructMatches(ref, uniquify=False, useChirality=False, maxMatches=5000)
    best = None
    for m in autos:
        msd = float(((dock_xyz[list(m)] - ref_xyz) ** 2).sum(1).mean())
        if best is None or msd < best[0]:
            best = (msd, m)
    return best


def dock_one(row, outdir):
    t0 = time.time()
    prot, ligf = paths(row)
    ref = Chem.MolFromMolFile(ligf, removeHs=True, sanitize=True)
    if ref is None:
        raise RuntimeError("reference ligand not sanitizable")
    center = ref.GetConformer().GetPositions().mean(0)
    # docking input: fresh conformer from the graph
    lig = Chem.AddHs(Chem.Mol(ref))
    lig.RemoveAllConformers()
    params = AllChem.ETKDGv3(); params.randomSeed = SEED
    if AllChem.EmbedMolecule(lig, params) != 0:
        params.useRandomCoords = True
        if AllChem.EmbedMolecule(lig, params) != 0:
            raise RuntimeError("ETKDG embedding failed")
    AllChem.MMFFOptimizeMolecule(lig, maxIters=500)
    setups = MoleculePreparation().prepare(lig)
    lig_pdbqt, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        raise RuntimeError(f"meeko: {err}")
    rec = f"{outdir}/receptor.pdbqt"
    if not os.path.exists(rec):
        r = subprocess.run(["obabel", "-ipdb", prot, "-xr", "-h", "-opdbqt", "-O", rec], capture_output=True, text=True)
        if not os.path.exists(rec) or os.path.getsize(rec) < 100:
            raise RuntimeError("receptor preparation failed: " + r.stderr[-300:])
        # drop receptor atoms whose AutoDock type Vina cannot score (e.g. Mo, Xe, B, Na, K)
        keep, dropped = [], 0
        for line in open(rec):
            if line.startswith(("ATOM", "HETATM")) and line[77:79].strip() not in VINA_TYPES:
                dropped += 1; continue
            keep.append(line)
        open(rec, "w").writelines(keep)
        open(f"{outdir}/receptor_dropped_atoms.txt", "w").write(str(dropped))
    v = Vina(sf_name="vina", cpu=1, seed=SEED, verbosity=0)
    v.set_receptor(rec)
    v.set_ligand_from_string(lig_pdbqt)
    v.compute_vina_maps(center=center.tolist(), box_size=[BOX] * 3)
    v.dock(exhaustiveness=EXH, n_poses=NPOSES)
    out = v.poses(n_poses=NPOSES)
    energies = v.energies(n_poses=NPOSES)[:, 0].tolist()
    open(f"{outdir}/poses.pdbqt", "w").write(out)
    pm = PDBQTMolecule(out, skip_typing=True)
    mols = RDKitMolCreate.from_pdbqt_mol(pm)
    dock = mols[0]
    # keep only rank-1 conformer
    keep = Chem.Mol(dock); keep.RemoveAllConformers(); keep.AddConformer(dock.GetConformer(0), assignId=True)
    w = Chem.SDWriter(f"{outdir}/docked.sdf"); w.write(keep); w.close()
    subprocess.run(["obabel", "-ipdbqt", f"{outdir}/poses.pdbqt", "-l", "1", "-osdf", "-O", f"{outdir}/docked_obabel.sdf"],
                   capture_output=True)
    heavy = Chem.RemoveHs(keep)
    if heavy.GetNumAtoms() != ref.GetNumAtoms():
        raise RuntimeError("atom matching failed: heavy-atom count differs")
    from match import heavy_mapping   # meeko does not preserve atom order: match by graph isomorphism
    msd, mapping = heavy_mapping(heavy, ref)
    return {"pdb": row["pdb"], "split": row["split"], "status": "ok", "vina_energies": energies,
            "baseline_rmsd": msd ** 0.5, "n_atoms": ref.GetNumAtoms(), "mapping": list(map(int, mapping)),
            "center": center.tolist(), "seconds": time.time() - t0}


def main():
    man = pd.read_csv(MAN)
    rows = man.to_dict("records")
    start = WID * len(rows) // NW
    rows = rows[start:] + rows[:start]   # every worker walks the whole list from its own offset: claims prevent
                                         # duplicates, and no complex is stranded if another worker dies
    for row in rows:
        outdir = f"{OUT}/{row['pdb']}"
        os.makedirs(outdir, exist_ok=True)
        if os.path.exists(f"{outdir}/dock.json"):
            continue
        try:   # claim the complex so several worker pools can share one manifest
            os.close(os.open(f"{outdir}/claim", os.O_CREAT | os.O_EXCL))
        except FileExistsError:
            continue
        try:
            res = dock_one(row, outdir)
        except Exception as e:
            res = {"pdb": row["pdb"], "split": row["split"], "status": "failed", "error": f"{type(e).__name__}: {e}"[:400]}
        json.dump(res, open(f"{outdir}/dock.json", "w"))
        print(row["pdb"], res["status"], round(res.get("seconds", 0), 1), round(res.get("baseline_rmsd", -1), 2), flush=True)


if __name__ == "__main__":
    main()
