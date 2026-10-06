"""Baselines that decide from the statement text or from optimizer estimates.

* NoVerification     - admits every action.
* KeywordGuardrail   - blocks any destructive keyword (DROP/TRUNCATE/DELETE/ALTER).
* ABAC               - attribute-based access control (NIST SP 800-162 style):
                       subject = agent, object attributes = table sensitivity
                       (protected iff named by an invariant), action attributes =
                       operation and predicate shape.
* EstimateAdmission  - effect-size admission as in query governors / Bytebase:
                       the optimizer's row estimate for the target relation must
                       not exceed the declared limit (cascades are not seen).
"""
from __future__ import annotations

import re

from .compiler import PEq, PIn, compile_action

DESTRUCTIVE = re.compile(r"\b(DROP|TRUNCATE|DELETE|ALTER)\b", re.I)


class NoVerification:
    name = "No verification"

    def decide(self, statements):
        return "allow"


class KeywordGuardrail:
    name = "Keyword guardrail"

    def decide(self, statements):
        return "block" if any(DESTRUCTIVE.search(s) for s in statements) else "allow"


class ABAC:
    name = "Access control (ABAC)"

    def __init__(self, invariants, catalog):
        self.protected = set().union(*[i.tables for i in invariants]) if invariants else set()
        self.keys = {(t, c) for (t, c) in catalog.unique}

    def decide(self, statements):
        for st in compile_action(statements):
            if st.op in ("drop_table", "truncate", "alter_table"):
                return "block"
            if st.op in ("delete", "update"):
                keyed = isinstance(st.pred, (PEq, PIn)) and (st.table, st.pred.col) in self.keys
                if st.table in self.protected and not keyed:
                    return "block"
        return "allow"


class EstimateAdmission:
    name = "Estimate admission"

    def __init__(self, invariants, conn, default_limit=100):
        self.conn = conn
        self.limits = {}
        for i in invariants:
            r = i.metric_relation
            if r:
                self.limits[r] = min(self.limits.get(r, default_limit), i.theta_down)
        self.default = default_limit

    def estimate(self, st):
        if st.op in ("truncate", "drop_table"):
            return sum(self.conn.execute(
                "SELECT GREATEST(reltuples,0)::bigint FROM pg_class WHERE relname=%s", (t,)).fetchone()[0]
                for t in st.tables)
        plan = self.conn.execute("EXPLAIN (FORMAT JSON) " + st.sql).fetchone()[0][0]["Plan"]
        while plan.get("Node Type") == "ModifyTable" and plan.get("Plans"):
            plan = plan["Plans"][0]
        return int(plan.get("Plan Rows", 0))

    def decide(self, statements):
        for st in compile_action(statements):
            if not st.state_changing:
                continue
            est = self.estimate(st)
            if est > self.limits.get(st.tables[0], self.default):
                return "block"
        return "allow"
