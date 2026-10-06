"""Certified bound rules R1-R8' (Section 3.3) and certified lower bounds.

A bound is B = <u, c, pi>: a value, a certification flag that carries
admission semantics, and the producing rule.  Every rule below consumes only
the certificate snapshot.  Uncertified bounds (unsupported grammar, invalid
snapshot, missing statistic, unmodelled trigger) are never used as evidence.
"""
from __future__ import annotations

from dataclasses import dataclass

from .compiler import PAnd, PEq, PIn, POr, PTrue, Pred, Stmt
from .snapshot import Snapshot, canonical


@dataclass(frozen=True)
class Bound:
    value: int
    certified: bool
    rule: str


@dataclass
class BoundConfig:
    per_value: bool = True        # per-value frequency certificates (R3*, R5*)
    d_max: int = 3                # cascade depth cap
    merge: str = "sum"            # how multiple cascade paths merge: "sum" (sound) or "max"
    provider: str = "certified"   # certified | estimate (optimizer, flagged uncertified)
    estimate_certified: bool = False   # a deliberately unsafe provider (for the defect study)


def _freq_bound(snap: Snapshot, T: str, c: str, v, cfg: BoundConfig) -> tuple[int, str] | None:
    if (T, c) not in snap.mf:
        return None
    if (T, c) in snap.catalog.unique:
        return 1, "R2"
    if cfg.per_value:
        cert = snap.freq.get((T, c))
        key = canonical(v, snap.catalog.col_types.get((T, c)))
        if cert is not None and key is not None:
            if key in cert.exact:
                return cert.exact[key], "R3*"
            return cert.rest_cap, "R3*"
    return snap.mf[(T, c)], "R3"


def pred_upper(snap: Snapshot, T: str, p: Pred, cfg: BoundConfig, valid: bool = True) -> Bound:
    """Upper bound on |{r in T : p(r)}| under snapshot ``snap``."""
    if not valid or T not in snap.card:
        return Bound(snap.card.get(T, 0), False, "invalid-snapshot")
    n = snap.card[T]
    if isinstance(p, PTrue):
        return Bound(n, True, "R1")
    if isinstance(p, PEq):
        r = _freq_bound(snap, T, p.col, p.val, cfg)
        if r is None:
            return Bound(n, False, "no-statistic")
        return Bound(min(n, r[0]), True, r[1])
    if isinstance(p, PIn):
        vals = set(p.vals)
        if (T, p.col) in snap.catalog.unique:
            return Bound(min(n, len(vals)), True, "R4")
        tot, rule = 0, "R5"
        for v in vals:
            r = _freq_bound(snap, T, p.col, v, cfg)
            if r is None:
                return Bound(n, False, "no-statistic")
            tot += r[0]
            rule = "R5*" if r[1] == "R3*" else rule
        return Bound(min(n, tot), True, rule)
    if isinstance(p, PAnd):
        a, b = pred_upper(snap, T, p.left, cfg), pred_upper(snap, T, p.right, cfg)
        # R6: a conjunction's matches lie in each operand's matches.  A
        # certified operand alone already bounds the conjunction.
        cands = [x for x in (a, b) if x.certified]
        if not cands:
            return Bound(n, False, "unsupported")
        best = min(cands, key=lambda x: x.value)
        return Bound(best.value, True, "R6")
    if isinstance(p, POr):
        a, b = pred_upper(snap, T, p.left, cfg), pred_upper(snap, T, p.right, cfg)
        if not (a.certified and b.certified):
            return Bound(n, False, "unsupported")
        return Bound(min(n, a.value + b.value), True, "R7")
    return Bound(n, False, "unsupported")


def pred_lower(snap: Snapshot, T: str, p: Pred) -> int:
    """Certified lower bound on matching rows (exact for TRUE, else 0)."""
    if isinstance(p, PTrue):
        return snap.card.get(T, 0)
    return 0


@dataclass
class Vector:
    """Per-relation certified bounds for one statement."""
    deleted: dict      # relation -> Bound on rows deleted
    modified: dict     # relation -> Bound on rows deleted or updated (A(S,C,a))
    lower_deleted: dict  # relation -> certified lower bound on rows deleted

    def certified(self) -> bool:
        return all(b.certified for b in self.deleted.values()) and all(
            b.certified for b in self.modified.values())


