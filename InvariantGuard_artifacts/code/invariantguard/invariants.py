"""Declared invariants I = <sigma, q_pre, q_post, rho, theta, w> (Eq. 1-4)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

import yaml

from .compiler import query_read_set

_COUNT_RE = re.compile(r"^\s*SELECT\s+COUNT\(\*\)\s+FROM\s+\"?(\w+)\"?\s*$", re.I)


@dataclass(frozen=True)
class Invariant:
    id: str
    description: str
    tables: frozenset
    columns: frozenset            # empty = wildcard ("*")
    operations: frozenset
    relation: str                 # point | structural | bounded-delta
    post_query: str
    pre_query: str | None = None
    params: dict = field(default_factory=dict, hash=False, compare=False)
    severity: float = 5.0
    scoping: str = "action"       # action | statement  (bounded deltas, Eq. 3/4)
    origin: str = "declared"      # declared | suggested (coverage tooling)

    @property
    def is_delta(self) -> bool:
        return self.relation == "bounded-delta"

    @property
    def metric_relation(self) -> str | None:
        """Relation R when the delta metric is exactly COUNT(*) FROM R."""
        if not self.is_delta or not self.pre_query:
            return None
        if self.pre_query.strip() != self.post_query.strip():
            return None
        m = _COUNT_RE.match(self.pre_query)
        return m.group(1) if m else None

    @property
    def theta_down(self) -> float:
        return float(self.params.get("max_decrease", float("inf")))

    @property
    def theta_up(self) -> float:
        return float(self.params.get("max_increase", float("inf")))

    def read_set(self):
        rels, cols, cat = query_read_set(self.post_query)
        if self.pre_query:
            r2, c2, k2 = query_read_set(self.pre_query)
            rels |= r2
            cols |= c2
            cat = cat or k2
        return rels, cols, cat

    def holds(self, pre, post) -> bool:
        """rho(q_pre(S), q_post(S'), theta)."""
        if self.is_delta:
            pre, post = float(pre), float(post)
            return (pre - post) <= self.theta_down and (post - pre) <= self.theta_up
        expected = self.params.get("expected", True)
        op = self.params.get("operator", "eq")
        if op == "eq":
            return post == expected
        if op == "le":
            return post <= expected
        if op == "ge":
            return post >= expected
        raise ValueError(op)


def load_invariants(path: str | Path, scoping: str | None = None) -> list[Invariant]:
    doc = yaml.safe_load(Path(path).read_text())
    out = []
    for d in doc["invariants"]:
        sc = d["scope"]
        cols = frozenset(c for c in sc.get("columns", []) if c != "*")
        inv = Invariant(
            id=d["id"], description=d.get("description", ""),
            tables=frozenset(sc["tables"]), columns=cols,
            operations=frozenset(sc.get("operations", [])),
            relation=d["relation"], post_query=d["post_query"], pre_query=d.get("pre_query"),
            params=dict(d.get("params", {})), severity=float(d.get("severity", 5)),
            scoping=d.get("scoping", "action"))
        if scoping is not None and inv.is_delta:
            inv = replace(inv, scoping=scoping)
        out.append(inv)
    return out
