"""RQ2/RQ3: admission on IG-Bench, baselines, ablations, defect reproduction,
threshold sweep, provider substitution and static-discharge analysis."""
from __future__ import annotations

import collections
import statistics
import time

from common import (admission_metrics, bootstrap_f1, close_verifiers, db, dump, inv_path,
                    load_bench, load_invariants, make_verifiers)
from invariantguard.baselines import ABAC, EstimateAdmission, KeywordGuardrail, NoVerification
from invariantguard.bounds import BoundConfig
from invariantguard.verifier import VerifierConfig, decide

RECORDS = load_bench()


def run(name, cfg_factory, loader=None, keep_records=True):
    vs = make_verifiers(cfg_factory, loader, suffix=name[:10].replace("-", "_"))
    rows, recs = [], []
    t0 = time.time()
    for r in RECORDS:
        v = vs[r["fixture"]]
        d = v.verify(r["action_sequence"])
        lab = r["ground_truth"]["label"]
        rows.append((lab, d.decision))
        recs.append({
            "id": r["scenario_id"], "fixture": r["fixture"], "category": r["category"],
            "label": lab, "decision": d.decision, "overall": d.overall, "risk": d.risk,
            "selected": d.selected, "empty_selection": d.empty_selection,
            "shadow_used": d.shadow_used, "latency_ms": d.latency_ms,
            "static_ms": d.static_ms, "shadow_ms": d.shadow_ms,
            "n_statements": len(r["action_sequence"]),
            "op": r["action_sequence"][0].split()[0].upper(),
            "evidence": [e.__dict__ for e in d.evidence], "cross_check": d.cross_check,
        })
    close_verifiers(vs)
    m = admission_metrics(rows)
    m["f1_ci"] = bootstrap_f1(rows)
    m["seconds"] = time.time() - t0
    m["latency_p50_ms"] = statistics.median(x["latency_ms"] for x in recs)
    m["latency_mean_ms"] = statistics.mean(x["latency_ms"] for x in recs)
    m["shadow_free_records"] = sum(not x["shadow_used"] for x in recs)
    m["shadow_free_selected"] = sum(not x["shadow_used"] and not x["empty_selection"] for x in recs)
    m["selected_pairs"] = sum(len(x["selected"]) for x in recs)
    m["static_pairs"] = sum(e["path"] in ("static", "frame") for x in recs for e in x["evidence"])
    m["empty_selection_records"] = sum(x["empty_selection"] for x in recs)
    m["empty_selection_safe"] = sum(x["empty_selection"] and x["label"] == "safe" for x in recs)
    print(f"{name:28s} cont={m['containment']:.3f} dec={m['decisiveness']:.3f} "
          f"fric={m['friction']:.3f} f1={m['f1']:.3f} static={m['static_pairs']} "
          f"p50={m['latency_p50_ms']:.1f}ms", flush=True)
    return m, recs


def per_fixture(recs):
    out = {}
    for fx in db.FIXTURES:
        rr = [(x["label"], x["decision"]) for x in recs if x["fixture"] == fx]
        m = admission_metrics(rr)
        m["empty_selection_safe"] = sum(x["empty_selection"] and x["label"] == "safe"
                                        for x in recs if x["fixture"] == fx)
        m["development"] = fx in db.DEVELOPMENT
        out[fx] = m
    return out


def tau_sweep(recs, cfg):
    out = {}
    for tau in (50, 60, 70, 80, 90):
        c = VerifierConfig(tau_block=tau)
        rows = []
        for x in recs:
            from invariantguard.verifier import Evidence
            ev = [Evidence(**e) for e in x["evidence"]]
            d, _, _ = decide(ev, x["empty_selection"], True, c)
            rows.append((x["label"], d))
        out[tau] = admission_metrics(rows)
    return out


def static_breakdown(recs):
    first = collections.Counter()
    for x in recs:
        for e in x["evidence"]:
            first[e["static_attempt"] or "none"] += 1
    return dict(first)


