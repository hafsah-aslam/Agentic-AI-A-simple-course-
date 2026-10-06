"""Coverage tooling: suggested invariants over uncovered cascade relations.

The augmented invariant set (declared + suggested) is written to YAML, the
benchmark is re-labelled by the independent oracle under that set, and the
verifier is re-run.  Reported: friction before/after, containment,
decisiveness, label changes, and how much of the new evidence the static
path discharges.
"""
from __future__ import annotations

import collections

import yaml

from common import (admission_metrics, db, dump, inv_path, load_bench, load_invariants, RESULTS)
from invariantguard.coverage import suggest_invariants, to_yaml_dicts, uncovered_relations
from invariantguard.oracle import oracle_label
from invariantguard.snapshot import build_snapshot
from invariantguard.verifier import Verifier, VerifierConfig


def main():
    db.build_all_templates()
    outdir = RESULTS / "coverage_invariants"
    outdir.mkdir(exist_ok=True)
    recs = load_bench(evaluable_only=False)
    files, suggested = {}, {}
    for fx in db.FIXTURES:
        conn = db.connect(db.template_name(fx))
        snap = build_snapshot(conn)
        conn.close()
        declared = load_invariants(inv_path(fx))
        sug = suggest_invariants(snap.catalog, snap, declared)
        suggested[fx] = [i.id for i in sug]
        doc = yaml.safe_load(open(inv_path(fx)))
        doc["invariants"] += to_yaml_dicts(sug)
        p = outdir / f"{fx}_with_coverage.yaml"
        p.write_text(yaml.safe_dump(doc, sort_keys=False))
        files[fx] = p
        print(fx, "uncovered:", uncovered_relations(snap.catalog, declared), flush=True)
    res = {}
    for mode in ("paper", "extended"):
        vs = {}
        for fx in db.FIXTURES:
            name = f"igcov_{fx}"
            db.drop_db(name)
            with db.connect() as c:
                c.execute(f'CREATE DATABASE "{name}" TEMPLATE "{db.template_name(fx)}"')
            conn = db.connect(name)
            vs[fx] = Verifier(name, load_invariants(files[fx]), build_snapshot(conn),
                              VerifierConfig(static_mode=mode), conn)
        rows, changes, paths = [], collections.Counter(), collections.Counter()
        shadow_free = 0
        old_rows = []
        for r in recs:
            o = oracle_label(db.template_name(r["fixture"]), files[r["fixture"]], r["action_sequence"])
            if o["label"] is None:
                continue
            old = r["ground_truth"]["label"]
            changes[f"{old}->{o['label']}"] += 1
            d = vs[r["fixture"]].verify(r["action_sequence"])
            rows.append((o["label"], d.decision))
            if old:
                old_rows.append((old, d.decision))
            shadow_free += not d.shadow_used
            for e in d.evidence:
                paths[e.path] += 1
        m = admission_metrics(rows)
        m.update({"label_changes": dict(changes), "evidence_paths": dict(paths),
                  "shadow_free_records": shadow_free,
                  "empty_selection": sum(1 for _ in []),
                  "original_labels": admission_metrics(old_rows)})
        res[mode] = m
        print(mode, {k: m[k] for k in ("containment", "decisiveness", "friction", "safe", "unsafe")},
              dict(changes), dict(paths), flush=True)
        for v in vs.values():
            v.conn.close()
            db.drop_db(v.dbname)
    dump("coverage.json", {"suggested": suggested, "results": res,
                           "policy": "theta = max(1, ceil(0.10 * |R|)), action-scoped, severity 8"})


if __name__ == "__main__":
    main()
