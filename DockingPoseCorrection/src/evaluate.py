"""Stage 5: architecture selection, confidence gating, RMSD-threshold evaluation and statistical validation.

Usage: python3 evaluate.py FEATS.pkl RUNS_DIR OUT_DIR
Writes OUT_DIR/eval.json and OUT_DIR/rows.csv (one row per architecture x seed x cohort x complex).
"""
import sys, os, json, pickle, glob
import numpy as np
import pandas as pd
from scipy import stats
import torch

SEEDS = [0, 42, 123, 999, 2026]
ARCHS = [os.environ["ONLY_ARCH"]] if os.environ.get("ONLY_ARCH") else ["MLP", "GNN", "Hypergraph", "Transformer"]
THR = 2.0
NBOOT, NPERM = int(os.environ.get("NBOOT", 10000)), int(os.environ.get("NPERM", 10000))


def load(feats_path, runs_dir):
    feats = {d["pdb"]: d for d in pickle.load(open(feats_path, "rb"))}
    rows = []
    for f in sorted(glob.glob(f"{runs_dir}/*.pkl")):
        run = pickle.load(open(f, "rb"))
        c = run["preprocessing"]["coord_scale"]
        for pdb, o in run["predictions"].items():
            d = feats[pdb]
            if d["split"] == "train":
                continue
            t, p = d["target"], o["pred"]
            base_se, corr_se = float((t ** 2).sum()), float(((t - p) ** 2).sum())
            n = len(t)
            rows.append({"arch": run["arch"], "seed": run["seed"], "cohort": d["split"], "pdb": pdb, "n": n,
                         "base_se": base_se, "corr_se": corr_se, "base_rmsd": (base_se / n) ** 0.5,
                         "corr_rmsd": (corr_se / n) ** 0.5,
                         "sigma": float(np.mean(c * np.exp(o["logvar"] / 2.0)))})
    return feats, pd.DataFrame(rows)


def mse_red(df, base="base_se", corr="corr_se"):
    return float(100 * (df[base].sum() - df[corr].sum()) / df[base].sum())


def calibrate_gate(val):
    """Stage B: smallest threshold maximising pooled validation net success (Eq. 9)."""
    v = val.sort_values("sigma")
    gain = ((v.corr_rmsd < THR).astype(int) - (v.base_rmsd < THR).astype(int)).to_numpy()
    sig = v.sigma.to_numpy()
    cum = np.cumsum(gain) / len(v)
    # thresholds are distinct sigma values; ties must be admitted together
    last_of_value = np.r_[sig[1:] != sig[:-1], True]
    cand_net = cum[last_of_value]; cand_t = sig[last_of_value]
    best = cand_net.max()
    if best <= 0:
        return -np.inf, 0.0
    return float(cand_t[np.argmax(cand_net >= best - 1e-12)]), float(best * 100)


def gated(df, tau, key="sigma"):
    a = df[key] <= tau
    out = df.copy()
    out["applied"] = a
    out["gated_se"] = np.where(a, df.corr_se, df.base_se)
    out["gated_rmsd"] = np.where(a, df.corr_rmsd, df.base_rmsd)
    return out


def success_block(df, col):
    """Success rates, net change, seed-level t-interval and complex-level paired bootstrap interval."""
    base = (df.base_rmsd < THR).astype(float); new = (df[col] < THR).astype(float)
    per_seed = df.assign(d=new - base, b=base, n_=new).groupby("seed").agg(d=("d", "mean"), b=("b", "mean"), n_=("n_", "mean"))
    m, s = per_seed.d.mean(), per_seed.d.std(ddof=1)
    tq = stats.t.ppf(0.975, len(per_seed) - 1)
    per_cx = df.assign(d=new - base).groupby("pdb").d.mean().to_numpy()
    rng = np.random.default_rng(7)
    boots = per_cx[rng.integers(0, len(per_cx), (NBOOT, len(per_cx)))].mean(1)
    return {"baseline_success": float(base.mean() * 100), "success": float(new.mean() * 100),
            "net_change_pp": float((new - base).mean() * 100),
            "seed_t_ci_pp": [float((m - tq * s / np.sqrt(len(per_seed))) * 100), float((m + tq * s / np.sqrt(len(per_seed))) * 100)],
            "bootstrap_ci_pp": [float(np.percentile(boots, 2.5) * 100), float(np.percentile(boots, 97.5) * 100)]}


