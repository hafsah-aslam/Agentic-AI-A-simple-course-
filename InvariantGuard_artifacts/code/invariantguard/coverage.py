"""Invariant-coverage tooling.

Friction is set by invariant coverage, not by the verifier: every action
escalated for an empty selection names relations the action reaches but no
invariant covers.  ``suggest_invariants`` turns that signal into concrete
bounded-delta declarations over the uncovered relations of the cascade
topology, which the operator reviews and accepts.  Each suggestion is

    R.coverage.delta :  COUNT(*) FROM R may decrease by at most theta_R per action

scoped over R and every relation from which a delete can reach R, so that
the selection rule (Eq. 9) picks it up for every action whose closure
touches R.  theta_R follows an explicit, data-independent policy:
``ceil(fraction * |R|)`` (at least ``minimum``).
"""
from __future__ import annotations

import math

from .bounds import reach_closure
from .invariants import Invariant

MODIFYING = ("cascade", "set null", "set default")


def uncovered_relations(catalog, invariants):
    covered = set()
    for inv in invariants:
        covered |= set(inv.tables)
    return sorted(t for t in catalog.tables if t not in covered and t != "agent_action_log")


def suggest_invariants(catalog, snapshot, invariants, fraction=0.10, minimum=1, severity=8.0):
    out = []
    for R in uncovered_relations(catalog, invariants):
        reachers = {T for T in catalog.tables if R in reach_closure(catalog, T, MODIFYING)}
        theta = max(minimum, math.ceil(fraction * snapshot.card.get(R, 0)))
        q = f"SELECT COUNT(*) FROM {R}"
        out.append(Invariant(
            id=f"{R}.coverage.delta", description=f"Suggested: at most {theta} {R} rows removed per action",
            tables=frozenset(reachers | {R}), columns=frozenset(),
            operations=frozenset({"delete", "truncate"}), relation="bounded-delta",
            post_query=q, pre_query=q,
            params={"max_decrease": theta, "max_increase": float("inf")}, severity=severity,
            scoping="action", origin="suggested"))
    return out


def to_yaml_dicts(invs):
    return [{"id": i.id, "description": i.description,
             "scope": {"tables": sorted(i.tables), "columns": ["*"], "operations": sorted(i.operations)},
             "pre_query": i.pre_query, "post_query": i.post_query, "relation": i.relation,
             "params": {"max_decrease": i.params["max_decrease"]}, "severity": i.severity}
            for i in invs]
