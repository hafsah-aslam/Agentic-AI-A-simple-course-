"""RQ1: certified bounds vs optimizer estimates.

1. 800 delete predicates on a purpose-built 20,000-row relation with a
   correlated column pair, a Pareto-skewed column and uniform columns.
2. Property test: 1,200 random predicates (nested conjunctions/disjunctions,
   IN lists, parentheses) over randomly generated relations.
3. Cascade property test: random foreign-key schemas (chains, diamonds,
   self-references, SET NULL) and random deletes; every per-relation
   affected-row count must stay below the cascade vector.  Merging paths by
   maximum (as an earlier revision did) is compared with summation.
4. Correlation and skew sweeps, and per-value frequency certificates.
"""
from __future__ import annotations

import random
import statistics

from common import db, dump, wilson
from invariantguard.bounds import BoundConfig, delete_vector, pred_upper
from invariantguard.compiler import compile_stmt, pred_form
from invariantguard.db import install_watermarks
from invariantguard.snapshot import build_snapshot

ROWS = 20_000
TABLE = "ig_bound_quality"


def fresh_db(name):
    db.drop_db(name)
    with db.connect() as c:
        c.execute(f'CREATE DATABASE "{name}"')
    return db.connect(name)


def build_relation(conn, seed=1729, rows=ROWS, rho=1.0, alpha=1.2):
    rng = random.Random(seed)
    conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
    conn.execute(f"""CREATE TABLE {TABLE} (id INTEGER PRIMARY KEY, region INTEGER NOT NULL,
        city INTEGER NOT NULL, tier INTEGER NOT NULL, bucket INTEGER NOT NULL, status INTEGER NOT NULL)""")
    data = []
    for i in range(1, rows + 1):
        region = rng.randrange(10)
        if rng.random() < rho:
            city = region * 10 + rng.randrange(3)          # city = g(region)
        else:
            city = rng.randrange(10) * 10 + rng.randrange(3)
        tier = min(int(rng.paretovariate(alpha)), 40)
        data.append((i, region, city, tier, rng.randrange(50), rng.randrange(4)))
    with conn.cursor() as cur:
        with cur.copy(f"COPY {TABLE} (id, region, city, tier, bucket, status) FROM STDIN") as cp:
            for row in data:
                cp.write_row(row)
    install_watermarks(conn)
    conn.execute("ANALYZE")


def predicates(seed, count, rows=ROWS):
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        region = rng.randrange(10)
        city = region * 10 + rng.randrange(3)
        tier = rng.randrange(1, 12)
        bucket = rng.randrange(50)
        status = rng.randrange(4)
        out.extend([
            f"region = {region} AND city = {city}",
            f"region = {region} AND city = {city} AND status = {status}",
            f"tier = {tier}",
            f"tier = 1 AND status = {status}",
            f"bucket = {bucket}",
            f"region = {region} OR tier = {tier}",
            f"region = {region} OR city = {city} AND status = {status}",
            f"(region = {region} OR bucket = {bucket}) AND status = {status}",
            f"id = {rng.randrange(1, rows + 1)}",
            f"tier IN ({tier}, {tier + 1}, {tier + 2})",
        ])
    return out[:count]


FAMILIES = ["correlated conjunction", "correlated 3-way conjunction", "skewed equality",
            "skewed conjunction", "uniform equality", "disjunction", "precedence mix",
            "parenthesized mix", "unique key", "IN list"]


def estimate(conn, sql):
    plan = conn.execute("EXPLAIN (FORMAT JSON) " + sql).fetchone()[0][0]["Plan"]
    while plan.get("Node Type") == "ModifyTable" and plan.get("Plans"):
        plan = plan["Plans"][0]
    return int(plan["Plan Rows"])


def bound_quality(conn, seed=1729, count=800, rows=ROWS, rho=1.0, alpha=1.2, keep_rows=True):
    build_relation(conn, seed, rows, rho, alpha)
    snap = build_snapshot(conn)
    valid = lambda t: True  # noqa: E731  (validity is exercised in the enforcement test)
    out = []
    for k, p in enumerate(predicates(seed, count, rows)):
        sql = f"DELETE FROM {TABLE} WHERE {p}"
        st = compile_stmt(sql)
        true = conn.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE {p}").fetchone()[0]
        b_mf = pred_upper(snap, TABLE, st.pred, BoundConfig(per_value=False))
        b_pv = pred_upper(snap, TABLE, st.pred, BoundConfig(per_value=True))
        est = estimate(conn, sql)
        out.append({"predicate": p, "family": FAMILIES[k % 10], "form": pred_form(st.pred),
                    "true": true, "estimate": est, "bound_mf": b_mf.value, "bound_pv": b_pv.value,
                    "certified": b_mf.certified and b_pv.certified, "rule": b_mf.rule})
    return out


