"""Connection proxy and the three transaction disciplines (Section 3.6).

The agent never holds a write connection.  Read-only statements are
forwarded; state-changing actions are withheld until the verifier decides,
and only an ``allow`` reaches real execution.

* separate                - verify (shadow, rolled back), then commit in a new
                            transaction.  Cheapest; containment-oriented.
* serializable            - serializable-through-commit: verify and commit in
                            one SERIALIZABLE transaction (the discipline the
                            full guarantee assumes); serialization failures
                            are retried and finally escalated.
* witness                 - witness-and-revalidate: verify, then in the commit
                            transaction lock and re-read the write watermarks
                            of every relation the decision depended on; any
                            change since verification forces re-verification.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import psycopg

from .compiler import compile_action
from .verifier import Evidence, Verifier, decide, select_invariants, shadow_verify


@dataclass
class Outcome:
    decision: str
    committed: bool
    latency_ms: float
    retries: int = 0
    error: str | None = None


class Proxy:
    def __init__(self, verifier: Verifier, discipline: str = "separate", think_ms: float = 0.0,
                 max_retries: int = 3):
        self.v = verifier
        self.discipline = discipline
        self.think = think_ms / 1000.0
        self.max_retries = max_retries
        self.on_verified = None   # test hook: called once an allow decision exists, before commit
        self.exec_conn = psycopg.connect(f"{self._dsn()}", autocommit=True)

    def _dsn(self):
        from .db import PG
        return f"{PG} dbname={self.v.dbname}"

    def close(self):
        self.exec_conn.close()

    # ------------------------------------------------------------------
    def submit(self, statements: list[str]) -> Outcome:
        stmts = compile_action(statements)
        if not any(s.state_changing for s in stmts):
            t0 = time.perf_counter()
            for s in statements:
                self.exec_conn.execute(s)
            return Outcome("allow", False, (time.perf_counter() - t0) * 1000)
        return getattr(self, "_" + self.discipline)(statements)

    def _hook(self):
        if self.on_verified is not None:
            self.on_verified()

    def _separate(self, statements):
        t0 = time.perf_counter()
        d = self.v.verify(statements)
        if d.decision != "allow":
            return Outcome(d.decision, False, (time.perf_counter() - t0) * 1000)
        self._hook()
        time.sleep(self.think)
        try:
            with self.exec_conn.transaction():
                for s in statements:
                    self.exec_conn.execute(s)
            return Outcome("allow", True, (time.perf_counter() - t0) * 1000)
        except Exception as e:
            return Outcome("allow", False, (time.perf_counter() - t0) * 1000, error=str(e)[:80])

    def _serializable(self, statements):
        t0 = time.perf_counter()
        writes = [s for s in compile_action(statements) if s.state_changing]
        selected, _ = select_invariants(self.v.snap.catalog, writes, self.v.invs, self.v.cfg)
        if not selected:
            d, _, _ = decide([], True, True, self.v.cfg)
            return Outcome(d, False, (time.perf_counter() - t0) * 1000)
        retries = 0
        while True:
            holder = {}

            def commit_if(out):
                ev = [Evidence(i.id, out[i.id], "shadow", i.severity) for i in selected]
                d, _, _ = decide(ev, False, True, self.v.cfg)
                holder["d"] = d
                if d == "allow":
                    self._hook()
                    time.sleep(self.think)
                return d == "allow"

            try:
                out, err, committed = shadow_verify(self.exec_conn, statements, selected,
                                                    "SERIALIZABLE", commit_if=commit_if)
                if err and "could not serialize" in err:
                    raise psycopg.errors.SerializationFailure(err)
                d = holder.get("d", "escalate") if not err else "escalate"
                return Outcome(d, committed, (time.perf_counter() - t0) * 1000, retries)
            except (psycopg.errors.SerializationFailure, psycopg.errors.DeadlockDetected):
                retries += 1
                if retries > self.max_retries:
                    return Outcome("escalate", False, (time.perf_counter() - t0) * 1000, retries)

    def _witness_set(self, statements):
        from .verifier import statement_closure
        writes = [s for s in compile_action(statements) if s.state_changing]
        selected, closure = select_invariants(self.v.snap.catalog, writes, self.v.invs, self.v.cfg)
        rels = set(closure)
        for inv in selected:
            rels |= inv.read_set()[0] | set(inv.tables)
        return sorted(rels)

    def _read_wm(self, conn, rels, lock=False):
        q = "SELECT relname, wm FROM ig_meta.watermark WHERE relname = ANY(%s) ORDER BY relname"
        if lock:
            q += " FOR UPDATE"
        return dict(conn.execute(q, (rels,)).fetchall())

    def _witness(self, statements):
        t0 = time.perf_counter()
        retries = 0
        rels = self._witness_set(statements)
        while True:
            # The witness is read *before* verification, so any write that
            # commits after this point is detected at revalidation.
            wm0 = self._read_wm(self.v.conn, rels)
            d = self.v.verify(statements)
            if d.decision != "allow":
                return Outcome(d.decision, False, (time.perf_counter() - t0) * 1000, retries)
            self._hook()
            time.sleep(self.think)
            try:
                with self.exec_conn.transaction():
                    # FOR UPDATE (taken in relname order) blocks concurrent writers' watermark bumps on
                    # these relations until this transaction commits.
                    wm1 = self._read_wm(self.exec_conn, rels, lock=True)
                    if wm1 != wm0:
                        raise _Changed()
                    for s in statements:
                        self.exec_conn.execute(s)
                return Outcome("allow", True, (time.perf_counter() - t0) * 1000, retries)
            except _Changed:
                retries += 1
                if retries > self.max_retries:
                    return Outcome("escalate", False, (time.perf_counter() - t0) * 1000, retries)
            except Exception as e:
                return Outcome("allow", False, (time.perf_counter() - t0) * 1000, retries, str(e)[:80])


class _Changed(Exception):
    pass
