"""G7 (new): split-to-split variance. Re-partitions the docked internal pool into train/val/test with the same
group-aware, hash-ordered filling rule but a different salt, keeping the frozen external cohort unchanged and
keeping the original cohort sizes.

Usage: python3 resplit.py FEATS.pkl MANIFEST SALT OUT.pkl
"""
import sys, pickle, hashlib
import pandas as pd

feats_p, man_p, salt, out = sys.argv[1:5]
data = pickle.load(open(feats_p, "rb"))
man = pd.read_csv(man_p).set_index("pdb")
internal = [d for d in data if d["split"] in ("train", "val", "test")]
sizes = {s: sum(d["split"] == s for d in internal) for s in ("train", "val", "test")}
groups = {}
for d in internal:
    groups.setdefault(man.loc[d["pdb"], "group_id"], []).append(d)
order = sorted(groups, key=lambda g: hashlib.sha256((salt + g).encode()).hexdigest())
filled = {s: 0 for s in sizes}
it = iter(("train", "val", "test")); cur = next(it)
for g in order:
    if cur is not None and filled[cur] >= sizes[cur]:
        cur = next(it, None)                      # the next split starts with a fresh group
    for d in sorted(groups[g], key=lambda x: x["pdb"]):
        if cur is not None and filled[cur] < sizes[cur]:
            d["split"] = cur; filled[cur] += 1
        else:
            d["split"] = "retired"                # truncated boundary group / pool exhausted
kept = [d for d in data if d["split"] != "retired"]
by = {}
for d in kept:
    by.setdefault(man.loc[d["pdb"], "group_id"] if d["split"] != "external" else d["pdb"], set()).add(d["split"])
assert all(len(v) == 1 for v in by.values()), "a group crosses splits"
pickle.dump(kept, open(out, "wb"))
print(salt, {s: sum(d["split"] == s for d in kept) for s in ("train", "val", "test", "external")})
