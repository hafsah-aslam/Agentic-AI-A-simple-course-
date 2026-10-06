"""SQL -> IR compilation (Section 3.2).

Each statement is parsed with pglast (PostgreSQL's own parser) and mapped to
``Stmt(op, tables, columns, pred)``.  Row predicates are mapped onto the
supported grammar

    p ::= TRUE | c = v | c IN (v1..vk) | p AND p | p OR p

by walking the parse tree, so operator precedence is exactly the one
PostgreSQL applies.  Anything else (negation, ranges, LIKE, sub-queries,
functions, NULL tests ...) becomes ``Unsupported`` and can never yield a
static verdict: it receives the fallback bound |T| with certification flag
False.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

import pglast
import pglast.visitors
from pglast import ast, enums

# --------------------------------------------------------------------------
# Predicate IR
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PTrue:
    pass


@dataclass(frozen=True)
class PEq:
    col: str
    val: Any


@dataclass(frozen=True)
class PIn:
    col: str
    vals: tuple


@dataclass(frozen=True)
class PAnd:
    left: "Pred"
    right: "Pred"


@dataclass(frozen=True)
class POr:
    left: "Pred"
    right: "Pred"


@dataclass(frozen=True)
class PUnsupported:
    reason: str


Pred = Union[PTrue, PEq, PIn, PAnd, POr, PUnsupported]


def pred_supported(p: Pred) -> bool:
    if isinstance(p, PUnsupported):
        return False
    if isinstance(p, (PAnd, POr)):
        return pred_supported(p.left) and pred_supported(p.right)
    return True


def pred_form(p: Pred) -> str:
    """Coarse grammar form used in the grammar-coverage table."""
    if isinstance(p, PTrue):
        return "true"
    if isinstance(p, PEq):
        return "equality"
    if isinstance(p, PIn):
        return "in-list"
    if isinstance(p, PAnd):
        return "conjunction"
    if isinstance(p, POr):
        return "disjunction"
    return "unsupported"


# --------------------------------------------------------------------------
# Statement IR
# --------------------------------------------------------------------------

STATE_CHANGING = {"delete", "update", "insert", "truncate", "drop_table", "alter_table", "other_write"}


@dataclass
class Stmt:
    sql: str
    op: str                       # delete|update|insert|truncate|drop_table|alter_table|select|other_write
    tables: tuple                 # target relation(s)
    columns: frozenset = frozenset()   # written columns (empty = all / none named)
    pred: Pred = field(default_factory=PTrue)
    cascade: bool = False         # TRUNCATE/DROP ... CASCADE
    insert_rows: int | None = None  # number of VALUES rows for INSERT ... VALUES
    set_values: dict = field(default_factory=dict)  # UPDATE col -> constant (if constant)

    @property
    def table(self) -> str:
        return self.tables[0]

    @property
    def state_changing(self) -> bool:
        return self.op in STATE_CHANGING


def _const(node):
    """Return (ok, python value) for an A_Const / signed constant / typecast."""
    if isinstance(node, ast.A_Const):
        if node.isnull:
            return False, None
        v = node.val
        if isinstance(v, ast.Integer):
            return True, int(v.ival)
        if isinstance(v, ast.Float):
            return True, float(v.fval)
        if isinstance(v, ast.String):
            return True, str(v.sval)
        if isinstance(v, ast.Boolean):
            return True, bool(v.boolval)
        return False, None
    if isinstance(node, ast.TypeCast):
        return _const(node.arg)
    if (isinstance(node, ast.A_Expr) and node.kind == enums.A_Expr_Kind.AEXPR_OP
            and node.lexpr is None and node.name[0].sval == "-"):
        ok, v = _const(node.rexpr)
        if ok and isinstance(v, (int, float)):
            return True, -v
    return False, None


def _colname(node):
    if isinstance(node, ast.ColumnRef):
        f = node.fields[-1]
        if isinstance(f, ast.String):
            return f.sval
    return None


def compile_pred(node) -> Pred:
    if node is None:
        return PTrue()
    if isinstance(node, ast.A_Const):
        ok, v = _const(node)
        if ok and v is True:
            return PTrue()
        return PUnsupported("constant predicate")
    if isinstance(node, ast.BoolExpr):
        if node.boolop == enums.BoolExprType.NOT_EXPR:
            return PUnsupported("negation")
        parts = [compile_pred(a) for a in node.args]
        out = parts[0]
        cls = PAnd if node.boolop == enums.BoolExprType.AND_EXPR else POr
        for p in parts[1:]:
            out = cls(out, p)
        return out
    if isinstance(node, ast.A_Expr):
        op = node.name[0].sval if node.name else None
        if node.kind == enums.A_Expr_Kind.AEXPR_OP and op == "=":
            c, (ok, v) = _colname(node.lexpr), _const(node.rexpr)
            if c is None:
                c, (ok, v) = _colname(node.rexpr), _const(node.lexpr)
            if c is not None and ok:
                return PEq(c, v)
            return PUnsupported("non column = constant comparison")
        if node.kind == enums.A_Expr_Kind.AEXPR_IN and op == "=":
            c = _colname(node.lexpr)
            vals = []
            for item in node.rexpr:
                ok, v = _const(item)
                if not ok:
                    return PUnsupported("non-constant IN list")
                vals.append(v)
            if c is not None:
                return PIn(c, tuple(vals))
        return PUnsupported(f"operator {op!r} kind {node.kind.name}")
    return PUnsupported(type(node).__name__)


def compile_stmt(sql: str) -> Stmt:
    raw = pglast.parse_sql(sql)
    if len(raw) != 1:
        raise ValueError("one statement per call")
    st = raw[0].stmt
    if isinstance(st, ast.DeleteStmt):
        if st.usingClause:
            return Stmt(sql, "delete", (st.relation.relname,), pred=PUnsupported("USING"))
        return Stmt(sql, "delete", (st.relation.relname,), pred=compile_pred(st.whereClause))
    if isinstance(st, ast.UpdateStmt):
        cols, setv = set(), {}
        for t in st.targetList:
            cols.add(t.name)
            ok, v = _const(t.val)
            if ok:
                setv[t.name] = v
        pred = compile_pred(st.whereClause) if not st.fromClause else PUnsupported("UPDATE FROM")
        return Stmt(sql, "update", (st.relation.relname,), frozenset(cols), pred, set_values=setv)
    if isinstance(st, ast.InsertStmt):
        cols = frozenset(t.name for t in (st.cols or ()))
        n = None
        sel = st.selectStmt
        if isinstance(sel, ast.SelectStmt) and sel.valuesLists:
            n = len(sel.valuesLists)
        return Stmt(sql, "insert", (st.relation.relname,), cols, PTrue(), insert_rows=n)
    if isinstance(st, ast.TruncateStmt):
        tabs = tuple(r.relname for r in st.relations)
        return Stmt(sql, "truncate", tabs, cascade=st.behavior == enums.DropBehavior.DROP_CASCADE)
    if isinstance(st, ast.DropStmt) and st.removeType == enums.ObjectType.OBJECT_TABLE:
        tabs = tuple(o[-1].sval for o in st.objects)
        return Stmt(sql, "drop_table", tabs, cascade=st.behavior == enums.DropBehavior.DROP_CASCADE)
    if isinstance(st, ast.AlterTableStmt):
        return Stmt(sql, "alter_table", (st.relation.relname,))
    if isinstance(st, ast.SelectStmt) and not st.intoClause and not st.lockingClause:
        return Stmt(sql, "select", ())
    return Stmt(sql, "other_write", ())


def compile_action(statements: list[str]) -> list[Stmt]:
    return [compile_stmt(s) for s in statements]


# --------------------------------------------------------------------------
# Read-set extraction for invariant queries (used by the frame rule)
# --------------------------------------------------------------------------


def query_read_set(sql: str) -> tuple[set[str], set[str], bool]:
    """Relations and column names an invariant query reads.

    Returns (relations, column names, reads_catalog).  Column names are
    unqualified; ``*`` is recorded when a star or COUNT(*) appears so that a
    row-count dependency is never missed.
    """
    rels: set[str] = set()
    cols: set[str] = set()
    catalog = False

    class V(pglast.visitors.Visitor):
        def visit_RangeVar(self, ancestors, node):
            nonlocal catalog
            if node.schemaname in ("information_schema", "pg_catalog"):
                catalog = True
            else:
                rels.add(node.relname)

        def visit_ColumnRef(self, ancestors, node):
            f = node.fields[-1]
            cols.add("*" if isinstance(f, ast.A_Star) else f.sval)

        def visit_FuncCall(self, ancestors, node):
            if node.agg_star:
                cols.add("*")

    V()(pglast.parse_sql(sql))
    return rels, cols, catalog
