"""The verification cascade (Sections 3.3-3.5): selection, static
certification, shadow verification, evidence aggregation and admission."""
from __future__ import annotations

import time
from dataclasses import dataclass, field, replace

import psycopg

from .bounds import Bound, BoundConfig, Vector, delete_vector, reach_closure, truncate_vector
from .compiler import Stmt, compile_action, pred_supported
from .invariants import Invariant
from .snapshot import Snapshot, watermark_reader

MODIFYING = ("cascade", "set null", "set default")
STRUCTURAL_OPS = {"drop_table", "alter_table"}


@dataclass
class VerifierConfig:
    cascade_closure: bool = True        # Eq. 8 closure in selection (False: named relation only)
    per_relation_scope: bool = True     # Eq. 12 (False: cross-relation bound use, defect)
    vacuity: bool = True                # Eq. 10 (False: empty selection admits, defect)
    static_mode: str = "extended"       # off | paper | extended
    frame_rule: bool = True             # extended only
    lower_bounds: bool = True           # extended only: certified static violations
    tau_block: float = 70.0
    bounds: BoundConfig = field(default_factory=BoundConfig)
    full_selection_closure: bool = True  # selection closure without depth cap
    shadow_all: bool = False            # also run shadow for statically decided pairs (cross-check)


@dataclass
class Evidence:
    inv: str
    verdict: str            # satisfied | violated | undecidable
    path: str               # static | frame | shadow
    severity: float
    reason: str = ""
    static_attempt: str = ""   # first failing certification condition, or "cleared"


@dataclass
class Decision:
    decision: str           # allow | escalate | block
    overall: str            # safe | unsafe | unresolved
    risk: float
    selected: list
    evidence: list
    empty_selection: bool
    shadow_used: bool
    latency_ms: float
    static_ms: float = 0.0
    shadow_ms: float = 0.0
    action_error: str | None = None
    cross_check: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Selection (Eq. 8-10)
# ---------------------------------------------------------------------------

def statement_closure(cat, st: Stmt, cfg: VerifierConfig) -> set:
    if not cfg.cascade_closure:
        return set(st.tables)
    if st.op == "delete":
        return reach_closure(cat, st.table, MODIFYING)
    if st.op == "truncate":
        out = set(st.tables)
        if st.cascade:
            for t in st.tables:
                out |= reach_closure(cat, t, None)
        return out
    if st.op in ("drop_table", "alter_table"):
        out = set(st.tables)
        for t in st.tables:
            out |= reach_closure(cat, t, None)
        return out
    if st.op == "update":
        out, work = {st.table}, [(st.table, set(st.columns))]
        while work:
            t, cols = work.pop()
            for fk in cat.fks:
                if fk.parent == t and fk.on_update in MODIFYING and (not cols or cols & set(fk.parent_cols)):
                    if fk.child not in out:
                        out.add(fk.child)
                        work.append((fk.child, set(fk.child_cols)))
        return out
    if st.op == "insert":
        return {st.table}
    return set(st.tables)


def select_invariants(cat, stmts: list[Stmt], invs: list[Invariant], cfg: VerifierConfig):
    cl, ops, cols = set(), set(), set()
    for st in stmts:
        if st.state_changing:
            cl |= statement_closure(cat, st, cfg)
            ops.add(st.op)
            cols |= set(st.columns)
    selected = []
    for inv in invs:
        if not (cl & inv.tables):
            continue
        if ops & STRUCTURAL_OPS:
            selected.append(inv)
            continue
        if not (ops & inv.operations):
            continue
        if inv.columns and cols and not (inv.columns & cols):
            continue
        selected.append(inv)
    return selected, cl


# ---------------------------------------------------------------------------
# Static certification (Section 3.3, Eq. 11-12, Theorem 3.1, Eq. 25)
# ---------------------------------------------------------------------------

