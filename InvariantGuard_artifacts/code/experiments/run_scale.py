"""Scalability: snapshot construction cost and admission latency of the
static path versus shadow execution from ~9k to ~4M rows."""
from __future__ import annotations

import random
import statistics
import time

from common import db, dump, inv_path, load_invariants
from invariantguard.snapshot import build_snapshot
from invariantguard.verifier import Verifier, VerifierConfig


def seed_sql(n_acc, tx_per_acc=3):
    return "\n".join([
        "INSERT INTO branches VALUES (1,'HQ',NULL),(2,'North',1),(3,'South',1),(4,'North Annex',2);",
        "INSERT INTO staff VALUES (10,1,'Ada'),(11,2,'Ben'),(12,3,'Cara'),(13,4,'Dev');",
        f"INSERT INTO customers SELECT g, 'c'||g, (ARRAY['retail','premier','private'])[1+g%3] FROM generate_series(1,{n_acc}) g;",
        f"INSERT INTO accounts SELECT g, 2+g%3, 1000*g, (ARRAY['open','open','frozen'])[1+g%3], NULL FROM generate_series(1,{n_acc}) g;",
        f"INSERT INTO account_holders SELECT g, g, 'primary' FROM generate_series(1,{n_acc}) g;",
        f"INSERT INTO transactions SELECT g, 1+(g-1)%{n_acc}, 100, TRUE FROM generate_series(1,{n_acc * tx_per_acc}) g;",
    ])


def build(n_acc):
    name = f"igscale_{n_acc}"
    fdir = db.DATA / "fixtures" / "banking_heldout"
    db.drop_db(name)
    with db.connect() as c:
        c.execute(f'CREATE DATABASE "{name}"')
    with db.connect(name) as c:
        c.execute((fdir / "schema.sql").read_text())
        c.execute(seed_sql(n_acc))
        db.install_watermarks(c)
        c.execute("VACUUM ANALYZE")
        rows = sum(c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                   for t in ("branches", "staff", "customers", "accounts", "account_holders", "transactions"))
    return name, rows


WORKLOADS = {
    # only bounded deltas are selected: decidable from the certificate alone
    "delta-only (DELETE transaction by key)": lambda rng, n: [f"DELETE FROM transactions WHERE transaction_id = {rng.randrange(1, 3 * n)}"],
    # two-statement action: needs the summed bound of Eq. (25)
    "multi-statement (2 transaction deletes)": lambda rng, n: [
        f"DELETE FROM transactions WHERE transaction_id = {rng.randrange(1, 3 * n)}",
        f"DELETE FROM transactions WHERE transaction_id = {rng.randrange(1, 3 * n)}"],
    # selects structural invariants too: shadow execution remains necessary
    "mixed (DELETE account, cascades)": lambda rng, n: [f"DELETE FROM accounts WHERE account_id = {rng.randrange(1, n)}"],
}


def main():
    out = []
    for n_acc in (1_500, 16_000, 170_000, 680_000):
        name, rows = build(n_acc)
        conn = db.connect(name)
        t = []
        for _ in range(3):
            s = build_snapshot(conn)
            t.append(s.build_seconds)
        rec = {"accounts": n_acc, "rows": rows, "snapshot_s": statistics.median(t)}
        invs = load_invariants(inv_path("banking_heldout"))
        for mode in ("extended", "off"):
            v = Verifier(name, invs, s, VerifierConfig(static_mode=mode), conn)
            for wname, gen in WORKLOADS.items():
                rng = random.Random(1)
                lat, shadow = [], 0
                for _ in range(40):
                    d = v.verify(gen(rng, n_acc))
                    lat.append(d.latency_ms)
                    shadow += d.shadow_used
                rec[f"{mode}|{wname}|p50_ms"] = statistics.median(lat)
                rec[f"{mode}|{wname}|shadow_frac"] = shadow / 40
        print(rec, flush=True)
        out.append(rec)
        conn.close()
        db.drop_db(name)
    dump("scale.json", {"points": out, "workloads": list(WORKLOADS)})


if __name__ == "__main__":
    main()
