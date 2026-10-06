"""Shared helpers for the experiment scripts."""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from invariantguard import db  # noqa: E402
from invariantguard.invariants import load_invariants  # noqa: E402
from invariantguard.snapshot import build_snapshot  # noqa: E402
from invariantguard.verifier import Verifier, VerifierConfig  # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
BENCH = db.DATA / "ig_bench" / "ig_bench_v3.jsonl"


def load_bench(evaluable_only=True, path=BENCH):
    rs = [json.loads(line) for line in open(path)]
    for r in rs:
        r["fixture"] = r["fixture_ref"].split("/")[0]
    if evaluable_only:
        rs = [r for r in rs if r["ground_truth"]["label"]]
    return rs


def inv_path(fixture):
    return db.DATA / "invariants" / db.INVARIANT_FILES[fixture]


def work_db(fixture, suffix="w"):
    """A disposable working copy of the fixture (never committed to by the verifier)."""
    name = f"igwork_{suffix}_{fixture}"
    db.drop_db(name)
    with db.connect() as c:
        c.execute(f'CREATE DATABASE "{name}" TEMPLATE "{db.template_name(fixture)}"')
    return name


def make_verifiers(cfg_factory, invariant_loader=None, suffix="w"):
    vs = {}
    for fx in db.FIXTURES:
        name = work_db(fx, suffix)
        conn = db.connect(name)
        snap = build_snapshot(conn)
        invs = invariant_loader(fx) if invariant_loader else load_invariants(inv_path(fx))
        vs[fx] = Verifier(name, invs, snap, cfg_factory(), conn)
    return vs


def close_verifiers(vs):
    for v in vs.values():
        try:
            v.conn.close()
        except Exception:
            pass
        db.drop_db(v.dbname)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def admission_metrics(rows):
    """rows: list of (label, decision)."""
    U = [d for l, d in rows if l == "unsafe"]
    F = [d for l, d in rows if l == "safe"]
    cont = sum(d != "allow" for d in U)
    dec = sum(d == "block" for d in U)
    fric = sum(d == "escalate" for d in F)
    safe_blocked = sum(d == "block" for d in F)
    blocks = sum(d == "block" for _, d in rows)
    P = dec / blocks if blocks else 0.0
    R = dec / len(U) if U else 0.0
    f1 = 2 * P * R / (P + R) if P + R else 0.0
    return {
        "n": len(rows), "unsafe": len(U), "safe": len(F),
        "contained": cont, "blocked": dec, "escalated_unsafe": sum(d == "escalate" for d in U),
        "admitted_unsafe": sum(d == "allow" for d in U),
        "safe_escalated": fric, "safe_blocked": safe_blocked, "safe_allowed": sum(d == "allow" for d in F),
        "containment": cont / len(U) if U else 0.0,
        "containment_ci": wilson(cont, len(U)),
        "decisiveness": dec / len(U) if U else 0.0,
        "decisiveness_ci": wilson(dec, len(U)),
        "friction": fric / len(F) if F else 0.0,
        "friction_ci": wilson(fric, len(F)),
        "precision": P, "recall": R, "f1": f1,
    }


def bootstrap_f1(rows, B=2000, seed=7):
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        s = [rows[rng.randrange(len(rows))] for _ in rows]
        vals.append(admission_metrics(s)["f1"])
    vals.sort()
    return (vals[int(0.025 * B)], vals[int(0.975 * B) - 1])


def dump(name, obj):
    p = RESULTS / name
    p.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")
    return p
