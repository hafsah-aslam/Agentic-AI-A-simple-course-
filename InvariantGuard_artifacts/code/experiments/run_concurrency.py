"""Transaction disciplines under concurrency.

(a) Latency from 1 to 16 concurrent agent clients under each discipline.
(b) Containment under concurrent writers: an agent deletes an account that
    has exactly one transaction when verified (safe under the "at most two
    cascaded transactions per action" invariant) while concurrent writers
    insert transactions for that account.  We count commits whose *actual*
    committed effect violates the invariant.
"""
from __future__ import annotations

import random
import statistics
import threading
import time

from common import db, dump, inv_path, load_invariants
from invariantguard.proxy import Proxy
from invariantguard.snapshot import build_snapshot
from invariantguard.verifier import Verifier, VerifierConfig

N_ACC = 20000


def bank_seed(n_acc=N_ACC, seed=5):
    rng = random.Random(seed)
    out = ["INSERT INTO branches VALUES (1,'HQ',NULL),(2,'North',1),(3,'South',1),(4,'North Annex',2);",
           "INSERT INTO staff VALUES (10,1,'Ada'),(11,2,'Ben'),(12,3,'Cara'),(13,4,'Dev');"]
    out.append("INSERT INTO customers SELECT g, 'c'||g, (ARRAY['retail','premier','private'])[1+g%3] "
               f"FROM generate_series(1,{n_acc}) g;")
    out.append(f"INSERT INTO accounts SELECT g, 2+g%3, 1000*g, 'open', NULL FROM generate_series(1,{n_acc}) g;")
    out.append(f"INSERT INTO account_holders SELECT g, g, 'primary' FROM generate_series(1,{n_acc}) g;")
    # one transaction per account
    out.append(f"INSERT INTO transactions SELECT g, g, 100, TRUE FROM generate_series(1,{n_acc}) g;")
    return "\n".join(out)


def make_db(name):
    tpl = f"igtpl_{name}"
    fdir = db.DATA / "fixtures" / "banking_heldout"
    db.drop_db(tpl)
    with db.connect() as c:
        c.execute(f'CREATE DATABASE "{tpl}"')
    with db.connect(tpl) as c:
        c.execute((fdir / "schema.sql").read_text())
        c.execute(bank_seed())
        c.execute("CREATE SEQUENCE txid_seq START 10000000")
        db.install_watermarks(c)
        c.execute("ANALYZE")
    return tpl


def fresh(tpl, tag):
    name = f"igconc_{tag}"
    db.drop_db(name)
    with db.connect() as c:
        c.execute(f'CREATE DATABASE "{name}" TEMPLATE "{tpl}"')
    return name


def verifier_for(name):
    conn = db.connect(name)
    snap = build_snapshot(conn)
    invs = load_invariants(inv_path("banking_heldout"))
    return Verifier(name, invs, snap, VerifierConfig(static_mode="extended"), conn)


def latency(tpl, disciplines=("separate", "serializable", "witness"), clients=(1, 2, 4, 8, 16), per_client=40):
    out = {}
    for disc in disciplines:
        for k in clients:
            name = fresh(tpl, f"lat_{disc[:3]}_{k}")
            lat, decisions, retries = [], [], []
            lock = threading.Lock()

            def worker(cid):
                v = verifier_for(name)
                p = Proxy(v, disc)
                rng = random.Random(cid)
                for j in range(per_client):
                    acc = 1 + (cid * per_client + j) % N_ACC
                    if j % 2 == 0:
                        stmts = [f"DELETE FROM transactions WHERE transaction_id = {acc}"]
                    else:
                        stmts = [f"UPDATE accounts SET balance_cents = balance_cents + {rng.randrange(100)} "
                                 f"WHERE account_id = {acc}"]
                    o = p.submit(stmts)
                    with lock:
                        lat.append(o.latency_ms)
                        decisions.append(o.decision)
                        retries.append(o.retries)
                p.close()
                v.conn.close()

            ths = [threading.Thread(target=worker, args=(c,)) for c in range(k)]
            t0 = time.time()
            for t in ths:
                t.start()
            for t in ths:
                t.join()
            wall = time.time() - t0
            out[f"{disc}|{k}"] = {"discipline": disc, "clients": k, "p50_ms": statistics.median(lat),
                                  "p90_ms": sorted(lat)[int(0.9 * len(lat))], "mean_ms": statistics.mean(lat),
                                  "throughput": len(lat) / wall, "allow": decisions.count("allow"),
                                  "n": len(lat), "retries": sum(retries)}
            print(disc, k, out[f"{disc}|{k}"], flush=True)
            db.drop_db(name)
    return out


def containment(tpl, disciplines=("separate", "serializable", "witness"), writers=(0, 1, 4, 16),
                trials=60, think_ms=5.0):
    out = {}
    for disc in disciplines:
        for w in writers:
            name = fresh(tpl, f"cont_{disc[:3]}_{w}")
            v = verifier_for(name)
            p = Proxy(v, disc, think_ms=think_ms)
            target = {"acc": None}
            stop = threading.Event()
            succ = {}
            lock = threading.Lock()

            def writer(wid):
                c = db.connect(name)
                done = {}
                while not stop.is_set():
                    a = target["acc"]
                    if a is None or done.get(a, 0) >= 3:   # bursts of at most 3 inserts per account
                        time.sleep(0.0005)
                        continue
                    done[a] = done.get(a, 0) + 1
                    try:
                        c.execute("INSERT INTO transactions VALUES (nextval('txid_seq'), %s, 5, TRUE)", (a,))
                        with lock:
                            succ[a] = succ.get(a, 0) + 1
                    except Exception:
                        pass
                    time.sleep(0.0005)
                c.close()

            ths = [threading.Thread(target=writer, args=(i,)) for i in range(w)]
            for t in ths:
                t.start()
            res = {"trials": 0, "allowed": 0, "committed": 0, "unsafe_commits": 0, "blocked": 0,
                   "escalated": 0, "retries": 0}
            for k in range(trials):
                acc = 15000 + k
                # concurrent writes arrive right after the verifier has decided
                p.on_verified = (lambda a=acc: target.__setitem__("acc", a)) if w else None
                o = p.submit([f"DELETE FROM accounts WHERE account_id = {acc}"])
                time.sleep(0.003)
                target["acc"] = None
                time.sleep(0.002)
                res["trials"] += 1
                res["retries"] += o.retries
                res[{"allow": "allowed", "block": "blocked", "escalate": "escalated"}[o.decision]] += 1
                if o.committed:
                    res["committed"] += 1
                    with lock:
                        removed = 1 + succ.get(acc, 0)
                    if removed > 2:
                        res["unsafe_commits"] += 1
            stop.set()
            for t in ths:
                t.join()
            p.close()
            v.conn.close()
            res["discipline"], res["writers"] = disc, w
            out[f"{disc}|{w}"] = res
            print(res, flush=True)
            db.drop_db(name)
    return out


def main():
    import json, sys
    tpl = make_db("bankscale")
    part = db.ROOT / "results" / "concurrency_latency.partial.json"
    if part.exists() and "--fresh" not in sys.argv:
        lat = json.loads(part.read_text())
    else:
        lat = latency(tpl)
        part.write_text(json.dumps(lat))
    cont = containment(tpl)
    dump("concurrency.json", {"latency": lat, "containment": cont, "accounts": N_ACC})
    db.drop_db(tpl)


if __name__ == "__main__":
    main()
