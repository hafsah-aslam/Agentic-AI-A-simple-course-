"""Stage 7: chemical-validity results (replicates Sec. 4.4 of the original study).

Joins the PoseBusters audit with the gate decisions: a gated pose is the corrected pose when the gate applied the
correction, otherwise the baseline. Reports pass rates, newly-invalid rates among valid baselines, relative
reduction by gating, per-check failure rates, the RMSD-transition x validity cross-tabulation, bonded-geometry
spot checks, and the Open Babel conversion artifact.

Usage: python3 validity.py FEATS.pkl ROWS_SELECTED.csv AUDIT.csv DOCK_DIR RUNS_DIR OUT.json
"""
import sys, json, pickle
import numpy as np
import pandas as pd
from scipy import stats
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolTransforms as T

RDLogger.DisableLog("rdApp.*")
SEEDS = [0, 42, 123, 999, 2026]
NBOOT = 10000
META = {"pdb", "cohort", "variant", "seed", "valid", "obabel_parse", "obabel_sanitizes", "obabel_n_valence4_uncharged"}


def ci(df, value):
    """Seed-level Student-t interval and complex-level percentile bootstrap for the mean of `value` (in %)."""
    ps = df.groupby("seed")[value].mean()
    m, s = ps.mean(), ps.std(ddof=1); tq = stats.t.ppf(0.975, len(ps) - 1)
    pc = df.groupby("pdb")[value].mean().to_numpy()
    rng = np.random.default_rng(13)
    b = pc[rng.integers(0, len(pc), (NBOOT, len(pc)))].mean(1)
    return {"mean": float(df[value].mean() * 100), "seed_t_ci": [float((m - tq * s / np.sqrt(len(ps))) * 100), float((m + tq * s / np.sqrt(len(ps))) * 100)],
            "bootstrap_ci": [float(np.percentile(b, 2.5) * 100), float(np.percentile(b, 97.5) * 100)]}


def build_table(rows, audit):
    base = audit[audit.variant == "baseline"].set_index("pdb").valid
    corr = audit[audit.variant == "corrected"].copy(); corr["seed"] = corr.seed.astype(int)
    corr = corr.set_index(["pdb", "seed"]).valid
    r = rows[rows.cohort.isin(["test", "external"])].copy()
    r = r[r.pdb.isin(base.index)]
    r["base_valid"] = r.pdb.map(base).astype(float)
    r["ungated_valid"] = [float(corr.get((p, s), np.nan)) for p, s in zip(r.pdb, r.seed)]
    r["gated_valid"] = np.where(r.applied, r.ungated_valid, r.base_valid)
    return r.dropna(subset=["ungated_valid"])


def bond_geometry(feats, pdb, pred, dockdir):
    """Minimum bond-length ratio (corrected/baseline) and maximum bond-angle change (degrees)."""
    m = Chem.RemoveHs(Chem.MolFromMolFile(f"{dockdir}/{pdb}/docked.sdf", removeHs=False))
    c0 = m.GetConformer(); X = c0.GetPositions(); Y = X + pred
    bl = [np.linalg.norm(Y[b.GetBeginAtomIdx()] - Y[b.GetEndAtomIdx()]) / np.linalg.norm(X[b.GetBeginAtomIdx()] - X[b.GetEndAtomIdx()])
          for b in m.GetBonds()]

    def ang(P, i, j, k):
        u, v = P[i] - P[j], P[k] - P[j]
        return np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
    da = [0.0]
    for a in m.GetAtoms():
        nb = [n.GetIdx() for n in a.GetNeighbors()]
        for x in range(len(nb)):
            for y in range(x + 1, len(nb)):
                da.append(abs(ang(Y, nb[x], a.GetIdx(), nb[y]) - ang(X, nb[x], a.GetIdx(), nb[y])))
    return min(bl) if bl else 1.0, max(da)