class StaticAnalyzer:
    def __init__(self, snap: Snapshot, conn, cfg: VerifierConfig, estimate=None, reader=None,
                 read_scalar=None):
        self.snap = snap
        self.cfg = cfg
        self.reader = reader or (watermark_reader(conn) if conn is not None else None)
        self.read_scalar = read_scalar
        self.conn = conn
        self.estimate = estimate     # callable(stmt) -> int, for the estimate provider
        self._valid_cache: dict = {}

    def valid(self, table: str) -> bool:
        if table not in self._valid_cache:
            self._valid_cache[table] = self.snap.valid(table, self.reader)
        return self._valid_cache[table]

    def reset(self):
        self._valid_cache = {}

    def vector(self, st: Stmt) -> Vector | None:
        if st.op == "delete":
            v = delete_vector(self.snap, st, self.cfg.bounds, self.valid)
        elif st.op == "truncate":
            v = truncate_vector(self.snap, st, self.valid)
        else:
            return None
        if self.cfg.bounds.provider == "estimate" and st.op == "delete" and self.estimate:
            # Replace the root bound by the optimizer estimate.  It is flagged
            # uncertified unless the deliberately unsafe variant is requested.
            est = self.estimate(st)
            flag = self.cfg.bounds.estimate_certified
            v.deleted[st.table] = Bound(est, flag, "estimate")
            v.modified[st.table] = Bound(est, flag, "estimate")
            for R in list(v.deleted):
                if R != st.table:
                    v.deleted[R] = Bound(v.deleted[R].value, flag and v.deleted[R].certified, "estimate-cascade")
        return v

    # -- extended static path -------------------------------------------
    def attempt(self, inv: Invariant, stmts: list[Stmt], vectors) -> tuple[str | None, str]:
        """Return (verdict or None, first failing condition / rule)."""
        mode = self.cfg.static_mode
        if mode == "off":
            return None, "static-off"
        if mode == "paper":
            return self._paper(inv, stmts, vectors)
        return self._extended(inv, stmts, vectors)

    def _paper(self, inv, stmts, vectors):
        if not inv.is_delta or any(v is None for v in vectors):
            return None, "not-static-class"
        if any(not pred_supported(st.pred) for st in stmts if st.op == "delete"):
            return None, "unsupported-grammar"
        for v in vectors:
            for R in inv.tables:
                if R not in v.deleted:
                    return None, "scope-containment"
        if inv.scoping == "action":
            return None, "action-scoped"
        for v in vectors:
            for R in inv.tables:
                if not v.deleted[R].certified:
                    return None, "uncertified"
        root = stmts[0].table
        for v in vectors:
            for R in inv.tables:
                b = v.deleted[R] if self.cfg.per_relation_scope else v.deleted.get(root, v.deleted[R])
                if b.value > inv.theta_down:
                    return None, "threshold"
        return "satisfied", "cleared"

    def _extended(self, inv, stmts, vectors):
        cat = self.snap.catalog
        if any(v is None for v in vectors):
            return None, "op-needs-shadow"
        closure = set()
        for v in vectors:
            closure |= set(v.modified)
        if closure & cat.unmodelled_triggers:
            return None, "unmodelled-trigger"
        for v in vectors:
            if not v.certified():
                return None, "uncertified"
        # Frame rule: the invariant reads nothing the action may modify.
        rels, cols, reads_catalog = inv.read_set()
        touched = {R for v in vectors for R, b in v.modified.items() if b.value > 0}
        if self.cfg.frame_rule and not (rels & touched) and not reads_catalog and rels:
            if inv.is_delta:
                return "satisfied", "frame"
            v = self._read_now(inv)
            return (v, "frame") if v else (None, "frame-read-failed")
        if not inv.is_delta:
            return None, "point/structural"
        Rm = inv.metric_relation
        if Rm is None:
            return None, "non-count-metric"
        if Rm not in self.snap.card or not self.valid(Rm):
            return None, "uncertified"
        ups = [v.deleted[Rm].value if Rm in v.deleted else 0 for v in vectors]
        # certified lower bound (first statement only; deletes only)
        if self.cfg.lower_bounds:
            low = vectors[0].lower_deleted.get(Rm, 0)
            if low > inv.theta_down:
                return "violated", "lower-bound"
        if inv.scoping == "statement":
            if all(u <= inv.theta_down for u in ups):
                return "satisfied", "cleared"
            return None, "threshold"
        total = min(sum(ups), self.snap.card[Rm])       # Eq. 25
        if total <= inv.theta_down:
            return "satisfied", "cleared-sum" if len(ups) > 1 else "cleared"
        return None, "threshold"

    def _read_now(self, inv) -> str:
        if self.read_scalar is not None:
            ok, post = self.read_scalar(inv.post_query)
            if not ok:
                return None
            return "satisfied" if inv.holds(None, post) else "violated"
        try:
            with self.conn.transaction():
                post = self.conn.execute(inv.post_query).fetchone()[0]
            return "satisfied" if inv.holds(None, post) else "violated"
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Shadow verification (Section 3.4)
# ---------------------------------------------------------------------------

