"""Portability: the unchanged bound rules, certification gate, scope
condition and decision rule on SQLite.

DELETE records are replayed (TRUNCATE and DROP ... CASCADE have no SQLite
equivalent with the same semantics).  An independent SQLite oracle labels
each record; the verifier's admission metrics and its agreement with the
PostgreSQL labels are reported, together with the 800-predicate bound
quality study on a SQLite copy of the correlated relation.
"""
from __future__ import annotations

import collections
import random
import shutil
import tempfile
from pathlib import Path

from common import admission_metrics, db, dump, inv_path, load_bench, load_invariants
from invariantguard import sqlite_backend as sq
from invariantguard.bounds import BoundConfig, pred_upper
from invariantguard.compiler import compile_stmt
from invariantguard.verifier import VerifierConfig


def main():
    work = Path(tempfile.mkdtemp(prefix="igsqlite_"))
    tpl = {fx: sq.build_fixture(fx, work / f"{fx}.sqlite") for fx in db.FIXTURES}
    recs = [r for r in load_bench(evaluable_only=False)
            if all(s.split()[0].upper() == "DELETE" for s in r["action_sequence"])]
    out = {}
    for mode in ("paper", "extended"):
        vs = {}
        for fx in db.FIXTURES:
            p = work / f"{fx}_work_{mode}.sqlite"
            shutil.copy(tpl[fx], p)
            vs[fx] = sq.SQLiteVerifier(p, load_invariants(inv_path(fx)),
                                       VerifierConfig(static_mode=mode, shadow_all=True))
        rows, agree, static, shadow_free = [], collections.Counter(), 0, 0
        xc = collections.Counter()
        for r in recs:
            invs = load_invariants(inv_path(r["fixture"]))
            o = sq.oracle_label(tpl[r["fixture"]], invs, r["action_sequence"], work)
            pg = r["ground_truth"]["label"]
            agree[f"pg={pg}|sqlite={o['label']}"] += 1
            if o["label"] is None:
                continue
            d = vs[r["fixture"]].verify(r["action_sequence"])
            rows.append((o["label"], d.decision))
            static += sum(e.path in ("static", "frame") for e in d.evidence)
            for e in d.evidence:
                if e.inv in d.cross_check:
                    xc[f"{e.verdict}->{d.cross_check[e.inv]}"] += 1
            shadow_free += (not d.shadow_used) and (not d.empty_selection)
        m = admission_metrics(rows)
        m.update({"label_agreement": dict(agree), "static_pairs": static, "shadow_free_selected": shadow_free,
                  "records": len(recs),
                  "static_vs_shadow": dict(xc),
                  "prefix_bug_note": "before the Boolean type fix the extended analyzer admitted 7 of 79 unsafe records"})
        out[mode] = m
        print(mode, {k: m[k] for k in ("n", "containment", "decisiveness", "friction", "static_pairs")},
              dict(agree), flush=True)
        for v in vs.values():
            v.conn.close()

    # bound quality on SQLite (no optimizer row estimates are exposed, so
    # only the certified side is measured)
    from run_bounds import ROWS, predicates
    rng = random.Random(1729)
    p = work / "bq.sqlite"
    c = sq.connect(p)
    c.execute("CREATE TABLE ig_bound_quality (id INTEGER PRIMARY KEY, region INTEGER NOT NULL, city INTEGER NOT NULL, "
              "tier INTEGER NOT NULL, bucket INTEGER NOT NULL, status INTEGER NOT NULL)")
    data = []
    for i in range(1, ROWS + 1):
        region = rng.randrange(10)
        city = region * 10 + rng.randrange(3)
        tier = min(int(rng.paretovariate(1.2)), 40)
        data.append((i, region, city, tier, rng.randrange(50), rng.randrange(4)))
    c.execute("BEGIN")
    c.executemany("INSERT INTO ig_bound_quality VALUES (?,?,?,?,?,?)", data)
    c.execute("COMMIT")
    c.execute("CREATE TABLE ig_watermark (relname TEXT PRIMARY KEY, wm INTEGER)")
    c.execute("INSERT INTO ig_watermark VALUES ('ig_bound_quality', 1)")
    snap = sq.build_snapshot(c)
    under = 0
    for pr in predicates(1729, 800):
        st = compile_stmt(f"DELETE FROM ig_bound_quality WHERE {pr}")
        true = c.execute(f"SELECT COUNT(*) FROM ig_bound_quality WHERE {pr}").fetchone()[0]
        b = pred_upper(snap, "ig_bound_quality", st.pred, BoundConfig())
        under += b.value < true
    out["bound_quality"] = {"n": 800, "certified_underpredictions": under}
    print(out["bound_quality"], flush=True)
    c.close()
    dump("sqlite_portability.json", out)
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
