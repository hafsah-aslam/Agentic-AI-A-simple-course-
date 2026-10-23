"""Stage 8: new experiments addressing gaps left open by the original study.

G1  Shift-robust (quantile-matched) gate: the validation admit fraction q is frozen and each held-out cohort is
    gated at the q-quantile of its own (unlabelled) sigma distribution. Uses no held-out labels.
G2  Validity-veto gate: apply the correction only if sigma <= tau AND the corrected pose passes all PoseBusters
    checks. PoseBusters needs only the pose and receptor, so the rule is deployable without ground truth.
G3  Rigid-body projection: replace the free per-atom correction by the rigid motion of the docked pose that best
    fits it (Kabsch). Internal geometry is preserved by construction; the gate is recalibrated on validation.
G4  Deep-ensemble uncertainty: mean correction over the five seeds, gated by ensemble spread (calibrated on
    validation exactly as Eq. 9), compared with the single-model log-variance head.
G5  Sequence-level leakage: exact and near-identical (3-mer Jaccard >= 0.9) protein-sequence overlap between the
    internal training set and the external cohort; RMSD outcomes stratified by overlap.
G6  Sigma-shift diagnosis: per-cohort sigma distributions (KS test), sigma-RMSD correlation per cohort.

Usage: python3 gaps.py FEATS.pkl RUNS_DIR EVAL_DIR AUDIT.csv MANIFEST LP_CSV PB_DIR OUT.json
"""
import sys, os, json, pickle
import numpy as np
import pandas as pd
from scipy import stats
import gemmi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate as E
import validity as V
from audit import kabsch_apply

SEEDS = E.SEEDS


def rmsd_rows(feats, preds, arch, kind):
    """Per (seed, complex) rows with baseline / variant RMSD for val, test, external."""
    rows = []
    for pdb, d in feats.items():
        if d["split"] == "train":
            continue
        X = d["lig_xyz"]; ref = X + d["target"]
        ens = np.mean([preds[s][pdb]["pred"] for s in SEEDS], 0)
        spread = float(np.mean(np.linalg.norm(np.std([preds[s][pdb]["pred"] for s in SEEDS], 0), axis=1)))
        it = [(None, ens)] if kind.startswith("ensemble") else [(s, preds[s][pdb]["pred"]) for s in SEEDS]
        for s, p in it:
            Y = X + p
            if kind.endswith("rigid"):
                Y = kabsch_apply(X, Y)
            n = len(X)
            base_se, corr_se = float(((X - ref) ** 2).sum()), float(((Y - ref) ** 2).sum())
            sig = spread if kind.startswith("ensemble") else preds[s][pdb]["sigma"]
            rows.append({"arch": arch, "seed": -1 if s is None else s, "cohort": d["split"], "pdb": pdb, "n": n,
                         "base_se": base_se, "corr_se": corr_se, "base_rmsd": (base_se / n) ** .5, "corr_rmsd": (corr_se / n) ** .5,
                         "sigma": sig})
    return pd.DataFrame(rows)


def success_boot(df, col):
    """Bootstrap-only success block (ensembles have one row per complex)."""
    base = (df.base_rmsd < 2).astype(float); new = (df[col] < 2).astype(float)
    per = (new - base).groupby(df.pdb).mean().to_numpy()
    rng = np.random.default_rng(7)
    b = per[rng.integers(0, len(per), (E.NBOOT, len(per)))].mean(1)
    return {"baseline_success": float(base.mean() * 100), "success": float(new.mean() * 100), "net_change_pp": float((new - base).mean() * 100),
            "bootstrap_ci_pp": [float(np.percentile(b, 2.5) * 100), float(np.percentile(b, 97.5) * 100)]}


def validity_rates(df, audit, variant, applied_col="applied"):
    base = audit[audit.variant == "baseline"].set_index("pdb").valid.astype(float)
    a = audit[audit.variant == variant].copy()
    if variant.startswith("ensemble"):
        v = a.set_index("pdb").valid.astype(float)
        corr = [v.get(p, np.nan) for p in df.pdb]
    else:
        a["seed"] = a.seed.astype(int); v = a.set_index(["pdb", "seed"]).valid.astype(float)
        corr = [v.get((p, s), np.nan) for p, s in zip(df.pdb, df.seed)]
    d = df.assign(base_valid=df.pdb.map(base), corr_valid=corr).dropna(subset=["base_valid", "corr_valid"])
    d["gated_valid"] = np.where(d[applied_col], d.corr_valid, d.base_valid)
    vb = d[d.base_valid == 1]
    return {"pass_baseline": float(d.base_valid.mean() * 100), "pass_ungated": float(d.corr_valid.mean() * 100),
            "pass_gated": float(d.gated_valid.mean() * 100),
            "newly_invalid_ungated": float((1 - vb.corr_valid).mean() * 100), "newly_invalid_gated": float((1 - vb.gated_valid).mean() * 100)}, d