def main():
    feats_p, rows_p, audit_p, dockdir, runs, out = sys.argv[1:7]
    rows = pd.read_csv(rows_p)
    audit = pd.read_csv(audit_p)
    t = build_table(rows, audit)
    res = {}
    for c in ("test", "external"):
        d = t[t.cohort == c].copy()
        if d.empty:
            continue
        vb = d[d.base_valid == 1].copy()
        vb["newly_invalid_ungated"] = 1 - vb.ungated_valid
        vb["newly_invalid_gated"] = 1 - vb.gated_valid
        nu, ng = vb.newly_invalid_ungated.mean(), vb.newly_invalid_gated.mean()
        b = d.base_rmsd < 2; n = d.corr_rmsd < 2
        cls = {"preservation": b & n, "harm": b & ~n, "rescue": ~b & n, "persistent_failure": ~b & ~n}
        a = audit[(audit.cohort == c)]
        checks = [x for x in audit.columns if x not in META]
        res[c] = {
            "n_complexes": int(d.pdb.nunique()), "n_rows": int(len(d)),
            "pass_baseline": ci(d, "base_valid"), "pass_ungated": ci(d, "ungated_valid"), "pass_gated": ci(d, "gated_valid"),
            "valid_baseline_rows": int(len(vb)),
            "newly_invalid_ungated": ci(vb, "newly_invalid_ungated"), "newly_invalid_gated": ci(vb, "newly_invalid_gated"),
            "relative_reduction_pct": float(100 * (nu - ng) / nu) if nu > 0 else None,
            "invalid_rate_by_transition_ungated": {k: {"n": int(m.sum()), "invalid_pct": float(100 * (1 - d.ungated_valid[m]).mean()) if m.sum() else None}
                                                   for k, m in cls.items()},
            "check_failure_rate_pct": {v: {k: float(100 * (1 - a[a.variant == v][k].astype(float)).mean()) for k in checks}
                                       for v in ("baseline", "corrected", "rigid", "ensemble", "ensemble_rigid")},
            "pass_rate_variants_pct": {v: float(100 * a[a.variant == v].valid.mean()) for v in a.variant.unique()},
            "obabel_artifact": {"complexes_failing_sanitization": int((a[a.variant == "baseline"].obabel_sanitizes == False).sum()),
                                "n_valence4_uncharged_atoms": int(a[a.variant == "baseline"].obabel_n_valence4_uncharged.sum())},
        }
    # bonded-geometry spot checks on preserved-but-invalid internal rows (seed 0)
    feats = {d["pdb"]: d for d in pickle.load(open(feats_p, "rb"))}
    spot = []
    d = t[(t.cohort == "test") & (t.seed == 0) & (t.base_rmsd < 2) & (t.corr_rmsd < 2) & (t.ungated_valid == 0)]
    arch = rows["arch"].iloc[0]
    p0 = pickle.load(open(f"{runs}/{arch}_s0.pkl", "rb"))["predictions"]
    for pdb in d.pdb:
        bl, da = bond_geometry(feats, pdb, p0[pdb]["pred"], dockdir)
        spot.append({"pdb": pdb, "min_bond_length_ratio": float(bl), "max_angle_change_deg": float(da)})
    res["spot_checks_preserved_invalid_internal_seed0"] = {
        "n": len(spot),
        "min_bond_length_ratio_min_median": [min(s["min_bond_length_ratio"] for s in spot), float(np.median([s["min_bond_length_ratio"] for s in spot]))] if spot else None,
        "max_angle_change_deg_max": max(s["max_angle_change_deg"] for s in spot) if spot else None,
        "rows": spot[:50]}
    json.dump(res, open(out, "w"), indent=2)
    print(json.dumps({c: {k: res[c][k] for k in ("pass_baseline", "pass_ungated", "pass_gated", "relative_reduction_pct")} for c in ("test", "external") if c in res}, indent=1))


if __name__ == "__main__":
    main()