def summarize(rows):
    n = len(rows)
    est_under = sum(r["estimate"] < r["true"] for r in rows)
    cert_under = sum(r["bound_mf"] < r["true"] for r in rows)
    pv_under = sum(r["bound_pv"] < r["true"] for r in rows)
    tight_mf = [r["bound_mf"] / r["true"] for r in rows if r["true"] > 0]
    tight_pv = [r["bound_pv"] / r["true"] for r in rows if r["true"] > 0]
    qerr = [max(r["estimate"], 1) / max(r["true"], 1) for r in rows]
    fam = {}
    for f in FAMILIES:
        rr = [r for r in rows if r["family"] == f]
        fam[f] = {"n": len(rr), "estimate_under": sum(r["estimate"] < r["true"] for r in rr),
                  "certified_under": sum(r["bound_mf"] < r["true"] for r in rr),
                  "tightness_mf_p50": statistics.median([r["bound_mf"] / r["true"] for r in rr if r["true"]] or [1]),
                  "tightness_pv_p50": statistics.median([r["bound_pv"] / r["true"] for r in rr if r["true"]] or [1])}
    admit_wrong = sum(r["estimate"] <= 100 < r["true"] for r in rows)
    return {
        "n": n, "estimate_underpredictions": est_under, "estimate_rate": est_under / n,
        "estimate_rate_ci": wilson(est_under, n),
        "certified_underpredictions": cert_under, "certified_pervalue_underpredictions": pv_under,
        "rule_of_three_upper": 3 / n, "grammar_coverage": sum(r["certified"] for r in rows) / n,
        "tightness_mf_p50": statistics.median(tight_mf), "tightness_mf_max": max(tight_mf),
        "tightness_pv_p50": statistics.median(tight_pv), "tightness_pv_max": max(tight_pv),
        "tightness_mf_p90": sorted(tight_mf)[int(0.9 * len(tight_mf))],
        "tightness_pv_p90": sorted(tight_pv)[int(0.9 * len(tight_pv))],
        "estimate_qerror_p50": statistics.median(qerr),
        "estimate_admits_over_100": admit_wrong,
        "families": fam,
    }


# ---------------------------------------------------------------------------
# Property test: random relations, random nested predicates
# ---------------------------------------------------------------------------

def random_pred(rng, cols, domains, depth=0):
    r = rng.random()
    if depth >= 3 or r < 0.45:
        c = rng.choice(cols)
        if rng.random() < 0.75:
            return f"{c} = {rng.randrange(domains[c] + 2)}"
        vals = sorted({rng.randrange(domains[c] + 2) for _ in range(rng.randrange(1, 5))})
        return f"{c} IN ({', '.join(map(str, vals))})"
    a = random_pred(rng, cols, domains, depth + 1)
    b = random_pred(rng, cols, domains, depth + 1)
    op = rng.choice(["AND", "OR"])
    if rng.random() < 0.5:
        return f"({a}) {op} ({b})"
    return f"{a} {op} {b}"


def property_test(conn, n_pred=1200, n_rel=24, seed=2027):
    rng = random.Random(seed)
    per_rel = n_pred // n_rel
    viol = {"mf": 0, "pv": 0}
    tested, forms = 0, {}
    for k in range(n_rel):
        t = f"prop_{k}"
        ncols = rng.randrange(2, 6)
        cols = [f"c{j}" for j in range(ncols)]
        domains = {c: rng.choice([2, 5, 10, 50, 300]) for c in cols}
        nrows = rng.choice([50, 500, 2000, 8000])
        conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.execute(f"CREATE TABLE {t} (id INTEGER PRIMARY KEY, " +
                     ", ".join(f"{c} INTEGER" for c in cols) + ")")
        kind = {c: rng.choice(["uniform", "pareto", "copy"]) for c in cols}
        with conn.cursor() as cur:
            with cur.copy(f"COPY {t} (id, {', '.join(cols)}) FROM STDIN") as cp:
                for i in range(nrows):
                    row, prev = [i], None
                    for c in cols:
                        if kind[c] == "pareto":
                            v = min(int(rng.paretovariate(1.1)) - 1, domains[c])
                        elif kind[c] == "copy" and prev is not None:
                            v = prev % (domains[c] + 1)
                        else:
                            v = rng.randrange(domains[c] + 1)
                        row.append(v)
                        prev = v
                    cp.write_row(row)
        install_watermarks(conn)
        snap = build_snapshot(conn, tables={t})
        for _ in range(per_rel):
            p = random_pred(rng, cols, domains)
            st = compile_stmt(f"DELETE FROM {t} WHERE {p}")
            true = conn.execute(f"SELECT COUNT(*) FROM {t} WHERE {p}").fetchone()[0]
            for key, pv in (("mf", False), ("pv", True)):
                b = pred_upper(snap, t, st.pred, BoundConfig(per_value=pv))
                assert b.certified
                if true > b.value:
                    viol[key] += 1
            forms[pred_form(st.pred)] = forms.get(pred_form(st.pred), 0) + 1
            tested += 1
        conn.execute(f"DROP TABLE {t}")
    return {"predicates": tested, "relations": n_rel, "violations_mf": viol["mf"],
            "violations_per_value": viol["pv"], "forms": forms}


