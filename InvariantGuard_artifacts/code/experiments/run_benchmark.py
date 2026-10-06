"""RQ4: IG-Bench validation, the boundary-matched oracle, systematic
selection-completeness analysis and invariant-set sanity checks."""
from __future__ import annotations

import collections

from common import db, dump, inv_path, load_bench, load_invariants, make_verifiers, close_verifiers
from invariantguard.compiler import compile_action
from invariantguard.oracle import oracle_label
from invariantguard.verifier import VerifierConfig, select_invariants


def release_criteria(all_records, oracle):
    n = len(all_records)
    distinct = len({tuple(r["action_sequence"]) for r in all_records})
    noops = sum(1 for r in all_records if oracle[r["scenario_id"]]["status"] == "executed"
                and oracle[r["scenario_id"]]["rows_changed"] == 0)
    unresolved = sum(1 for r in all_records if oracle[r["scenario_id"]]["status"] != "executed")
    U = sum(1 for r in all_records if oracle[r["scenario_id"]]["label"] == "unsafe")
    F = sum(1 for r in all_records if oracle[r["scenario_id"]]["label"] == "safe")
    repeats = sum(1 for r in all_records if len(r["action_sequence"]) > 1
                  and len(set(r["action_sequence"])) == 1)
    crit = {
        "distinct_ratio": distinct / n, "noop_ratio": noops / n, "unresolved_ratio": unresolved / n,
        "balance": min(U, F) / (U + F), "repeated_statement_sequences": repeats,
    }
    crit["accepted"] = (crit["distinct_ratio"] >= 0.85 and crit["noop_ratio"] <= 0.05 and
                        crit["unresolved_ratio"] <= 0.15 and crit["balance"] >= 0.25 and repeats == 0)
    crit.update({"records": n, "distinct": distinct, "noops": noops, "unresolved": unresolved,
                 "unsafe": U, "safe": F})
    return crit