def _merge(old: Bound | None, new: Bound, cap: int, how: str) -> Bound:
    if old is None:
        return new
    if how == "max":
        v = max(old.value, new.value)
    else:
        v = min(cap, old.value + new.value)
    return Bound(v, old.certified and new.certified, "R8'")


def delete_vector(snap: Snapshot, stmt: Stmt, cfg: BoundConfig, valid) -> Vector:
    """R8': propagate the root bound through modifying referential actions.

    ``valid`` is a callable table -> bool implementing Definition 2.  Paths
    are enumerated up to depth d_max; a relation reached beyond the cap (and
    everything reachable from it) receives |C|.  Multiple paths reaching the
    same child are merged by *summation*, capped at |C|: the affected child
    rows are the union of the rows reached through each path, and a union is
    bounded by the sum of its parts, not by their maximum.
    """
    cat = snap.catalog
    T = stmt.table
    root = pred_upper(snap, T, stmt.pred, cfg, valid(T))
    if T in cat.unmodelled_triggers:
        root = Bound(root.value, False, "unmodelled-trigger")
    deleted = {T: root}
    modified = {T: root}
    lower = {T: pred_lower(snap, T, stmt.pred) if valid(T) else 0}
    capped: set = set()

    def fk_mf(C, cols):
        fs = [snap.mf.get((C, c)) for c in cols]
        return None if any(x is None for x in fs) else min(fs)

    def visit(P, pb, d, plow):
        for fk in cat.children(P):
            C = fk.child
            capC = snap.card.get(C, 0)
            if d + 1 > cfg.d_max:
                capped.update(reach_closure(cat, C, ("cascade", "set null", "set default")))
                continue
            ok = valid(C) and pb.certified and C not in cat.unmodelled_triggers
            f = fk_mf(C, fk.child_cols)
            b = Bound(capC, False, "no-statistic") if f is None else Bound(min(capC, pb.value * f), ok, "R8'")
            modified[C] = _merge(modified.get(C), b, capC, cfg.merge)
            if fk.on_delete == "cascade":
                deleted[C] = _merge(deleted.get(C), b, capC, cfg.merge)
                low = 0
                if plow > 0 and plow == snap.card.get(P) and len(fk.child_cols) == 1:
                    low = snap.nonnull.get((C, fk.child_cols[0]), 0)
                lower[C] = max(lower.get(C, 0), low)
                visit(C, b, d + 1, low)

    visit(T, root, 0, lower[T])
    for R in capped:
        capR = snap.card.get(R, 0)
        bb = Bound(capR, valid(R) and R in snap.card and R not in cat.unmodelled_triggers, "R8'-cap")
        modified[R] = bb
        deleted[R] = bb
    return Vector(deleted, modified, lower)


def truncate_vector(snap: Snapshot, stmt: Stmt, valid) -> Vector:
    cat = snap.catalog
    rels = set(stmt.tables)
    if stmt.cascade:
        for t in list(stmt.tables):
            rels |= reach_closure(cat, t, None)
    deleted, lower = {}, {}
    for R in rels:
        ok = valid(R) and R in snap.card and R not in cat.unmodelled_triggers
        deleted[R] = Bound(snap.card.get(R, 0), ok, "R1-truncate")
        lower[R] = snap.card.get(R, 0) if ok else 0
    return Vector(deleted, dict(deleted), lower)


def reach_closure(cat, table: str, actions) -> set:
    """Relations reachable from ``table`` through referencing FKs.

    ``actions`` restricts the referential actions followed (None = any FK,
    i.e. the reference closure used for TRUNCATE ... CASCADE and DROP).
    """
    seen, stack = {table}, [table]
    while stack:
        t = stack.pop()
        for fk in cat.fks:
            if fk.parent == t and (actions is None or fk.on_delete in actions):
                if fk.child not in seen:
                    seen.add(fk.child)
                    stack.append(fk.child)
    return seen