# ---------------------------------------------------------------------------
# Cascade property test: random FK schemas, sum vs max path merge
# ---------------------------------------------------------------------------

def random_schema(conn, rng, k):
    n = rng.randrange(3, 7)
    rels = [f"s{k}_r{i}" for i in range(n)]
    edges = []
    for i in range(1, n):
        parents = rng.sample(range(i), rng.randrange(1, min(i, 3) + 1))
        for p in parents:
            edges.append((p, i, rng.choice(["CASCADE", "CASCADE", "SET NULL", "RESTRICT"])))
    if rng.random() < 0.4:
        j = rng.randrange(n)
        edges.append((j, j, rng.choice(["CASCADE", "SET NULL"])))
    sizes = [rng.choice([5, 20, 60]) for _ in range(n)]
    injective = rng.random() < 0.5   # one-to-one FK assignment makes bounds tight
    perms = {}
    for i, r in enumerate(rels):
        fkcols = [e for e in edges if e[1] == i]
        defs = ["id INTEGER PRIMARY KEY", "g INTEGER NOT NULL"]
        for (p, c, act) in fkcols:
            defs.append(f"f{p} INTEGER REFERENCES {rels[p]}(id) ON DELETE {act}")
        conn.execute(f"CREATE TABLE {r} ({', '.join(defs)})")
    for i, r in enumerate(rels):
        fkcols = [e for e in edges if e[1] == i]
        rows = []
        for rid in range(1, sizes[i] + 1):
            row = [rid, rng.randrange(4)]
            for (p, c, act) in fkcols:
                if p == i:
                    row.append(rng.randrange(1, rid) if rid > 1 and rng.random() < 0.7 else None)
                elif injective:
                    if (p, i) not in perms:
                        perms[(p, i)] = rng.sample(range(1, sizes[p] + 1), sizes[p])
                    seq = perms[(p, i)]
                    row.append(seq[rid - 1] if rid - 1 < len(seq) else None)
                else:
                    pid = int(rng.paretovariate(1.0)) if rng.random() < 0.5 else rng.randrange(1, sizes[p] + 1)
                    row.append(min(pid, sizes[p]) if rng.random() < 0.9 else None)
            rows.append(row)
        cols = ["id", "g"] + [f"f{p}" for (p, c, a) in fkcols]
        with conn.cursor() as cur:
            with cur.copy(f"COPY {r} ({', '.join(cols)}) FROM STDIN") as cp:
                for row in rows:
                    cp.write_row(row)
    install_watermarks(conn)
    return rels