def gate_eval(rows, tau, audit, variant, label, q=None):
    out = {}
    for c in ("test", "external"):
        d = rows[rows.cohort == c].copy()
        t = tau if q is None else float(np.quantile(d.sigma, q))
        d["applied"] = d.sigma <= t
        d["gated_rmsd"] = np.where(d.applied, d.corr_rmsd, d.base_rmsd)
        d["gated_se"] = np.where(d.applied, d.corr_se, d.base_se)
        sb = E.success_block(d, "gated_rmsd") if d.seed.nunique() > 1 else success_boot(d, "gated_rmsd")
        su = E.success_block(d, "corr_rmsd") if d.seed.nunique() > 1 else success_boot(d, "corr_rmsd")
        vr, _ = validity_rates(d, audit, variant)
        out[c] = {"threshold": t, "admit_rate_pct": float(d.applied.mean() * 100), "mse_reduction_ungated": E.mse_red(d),
                  "mse_reduction_gated": E.mse_red(d, corr="gated_se"), "ungated": su, "gated": sb, "validity": vr}
    return out


def sequences_from_pdb(path):
    st = gemmi.read_structure(path)
    seqs = []
    for ch in st[0]:
        s = gemmi.one_letter_code([r.name for r in ch])
        s = s.upper().replace("X", "")
        if len(s) >= 20:
            seqs.append(s)
    return seqs


def kmers(s, k=3):
    return {s[i:i + k] for i in range(len(s) - k + 1)}


