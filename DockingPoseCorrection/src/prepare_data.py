"""Stage 1: eligibility, provenance, leakage-controlled manifest, and structure preparation.

Internal pool: exact intersection of PDBbind v2020 P-L identifiers (as distributed in LP-PDBBind, which covers
all 19,443 P-L entries) with LP-PDBBind and MISATO MD identifiers. External cohort: the 428-complex PoseBusters
benchmark set. Structures for internal complexes are downloaded from the RCSB PDB (mmCIF); the crystal ligand is
located by heavy-atom count and its chemistry is assigned from the LP-PDBBind SMILES template.

Usage: python3 prepare_data.py DATA_DIR LP_CSV MISATO_DIR POSEBUSTERS_DIR MANIFEST_OUT_DIR
"""
import sys, os, json, hashlib, urllib.request, time, traceback
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import gemmi
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

RDLogger.DisableLog("rdApp.*")
DATA, LP_CSV, MIS_DIR, PB_DIR, MAN = sys.argv[1:6]
TARGET = {"train": 1200, "val": 400, "test": 400}
if os.environ.get("DPC_TARGET"):          # e.g. "20,5,5" for a quick smoke test; leave unset for the real study
    TARGET = dict(zip(("train", "val", "test"), map(int, os.environ["DPC_TARGET"].split(","))))
# Docking applicability limit: ligands with more rotatable bonds (long peptides, mostly) take Vina hours to days
# at exhaustiveness 8 and are outside its reliable range. The PoseBusters set has at most 20.
MAX_ROTB = int(os.environ.get("DPC_MAX_ROTB", 30))
IGNORE = set("HOH WAT DOD NA CL K MG CA ZN MN FE CO NI CU CD HG SO4 PO4 GOL EDO PEG ACT FMT DMS BR IOD NO3 SCN".split())
# crystallisation additives removed from the receptor; metals and organic cofactors are kept (as in the
# PoseBusters receptor files used for the external cohort)
ADDITIVES = set("HOH WAT DOD SO4 PO4 GOL EDO PEG PG4 PGE 1PE ACT FMT DMS IOD NO3 SCN MPD TRS EPE MES BME CIT ACY IPA EOH".split())
AA = set("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL MSE SEP TPO PTR HYP CSO".split())


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def fetch(pdb):
    path = f"{DATA}/raw/{pdb}.cif"
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    for attempt in range(4):
        try:
            data = urllib.request.urlopen(f"https://files.rcsb.org/download/{pdb.upper()}.cif", timeout=60).read()
            with open(path, "wb") as f:
                f.write(data)
            return path
        except Exception:
            time.sleep(2 ** attempt)
    raise RuntimeError("download failed")


def residue_pdb_block(res, chain_name):
    lines = []
    for i, a in enumerate(res, 1):
        if a.element.name == "H":
            continue
        lines.append("HETATM%5d %-4s %3s %1s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s" % (
            i, a.name[:4], res.name[:3], chain_name[:1], res.seqid.num, a.pos.x, a.pos.y, a.pos.z, a.element.name.upper()))
    return "\n".join(lines) + "\nEND\n"


def write_receptor(st, ligand_key, path, lig_xyz):
    """Receptor = polymer residues + metals + organic cofactors; drop water, additives, hydrogens, the ligand,
    and any hetero group overlapping the ligand site (alternate ligand copies, < 1 A from a ligand atom)."""
    from scipy.spatial import cKDTree
    lt = cKDTree(lig_xyz)
    model = st[0]
    prot = gemmi.Structure(); prot.cell = st.cell
    m = gemmi.Model("1")
    for ch in model:
        nc = gemmi.Chain(ch.name)
        for r in ch:
            if r.is_water() or r.name in ADDITIVES or (ch.name, str(r.seqid), r.name) == ligand_key:
                continue
            if r.het_flag == "H" and lt.query(np.array([[a.pos.x, a.pos.y, a.pos.z] for a in r]))[0].min() < 1.0:
                continue
            nr = gemmi.Residue(); nr.name, nr.seqid, nr.het_flag = r.name, r.seqid, r.het_flag
            for a in r:
                if a.element.name != "H":
                    nr.add_atom(a)
            if len(nr):
                nc.add_residue(nr)
        if len(nc):
            m.add_chain(nc)
    prot.add_model(m)
    prot.setup_entities()
    prot.write_pdb(path)


