"""PostgreSQL plumbing: connections, fixture templates, disposable clones and
the monotonic write watermark used by the certificate snapshot.

Every user relation receives a statement-level AFTER trigger that bumps
``ig_meta.watermark`` for that relation.  Referential actions (ON DELETE
CASCADE / SET NULL) are executed by PostgreSQL as separate statements on the
child relation, so the child's watermark moves as well.  The watermark is the
``omega_Sigma(T)`` of Definition 1; a snapshot is valid for T only while the
live watermark equals the recorded one (Definition 2).
"""
from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from pathlib import Path

import psycopg

PG = os.environ.get("IG_PG", "host=/tmp port=5433 user=postgres")
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
FIXTURES = ["chinook_derived", "northwind_derived", "hr_payroll", "banking_heldout", "healthcare_heldout"]
INVARIANT_FILES = {
    "chinook_derived": "chinook_v1.yaml",
    "northwind_derived": "northwind_v1.yaml",
    "hr_payroll": "hr_payroll_v1.yaml",
    "banking_heldout": "banking_heldout_v1.yaml",
    "healthcare_heldout": "healthcare_heldout_v1.yaml",
}
DEVELOPMENT = {"chinook_derived", "northwind_derived", "hr_payroll"}


def connect(dbname: str = "postgres", autocommit: bool = True) -> psycopg.Connection:
    return psycopg.connect(f"{PG} dbname={dbname}", autocommit=autocommit)


WATERMARK_SQL = """
CREATE SCHEMA IF NOT EXISTS ig_meta;
CREATE TABLE IF NOT EXISTS ig_meta.watermark (relname text PRIMARY KEY, wm bigint NOT NULL);
CREATE OR REPLACE FUNCTION ig_meta.bump() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO ig_meta.watermark VALUES (TG_TABLE_NAME, 1)
  ON CONFLICT (relname) DO UPDATE SET wm = ig_meta.watermark.wm + 1;
  RETURN NULL;
END $$;
"""


def install_watermarks(conn) -> None:
    conn.execute(WATERMARK_SQL)
    tables = [r[0] for r in conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname='public'")]
    for t in tables:
        conn.execute(f'DROP TRIGGER IF EXISTS ig_wm ON "{t}"')
        conn.execute(
            f'CREATE TRIGGER ig_wm AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON "{t}" '
            "FOR EACH STATEMENT EXECUTE FUNCTION ig_meta.bump()")
        conn.execute("INSERT INTO ig_meta.watermark VALUES (%s, 1) ON CONFLICT DO NOTHING", (t,))


def template_name(fixture: str) -> str:
    return f"igtpl_{fixture}"


def drop_db(name: str) -> None:
    with connect() as c:
        c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def build_template(fixture: str, seed_file: str = "seed.sql", extra_sql: str | None = None,
                   name: str | None = None) -> str:
    """(Re)create the template database of a fixture and return its name."""
    name = name or template_name(fixture)
    drop_db(name)
    with connect() as c:
        c.execute(f'CREATE DATABASE "{name}"')
    fdir = DATA / "fixtures" / fixture
    with connect(name) as c:
        c.execute((fdir / "schema.sql").read_text())
        c.execute((fdir / seed_file).read_text())
        if extra_sql:
            c.execute(extra_sql)
        install_watermarks(c)
        c.execute("ANALYZE")
    return name


def build_all_templates() -> None:
    for f in FIXTURES:
        build_template(f)


@contextmanager
def clone(template: str):
    """A disposable copy of a template database (dropped on exit)."""
    name = f"igc_{uuid.uuid4().hex[:12]}"
    with connect() as c:
        c.execute(f'CREATE DATABASE "{name}" TEMPLATE "{template}"')
    try:
        yield name
    finally:
        drop_db(name)


def server_version() -> str:
    with connect() as c:
        return c.execute("SHOW server_version").fetchone()[0]