def main():
    feats_p, runs, evald, audit_p, man_p, lp_p, pbdir, out = sys.argv[1:9]
    ev = json.load(open(f"{evald}/eval.json"))
    arch, tau = ev["selection"]["selected"], ev["gate"]["tau"]
    feats = {d["pdb"]: d for d in pickle.load(open(feats_p, "rb"))}
    preds = {}
    for s in SEEDS:
        r = pickle.load(open(f"{runs}/{arch}_s{s}.pkl", "rb"))
        c = r["preprocessing"]["coord_scale"]
        preds[s] = {p: {"pred": o["pred"], "sigma": float(np.mean(c * np.exp(o["logvar"] / 2)))} for p, o in r["predictions"].items()}
    audit = pd.read_csv(audit_p)
    rows = pd.read_csv(f"{evald}/rows_selected.csv")
    res = {"selected_arch": arch, "tau": tau}

    # G1 quantile-matched gate
    q = ev["gate"]["admit_rate"]["val"] / 100
    res["G1_quantile_gate"] = {"q": q, **gate_eval(rows, tau, audit, "corrected", "quantile", q=q)}
    res["G0_frozen_gate_reference"] = gate_eval(rows, tau, audit, "corrected", "frozen")

    # G2 validity-veto gate
    corr_valid = audit[audit.variant == "corrected"].copy(); corr_valid["seed"] = corr_valid.seed.astype(int)
    cv = corr_valid.set_index(["pdb", "seed"]).valid.astype(bool)
    g2 = {}
    for c in ("test", "external"):
        d = rows[rows.cohort == c].copy()
        d = d[[(p, s) in cv.index for p, s in zip(d.pdb, d.seed)]]
        ok = np.array([cv[(p, s)] for p, s in zip(d.pdb, d.seed)])
        for name, applied in (("veto_only", ok), ("sigma_and_veto", (d.sigma <= tau).to_numpy() & ok)):
            e = d.assign(applied=applied)
            e["gated_rmsd"] = np.where(e.applied, e.corr_rmsd, e.base_rmsd)
            e["gated_se"] = np.where(e.applied, e.corr_se, e.base_se)
            vr, _ = validity_rates(e, audit, "corrected")
            g2.setdefault(c, {})[name] = {"admit_rate_pct": float(e.applied.mean() * 100), "gated": E.success_block(e, "gated_rmsd"),
                                          "mse_reduction_gated": E.mse_red(e, corr="gated_se"), "validity": vr}
    res["G2_validity_veto"] = g2

    # G3 rigid-body projection (gate recalibrated on validation RMSD outcomes)
    rr = rmsd_rows(feats, preds, arch, "rigid")
    t3, net3 = E.calibrate_gate(rr[rr.cohort == "val"])
    res["G3_rigid_projection"] = {"tau": t3, "val_net_success_pp": net3, "val_mse_reduction": E.mse_red(rr[rr.cohort == "val"]),
                                  **gate_eval(rr, t3, audit, "rigid", "rigid")}

    # G4 deep ensemble (spread-gated), plus rigid ensemble
    for kind, variant in (("ensemble", "ensemble"), ("ensemble_rigid", "ensemble_rigid")):
        er = rmsd_rows(feats, preds, arch, kind)
        v = er[er.cohort == "val"]
        r_a = float(stats.pearsonr(v.sigma, v.base_rmsd)[0])
        t4, net4 = E.calibrate_gate(v)
        res[f"G4_{kind}"] = {"stage_a_pearson_spread_vs_rmsd": r_a, "tau": t4, "val_net_success_pp": net4,
                             "val_mse_reduction": E.mse_red(v), **gate_eval(er, t4, audit, variant, kind)}

    # G5 sequence overlap
    man = pd.read_csv(man_p)
    lp = pd.read_csv(lp_p).rename(columns={"Unnamed: 0": "pdb"}).set_index("pdb")
    train_seqs = {p: lp.loc[p, "seq"] for p in man[man.split == "train"].pdb if isinstance(lp.loc[p, "seq"], str)}
    train_chains = {p: [c for c in s.split(":") if len(c) >= 20] for p, s in train_seqs.items()}
    all_train = [c for v in train_chains.values() for c in v]
    train_set = set(all_train)
    train_k = [(kmers(c), c) for c in set(all_train)]
    ext = {}
    for p in man[man.split == "external"].pdb:
        seqs = sequences_from_pdb(f"{pbdir}/posebusters_benchmark_set/{p}/{p}_protein.pdb")
        exact = any(s in train_set for s in seqs)
        best = 0.0
        for s in seqs:
            ks = kmers(s)
            for tk, _ in train_k:
                j = len(ks & tk) / max(1, len(ks | tk))
                if j > best:
                    best = j
        ext[p] = {"exact": exact, "max_3mer_jaccard": best}
    ex = pd.DataFrame(ext).T
    ex["near_identical"] = ex.max_3mer_jaccard.astype(float) >= 0.9
    er_ = rows[rows.cohort == "external"].copy()
    er_["near_identical"] = er_.pdb.map(ex.near_identical)
    strat = {}
    for flag, g in er_.groupby("near_identical"):
        strat["near_identical" if flag else "novel"] = {"n_complexes": int(g.pdb.nunique()), "mse_reduction_ungated": E.mse_red(g),
                                                        "ungated": E.success_block(g, "corr_rmsd"), "gated": E.success_block(g, "gated_rmsd"),
                                                        "admit_rate_pct": float(g.applied.mean() * 100), "mean_sigma": float(g.sigma.mean())}
    res["G5_sequence_overlap"] = {"external_exact_chain_match_with_train": int(ex.exact.sum()),
                                  "external_near_identical_3mer_jaccard_ge_0.9": int(ex.near_identical.sum()),
                                  "n_external": int(len(ex)), "stratified": strat}

    # G6 sigma-shift diagnosis
    sv, se_, st_ = (rows[rows.cohort == c].sigma for c in ("val", "external", "test"))
    res["G6_sigma_shift"] = {
        "mean_sigma": {c: float(rows[rows.cohort == c].sigma.mean()) for c in ("val", "test", "external")},
        "external_vs_val_mean_sigma_change_pct": float(100 * (se_.mean() - sv.mean()) / sv.mean()),
        "test_vs_val_mean_sigma_change_pct": float(100 * (st_.mean() - sv.mean()) / sv.mean()),
        "ks_val_vs_external": dict(zip(("D", "p"), map(float, stats.ks_2samp(sv, se_)))),
        "ks_val_vs_test": dict(zip(("D", "p"), map(float, stats.ks_2samp(sv, st_)))),
        "pearson_sigma_vs_baseline_rmsd": {c: float(stats.pearsonr(rows[rows.cohort == c].sigma, rows[rows.cohort == c].base_rmsd)[0]) for c in ("val", "test", "external")},
        "spearman_sigma_vs_correction_gain": {c: float(stats.spearmanr(rows[rows.cohort == c].sigma,
                                                                        rows[rows.cohort == c].base_rmsd - rows[rows.cohort == c].corr_rmsd)[0]) for c in ("val", "test", "external")},
        "mean_ligand_heavy_atoms": {c: float(np.mean([len(d["target"]) for d in feats.values() if d["split"] == c])) for c in ("train", "val", "test", "external")},
        "mean_pocket_residues": {c: float(np.mean([len(d["res_aa"]) for d in feats.values() if d["split"] == c])) for c in ("train", "val", "test", "external")}}
    json.dump(res, open(out, "w"), indent=2, default=float)
    print(json.dumps({k: (v if not isinstance(v, dict) else list(v)) for k, v in res.items()}, indent=1, default=float)[:2000])


if __name__ == "__main__":
    main()