def _q(conn, sql):
    conn.execute("SAVEPOINT igq")
    try:
        v = conn.execute(sql).fetchone()[0]
        conn.execute("RELEASE SAVEPOINT igq")
        return True, v
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT igq")
        return False, None


def shadow_verify(conn, statements: list[str], invs: list[Invariant], isolation="SERIALIZABLE",
                  commit_if=None, begin_sql=None):
    """Execute the action in an isolated transaction, evaluate invariants,
    and roll back unconditionally (unless ``commit_if`` is given, which is
    used by the serializable-through-commit discipline)."""
    out: dict = {}
    err = None
    committed = False
    stmt_scoped = [i for i in invs if i.is_delta and i.scoping == "statement"]
    whole = [i for i in invs if i not in stmt_scoped]
    conn.execute(begin_sql or f"BEGIN ISOLATION LEVEL {isolation}")
    try:
        pre = {}
        for inv in whole:
            if inv.is_delta:
                pre[inv.id] = _q(conn, inv.pre_query)
        step_bad = {i.id: False for i in stmt_scoped}
        step_err = {i.id: False for i in stmt_scoped}
        for sql in statements:
            sp = {}
            for inv in stmt_scoped:
                sp[inv.id] = _q(conn, inv.pre_query)
            conn.execute("SAVEPOINT igs")
            try:
                conn.execute(sql)
                conn.execute("RELEASE SAVEPOINT igs")
            except Exception as e:  # the DBMS rejects the action
                conn.execute("ROLLBACK TO SAVEPOINT igs")
                err = f"{type(e).__name__}: {str(e).splitlines()[0]}"
                break
            for inv in stmt_scoped:
                ok, post = _q(conn, inv.post_query)
                ok0, v0 = sp[inv.id]
                if not (ok and ok0) or v0 is None or post is None:
                    step_err[inv.id] = True
                elif not inv.holds(v0, post):
                    step_bad[inv.id] = True
        if err is not None:
            for inv in invs:
                out[inv.id] = "undecidable"
        else:
            for inv in stmt_scoped:
                out[inv.id] = "violated" if step_bad[inv.id] else ("undecidable" if step_err[inv.id] else "satisfied")
            for inv in whole:
                ok, post = _q(conn, inv.post_query)
                if not ok or post is None:
                    out[inv.id] = "undecidable"
                    continue
                if inv.is_delta:
                    ok0, v0 = pre[inv.id]
                    if not ok0 or v0 is None:
                        out[inv.id] = "undecidable"
                        continue
                    out[inv.id] = "satisfied" if inv.holds(v0, post) else "violated"
                else:
                    out[inv.id] = "satisfied" if inv.holds(None, post) else "violated"
        if commit_if is not None and err is None and commit_if(out):
            conn.execute("COMMIT")
            committed = True
    finally:
        if not committed:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
    return out, err, committed


# ---------------------------------------------------------------------------
# Aggregation and admission (Eq. 14-16)
# ---------------------------------------------------------------------------

