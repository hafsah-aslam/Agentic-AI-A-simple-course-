"""Figures for the reproduction paper (vector PDF + 300 dpi PNG).

Colour roles (fixed categorical order of the reference palette, never cycled): baseline = neutral grey,
ungated = slot 1 blue, gated = slot 2 orange, then new gate variants in slots 3-6. Text never wears series colour.

Usage: python3 figures.py RESULTS_DIR FIG_DIR
"""
import sys, os, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RES, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
GREY, BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET = "#8f8d87", "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False})


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def load(name):
    p = f"{RES}/{name}"
    return json.load(open(p)) if os.path.exists(p) else None


def bars(ax, groups, series, values, colors, errs=None, fmt="{:.1f}", ylim=None):
    """Grouped bars with 2px surface gaps and value labels in ink colour."""
    n = len(series); w = 0.8 / n
    x = np.arange(len(groups))
    for i, (s, c) in enumerate(zip(series, colors)):
        v = np.array([values[g][i] for g in range(len(groups))], float)
        pos = x - 0.4 + w * (i + 0.5)
        ax.bar(pos, v, w * 0.92, color=c, label=s, edgecolor="white", linewidth=1.0, zorder=2)
        if errs is not None:
            lo = np.array([errs[g][i][0] for g in range(len(groups))]); hi = np.array([errs[g][i][1] for g in range(len(groups))])
            ax.errorbar(pos, v, yerr=[v - lo, hi - v], fmt="none", ecolor=INK, elinewidth=0.8, capsize=2, zorder=3)
        for p, val in zip(pos, v):
            ax.text(p, (val if errs is None else max(val, 0)) + (ylim[1] - ylim[0]) * 0.015 if ylim else val, fmt.format(val),
                    ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(groups)
    if ylim: ax.set_ylim(*ylim)
    ax.grid(axis="x", visible=False)


# ------------------------------------------------------------------ Fig 1 methodology
def methodology():
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    ax.set_xlim(0, 100); ax.set_ylim(-17, 66); ax.axis("off"); ax.grid(False)
    W, X1, X2, X3 = 30, 1, 35, 69
    ROWS = {"top": (45, 16), "mid": (24, 16), "bot": (3, 16)}

    def box(x, row, title, body, fc="#f3f6fb", ec=BLUE):
        y, h = ROWS[row]
        ax.add_patch(FancyBboxPatch((x, y), W, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=fc, ec=ec, lw=1.0))
        ax.text(x + W / 2, y + h - 1.5, title, ha="center", va="top", fontsize=7.0, fontweight="bold", color=INK)
        ax.text(x + W / 2, y + h - 4.8, body, ha="center", va="top", fontsize=5.5, color=INK2, linespacing=1.32)

    def arrow(p, q, style="arc3"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, color=INK2, lw=1.0, connectionstyle=style))

    for x, t in ((X1, "1  Data and leakage control"), (X2, "2  Docking and representation"), (X3, "3  Correction, gate, evaluation")):
        ax.text(x + W / 2, 64.5, t, fontsize=7.8, fontweight="bold", color=INK, va="top", ha="center")
    # column 1 (down)
    box(X1, "top", "Sources", "PDBbind v2020 P-L ∩ LP-PDBBind ∩ MISATO\n16,965 shared IDs; 663 covalent removed\nexternal: PoseBusters benchmark (428)")
    box(X1, "mid", "Eligibility and frozen manifest", "RCSB mmCIF; ligand located by heavy-atom\ncount, chemistry from the SMILES template\nidentical-sequence groups in SHA-256 order\nfill train → val → test, truncate boundary")
    box(X1, "bot", "Cohorts", "train 1,200 · val 400 · test 400\nexternal 428, zero PDB overlap\nno group crosses splits\nmanifest hash recorded")
    # column 2 (up)
    box(X2, "bot", "AutoDock Vina", "fresh ETKDG conformer (crystal discarded)\n20 Å cube at the pocket centre\nexhaustiveness 8, 5 poses\nrank-1 pose = $X_{dock}$")
    box(X2, "mid", "Atom matching and targets", "element-labelled graph isomorphism\nsymmetry-aware, minimum in-place RMSD\ntarget $\\Delta X = X_{ref} - X_{dock}$")
    box(X2, "top", "Features (fit on train only)", "ligand: 18 atom features + coordinates\npocket within 8 Å of $X_{dock}$: 28 features\nMISATO trajectory RMSF (flexibility)\nfrozen training-mean imputation")
    # column 3 (down)
    box(X3, "top", "Dual-head correction model", "ligand MLP + pocket encoder, chosen on\nvalidation only (MLP, GNN, hypergraph,\ntransformer); distance-biased cross-\nattention; $\\hat{\\Delta X}$ head + log-variance $s_i$")
    box(X3, "mid", "Frozen confidence gate", "A  r($\\bar\\sigma$, RMSD) > 0.30 on validation\nB  smallest τ maximising net success\nC  use $X_{dock} + \\hat{\\Delta X}$ if $\\bar\\sigma \\leq$ τ,\n    otherwise keep $X_{dock}$")
    box(X3, "bot", "Three evaluation axes", "geometric: pooled MSE reduction\nthreshold: RMSD < 2 Å transitions\nvalidity: PoseBusters dock, 22 checks\ninternal test and external cohorts", fc="#fff4ee", ec=ORANGE)
    # flow
    arrow((X1 + W / 2, 45), (X1 + W / 2, 40.6)); arrow((X1 + W / 2, 24), (X1 + W / 2, 19.6))
    arrow((X1 + W + 0.6, 11), (X2 - 0.6, 11))
    arrow((X2 + W / 2, 19.4), (X2 + W / 2, 23.6)); arrow((X2 + W / 2, 40.4), (X2 + W / 2, 44.6))
    arrow((X2 + W + 0.6, 53), (X3 - 0.6, 53))
    arrow((X3 + W / 2, 45), (X3 + W / 2, 40.6)); arrow((X3 + W / 2, 24), (X3 + W / 2, 19.6))
    # new experiments band
    ax.add_patch(FancyBboxPatch((X1, -15.5), X3 + W - X1, 14, boxstyle="round,pad=0.25,rounding_size=1.2", fc="#effaf5", ec=AQUA, lw=1.0, ls="--"))
    ax.text(X1 + 1.5, -2.6, "New in this study (gap experiments)", fontsize=7.4, fontweight="bold", color=INK, va="top")
    items = ["G1  quantile-matched gate (label-free shift adjustment)", "G2  validity-veto gate (PoseBusters before applying)",
             "G3  rigid-body projection of the correction", "G4  deep-ensemble spread as the gate signal",
             "G5  sequence-level train/external overlap", "G6  σ-shift diagnosis;  G7  three alternative splits"]
    for i, t in enumerate(items):
        ax.text(X1 + 1.5 + (i % 2) * 49, -6.2 - (i // 2) * 3.0, t, fontsize=6.0, color=INK2, va="top")
    arrow((X3 + W / 2, 3), (X3 + W / 2, -1.2))
    save(fig, "fig01_methodology")


def fig_selection(ev):
    s = ev["selection"]; archs = list(s["mean"])
    m = [s["mean"][a] for a in archs]; sd = [np.std(s["per_seed_val_mse_reduction"][a], ddof=1) for a in archs]
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    cols = [BLUE if a == s["selected"] else GREY for a in archs]
    ax.bar(archs, m, 0.6, color=cols, edgecolor="white", zorder=2)
    ax.errorbar(archs, m, yerr=sd, fmt="none", ecolor=INK, elinewidth=0.8, capsize=2.5, zorder=3)
    for i, a in enumerate(archs):
        ax.scatter([i] * 5, s["per_seed_val_mse_reduction"][a], s=9, color=INK, zorder=4, alpha=0.6, linewidths=0)
        lab = f"{m[i]:.2f}%"
        if a != s["selected"]:
            p = s["paired_t_vs_selected"][a]["p"]; lab += f"\np={p:.3f}"
        ax.text(i, max(m[i] + sd[i], max(s["per_seed_val_mse_reduction"][a])) + 0.4, lab, ha="center", va="bottom", fontsize=6.8, color=INK)
    ax.set_ylabel("Validation MSE reduction (%)")
    ax.axhline(0, color=INK2, lw=0.6)
    an = s.get("anova") or {}
    ax.set_title(f"Validation-only selection (ANOVA F={an.get('F', float('nan')):.2f}, p={an.get('p', float('nan')):.3f})", fontsize=8)
    ax.grid(axis="x", visible=False)
    lo = min(0, min(min(v) for v in s["per_seed_val_mse_reduction"].values())) - 1
    hi = max(max(v) for v in s["per_seed_val_mse_reduction"].values()) + 3
    ax.set_ylim(lo, hi)
    save(fig, "fig02_selection")


def fig_rmsd(ev):
    h = ev["heldout"]
    fig, ax = plt.subplots(figsize=(3.8, 2.7))
    groups = ["Internal test", "External"]
    vals = [[h[c]["ungated"]["baseline_success"], h[c]["ungated"]["success"], h[c]["gated"]["success"]] for c in ("test", "external")]
    bars(ax, groups, ["Vina baseline", "Ungated", "Gated"], vals, [GREY, BLUE, ORANGE], ylim=(0, 100))
    for g, c in enumerate(("test", "external")):
        for k, (key, off) in enumerate((("ungated", 0), ("gated", 1))):
            lo, hi = h[c][key]["bootstrap_ci_pp"]
            ax.text(g + (k - 0.0) * 0.27, 6, f"Δ {h[c][key]['net_change_pp']:+.1f}\n[{lo:+.1f}, {hi:+.1f}]", ha="center", fontsize=5.8, color=INK, va="bottom")
    ax.set_ylabel("RMSD < 2 Å success (%)")
    ax.legend(loc="upper center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 1.13))
    save(fig, "fig04_rmsd_success")


def fig_transitions(ev):
    h = ev["heldout"]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4), sharey=True)
    keys = ["preservation", "harm", "rescue", "persistent_failure"]
    for ax, c, t in zip(axes, ("test", "external"), ("Internal test", "External")):
        u = [h[c]["transitions_ungated"][k] for k in keys]; g = [h[c]["transitions_gated"][k] for k in keys]
        n = sum(u)
        bars(ax, ["Preserved", "Harmed", "Rescued", "Persistent\nfailure"], ["Ungated", "Gated"],
             [[100 * u[i] / n, 100 * g[i] / n] for i in range(4)], [BLUE, ORANGE], ylim=(0, 70))
        ax.set_title(t, fontsize=8)
    axes[0].set_ylabel("Seed-complex rows (%)")
    axes[1].legend(loc="upper right", fontsize=7)
    save(fig, "fig03_transitions")


def fig_validity(va):
    fig, ax = plt.subplots(figsize=(3.8, 2.7))
    groups = ["Internal test", "External"]
    keys = ("pass_baseline", "pass_ungated", "pass_gated")
    vals = [[va[c][k]["mean"] for k in keys] for c in ("test", "external")]
    errs = [[va[c][k]["bootstrap_ci"] for k in keys] for c in ("test", "external")]
    bars(ax, groups, ["Vina baseline", "Ungated", "Gated"], vals, [GREY, BLUE, ORANGE], errs=errs, ylim=(0, 110))
    ax.set_ylabel("PoseBusters pass rate (%)")
    ax.legend(loc="upper center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 1.13))
    save(fig, "fig05_posebusters_pass")


def fig_newly_invalid(va):
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    groups = ["Internal test", "External"]
    keys = ("newly_invalid_ungated", "newly_invalid_gated")
    vals = [[va[c][k]["mean"] for k in keys] for c in ("test", "external")]
    errs = [[va[c][k]["bootstrap_ci"] for k in keys] for c in ("test", "external")]
    top = np.nanmax([e[1] for row in errs for e in row] + [1.0])
    bars(ax, groups, ["Ungated", "Gated"], vals, [BLUE, ORANGE], errs=errs, ylim=(0, top * 1.25 + 2))
    ax.set_ylabel("Newly invalid among valid baselines (%)")
    ax.legend(loc="upper right", fontsize=7)
    save(fig, "fig06_newly_invalid")


def fig_cross(va):
    fig, ax = plt.subplots(figsize=(4.4, 2.6))
    keys = ["preservation", "harm", "rescue", "persistent_failure"]
    labels = ["Preserved", "Harmed", "Rescued", "Persistent\nfailure"]
    vals = [[va[c]["invalid_rate_by_transition_ungated"][k]["invalid_pct"] or 0 for c in ("test", "external")] for k in keys]
    bars(ax, labels, ["Internal test", "External"], vals, [BLUE, ORANGE], ylim=(0, 110))
    for i, k in enumerate(keys):
        for j, c in enumerate(("test", "external")):
            ax.text(i - 0.2 + 0.4 * j, 101, f"n={va[c]['invalid_rate_by_transition_ungated'][k]['n']}", ha="center", fontsize=5.8, color=INK2)
    ax.set_ylabel("Chemically invalid after ungated\ncorrection (%)")
    ax.legend(loc="upper center", ncol=2, fontsize=7, bbox_to_anchor=(0.5, 1.15))
    save(fig, "fig07_invalid_by_transition")


def fig_checks(va):
    """NEW: which PoseBusters checks fail after correction."""
    checks = [k for k, v in va["test"]["check_failure_rate_pct"]["corrected"].items()
              if max(va[c]["check_failure_rate_pct"]["corrected"][k] for c in ("test", "external")) >= 1.0]
    checks = sorted(checks, key=lambda k: -va["test"]["check_failure_rate_pct"]["corrected"][k])
    fig, ax = plt.subplots(figsize=(4.6, 0.32 * len(checks) + 0.9))
    y = np.arange(len(checks))
    for j, (c, col, lab) in enumerate((("test", BLUE, "Internal test"), ("external", ORANGE, "External"))):
        v = [va[c]["check_failure_rate_pct"]["corrected"][k] for k in checks]
        ax.barh(y + (j - 0.5) * 0.38, v, 0.36, color=col, label=lab, edgecolor="white", zorder=2)
        b = [va[c]["check_failure_rate_pct"]["baseline"][k] for k in checks]
        ax.scatter(b, y + (j - 0.5) * 0.38, marker="|", color=INK, s=40, zorder=3, label="Baseline rate" if j == 0 else None)
    ax.set_yticks(y); ax.set_yticklabels([k.replace("_", " ") for k in checks], fontsize=7)
    ax.invert_yaxis(); ax.set_xlabel("Failure rate after ungated correction (%)")
    ax.grid(axis="y", visible=False); ax.legend(fontsize=7, loc="lower right")
    save(fig, "fig08_check_failures")


def fig_gates(ev, va, gp):
    """NEW: success change vs validity for every gate variant."""
    variants = [("Frozen σ gate (paper)", "G0_frozen_gate_reference", ORANGE),
                ("Quantile-matched gate", "G1_quantile_gate", AQUA),
                ("Rigid projection + gate", "G3_rigid_projection", MAGENTA),
                ("Ensemble spread gate", "G4_ensemble", GREEN),
                ("Ensemble + rigid", "G4_ensemble_rigid", VIOLET)]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True)
    for ax, c, t in zip(axes, ("test", "external"), ("Internal test", "External")):
        base_valid = gp["G0_frozen_gate_reference"][c]["validity"]["pass_baseline"]
        ax.axvline(0, color=INK2, lw=0.6); ax.axhline(base_valid, color=GREY, lw=0.8, ls="--")
        ax.text(ax.get_xlim()[0] if False else 0.02, base_valid + 0.8, "baseline validity", transform=ax.get_yaxis_transform(), fontsize=6.3, color=INK2)
        # ungated reference
        u = gp["G0_frozen_gate_reference"][c]
        ax.scatter(u["ungated"]["net_change_pp"], u["validity"]["pass_ungated"], s=40, color=BLUE, zorder=3, label="Ungated (paper)",
                   edgecolors="white", linewidths=1.5)
        for name, key, col in variants:
            g = gp[key][c]
            ax.scatter(g["gated"]["net_change_pp"], g["validity"]["pass_gated"], s=40, color=col, zorder=3, label=name, edgecolors="white", linewidths=1.5)
        for name, key in (("Validity veto", "veto_only"), ("σ gate + veto", "sigma_and_veto")):
            g = gp["G2_validity_veto"][c][key]
            ax.scatter(g["gated"]["net_change_pp"], g["validity"]["pass_gated"], s=40, color=YELLOW if key == "veto_only" else "#b07a00",
                       marker="D", zorder=3, label=name, edgecolors="white", linewidths=1.5)
        ax.set_title(t, fontsize=8); ax.set_xlabel("Net change in RMSD < 2 Å success (pp)")
    axes[0].set_ylabel("PoseBusters pass rate (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=6.6, bbox_to_anchor=(0.5, -0.12))
    save(fig, "fig09_gate_variants")


def fig_sigma(gp, rows_csv):
    import pandas as pd
    r = pd.read_csv(rows_csv)
    fig, ax = plt.subplots(figsize=(3.8, 2.5))
    bins = np.linspace(r.sigma.quantile(0.005), r.sigma.quantile(0.995), 40)
    for c, col, lab in (("val", GREY, "Validation"), ("test", BLUE, "Internal test"), ("external", ORANGE, "External")):
        ax.hist(r[r.cohort == c].sigma, bins=bins, histtype="step", lw=1.6, color=col, density=True, label=lab)
    tau = json.load(open(f"{RES}/eval.json"))["gate"]["tau"]
    if np.isfinite(tau):
        ax.axvline(tau, color=INK, lw=0.8, ls="--"); ax.text(tau, ax.get_ylim()[1] * 0.92, " τ", fontsize=7, color=INK)
    ax.set_xlabel("Mean predicted σ per complex (Å)"); ax.set_ylabel("Density")
    ax.legend(fontsize=7)
    save(fig, "fig10_sigma_shift")


def fig_splits():
    files = sorted(glob.glob(f"{RES}/split_*_eval.json"))
    if not files:
        return
    main = json.load(open(f"{RES}/eval.json")); mv = load("validity.json")
    rows = [("original", main, mv)] + [(os.path.basename(f).split("_")[1], json.load(open(f)), load(os.path.basename(f).replace("eval", "validity"))) for f in files]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
    labels = [r[0] for r in rows]
    metrics = [("Test MSE reduction (%)", lambda e, v: e["heldout"]["test"]["mse_reduction_ungated"]),
               ("Ungated success change (pp)", lambda e, v: e["heldout"]["test"]["ungated"]["net_change_pp"]),
               ("Ungated pass rate (%)", lambda e, v: v["test"]["pass_ungated"]["mean"] if v else np.nan)]
    for ax, (t, f) in zip(axes, metrics):
        vals = [f(e, v) for _, e, v in rows]
        ax.bar(labels, vals, 0.6, color=[BLUE] + [GREY] * (len(vals) - 1), edgecolor="white", zorder=2)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:.1f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=6.8, color=INK)
        ax.set_title(t, fontsize=7.6); ax.axhline(0, color=INK2, lw=0.6); ax.grid(axis="x", visible=False)
        ax.tick_params(axis="x", labelsize=6.8)
    save(fig, "fig11_split_variance")


if __name__ == "__main__":
    methodology()
    ev, va, gp = load("eval.json"), load("validity.json"), load("gaps.json")
    if ev:
        fig_selection(ev); fig_rmsd(ev); fig_transitions(ev)
    if va:
        fig_validity(va); fig_newly_invalid(va); fig_cross(va); fig_checks(va)
    if gp and va and ev:
        fig_gates(ev, va, gp); fig_sigma(gp, f"{RES}/rows_selected.csv")
    fig_splits()
