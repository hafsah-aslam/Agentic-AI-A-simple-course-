"""Write every number quoted in the paper as a LaTeX macro (paper/numbers.tex) from the result files.

Usage: python3 make_numbers.py RESULTS_DIR MANIFEST_LOG OUT.tex
"""
import sys, json, glob, os, re

RES, MANLOG, OUT = sys.argv[1:4]
e = json.load(open(f"{RES}/eval.json"))
v = json.load(open(f"{RES}/validity.json"))
g = json.load(open(f"{RES}/gaps.json"))
m = json.load(open(MANLOG))
M = {}


def put(name, value, fmt="{:.2f}"):
    if value is None or (isinstance(value, float) and value != value):
        M[name] = "n/a"; return
    M[name] = fmt.format(value) if isinstance(value, (int, float)) and fmt else str(value)


def ci(name, pair, fmt="{:.2f}"):
    put(name + "Lo", pair[0], fmt); put(name + "Hi", pair[1], fmt)


C = {"test": "Int", "external": "Ext", "val": "Val"}
SECTIONS = []
SECTIONS.append('# data\nput("IntersectN", f"{m[\'three_way_intersection\']:,}", None); put("CovalentN", m["excluded_covalent"], "{:,}")\nput("LigNotLocated", m["eligibility_status_counts"].get("ligand_not_located", 0), "{:,}")\nput("StructFail", m["eligibility_status_counts"].get("structure_failure", 0), "{:,}")\nput("TouchedGroups", f"{m[\'candidate_touching_groups\']:,}", None)\nput("CandidateGroups", f"{m[\'candidate_groups\']:,}", None)')
SECTIONS.append('# selection\ns = e["selection"]\nfor a, val in s["mean"].items():\n    put(f"Sel{a}", val)\nput("SelArch", s["selected"], None); put("AnovaF", s["anova"]["F"]); put("AnovaP", s["anova"]["p"], "{:.3f}")\nfor a, d in s["paired_t_vs_selected"].items():\n    put(f"T{a}", d["t"]); put(f"P{a}", d["p"], "{:.3f}")')
SECTIONS.append('# gate\ngt = e["gate"]\nput("StageA", gt["stage_a_pearson"], "{:.3f}"); put("Tau", gt["tau"], "{:.3f}"); put("ValNet", gt["val_net_success_pp"])\nfor c, k in C.items():\n    put(f"Admit{k}", gt["admit_rate"][c], "{:.1f}"); put(f"Sigma{k}", gt["mean_sigma"][c], "{:.2f}")\n    put(f"BaseRMSD{k}", gt["mean_baseline_rmsd"][c], "{:.2f}")\nctrl = e["baseline_rmsd_control_gate"]\nput("CtrlLe", ctrl["apply_if_rmsd_le_t"]["best_val_net_success_pp"]); put("CtrlGe", ctrl["apply_if_rmsd_ge_t"]["best_val_net_success_pp"])\nput("CtrlGeT", ctrl["apply_if_rmsd_ge_t"]["threshold"] or 0)')
SECTIONS.append('# held-out RMSD results\nfor c, k in C.items():\n    h = e["heldout"][c]\n    put(f"N{k}", h["n_complexes"], "{:,}"); put(f"Rows{k}", h["n_rows"], "{:,}")\n    put(f"MSE{k}", h["mse_reduction_ungated"]); put(f"MSEGated{k}", h["mse_reduction_gated"])\n    put(f"MSE{k}Min", min(h["mse_reduction_ungated_per_seed"])); put(f"MSE{k}Max", max(h["mse_reduction_ungated_per_seed"]))\n    for kind in ("ungated", "gated"):\n        b = h[kind]; K = "Ung" if kind == "ungated" else "Gat"\n        put(f"Base{k}", b["baseline_success"], "{:.1f}"); put(f"Succ{K}{k}", b["success"], "{:.1f}")\n        put(f"Net{K}{k}", b["net_change_pp"], "{:+.1f}"); ci(f"Boot{K}{k}", b["bootstrap_ci_pp"], "{:+.1f}"); ci(f"SeedT{K}{k}", b["seed_t_ci_pp"], "{:+.1f}")\n    for kind, K in (("transitions_ungated", "Ung"), ("transitions_gated", "Gat")):\n        for t, n in h[kind].items():\n            put(f"Tr{K}{k}{t.replace(\'_\', \'\').title()}", n, "{:,}")')
SECTIONS.append('# statistics\nfor name, d in e["permutation_test"].items():\n    K = "Ca" if name == "nearest_pocket_ca" else "Cen"\n    put(f"PermR{K}", d["r"], "{:.3f}"); put(f"PermNull{K}", d["null_mean_r"], "{:.3f}")\n    put(f"PermP{K}", d["p_two_sided_centred"], "{:.1e}")\n    put("PermAtoms", f"{d[\'atoms\']:,}", None); put("PermComplexes", f"{d[\'complexes\']:,}", None)\nr = e["rotation_audit"]\nfor k, K in (("mean", "Mean"), ("median", "Median"), ("p95", "Pct"), ("max", "Max")):\n    put(f"Rot{K}", r[k], "{:.2f}")\nput("MetricId", e["metric_identity_abs_error"], "{:.1e}")')
SECTIONS.append('# validity\nfor c, k in (("test", "Int"), ("external", "Ext")):\n    x = v[c]\n    for key, K in (("pass_baseline", "PassBase"), ("pass_ungated", "PassUng"), ("pass_gated", "PassGat"),\n                   ("newly_invalid_ungated", "NewInvUng"), ("newly_invalid_gated", "NewInvGat")):\n        put(f"{K}{k}", x[key]["mean"]); ci(f"{K}{k}Boot", x[key]["bootstrap_ci"])\n    put(f"RelRed{k}", x["relative_reduction_pct"], "{:.1f}")\n    for t, d in x["invalid_rate_by_transition_ungated"].items():\n        put(f"Inv{k}{t.replace(\'_\', \'\').title()}", d["invalid_pct"] or 0, "{:.1f}")\n    cf = x["check_failure_rate_pct"]["corrected"]\n    for chk in ("bond_lengths", "bond_angles", "internal_steric_clash", "internal_energy", "minimum_distance_to_protein"):\n        put(f"Chk{k}{chk.replace(\'_\', \'\').replace(\'-\', \'\').title()}", cf[chk], "{:.1f}")\n    pv = x["pass_rate_variants_pct"]\n    put(f"PassRigid{k}", pv["rigid"], "{:.1f}"); put(f"PassEns{k}", pv["ensemble"], "{:.1f}"); put(f"PassEnsRigid{k}", pv["ensemble_rigid"], "{:.1f}")\n    put(f"Obabel{k}", x["obabel_artifact"]["complexes_failing_sanitization"], "{:,}")\n    put(f"ObabelAtoms{k}", x["obabel_artifact"]["n_valence4_uncharged_atoms"], "{:,}")\nsp = v["spot_checks_preserved_invalid_internal_seed0"]\nbl = sp.get("min_bond_length_ratio_min_median") or [None, None]\nput("SpotN", sp["n"], "{:,}"); put("SpotBondMin", 100 * bl[0] if bl[0] is not None else None, "{:.0f}")\nput("SpotBondMed", 100 * bl[1] if bl[1] is not None else None, "{:.0f}"); put("SpotAngleMax", sp.get("max_angle_change_deg_max"), "{:.0f}")')
SECTIONS.append('# gaps\nfor key, K in (("G0_frozen_gate_reference", "Gz"), ("G1_quantile_gate", "Gq"), ("G3_rigid_projection", "Gr"), ("G4_ensemble", "Ge"), ("G4_ensemble_rigid", "Ger")):\n    d = g[key]\n    for c, k in (("test", "Int"), ("external", "Ext")):\n        x = d[c]\n        put(f"{K}Admit{k}", x["admit_rate_pct"], "{:.1f}"); put(f"{K}MSE{k}", x["mse_reduction_ungated"])\n        put(f"{K}Succ{k}", x["ungated"]["success"], "{:.1f}"); put(f"{K}Net{k}", x["ungated"]["net_change_pp"], "{:+.1f}")\n        put(f"{K}GNet{k}", x["gated"]["net_change_pp"], "{:+.2f}")\n        put(f"{K}PassUng{k}", x["validity"]["pass_ungated"], "{:.1f}"); put(f"{K}PassGat{k}", x["validity"]["pass_gated"], "{:.1f}")\nput("GqQ", 100 * g["G1_quantile_gate"]["q"], "{:.1f}")\nput("GrValMSE", g["G3_rigid_projection"]["val_mse_reduction"]); put("GeValMSE", g["G4_ensemble"]["val_mse_reduction"])\nput("GeStageA", g["G4_ensemble"]["stage_a_pearson_spread_vs_rmsd"], "{:.3f}"); put("GerValNet", g["G4_ensemble_rigid"]["val_net_success_pp"])\nfor c, k in (("test", "Int"), ("external", "Ext")):\n    for name, K in (("veto_only", "Veto"), ("sigma_and_veto", "SigVeto")):\n        x = g["G2_validity_veto"][c][name]\n        put(f"{K}Admit{k}", x["admit_rate_pct"], "{:.1f}"); put(f"{K}Net{k}", x["gated"]["net_change_pp"], "{:+.2f}")\ns5 = g["G5_sequence_overlap"]\nput("SeqExact", s5["external_exact_chain_match_with_train"], "{:,}"); put("SeqNear", s5["external_near_identical_3mer_jaccard_ge_0.9"], "{:,}")\nput("SeqNearPct", 100 * s5["external_near_identical_3mer_jaccard_ge_0.9"] / s5["n_external"], "{:.1f}")\nfor name, K in (("novel", "Novel"), ("near_identical", "Near")):\n    x = s5["stratified"][name]\n    put(f"Seq{K}N", x["n_complexes"], "{:,}"); put(f"Seq{K}MSE", x["mse_reduction_ungated"])\n    put(f"Seq{K}Base", x["ungated"]["baseline_success"], "{:.1f}"); put(f"Seq{K}Net", x["ungated"]["net_change_pp"], "{:+.1f}")\ns6 = g["G6_sigma_shift"]\nput("SigShiftExt", s6["external_vs_val_mean_sigma_change_pct"], "{:+.1f}"); put("SigShiftInt", s6["test_vs_val_mean_sigma_change_pct"], "{:+.1f}")\nput("KSExtD", s6["ks_val_vs_external"]["D"], "{:.3f}"); put("KSExtP", s6["ks_val_vs_external"]["p"], "{:.3f}")\nput("KSIntD", s6["ks_val_vs_test"]["D"], "{:.3f}"); put("KSIntP", s6["ks_val_vs_test"]["p"], "{:.1e}")\nfor c, k in (("val", "Val"), ("test", "Int"), ("external", "Ext")):\n    put(f"SigR{k}", s6["pearson_sigma_vs_baseline_rmsd"][c], "{:.3f}"); put(f"SigGain{k}", s6["spearman_sigma_vs_correction_gain"][c], "{:.3f}")\nfor c, k in (("train", "Train"), ("val", "Val"), ("test", "Int"), ("external", "Ext")):\n    put(f"LigAtoms{k}", s6["mean_ligand_heavy_atoms"][c], "{:.1f}"); put(f"PocketRes{k}", s6["mean_pocket_residues"][c], "{:.1f}")')
SECTIONS.append('# G8 shrinkage / deformation\nsh = json.load(open(f"{RES}/shrinkage.json"))["summary"]\nfor c, k in (("val", "Val"), ("test", "Int"), ("external", "Ext")):\n    x = sh[c]\n    put(f"RgCorr{k}", x["rg_ratio_corrected_q25_50_75"][1]); put(f"RgCorr{k}Lo", x["rg_ratio_corrected_q25_50_75"][0]); put(f"RgCorr{k}Hi", x["rg_ratio_corrected_q25_50_75"][2])\n    put(f"RgRef{k}", x["rg_ratio_reference_q25_50_75"][1]); put(f"InternalShare{k}", 100 * x["internal_share_q25_50_75"][1], "{:.0f}")\n    put(f"Contracted{k}", 100 * x["frac_contracted_below_0p8"], "{:.1f}")\n    put(f"MedianGain{k}", 100 * x["median_sq_error_reduction_full"], "{:+.1f}")')
SECTIONS.append('# split variance (G7)\nsplits = sorted(glob.glob(f"{RES}/split_*_eval.json"))\nfor K in ("SA", "SB", "SC"):            # placeholders when the alternative splits were skipped\n    for f in ("NTest", "StageA", "Pass", "MSEInt", "MSEExt", "BaseInt", "NetInt", "NetExt", "AdmitVal", "PassBase", "PassUng"):\n        M[K + f] = "n/a"\nfor i, f in enumerate(splits, 1):\n    a = json.load(open(f)); vf = f.replace("eval", "validity"); vv = json.load(open(vf)) if os.path.exists(vf) else None\n    K = "S" + "ABC"[i - 1]\n    t = a["heldout"]["test"]; x = a["heldout"]["external"]\n    put(f"{K}NTest", a["cohort_sizes"]["test"], "{:,}"); put(f"{K}StageA", a["gate"]["stage_a_pearson"], "{:.3f}")\n    put(f"{K}Pass", "passes" if a["gate"]["stage_a_pass"] else "fails", None)\n    put(f"{K}MSEInt", t["mse_reduction_ungated"]); put(f"{K}MSEExt", x["mse_reduction_ungated"])\n    put(f"{K}BaseInt", t["ungated"]["baseline_success"], "{:.1f}"); put(f"{K}NetInt", t["ungated"]["net_change_pp"], "{:+.1f}")\n    put(f"{K}NetExt", x["ungated"]["net_change_pp"], "{:+.1f}"); put(f"{K}AdmitVal", a["gate"]["admit_rate"]["val"], "{:.1f}")\n    if vv:\n        put(f"{K}PassBase", vv["test"]["pass_baseline"]["mean"], "{:.1f}"); put(f"{K}PassUng", vv["test"]["pass_ungated"]["mean"], "{:.1f}")\n')
for _sec in SECTIONS:
    try:
        exec(_sec, globals())
    except (KeyError, TypeError, IndexError, FileNotFoundError, ValueError) as _e:
        print("warning: section skipped:", _sec.splitlines()[0], "->", type(_e).__name__, _e)