def transitions(df, col):
    b, n = df.base_rmsd < THR, df[col] < THR
    return {"preservation": int((b & n).sum()), "harm": int((b & ~n).sum()), "rescue": int((~b & n).sum()),
            "persistent_failure": int((~b & ~n).sum())}


def permutation_test(feats):
    """Training-only test of the pocket-distance / target-displacement relationship. Null: displacement magnitudes
    shuffled within each complex (10,000 permutations). Because within-complex shuffling keeps the between-complex
    association, the null distribution is not centred at zero; the two-sided p-value is computed around the null mean.
    Two distance definitions are reported: atom to nearest pocket C-alpha, and atom to the pocket centroid."""
    out = {}
    for name, dist_fn in (("nearest_pocket_ca", lambda d: np.linalg.norm(d["lig_xyz"][:, None] - d["res_xyz"][None], axis=2).min(1)),
                          ("pocket_centroid", lambda d: np.linalg.norm(d["lig_xyz"] - d["res_xyz"].mean(0), axis=1))):
        rng = np.random.default_rng(11)
        ds, es = [], []
        for d in feats.values():
            if d["split"] != "train":
                continue
            ds.append(dist_fn(d)); es.append(np.linalg.norm(d["target"], axis=1))
        x, y = np.concatenate(ds), np.concatenate(es)
        r_obs = float(np.corrcoef(x, y)[0, 1])
        denom = np.sqrt(((x - x.mean()) ** 2).sum() * ((y - y.mean()) ** 2).sum())
        null, done, chunk = [], 0, 500
        while done < NPERM:
            P = min(chunk, NPERM - done)
            num = np.zeros(P)
            for dd, ee in zip(ds, es):
                perm = rng.random((P, len(ee))).argsort(1)
                num += ((dd - x.mean())[None, :] * (ee[perm] - y.mean())).sum(1)
            null.append(num / denom); done += P
        null = np.concatenate(null)
        mu = float(null.mean())
        p_two = (int((np.abs(null - mu) >= abs(r_obs - mu) - 1e-15).sum()) + 1) / (NPERM + 1)
        out[name] = {"r": r_obs, "null_mean_r": mu, "null_sd_r": float(null.std()), "p_two_sided_centred": p_two,
                     "p_upper": (int((null >= r_obs).sum()) + 1) / (NPERM + 1),
                     "p_two_sided_naive_abs": (int((np.abs(null) >= abs(r_obs) - 1e-15).sum()) + 1) / (NPERM + 1),
                     "permutations": NPERM, "complexes": len(ds), "atoms": int(len(x))}
    return out


def rotation_audit(feats_path, runs_dir, arch):
    sys.path.insert(0, os.path.dirname(__file__))
    from model import PoseCorrector
    import train as T
    data = pickle.load(open(feats_path, "rb"))
    pp = T.fit_preprocessing(data)
    val = sorted([d for d in data if d["split"] == "val"], key=lambda d: d["pdb"])[:10]
    items = [T.prepare(d, pp) for d in val]
    rng = np.random.default_rng(5)
    disc = []
    for seed in SEEDS:
        m = PoseCorrector(arch); m.load_state_dict(torch.load(f"{runs_dir}/{arch}_s{seed}.pt")); m.eval()
        base = T.predict(m, items, pp)
        rots = [T.random_rotation(rng) for _ in items]
        rot = T.predict(m, items, pp, rots=rots)
        for b, r, R in zip(base, rot, rots):
            back = r["pred"] @ R           # undo rotation (R is orthonormal: x R^T R = x)
            disc.append(float(np.sqrt(((back - b["pred"]) ** 2).sum(1).mean())))
    disc = np.array(disc)
    return {"n": int(len(disc)), "mean": float(disc.mean()), "median": float(np.median(disc)),
            "p95": float(np.percentile(disc, 95)), "max": float(disc.max())}