def baselines():
    out = {}
    conns, invs, cats = {}, {}, {}
    from invariantguard.snapshot import load_catalog
    for fx in db.FIXTURES:
        conns[fx] = db.connect(db.template_name(fx))
        invs[fx] = load_invariants(inv_path(fx))
        cats[fx] = load_catalog(conns[fx])
    makers = {
        "no_verification": lambda fx: NoVerification(),
        "keyword_guardrail": lambda fx: KeywordGuardrail(),
        "abac": lambda fx: ABAC(invs[fx], cats[fx]),
        "estimate_admission": lambda fx: EstimateAdmission(invs[fx], conns[fx]),
    }
    for name, mk in makers.items():
        bs = {fx: mk(fx) for fx in db.FIXTURES}
        rows, lat = [], []
        for r in RECORDS:
            t = time.perf_counter()
            d = bs[r["fixture"]].decide(r["action_sequence"])
            lat.append((time.perf_counter() - t) * 1000)
            rows.append((r["ground_truth"]["label"], d))
        m = admission_metrics(rows)
        m["f1_ci"] = bootstrap_f1(rows)
        m["latency_p50_ms"] = statistics.median(lat)
        out[name] = m
        print(f"{name:28s} cont={m['containment']:.3f} f1={m['f1']:.3f} "
              f"safe_blocked={m['safe_blocked']} admitted_unsafe={m['admitted_unsafe']}", flush=True)
    for c in conns.values():
        c.close()
    return out


def main():
    db.build_all_templates()
    results, all_recs = {}, {}
    configs = {
        "paper": (lambda: VerifierConfig(static_mode="paper"), None),
        "extended": (lambda: VerifierConfig(static_mode="extended"), None),
        "extended_crosscheck": (lambda: VerifierConfig(static_mode="extended", shadow_all=True), None),
        "no_static": (lambda: VerifierConfig(static_mode="off"), None),
        "ablation_no_cascade": (lambda: VerifierConfig(static_mode="paper", cascade_closure=False), None),
        "ext_no_cascade": (lambda: VerifierConfig(static_mode="extended", cascade_closure=False), None),
        "ext_no_pervalue": (lambda: VerifierConfig(static_mode="extended", bounds=BoundConfig(per_value=False)), None),
        "ext_no_frame_lower": (lambda: VerifierConfig(static_mode="extended", frame_rule=False, lower_bounds=False), None),
        # defects of Table 3, reintroduced one at a time
        "defect_cross_relation": (lambda: VerifierConfig(static_mode="paper", per_relation_scope=False, shadow_all=True),
                                  lambda fx: load_invariants(inv_path(fx), scoping="statement")),
        "defect_no_vacuity": (lambda: VerifierConfig(static_mode="paper", vacuity=False), None),
        "defect_statement_scope": (lambda: VerifierConfig(static_mode="paper"),
                                   lambda fx: load_invariants(inv_path(fx), scoping="statement")),
        "defect_all": (lambda: VerifierConfig(static_mode="paper", cascade_closure=False, per_relation_scope=False,
                                              vacuity=False),
                       lambda fx: load_invariants(inv_path(fx), scoping="statement")),
        # provider substitution
        "estimate_provider": (lambda: VerifierConfig(static_mode="extended", bounds=BoundConfig(provider="estimate")), None),
        "estimate_flagged_certified": (lambda: VerifierConfig(static_mode="extended", frame_rule=False,
                                                              bounds=BoundConfig(provider="estimate", estimate_certified=True)), None),
    }
    for name, (cf, loader) in configs.items():
        m, recs = run(name, cf, loader)
        results[name] = m
        all_recs[name] = recs
    # unsound static certifications under the cross-relation defect
    unsound = 0
    for x in all_recs["defect_cross_relation"]:
        for e in x["evidence"]:
            if e["path"] == "static" and e["verdict"] == "satisfied" and x["cross_check"].get(e["inv"]) == "violated":
                unsound += 1
    results["defect_cross_relation"]["unsound_static_certifications"] = unsound
    xc = collections.Counter()
    for x in all_recs["extended_crosscheck"]:
        for e in x["evidence"]:
            if e["inv"] in x["cross_check"]:
                xc[f"{e['verdict']}->{x['cross_check'][e['inv']]}"] += 1
    results["extended_crosscheck"]["static_vs_shadow"] = dict(xc)
    results["per_fixture_paper"] = per_fixture(all_recs["paper"])
    results["per_fixture_extended"] = per_fixture(all_recs["extended"])
    results["tau_sweep"] = tau_sweep(all_recs["paper"], None)
    results["static_breakdown_paper"] = static_breakdown(all_recs["paper"])
    results["static_breakdown_extended"] = static_breakdown(all_recs["extended"])
    results["baselines"] = baselines()
    dump("admission.json", results)
    import json
    with open(db.ROOT / "results" / "admission_records.jsonl", "w") as f:
        for name in ("paper", "extended", "no_static"):
            for x in all_recs[name]:
                f.write(json.dumps({"config": name, **x}, default=str) + "\n")


if __name__ == "__main__":
    main()
