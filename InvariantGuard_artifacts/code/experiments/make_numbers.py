"""Write results/numbers.tex: every measured number quoted in the paper, as a
LaTeX macro generated from the results files (nothing is typed by hand)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results"


def j(name):
    p = R / name
    return json.loads(p.read_text()) if p.exists() else None


def f3(x):
    return f"{x:.3f}"


def main():
    m = {}
    bq, adm, bv = j("bound_quality.json"), j("admission.json"), j("benchmark_validation.json")
    cc, sc, cv, sq = j("concurrency.json"), j("scale.json"), j("coverage.json"), j("sqlite_portability.json")
    s = bq["summary"]
    m.update({
        "BQCertUnder": f"{s['certified_underpredictions']} / {s['certified_pervalue_underpredictions']}",
        "BQEstUnder": s["estimate_underpredictions"], "BQEstRate": f3(s["estimate_rate"]),
        "BQEstLo": f3(s["estimate_rate_ci"][0]), "BQEstHi": f3(s["estimate_rate_ci"][1]),
        "BQAdmitWrong": s["estimate_admits_over_100"],
        "BQTmf": f"{s['tightness_mf_p50']:.2f}", "BQTpv": f"{s['tightness_pv_p50']:.2f}",
        "BQTmfMax": f"{s['tightness_mf_max']:.1f}", "BQTpvMax": f"{s['tightness_pv_max']:.1f}",
        "BQTmfNinety": f"{s['tightness_mf_p90']:.1f}", "BQTpvNinety": f"{s['tightness_pv_p90']:.1f}",
        "PropViol": bq["property_test"]["violations_mf"] + bq["property_test"]["violations_per_value"],
        "CascSum": bq["cascade_property"]["violations_sum"], "CascMax": bq["cascade_property"]["violations_max"],
        "CascCases": f"{bq['cascade_property']['cases']:,}", "CascChecks": f"{bq['cascade_property']['relation_checks']:,}",
        "CascDiamonds": bq["cascade_property"]["diamond_schemas"],
    })
    rows = [json.loads(x) for x in open(R / "bound_quality_rows.jsonl")]
    r = next(x for x in rows if x["predicate"] == "region = 0 AND city = 2")
    m["FigOneTrue"], m["FigOneBound"] = r["true"], r["bound_mf"]
    sw = bq["sweeps"]
    m["SweepRhoMin"] = f"{min(d['estimate_rate'] for d in sw['correlation']):.2f}"
    m["SweepRhoMax"] = f"{max(d['estimate_rate'] for d in sw['correlation']):.2f}"
    m["SweepScaleMax"] = f"{sw['scale'][-1]['estimate_rate']:.2f}"
    m["SweepSkewMinMf"] = f"{min(d['tightness_mf_max'] for d in sw['skew']):.0f}"
    m["SweepSkewMaxMf"] = f"{max(d['tightness_mf_max'] for d in sw['skew']):,.0f}"
    p, b = adm["paper"], adm["baselines"]
    m.update({
        "IGFone": f3(p["f1"]), "IGFoneLo": f3(p["f1_ci"][0]), "IGFoneHi": f3(p["f1_ci"][1]),
        "ABACFone": f3(b["abac"]["f1"]), "KWFone": f3(b["keyword_guardrail"]["f1"]), "ESTFone": f3(b["estimate_admission"]["f1"]),
        "ABACSafeBlocked": b["abac"]["safe_blocked"], "ABACAdmitted": b["abac"]["admitted_unsafe"],
        "ESTAdmitted": b["estimate_admission"]["admitted_unsafe"], "ESTCont": f3(b["estimate_admission"]["containment"]),
        "NoCascCont": f3(adm["ablation_no_cascade"]["containment"]), "NoCascDec": f3(adm["ablation_no_cascade"]["decisiveness"]),
        "NoCascFric": f3(adm["ablation_no_cascade"]["friction"]),
        "NoCascDelta": p["blocked"] - adm["ablation_no_cascade"]["blocked"],
        "DefAllCont": f3(adm["defect_all"]["containment"]),
        "CrossUnsound": adm["defect_cross_relation"]["unsound_static_certifications"],
        "CrossCont": f3(adm["defect_cross_relation"]["containment"]),
        "StmtCont": f3(adm["defect_statement_scope"]["containment"]),
        "StmtAdmitted": adm["defect_statement_scope"]["admitted_unsafe"],
        "EstCertAdmitted": adm["estimate_flagged_certified"]["admitted_unsafe"],
        "EstCertCont": f3(adm["estimate_flagged_certified"]["containment"]),
    })
    rc = bv["release_criteria"]
    c = bv["oracle_vs_shadow"]
    m.update({
        "RelDistinct": f"{rc['distinct_ratio']:.2f}", "RelNoop": f"{rc['noop_ratio']:.3f}", "RelNoops": rc["noops"],
        "RelUnres": f"{rc['unresolved_ratio']:.3f}", "RelBalance": f"{rc['balance']:.3f}",
        "OSPairs": c["action"]["pairs"], "OSStmtFinal": f"{c['statement']['agreement_final']:.3f}",
        "OSStmtMultiFinal": f"{c['statement']['multi_agreement_final']:.2f}",
        "OSStmtBoundary": f"{c['statement']['agreement_boundary']:.2f}",
        "SelViolPairs": bv["selection_completeness"].get("violated_pairs", 0),
        "SelChangedPairs": bv["selection_completeness"].get("changed_pairs", 0),
    })
    if cc:
        L = cc["latency"]
        g = lambda d, k: f"{L[f'{d}|{k}']['p50_ms']:.1f}"  # noqa: E731
        m.update({"LatSepOne": g("separate", 1), "LatSepSixteen": g("separate", 16),
                  "LatSerOne": g("serializable", 1), "LatSerSixteen": g("serializable", 16),
                  "LatWitOne": g("witness", 1), "LatWitSixteen": g("witness", 16)})
        C = cc["containment"]
        tot = lambda d: sum(v["unsafe_commits"] for v in C.values() if v["discipline"] == d)  # noqa: E731
        m.update({"UnsafeSep": tot("separate"), "UnsafeSer": tot("serializable"), "UnsafeWit": tot("witness"),
                  "UnsafeSepMax": max(v["unsafe_commits"] for v in C.values() if v["discipline"] == "separate")})
    if sc:
        pts = sc["points"]
        w0 = sc["workloads"][0]
        for k, pt in zip("ABCD", pts):
            m[f"Snap{k}"] = f"{pt['snapshot_s']:.2f}"
            rws = pt["rows"]
            m[f"Rows{k}"] = f"{rws / 1e6:.2f}M" if rws >= 1e6 else f"{rws / 1e3:.0f}k"
        st = [pt[f"extended|{w0}|p50_ms"] for pt in pts]
        m["StaticSmall"], m["StaticBig"] = f"{min(st):.1f}", f"{max(st):.1f}"
        m["ShadowBig"] = f"{pts[-1][f'off|{w0}|p50_ms']:.0f}"
        m["Speedup"] = f"{pts[-1][f'off|{w0}|p50_ms'] / pts[-1][f'extended|{w0}|p50_ms']:.0f}"
    if cv:
        e = cv["results"]["extended"]
        m.update({"CovSuggested": sum(len(v) for v in cv["suggested"].values()),
                  "CovFlips": e["label_changes"].get("safe->unsafe", 0),
                  "CovCont": f3(e["containment"]), "CovDec": f3(e["decisiveness"]), "CovFric": f3(e["friction"]),
                  "CovN": e["n"], "CovStatic": e["evidence_paths"].get("static", 0) + e["evidence_paths"].get("frame", 0)})
    if sq:
        e = sq["extended"]
        ag = e["label_agreement"]
        same = sum(v for k, v in ag.items() if k.split("|")[0][3:] == k.split("|")[1][7:])
        m.update({"SqRecords": e["records"], "SqAgree": same, "SqN": e["n"], "SqCont": f3(e["containment"]),
                  "SqDec": f3(e["decisiveness"]), "SqFric": f3(e["friction"]), "SqStatic": e["static_pairs"],
                  "SqBQ": sq["bound_quality"]["certified_underpredictions"]})
    out = ["% generated by code/experiments/make_numbers.py -- do not edit"]
    for k, v in sorted(m.items()):
        out.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    (ROOT / "results" / "numbers.tex").write_text("\n".join(out) + "\n")
    print(f"{len(m)} macros")


if __name__ == "__main__":
    main()