# any macro the paper uses but that could not be computed is defined as n/a, so the paper always compiles
_paper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper")
_used = set()
for _f in glob.glob(os.path.join(_paper, "*.tex")) + glob.glob(os.path.join(_paper, "sections", "*.tex")):
    if os.path.abspath(_f) != os.path.abspath(OUT):
        _used |= set(re.findall(r"\\([A-Z][A-Za-z]+)", open(_f).read()))
_defined_elsewhere = {"Ang", "AA", "AE", "OE", "L", "O", "P", "S", "TeX", "LaTeX", "Delta", "Gamma", "Lambda", "Omega", "Phi", "Pi",
                      "Psi", "Sigma", "Theta", "Upsilon", "Xi", "Pr", "Re", "Im", "Huge", "Large", "LARGE", "Rightarrow", "Leftarrow",
                      "Leftrightarrow", "Longrightarrow", "IfFileExists", "AtBeginDocument", "AtBeginMaketitle", "PassOptionsToPackage"}
for _m in sorted(_used - set(M) - _defined_elsewhere):
    if _m[0].isupper() and _m not in ("TeX", "LaTeX"):
        M[_m] = "n/a"
with open(OUT, "w") as fh:
    fh.write("% generated by src/make_numbers.py from results/*.json -- do not edit by hand\n")
    for k, val in M.items():
        assert k.isalpha(), k
        fh.write(f"\\newcommand{{\\{k}}}{{{val}}}\n")
print(len(M), "macros written to", OUT)