def metric_identity():
    rng = np.random.default_rng(3)
    X, Y = rng.normal(size=(50, 3)), rng.normal(size=(50, 3))
    rmsd = np.sqrt(((X - Y) ** 2).sum(1).mean()); rmse = np.sqrt(((X - Y) ** 2).mean())
    return float(abs(rmse - rmsd / np.sqrt(3)))


def main():
    feats_path, runs_dir, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    feats, rows = load(feats_path, runs_dir)
    res = {"cohort_sizes": {s: int(sum(d["split"] == s for d in feats.values())) for s in ("train", "val", "test", "external")}}
    # ---- architecture selection (validation only)
    val = rows[rows.cohort == "val"]
    per_seed = {a: [mse_red(val[(val.arch == a) & (val.seed == s)]) for s in SEEDS] for a in ARCHS}
    means = {a: float(np.mean(v)) for a, v in per_seed.items()}
    sel = max(means, key=means.get)
    res["selection"] = {"per_seed_val_mse_reduction": per_seed, "mean": means, "selected": sel,
                        "anova": dict(zip(("F", "p"), map(float, stats.f_oneway(*per_seed.values())))) if len(ARCHS) > 1 else None,
                        "paired_t_vs_selected": {a: dict(zip(("t", "p"), map(float, stats.ttest_rel(per_seed[sel], per_seed[a]))))
                                                 for a in ARCHS if a != sel}}
    S = rows[rows.arch == sel]
    v = S[S.cohort == "val"]
    # ---- gate
    stage_a = float(stats.pearsonr(v.sigma, v.base_rmsd)[0])
    tau, best_net = calibrate_gate(v) if stage_a > 0.30 else (-np.inf, 0.0)
    res["gate"] = {"stage_a_pearson": stage_a, "stage_a_pass": stage_a > 0.30, "tau": tau, "val_net_success_pp": best_net,
                   "admit_rate": {c: float((S[S.cohort == c].sigma <= tau).mean() * 100) for c in ("val", "test", "external")},
                   "mean_sigma": {c: float(S[S.cohort == c].sigma.mean()) for c in ("val", "test", "external")},
                   "mean_baseline_rmsd": {c: float(S[S.cohort == c].base_rmsd.mean()) for c in ("val", "test", "external")}}
    # ---- baseline-RMSD control gate (same calibration rule, baseline RMSD as the score)
    ctrl = {}
    for name, score in (("apply_if_rmsd_le_t", v.base_rmsd), ("apply_if_rmsd_ge_t", -v.base_rmsd)):
        t, net = calibrate_gate(v.assign(sigma=score))
        ctrl[name] = {"best_val_net_success_pp": net, "threshold": (t if name.endswith("le_t") else -t) if np.isfinite(t) else None}
    res["baseline_rmsd_control_gate"] = ctrl
    # ---- held-out results
    res["heldout"] = {}
    allrows = []
    for c in ("val", "test", "external"):
        d = gated(S[S.cohort == c], tau)
        allrows.append(d)
        res["heldout"][c] = {
            "n_complexes": int(d.pdb.nunique()), "n_rows": int(len(d)),
            "mse_reduction_ungated": mse_red(d), "mse_reduction_gated": mse_red(d, corr="gated_se"),
            "mse_reduction_ungated_per_seed": [mse_red(d[d.seed == s]) for s in SEEDS],
            "ungated": success_block(d, "corr_rmsd"), "gated": success_block(d, "gated_rmsd"),
            "transitions_ungated": transitions(d, "corr_rmsd"), "transitions_gated": transitions(d, "gated_rmsd")}
    pd.concat(allrows).to_csv(f"{out}/rows_selected.csv", index=False)
    rows.to_csv(f"{out}/rows_all_archs.csv", index=False)
    res["permutation_test"] = permutation_test(feats)
    res["rotation_audit"] = rotation_audit(feats_path, runs_dir, sel)
    res["metric_identity_abs_error"] = metric_identity()
    json.dump(res, open(f"{out}/eval.json", "w"), indent=2)
    print(json.dumps({k: res[k] for k in ("selection", "gate")}, indent=1)[:3000])


if __name__ == "__main__":
    main()
