#!/usr/bin/env python3
"""Per-complex comparison of a reproduction run with the original study's frozen outputs.

Reads the original manifest.csv and per_complex_evaluation.csv (frozen files of the original bundle) and a run's
manifest and results, and writes results/original_comparison.json plus a printed summary:
  - the original headline numbers recomputed from its own per-complex file (a check of the frozen files),
  - cohort overlap between the original and the reproduction splits,
  - Vina baseline agreement on the shared PoseBusters complexes, overall and by ligand size,
  - the predicted-sigma scale of both models, and the admit rate of each gate threshold on both models.

Usage: python3 compare_with_original.py --original DIR [--repo DockingPoseCorrection] [--results DIR]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ORIGINAL_TAU = 1.367134928703308   # frozen gate threshold in the original aggregate_external_baselines.py
SPLITS = {"validation": "val"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", type=Path, required=True, help="folder with the original manifest.csv and per_complex_evaluation.csv")
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--results", type=Path, default=None)
    a = ap.parse_args()
    res = a.results or a.repo / "results"
    om = pd.read_csv(a.original / "manifest.csv")
    oe = pd.read_csv(a.original / "per_complex_evaluation.csv")
    oe["split"] = oe.split.replace(SPLITS)
    om["split"] = om.split.replace(SPLITS)
    man = pd.read_csv(a.repo / "manifests" / "manifest.csv")
    rows = pd.read_csv(res / "rows_selected.csv")
    tau = json.load(open(res / "eval.json"))["gate"]["tau"]
    out = {"original_tau": ORIGINAL_TAU, "reproduction_tau": tau}

    # 1. original headline numbers from its own per-complex file
    head = {}
    for s in ("val", "test", "external"):
        d = oe[oe.split == s]
        if not len(d):
            continue
        first = d.drop_duplicates("complex_id")
        head[s] = {"complexes": int(first.complex_id.nunique()), "vina_success_pct": 100 * first.baseline_success.mean(),
                   "mse_reduction_pct": 100 * (1 - d.corrected_squared_error_sum.sum() / d.baseline_squared_error_sum.sum()),
                   "ungated_success_pct": 100 * d.corrected_success.mean(),
                   "admit_pct_original_tau": 100 * (d.mean_predicted_sigma <= ORIGINAL_TAU).mean()}
    out["original_recomputed"] = head

    # 2. cohort overlap
    out["overlap"] = {s: {"original": int((om.split == s).sum()), "reproduction": int((man.split == s).sum()),
                          "shared": len(set(om[om.split == s].pdb_id.str.lower()) & set(man[man.split == s].pdb.str.lower()))}
                      for s in ("train", "val", "test", "external")}

    # 3. Vina agreement on shared PoseBusters complexes, 4. sigma scale and gate thresholds
    O = oe.groupby(["split", "complex_id"]).agg(base_o=("baseline_rmsd", "first"), sig_o=("mean_predicted_sigma", "mean"), n=("n_atoms", "first"))
    R = rows.rename(columns={"cohort": "split", "pdb": "complex_id"}).groupby(["split", "complex_id"]).agg(base_r=("base_rmsd", "first"), sig_r=("sigma", "mean"))
    j = O.join(R, how="inner").reset_index()
    ext = j[j.split == "external"].copy()
    so, sr = ext.base_o < 2, ext.base_r < 2
    ext["size"] = pd.cut(ext.n, [0, 20, 30, 40, 1000], labels=["<=20", "21-30", "31-40", ">40"])
    out["external_vina"] = {
        "paired": int(len(ext)), "success_original_pct": 100 * so.mean(), "success_reproduction_pct": 100 * sr.mean(),
        "outcome_agreement_pct": 100 * (so == sr).mean(), "original_only_success": int((so & ~sr).sum()),
        "reproduction_only_success": int((~so & sr).sum()), "spearman_rmsd": float(stats.spearmanr(ext.base_o, ext.base_r)[0]),
        "by_ligand_heavy_atoms": {str(k): {"n": int(len(g)), "original_pct": 100 * (g.base_o < 2).mean(), "reproduction_pct": 100 * (g.base_r < 2).mean()}
                                  for k, g in ext.groupby("size", observed=True)}}
    out["sigma"] = {"external_spearman": float(stats.spearmanr(ext.sig_o, ext.sig_r)[0]),
                    "external_median_ratio_original_over_reproduction": float((ext.sig_o / ext.sig_r).median()),
                    "quantiles": {}}
    for s in ("val", "test", "external"):
        qo = oe[oe.split == s].mean_predicted_sigma
        qr = rows[rows.cohort == s].sigma
        out["sigma"]["quantiles"][s] = {
            "original_q05_q50_q95": qo.quantile([.05, .5, .95]).round(3).tolist() if len(qo) else None,
            "reproduction_q05_q50_q95": qr.quantile([.05, .5, .95]).round(3).tolist(),
            "reproduction_admit_pct_at_original_tau": 100 * (qr <= ORIGINAL_TAU).mean(),
            "reproduction_admit_pct_at_own_tau": 100 * (qr <= tau).mean()}
    json.dump(out, open(res / "original_comparison.json", "w"), indent=2)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