def rebuild_receptors(manifest):
    """Re-write internal receptors (used after the stripped-receptor version was replaced)."""
    from scipy.spatial import cKDTree
    man = pd.read_csv(manifest)
    for p in man[man.split != "external"].pdb:
        st = gemmi.read_structure(f"{DATA}/raw/{p}.cif"); st.setup_entities(); st.remove_alternative_conformations()
        lig = Chem.MolFromMolFile(f"{DATA}/internal/{p}/ligand_ref.sdf").GetConformer().GetPositions()
        tree = cKDTree(lig); key = None
        for ch in st[0]:
            for r in ch:
                xyz = np.array([[a.pos.x, a.pos.y, a.pos.z] for a in r if a.element.name != "H"])
                if len(xyz) == len(lig) and tree.query(xyz)[0].max() < 1e-3:
                    key = (ch.name, str(r.seqid), r.name)
        if key is None:
            raise RuntimeError(f"{p}: ligand residue not found")
        write_receptor(st, key, f"{DATA}/internal/{p}/protein.pdb", lig)


_PDBBIND_INDEX = None


def pdbbind_files(pdb):
    """Locate {pdb}_protein.pdb and {pdb}_ligand.sdf/.mol2 anywhere under $PDBBIND_DIR (any PDBbind release layout)."""
    global _PDBBIND_INDEX
    root = os.environ.get("PDBBIND_DIR")
    if not root:
        return None
    if _PDBBIND_INDEX is None:
        _PDBBIND_INDEX = {}
        for dirpath, _, files in os.walk(root):
            for f in files:
                code, _, kind = f.partition("_")
                if kind in ("protein.pdb", "ligand.sdf", "ligand.mol2"):
                    _PDBBIND_INDEX.setdefault(code.lower(), {})[kind] = os.path.join(dirpath, f)
    return _PDBBIND_INDEX.get(pdb.lower())


def prepare_from_pdbbind(pdb, files, out):
    """Use the curated PDBbind protein and ligand files (also covers multi-residue / peptide ligands)."""
    mol = None
    if "ligand.sdf" in files:
        mol = Chem.MolFromMolFile(files["ligand.sdf"], removeHs=True, sanitize=True)
    if mol is None and "ligand.mol2" in files:
        mol = Chem.MolFromMol2File(files["ligand.mol2"], removeHs=True, sanitize=True)
    if mol is None or "protein.pdb" not in files:
        return "ligand_parse_failure", "PDBbind ligand not sanitizable or protein missing"
    os.makedirs(out, exist_ok=True)
    mol.SetProp("_Name", f"{pdb}_pdbbind_ligand")
    w = Chem.SDWriter(f"{out}/ligand_ref.sdf"); w.write(mol); w.close()
    st = gemmi.read_structure(files["protein.pdb"]); st.setup_entities(); st.remove_alternative_conformations()
    write_receptor(st, None, f"{out}/protein.pdb", mol.GetConformer().GetPositions())
    return "ok", {"ligand_resname": "PDBbind", "ligand_chain": "", "n_heavy": mol.GetNumAtoms()}


def prepare_internal(row):
    """Return (status, info). Writes protein.pdb and ligand_ref.sdf on success.
    With $PDBBIND_DIR set, PDBbind's own files are used; otherwise structures are taken from the RCSB PDB."""
    pdb, smiles = row["pdb"], row["smiles"]
    out = f"{DATA}/internal/{pdb}"
    files = pdbbind_files(pdb)
    if files:
        try:
            return prepare_from_pdbbind(pdb, files, out)
        except Exception as e:
            return "structure_failure", f"PDBbind: {type(e).__name__}: {e}"
    try:
        tmpl = Chem.MolFromSmiles(smiles)
        if tmpl is None:
            return "ligand_parse_failure", "template SMILES not parseable"
        nheavy = tmpl.GetNumHeavyAtoms()
        st = gemmi.read_structure(fetch(pdb))
        st.setup_entities()
        st.remove_alternative_conformations()
        model = st[0]
        best = None
        for ch in model:
            for res in ch:
                if res.name in IGNORE or res.name in AA or res.is_water():
                    continue
                if res.entity_type not in (gemmi.EntityType.NonPolymer, gemmi.EntityType.Branched, gemmi.EntityType.Unknown):
                    continue
                if sum(1 for a in res if a.element.name != "H") != nheavy:
                    continue
                mol = Chem.MolFromPDBBlock(residue_pdb_block(res, ch.name), removeHs=True, proximityBonding=True, sanitize=False)
                if mol is None:
                    continue
                try:
                    mol = AllChem.AssignBondOrdersFromTemplate(tmpl, mol)
                    Chem.SanitizeMol(mol)
                except Exception:
                    continue
                best = (ch.name, res, mol)
                break
            if best:
                break
        if best is None:
            return "ligand_not_located", f"no single residue with {nheavy} heavy atoms matching the template"
        chain_name, res, mol = best
        os.makedirs(out, exist_ok=True)
        mol.SetProp("_Name", f"{pdb}_{res.name}")
        w = Chem.SDWriter(f"{out}/ligand_ref.sdf"); w.write(mol); w.close()
        write_receptor(st, (chain_name, str(res.seqid), res.name), f"{out}/protein.pdb", mol.GetConformer().GetPositions())
        return "ok", {"ligand_resname": res.name, "ligand_chain": chain_name, "n_heavy": nheavy}
    except Exception as e:
        return "structure_failure", f"{type(e).__name__}: {e}"


