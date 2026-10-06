"""Certificate snapshot Sigma (Definitions 1 and 2).

The static analyzer never consumes optimizer statistics.  Its only numerical
input is this snapshot, built from the data with exact counting/grouping
queries:

  (i)   exact cardinality |T|
  (ii)  maximum frequency mf(T, c) for every profiled column, plus (new) a
        per-value frequency certificate: the exact frequency of every value
        when the column has at most ``topk`` distinct values, otherwise the
        exact top-k frequencies and the (k+1)-th frequency as a certified cap
        for every value outside the top-k;
  (iii) single-column key / uniqueness facts (composite-key members are never
        recorded as individually unique);
  (iv)  foreign keys with their referential actions;
  (v)   the monotonic write watermark omega(T);
  plus non-null counts of FK columns (used by certified lower bounds) and the
  set of user triggers, so that an unmodelled trigger fails closed.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

ACTION_CODES = {"a": "no action", "r": "restrict", "c": "cascade", "n": "set null", "d": "set default"}


@dataclass(frozen=True)
class FK:
    name: str
    child: str
    child_cols: tuple
    parent: str
    parent_cols: tuple
    on_delete: str
    on_update: str


@dataclass
class Catalog:
    tables: dict                       # table -> [columns]
    col_types: dict                    # (table, col) -> type name
    fks: list
    unique: set                        # {(table, col)} single-column unique facts
    unmodelled_triggers: set           # tables carrying triggers other than ig_wm

    def children(self, table, modifying=("cascade", "set null", "set default"), on="delete"):
        out = []
        for fk in self.fks:
            act = fk.on_delete if on == "delete" else fk.on_update
            if fk.parent == table and act in modifying:
                out.append(fk)
        return out

    def referencing(self, table):
        return [fk for fk in self.fks if fk.parent == table]


def load_catalog(conn) -> Catalog:
    tables: dict = {}
    types: dict = {}
    for t, c, ty in conn.execute(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='public' ORDER BY table_name, ordinal_position"):
        tables.setdefault(t, []).append(c)
        types[(t, c)] = ty
    fks = []
    for name, child, parent, ccols, pcols, dl, up in conn.execute("""
        SELECT con.conname, cl.relname, pl.relname,
               ARRAY(SELECT a.attname FROM unnest(con.conkey) WITH ORDINALITY k(n, o)
                     JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.n ORDER BY k.o),
               ARRAY(SELECT a.attname FROM unnest(con.confkey) WITH ORDINALITY k(n, o)
                     JOIN pg_attribute a ON a.attrelid = con.confrelid AND a.attnum = k.n ORDER BY k.o),
               con.confdeltype, con.confupdtype
        FROM pg_constraint con
        JOIN pg_class cl ON cl.oid = con.conrelid
        JOIN pg_class pl ON pl.oid = con.confrelid
        JOIN pg_namespace ns ON ns.oid = cl.relnamespace
        WHERE con.contype = 'f' AND ns.nspname = 'public'"""):
        fks.append(FK(name, child, tuple(ccols), parent, tuple(pcols),
                      ACTION_CODES[dl], ACTION_CODES[up]))
    unique = set()
    for t, cols in conn.execute("""
        SELECT c.relname,
               ARRAY(SELECT a.attname FROM unnest(i.indkey) k(n)
                     JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.n)
        FROM pg_index i JOIN pg_class c ON c.oid = i.indrelid
        JOIN pg_namespace ns ON ns.oid = c.relnamespace
        WHERE ns.nspname='public' AND i.indisunique AND i.indpred IS NULL
          AND i.indexprs IS NULL AND i.indnkeyatts = 1"""):
        if len(cols) == 1:
            unique.add((t, cols[0]))
    trig = {r[0] for r in conn.execute("""
        SELECT DISTINCT c.relname FROM pg_trigger tg JOIN pg_class c ON c.oid = tg.tgrelid
        JOIN pg_namespace ns ON ns.oid = c.relnamespace
        WHERE ns.nspname='public' AND NOT tg.tgisinternal AND tg.tgname <> 'ig_wm'""")}
    rules = {r[0] for r in conn.execute(
        "SELECT tablename FROM pg_rules WHERE schemaname='public'")}
    return Catalog(tables, types, fks, unique, trig | rules)


@dataclass
class FreqCert:
    """Per-value frequency certificate for one column."""
    exact: dict          # canonical value -> count
    rest_cap: int        # certified cap for any value not in ``exact`` (0 if complete)
    complete: bool


@dataclass
class Snapshot:
    card: dict
    mf: dict                              # (T, c) -> max frequency
    freq: dict                            # (T, c) -> FreqCert
    nonnull: dict                         # (T, c) -> non-null count
    watermark: dict                       # T -> omega(T)
    catalog: Catalog
    build_seconds: float = 0.0
    epoch: int = 0
    meta: dict = field(default_factory=dict)

    # Definition 2 ---------------------------------------------------------
    def valid(self, table: str, reader) -> bool:
        w = self.watermark.get(table)
        if w is None or reader is None:
            return False
        try:
            live = reader(table)
        except Exception:
            return False
        return live is not None and live == w


INT_TYPES = {"integer", "bigint", "smallint"}
TEXT_TYPES = {"text", "character varying", "character"}


def canonical(value, col_type):
    """Canonical text form of a predicate literal, or None when the literal's
    type does not round-trip for the column type (then only mf is used)."""
    if col_type in INT_TYPES and isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if col_type in TEXT_TYPES and isinstance(value, str):
        return value
    if col_type == "boolean" and isinstance(value, bool):
        return "true" if value else "false"
    return None


def build_snapshot(conn, topk: int = 256, tables=None) -> Snapshot:
    t0 = time.perf_counter()
    cat = load_catalog(conn)
    card, mf, freq, nonnull, wm = {}, {}, {}, {}, {}
    for t, cols in cat.tables.items():
        if tables is not None and t not in tables:
            continue
        card[t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        for c in cols:
            ty = cat.col_types[(t, c)]
            if ty not in INT_TYPES | TEXT_TYPES | {"boolean"}:
                # still profile mf for any type
                rows = conn.execute(
                    f'SELECT COUNT(*) FROM "{t}" WHERE "{c}" IS NOT NULL GROUP BY "{c}" '
                    f'ORDER BY 1 DESC LIMIT 1').fetchall()
                mf[(t, c)] = rows[0][0] if rows else 0
                nonnull[(t, c)] = conn.execute(
                    f'SELECT COUNT("{c}") FROM "{t}"').fetchone()[0]
                continue
            rows = conn.execute(
                f'SELECT "{c}"::text, COUNT(*) FROM "{t}" WHERE "{c}" IS NOT NULL '
                f'GROUP BY 1 ORDER BY 2 DESC LIMIT {topk + 1}').fetchall()
            mf[(t, c)] = rows[0][1] if rows else 0
            complete = len(rows) <= topk
            exact = {v: n for v, n in rows[:topk]}
            rest = 0 if complete else rows[topk][1]
            freq[(t, c)] = FreqCert(exact, rest, complete)
            nonnull[(t, c)] = sum(n for _, n in rows) if complete else conn.execute(
                f'SELECT COUNT("{c}") FROM "{t}"').fetchone()[0]
    for rel, w in conn.execute("SELECT relname, wm FROM ig_meta.watermark"):
        if tables is None or rel in tables:
            wm[rel] = w
    return Snapshot(card, mf, freq, nonnull, wm, cat, time.perf_counter() - t0)


def watermark_reader(conn):
    """Live watermark reader bound to a connection (fails closed on error)."""
    def read(table):
        r = conn.execute("SELECT wm FROM ig_meta.watermark WHERE relname=%s", (table,)).fetchone()
        return None if r is None else r[0]
    return read
