"""Independent commit oracle (Section 3.7).

Deliberately shares no decision or evidence code with the verifier: it reads
the invariant YAML itself, evaluates *every* invariant (not a selection),
commits the action on a disposable clone of the fixture, re-evaluates on the
final state, and discards the clone.

Two observation modes are provided:

* ``final``     - the released oracle: compares the initial and final states
                  only (statement-scoped deltas are judged on S0 -> Sm);
* ``boundary``  - the boundary-matched oracle: commits statement by statement
                  and evaluates every invariant at every statement boundary,
                  so statement-scoped invariants are judged exactly as the
                  shadow executor judges them.
"""
from __future__ import annotations

from pathlib import Path

import psycopg
import yaml

from . import db


def _load(path):
    return yaml.safe_load(Path(path).read_text())["invariants"]


def _scalar(conn, sql):
    try:
        with conn.transaction():
            return True, conn.execute(sql).fetchone()[0]
    except Exception:
        return False, None


def _delta_ok(d, pre, post):
    p = d.get("params", {})
    dec = p.get("max_decrease", float("inf"))
    inc = p.get("max_increase", float("inf"))
    return (float(pre) - float(post)) <= dec and (float(post) - float(pre)) <= inc


def _point_ok(d, post):
    p = d.get("params", {})
    exp = p.get("expected", True)
    return post == exp


def oracle_label(template: str, invariant_file, statements, mode="final", scoping=None):
    """Return dict(status, label, violated, per_invariant, error)."""
    defs = _load(invariant_file)
    if scoping:
        for d in defs:
            if d["relation"] == "bounded-delta":
                d["scoping"] = scoping
    with db.clone(template) as name:
        conn = psycopg.connect(f"{db.PG} dbname={name}", autocommit=True)
        try:
            tables = [r[0] for r in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'")]
            counts0 = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
            vals0 = {}
            for d in defs:
                q = d.get("pre_query") or d["post_query"]
                vals0[d["id"]] = _scalar(conn, q)
            per = {d["id"]: True for d in defs}
            err = None
            if mode == "final":
                try:
                    with conn.transaction():
                        for s in statements:
                            conn.execute(s)
                except Exception as e:
                    err = f"{type(e).__name__}: {str(e).splitlines()[0]}"
            else:
                # boundary-matched: the action is one unit; if any statement
                # fails the whole action is rejected, so run it in a
                # transaction but observe every boundary inside it.
                try:
                    with conn.transaction():
                        prev = dict(vals0)
                        for s in statements:
                            conn.execute(s)
                            cur = {}
                            for d in defs:
                                if d["relation"] == "bounded-delta" and d.get("scoping", "action") == "statement":
                                    ok, v = _scalar(conn, d["post_query"])
                                    cur[d["id"]] = (ok, v)
                                    okp, vp = prev[d["id"]]
                                    if ok and okp and v is not None and vp is not None:
                                        if not _delta_ok(d, vp, v):
                                            per[d["id"]] = False
                            prev.update(cur)
                except Exception as e:
                    err = f"{type(e).__name__}: {str(e).splitlines()[0]}"
            if err is not None:
                return {"status": "unresolved", "label": None, "violated": [], "error": err,
                        "per_invariant": {}}
            unevaluable = []
            values = {}
            tables1 = {r[0] for r in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'")}
            rows_changed = 0
            for t, n0 in counts0.items():
                if t not in tables1:
                    rows_changed += max(n0, 1)
                else:
                    rows_changed += abs(n0 - conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0])
            for d in defs:
                if mode == "boundary" and d["relation"] == "bounded-delta" and d.get("scoping", "action") == "statement":
                    continue
                ok, post = _scalar(conn, d["post_query"])
                values[d["id"]] = (vals0[d["id"]][1], post if ok else "<error>")
                if not ok or post is None:
                    # an invariant over a dropped relation cannot hold
                    per[d["id"]] = False if vals0[d["id"]][0] else True
                    unevaluable.append(d["id"])
                    continue
                if d["relation"] == "bounded-delta":
                    ok0, pre = vals0[d["id"]]
                    per[d["id"]] = _delta_ok(d, pre, post) if ok0 else True
                else:
                    per[d["id"]] = _point_ok(d, post)
            violated = sorted(k for k, v in per.items() if not v)
            sev = max([d.get("severity", 0) for d in defs if d["id"] in violated], default=0)
            return {"status": "executed", "label": "unsafe" if violated else "safe",
                    "violated": violated, "error": None, "per_invariant": per,
                    "unevaluable": unevaluable, "severity": sev,
                    "values": values, "rows_changed": rows_changed}
        finally:
            conn.close()