def main():
    db.build_all_templates()
    allr = load_bench(evaluable_only=False)
    # 1. re-derive every label with the independent oracle
    oracle = {}
    for r in allr:
        oracle[r["scenario_id"]] = oracle_label(db.template_name(r["fixture"]), inv_path(r["fixture"]),
                                                r["action_sequence"])
    agree = collections.Counter()
    for r in allr:
        g, o = r["ground_truth"], oracle[r["scenario_id"]]
        agree["label_match" if g["label"] == o["label"] else "label_mismatch"] += 1
        agree["violations_match" if set(g["violated_invariants"]) == set(o["violated"]) else "violations_mismatch"] += 1
    rejected = collections.Counter(o["error"].split(":")[0] for o in oracle.values() if o["error"])
    crit = release_criteria(allr, oracle)
    by_cat = collections.Counter((r["category"], oracle[r["scenario_id"]]["label"]) for r in allr)
    mech = collections.Counter()
    for r in allr:
        o = oracle[r["scenario_id"]]
        if o["label"] == "unsafe":
            ops = {s.split()[0].upper() for s in r["action_sequence"]}
            if len(r["action_sequence"]) > 1:
                mech["multi-statement cumulative"] += 1
            elif "DROP" in ops:
                mech["DROP TABLE"] += 1
            elif "TRUNCATE" in ops:
                mech["TRUNCATE CASCADE"] += 1
            elif any(v.endswith("cascade.delta") or "integrity" in v or "exists" in v for v in o["violated"]) \
                    and not any(v.split(".")[0] == r["action_sequence"][0].split('"')[1] for v in o["violated"]):
                mech["cascade to child relation"] += 1
            else:
                mech["direct over-broad delete"] += 1

    # 2. boundary-matched oracle vs shadow verification, statement-scoped declarations
    evaluable = [r for r in allr if oracle[r["scenario_id"]]["label"]]
    comp = {}
    for scoping in ("action", "statement"):
        vs = make_verifiers(lambda: VerifierConfig(static_mode="off"),
                            lambda fx: load_invariants(inv_path(fx), scoping=scoping), suffix=f"b{scoping[:3]}")
        pairs = collections.Counter()
        multi = collections.Counter()
        for r in evaluable:
            fin = oracle_label(db.template_name(r["fixture"]), inv_path(r["fixture"]), r["action_sequence"],
                               mode="final", scoping=scoping) if scoping == "statement" else oracle[r["scenario_id"]]
            bnd = oracle_label(db.template_name(r["fixture"]), inv_path(r["fixture"]), r["action_sequence"],
                               mode="boundary", scoping=scoping)
            d = vs[r["fixture"]].verify(r["action_sequence"])
            for e in d.evidence:
                if e.verdict == "undecidable":
                    continue
                sh = e.verdict == "satisfied"
                pairs[("final", sh == fin["per_invariant"].get(e.inv, True))] += 1
                pairs[("boundary", sh == bnd["per_invariant"].get(e.inv, True))] += 1
                if len(r["action_sequence"]) > 1:
                    multi[("final", sh == fin["per_invariant"].get(e.inv, True))] += 1
                    multi[("boundary", sh == bnd["per_invariant"].get(e.inv, True))] += 1
        close_verifiers(vs)
        comp[scoping] = {
            "pairs": sum(v for (k, _), v in pairs.items() if k == "final"),
            "agreement_final": pairs[("final", True)] / max(1, pairs[("final", True)] + pairs[("final", False)]),
            "agreement_boundary": pairs[("boundary", True)] / max(1, pairs[("boundary", True)] + pairs[("boundary", False)]),
            "disagree_final": pairs[("final", False)], "disagree_boundary": pairs[("boundary", False)],
            "multi_pairs": multi[("final", True)] + multi[("final", False)],
            "multi_agreement_final": multi[("final", True)] / max(1, multi[("final", True)] + multi[("final", False)]),
            "multi_agreement_boundary": multi[("boundary", True)] / max(1, multi[("boundary", True)] + multi[("boundary", False)]),
        }
        print(scoping, comp[scoping], flush=True)

    # 3. selection completeness: every invariant whose value changed must be selected
    gaps = collections.Counter()
    gap_examples = []
    per_inv = {}
    for fx in db.FIXTURES:
        invs = load_invariants(inv_path(fx))
        conn = db.connect(db.template_name(fx))
        from invariantguard.snapshot import load_catalog
        cat = load_catalog(conn)
        conn.close()
        for inv in invs:
            per_inv[inv.id + "@" + fx] = {"fixture": fx, "kind": inv.relation, "selected": 0, "violated": 0,
                                          "changed": 0, "holds_initially": True}
        for r in [x for x in evaluable if x["fixture"] == fx]:
            o = oracle[r["scenario_id"]]
            stmts = [s for s in compile_action(r["action_sequence"]) if s.state_changing]
            sel, _ = select_invariants(cat, stmts, invs, VerifierConfig())
            sel_ids = {i.id for i in sel}
            for inv in invs:
                pre, post = o["values"].get(inv.id, (None, None))
                changed = pre != post if inv.is_delta else (post != inv.params.get("expected", True))
                key = inv.id + "@" + fx
                per_inv[key]["selected"] += inv.id in sel_ids
                per_inv[key]["violated"] += inv.id in o["violated"]
                per_inv[key]["changed"] += bool(pre != post)
                if inv.id in o["violated"]:
                    gaps["violated_pairs"] += 1
                    if inv.id not in sel_ids:
                        gaps["violated_not_selected"] += 1
                        gap_examples.append((r["scenario_id"], r["action_sequence"], inv.id))
                if pre != post:
                    gaps["changed_pairs"] += 1
                    if inv.id not in sel_ids:
                        gaps["changed_not_selected"] += 1
        # invariant sanity: holds on the pristine fixture
        conn = db.connect(db.template_name(fx))
        for inv in invs:
            try:
                v = conn.execute(inv.post_query).fetchone()[0]
                per_inv[inv.id + "@" + fx]["holds_initially"] = inv.holds(v, v) if inv.is_delta else inv.holds(None, v)
            except Exception:
                per_inv[inv.id + "@" + fx]["holds_initially"] = False
        conn.close()
    # violations that would not have changed the decision (another selected invariant is violated)
    critical = 0
    for sid, seq, iid in gap_examples:
        o = oracle[sid]
        fx = next(r["fixture"] for r in evaluable if r["scenario_id"] == sid)
        invs = load_invariants(inv_path(fx))
        conn = db.connect(db.template_name(fx))
        from invariantguard.snapshot import load_catalog
        cat = load_catalog(conn)
        conn.close()
        sel, _ = select_invariants(cat, [s for s in compile_action(seq) if s.state_changing], invs, VerifierConfig())
        if not ({i.id for i in sel} & set(o["violated"])):
            critical += 1
    gaps["records_with_no_selected_violation"] = critical
    print("gaps", dict(gaps), flush=True)
    dump("benchmark_validation.json", {
        "release_criteria": crit, "oracle_agreement": dict(agree), "rejected_by_dbms": dict(rejected),
        "category_by_label": {f"{c}|{l}": v for (c, l), v in by_cat.items()},
        "unsafe_mechanisms": dict(mech), "oracle_vs_shadow": comp,
        "selection_completeness": dict(gaps), "gap_examples": gap_examples[:20],
        "invariant_sanity": per_inv,
    })


if __name__ == "__main__":
    main()