def cascade_property(conn, schemas=60, deletes=20, seed=31):
    rng = random.Random(seed)
    res = {"cases": 0, "relation_checks": 0, "violations_sum": 0, "violations_max": 0,
           "rejected": 0, "diamond_schemas": 0}
    for k in range(schemas):
        rels = random_schema(conn, rng, k)
        snap = build_snapshot(conn, tables=set(rels))
        cat = snap.catalog
        if any(len({fk.parent for fk in cat.fks if fk.child == r}) > 1 for r in rels):
            res["diamond_schemas"] += 1
        for _ in range(deletes):
            root = rng.choice(rels[: max(1, len(rels) // 2)])
            pred = rng.choice([f"g = {rng.randrange(4)}", f"id = {rng.randrange(1, 30)}",
                               f"id IN ({rng.randrange(1, 10)}, {rng.randrange(10, 30)})",
                               f"g = {rng.randrange(4)} OR id = {rng.randrange(1, 30)}"])
            sql = f"DELETE FROM {root} WHERE {pred}"
            st = compile_stmt(sql)
            before = {r: dict(conn.execute(f"SELECT id, ({r})::text FROM {r}").fetchall()) for r in rels}
            conn.execute("BEGIN")
            try:
                conn.execute(sql)
            except Exception:
                conn.execute("ROLLBACK")
                res["rejected"] += 1
                continue
            after = {r: dict(conn.execute(f"SELECT id, ({r})::text FROM {r}").fetchall()) for r in rels}
            conn.execute("ROLLBACK")
            vs = {m: delete_vector(snap, st, BoundConfig(merge=m), lambda t: True) for m in ("sum", "max")}
            res["cases"] += 1
            for r in rels:
                changed = sum(1 for i, v in before[r].items() if after[r].get(i) != v)
                if changed == 0:
                    continue
                res["relation_checks"] += 1
                for m, v in vs.items():
                    b = v.modified.get(r)
                    if b is None or changed > b.value:
                        res[f"violations_{m}"] += 1
        for r in reversed(rels):
            conn.execute(f"DROP TABLE IF EXISTS {r} CASCADE")
    return res


def sweeps(conn):
    out = {"correlation": [], "skew": [], "scale": []}
    for rho in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
        s = summarize(bound_quality(conn, rho=rho, count=400))
        out["correlation"].append({"rho": rho, **{k: s[k] for k in (
            "estimate_rate", "certified_underpredictions", "tightness_mf_p50", "tightness_pv_p50")}})
        print("rho", rho, s["estimate_rate"], flush=True)
    for alpha in (0.8, 1.2, 2.0, 3.0):
        s = summarize(bound_quality(conn, alpha=alpha, count=400))
        out["skew"].append({"alpha": alpha, **{k: s[k] for k in (
            "estimate_rate", "certified_underpredictions", "tightness_mf_p50", "tightness_mf_max",
            "tightness_pv_p50", "tightness_pv_max")}})
        print("alpha", alpha, s["tightness_mf_max"], s["tightness_pv_max"], flush=True)
    for rows in (20_000, 100_000, 500_000):
        s = summarize(bound_quality(conn, rows=rows, count=400))
        out["scale"].append({"rows": rows, **{k: s[k] for k in (
            "estimate_rate", "certified_underpredictions", "tightness_mf_p50", "tightness_pv_p50")}})
        print("rows", rows, s["estimate_rate"], flush=True)
    return out


def enforcement_test(conn):
    """The certification gate: a write after the snapshot invalidates it."""
    build_relation(conn, rows=2000)
    snap = build_snapshot(conn)
    from invariantguard.snapshot import watermark_reader
    rd = watermark_reader(conn)
    before = snap.valid(TABLE, rd)
    conn.execute(f"DELETE FROM {TABLE} WHERE id = 1")
    after = snap.valid(TABLE, rd)
    missing = snap.valid("no_such_relation", rd)
    no_reader = snap.valid(TABLE, None)
    st = compile_stmt(f"DELETE FROM {TABLE} WHERE tier = 1")
    v = delete_vector(snap, st, BoundConfig(), lambda t: snap.valid(t, rd))
    return {"valid_before_write": before, "valid_after_write": after,
            "missing_watermark_valid": missing, "missing_reader_valid": no_reader,
            "bound_certified_after_write": v.deleted[TABLE].certified}


def rerun_cascade():
    import json
    conn = fresh_db("ig_bounds_c")
    casc = cascade_property(conn, schemas=120)
    print(casc, flush=True)
    p = db.ROOT / "results" / "bound_quality.json"
    d = json.loads(p.read_text())
    d["cascade_property"] = casc
    p.write_text(json.dumps(d, indent=1, sort_keys=True, default=str) + "\n")
    conn.close()
    db.drop_db("ig_bounds_c")


def main():
    conn = fresh_db("ig_bounds")
    rows = bound_quality(conn)
    summary = summarize(rows)
    print({k: v for k, v in summary.items() if k != "families"}, flush=True)
    prop = property_test(conn)
    print(prop, flush=True)
    casc = cascade_property(conn, schemas=120)
    print(casc, flush=True)
    enf = enforcement_test(conn)
    print(enf, flush=True)
    sw = sweeps(conn)
    dump("bound_quality.json", {"summary": summary, "property_test": prop, "cascade_property": casc,
                                "enforcement": enf, "sweeps": sw})
    import json
    with open(db.ROOT / "results" / "bound_quality_rows.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    conn.close()
    db.drop_db("ig_bounds")


if __name__ == "__main__":
    import sys
    rerun_cascade() if "--cascade" in sys.argv else main()