def prepare_eligible(row):
    st, info = prepare_internal(row)
    if st == "ok":
        from rdkit.Chem import rdMolDescriptors
        mol = Chem.MolFromMolFile(f"{DATA}/internal/{row['pdb']}/ligand_ref.sdf")
        nrot = rdMolDescriptors.CalcNumRotatableBonds(mol)
        if nrot > MAX_ROTB:
            return "too_flexible", f"{nrot} rotatable bonds > {MAX_ROTB}"
    return st, info


def main():
    os.makedirs(f"{DATA}/raw", exist_ok=True)
    lp = pd.read_csv(LP_CSV).rename(columns={"Unnamed: 0": "pdb"})
    misato = set()
    for f in ("train_MD.txt", "val_MD.txt", "test_MD.txt"):
        misato |= {x.strip().lower() for x in open(f"{MIS_DIR}/{f}") if x.strip()}
    pb_ids = sorted(os.listdir(f"{PB_DIR}/posebusters_benchmark_set"))
    pb_pdb = {x.split("_")[0].lower() for x in pb_ids}
    log = {"pdbbind_pl": int(len(lp)), "misato_md": len(misato), "max_rotatable_bonds": MAX_ROTB}
    pool = lp[lp.pdb.isin(misato)].copy()
    log["three_way_intersection"] = int(len(pool))
    log["excluded_covalent"] = int(pool.covalent.sum())
    pool = pool[~pool.covalent]
    log["excluded_external_pdb_overlap"] = int(pool.pdb.isin(pb_pdb).sum())
    pool = pool[~pool.pdb.isin(pb_pdb)]
    # leakage-control group: identical protein sequence (LP-PDBBind provides the chain sequence per entry)
    pool["group_id"] = pool.seq.fillna("").map(lambda s: "seq:" + sha(s)[:16])
    pool["order_key"] = pool.group_id.map(sha)
    groups = pool.sort_values(["order_key", "group_id", "pdb"]).groupby("group_id", sort=False)
    ordered = [(gid, g.sort_values("pdb")) for gid, g in groups]
    ordered.sort(key=lambda t: (sha(t[0]), t[0]))
    log["candidate_groups"] = len(ordered)

    # fill train -> val -> test; eligibility (structure + ligand) is checked before a complex takes a slot
    rows, status_counts, touched = [], {}, 0
    split_iter = iter(["train", "val", "test"])
    split = next(split_iter)
    filled = {k: 0 for k in TARGET}
    gi = 0
    with ThreadPoolExecutor(8) as ex:
        while split is not None and gi < len(ordered):
            batch = ordered[gi:gi + 40]
            gi += len(batch)
            members = [r for _, g in batch for r in g.to_dict("records")]
            results = dict(zip([m["pdb"] for m in members], ex.map(prepare_eligible, members)))
            for gid, g in batch:
                if split is None:
                    break
                touched += 1
                for r in g.to_dict("records"):
                    st, info = results[r["pdb"]]
                    status_counts[st] = status_counts.get(st, 0) + 1
                    if st != "ok":
                        continue
                    if split is None or filled[split] >= TARGET[split]:
                        r["split"] = "retired"   # unselected member of the boundary group
                    else:
                        r["split"] = split; filled[split] += 1
                    rows.append({"pdb": r["pdb"], "split": r["split"], "group_id": gid, "smiles": r["smiles"],
                                 "category": r["category"], "resolution": r["resolution"], **info})
                if split is not None and filled[split] >= TARGET[split]:
                    split = next(split_iter, None)
            print(f"groups {gi}/{len(ordered)} filled {filled} statuses {status_counts}", flush=True)
    log["candidate_touching_groups"] = touched
    log["eligibility_status_counts"] = status_counts
    man = pd.DataFrame(rows)
    man = man[man.split != "retired"]
    # internal group integrity check
    crossing = man.groupby("group_id").split.nunique()
    log["groups_crossing_splits"] = int((crossing > 1).sum())
    for pb in pb_ids:
        man = pd.concat([man, pd.DataFrame([{"pdb": pb, "split": "external", "group_id": "posebusters:" + pb}])])
    log["split_counts"] = man.split.value_counts().to_dict()
    log["internal_external_pdb_overlap"] = int(len(set(man[man.split != "external"].pdb) & pb_pdb))
    os.makedirs(MAN, exist_ok=True)
    man.to_csv(f"{MAN}/manifest.csv", index=False)
    log["manifest_sha256"] = hashlib.sha256(open(f"{MAN}/manifest.csv", "rb").read()).hexdigest()
    json.dump(log, open(f"{MAN}/manifest_log.json", "w"), indent=2)
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 6 and sys.argv[6] == "--rebuild-receptors":
        rebuild_receptors(f"{MAN}/manifest.csv")
    else:
        main()