def aggregate(evidence: list[Evidence]) -> str:
    if any(e.verdict == "violated" for e in evidence):
        return "unsafe"
    if any(e.verdict == "undecidable" for e in evidence):
        return "unresolved"
    return "safe"


def risk(evidence: list[Evidence]) -> float:
    k = {"violated": 10.0, "undecidable": 5.0, "satisfied": 0.0}
    return min(100.0, sum(e.severity * k[e.verdict] for e in evidence))


def decide(evidence, empty_selection, state_changing, cfg: VerifierConfig):
    if empty_selection and state_changing:
        if cfg.vacuity:
            return "escalate", "unresolved", 0.0
        return "allow", "safe", 0.0
    overall = aggregate(evidence)
    r = risk(evidence)
    if overall == "unresolved":
        return "escalate", overall, r
    if overall == "unsafe":
        return ("block" if r >= cfg.tau_block else "escalate"), overall, r
    return "allow", overall, r


class Verifier:
    """End-to-end verifier for one database."""

    def __init__(self, dbname: str, invariants: list[Invariant], snap: Snapshot,
                 cfg: VerifierConfig | None = None, conn=None):
        self.dbname = dbname
        self.invs = invariants
        self.snap = snap
        self.cfg = cfg or VerifierConfig()
        from .db import connect
        self.conn = conn or connect(dbname)
        self.static = StaticAnalyzer(snap, self.conn, self.cfg, estimate=self._estimate)

    def _shadow(self, statements, invs, isolation):
        return shadow_verify(self.conn, statements, invs, isolation)

    def _estimate(self, st: Stmt) -> int:
        plan = self.conn.execute("EXPLAIN (FORMAT JSON) " + st.sql).fetchone()[0]
        node = plan[0]["Plan"]
        while node.get("Plans") and node.get("Node Type") == "ModifyTable":
            node = node["Plans"][0]
        return int(node.get("Plan Rows", 0))

    def verify(self, statements: list[str], shadow_isolation="SERIALIZABLE") -> Decision:
        t0 = time.perf_counter()
        self.static.reset()
        stmts = compile_action(statements)
        state_changing = any(s.state_changing for s in stmts)
        writes = [s for s in stmts if s.state_changing]
        selected, closure = select_invariants(self.snap.catalog, writes, self.invs, self.cfg)
        evidence: list[Evidence] = []
        pending: list[Invariant] = []
        attempts = {}
        ts = time.perf_counter()
        vectors = None
        if selected and self.cfg.static_mode != "off":
            vectors = [self.static.vector(s) for s in writes]
            for inv in selected:
                verdict, why = self.static.attempt(inv, writes, vectors)
                attempts[inv.id] = why
                if verdict is not None:
                    evidence.append(Evidence(inv.id, verdict, "frame" if why == "frame" else "static",
                                             inv.severity, why, why))
                else:
                    pending.append(inv)
        else:
            pending = list(selected)
        static_ms = (time.perf_counter() - ts) * 1000
        shadow_ms, err, cross = 0.0, None, {}
        to_shadow = list(pending)
        if self.cfg.shadow_all:
            to_shadow = list(selected)
        if to_shadow:
            ts = time.perf_counter()
            out, err, _ = self._shadow(statements, to_shadow, shadow_isolation)
            shadow_ms = (time.perf_counter() - ts) * 1000
            done = {e.inv for e in evidence}
            for inv in to_shadow:
                if inv.id in done:
                    cross[inv.id] = out[inv.id]
                    continue
                evidence.append(Evidence(inv.id, out[inv.id], "shadow", inv.severity,
                                         err or "", attempts.get(inv.id, "")))
        d, overall, r = decide(evidence, not selected, state_changing, self.cfg)
        return Decision(d, overall, r, [i.id for i in selected], evidence, not selected,
                        bool(to_shadow), (time.perf_counter() - t0) * 1000, static_ms, shadow_ms,
                        err, cross)
