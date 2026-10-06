"""Unit tests that need no database."""
from invariantguard.bounds import BoundConfig, delete_vector, pred_upper
from invariantguard.compiler import PAnd, PEq, PIn, POr, PTrue, PUnsupported, compile_stmt, pred_supported
from invariantguard.invariants import Invariant
from invariantguard.snapshot import FK, Catalog, FreqCert, Snapshot
from invariantguard.verifier import Evidence, VerifierConfig, decide


def snap_of(card, mf, fks=(), unique=(), freq=None, types=None):
    tables = {t: sorted({c for (tt, c) in mf if tt == t} | {"id"}) for t in card}
    cat = Catalog(tables, types or {}, list(fks), set(unique), set())
    return Snapshot(card, mf, freq or {}, {}, {t: 1 for t in card}, cat)


def test_precedence_follows_parse_tree():
    p = compile_stmt("DELETE FROM t WHERE a = 1 OR b = 2 AND c = 3").pred
    assert isinstance(p, POr) and isinstance(p.right, PAnd)


def test_unsupported_constructs_are_marked():
    for w in ("NOT a = 1", "a > 3", "a LIKE 'x%'", "a IN (SELECT 1)", "a IS NULL"):
        assert not pred_supported(compile_stmt(f"DELETE FROM t WHERE {w}").pred)
    assert isinstance(compile_stmt("DELETE FROM t WHERE TRUE").pred, PTrue)
    assert isinstance(compile_stmt("DELETE FROM t").pred, PTrue)


def test_worked_example_banking():
    # Section 3.3: |accounts| = 4, mf(branch_id) = 2, mf(status) = 3
    s = snap_of({"accounts": 4}, {("accounts", "branch_id"): 2, ("accounts", "status"): 3})
    st = compile_stmt("DELETE FROM accounts WHERE branch_id = 2 OR status = 'frozen'")
    b = pred_upper(s, "accounts", st.pred, BoundConfig(per_value=False))
    assert b.certified and b.value == 4 and b.rule == "R7"


def test_conjunction_takes_minimum():
    s = snap_of({"t": 100}, {("t", "a"): 40, ("t", "b"): 7})
    b = pred_upper(s, "t", compile_stmt("DELETE FROM t WHERE a = 1 AND b = 2").pred, BoundConfig(per_value=False))
    assert b.value == 7 and b.rule == "R6"


def test_per_value_certificate_is_tighter_and_absent_values_are_zero():
    fc = FreqCert({"1": 90, "2": 3}, 0, True)
    s = snap_of({"t": 93}, {("t", "a"): 90}, freq={("t", "a"): fc}, types={("t", "a"): "integer"})
    assert pred_upper(s, "t", PEq("a", 2), BoundConfig()).value == 3
    assert pred_upper(s, "t", PEq("a", 7), BoundConfig()).value == 0
    assert pred_upper(s, "t", PEq("a", 2), BoundConfig(per_value=False)).value == 90
    # a literal whose type does not round-trip falls back to mf
    assert pred_upper(s, "t", PEq("a", "2"), BoundConfig()).value == 90


def test_diamond_requires_sum_merge():
    # A -> B, A -> C, B -> D, C -> D, all CASCADE, all FKs one-to-one
    fks = [FK("b", "pb", ("a",), "pa", ("id",), "cascade", "no action"),
           FK("c", "pc", ("a",), "pa", ("id",), "cascade", "no action"),
           FK("db", "pd", ("b",), "pb", ("id",), "cascade", "no action"),
           FK("dc", "pd", ("c",), "pc", ("id",), "cascade", "no action")]
    mf = {("pa", "id"): 1, ("pb", "a"): 1, ("pc", "a"): 1, ("pd", "b"): 1, ("pd", "c"): 1}
    s = snap_of({"pa": 5, "pb": 5, "pc": 5, "pd": 5}, mf, fks, unique=[("pa", "id")])
    st = compile_stmt("DELETE FROM pa WHERE id = 1")
    v_sum = delete_vector(s, st, BoundConfig(merge="sum"), lambda t: True)
    v_max = delete_vector(s, st, BoundConfig(merge="max"), lambda t: True)
    # one D row may hang off the deleted B row and another off the deleted C row
    assert v_sum.deleted["pd"].value == 2
    assert v_max.deleted["pd"].value == 1   # unsound: two D rows can be deleted


def test_invalid_snapshot_is_uncertified():
    s = snap_of({"t": 10}, {("t", "a"): 2})
    b = pred_upper(s, "t", PEq("a", 1), BoundConfig(), valid=False)
    assert not b.certified


def test_decision_rule_fail_closed():
    cfg = VerifierConfig()
    ev = lambda v, w=8: Evidence("i", v, "shadow", w)  # noqa: E731
    assert decide([], True, True, cfg)[0] == "escalate"          # vacuity
    assert decide([ev("satisfied")], False, True, cfg)[0] == "allow"
    assert decide([ev("undecidable")], False, True, cfg)[0] == "escalate"
    assert decide([ev("violated", 8)], False, True, cfg)[0] == "block"
    assert decide([ev("violated", 5)], False, True, cfg)[0] == "escalate"
    # the threshold only moves actions between the two refusals
    for tau in (0, 50, 100, 1000):
        assert decide([ev("violated", 1)], False, True, VerifierConfig(tau_block=tau))[0] != "allow"


def test_bounded_delta_semantics():
    i = Invariant("x", "", frozenset({"t"}), frozenset(), frozenset({"delete"}), "bounded-delta",
                  "SELECT COUNT(*) FROM t", "SELECT COUNT(*) FROM t", {"max_decrease": 1, "max_increase": 0})
    assert i.metric_relation == "t"
    assert i.holds(5, 4) and not i.holds(5, 3) and not i.holds(5, 6)


def test_sqlite_boolean_columns_never_use_per_value_lookup():
    # SQLite stores TRUE as 1: a PostgreSQL-style canonical 'true' would miss
    # the certificate and receive cap 0 (this admitted unsafe actions once).
    from invariantguard.snapshot import canonical
    from invariantguard.sqlite_backend import _type
    assert canonical(True, _type("BOOLEAN")) is None
    assert canonical(3, _type("INTEGER")) == "3"
