"""G8 (new): why the correction destroys chemistry. Decomposes every predicted correction into a rigid part
(Kabsch fit of the docked pose onto the corrected pose) and an internal-deformation part, and measures ligand
contraction as the radius-of-gyration ratio corrected/docked (reference/docked as the target behaviour).

Usage: python3 shrinkage.py FEATS.pkl RUNS_DIR ARCH OUT.json
"""
import sys, json, pickle
import numpy as np

feats_p, runs, arch, out = sys.argv[1:5]
SEEDS = [0, 42, 123, 999, 2026]
feats = {d["pdb"]: d for d in pickle.load(open(feats_p, "rb"))}
preds = {s: pickle.load(open(f"{runs}/{arch}_s{s}.pkl", "rb"))["predictions"] for s in SEEDS}


def rg(X):
    return float(np.sqrt(((X - X.mean(0)) ** 2).sum(1).mean()))


def rigid_fit(P, Q):
    pc, qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    d = np.sign(np.linalg.det(U @ Vt))
    return (P - pc) @ (U @ np.diag([1, 1, d]) @ Vt) + qc


res, rows = {}, []
for c in ("val", "test", "external"):
    rc, rr, share, gain_int, gain_rig = [], [], [], [], []
    for pdb, d in feats.items():
        if d["split"] != c:
            continue
        X = d["lig_xyz"]; R = X + d["target"]
        for s in SEEDS:
            Y = X + preds[s][pdb]["pred"]
            Xr = rigid_fit(X, Y)
            tot = ((Y - X) ** 2).sum()
            rc.append(rg(Y) / rg(X)); rr.append(rg(R) / rg(X))
            share.append(float(((Y - Xr) ** 2).sum() / tot) if tot > 0 else 0.0)
            base = ((X - R) ** 2).sum()
            gain_int.append(float((base - ((Y - R) ** 2).sum()) / base)); gain_rig.append(float((base - ((Xr - R) ** 2).sum()) / base))
            if s == 0:
                rows.append({"cohort": c, "pdb": pdb, "rg_ratio_corrected": rc[-1], "rg_ratio_reference": rr[-1], "internal_share": share[-1]})
    q = lambda a: [float(x) for x in np.percentile(a, [25, 50, 75])]
    res[c] = {"n_rows": len(rc), "rg_ratio_corrected_q25_50_75": q(rc), "rg_ratio_reference_q25_50_75": q(rr),
              "internal_share_q25_50_75": q(share), "frac_contracted_below_0p8": float(np.mean(np.array(rc) < 0.8)),
              "median_sq_error_reduction_full": float(np.median(gain_int)), "median_sq_error_reduction_rigid_part": float(np.median(gain_rig))}
json.dump({"summary": res, "rows_seed0": rows}, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
