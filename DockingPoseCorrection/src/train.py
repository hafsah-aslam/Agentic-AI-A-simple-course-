"""Stage 4: train one (architecture, seed) and write per-atom predictions for every cohort.

Preprocessing fit on training complexes only: coordinate scale c (RMS of training pocket coordinates relative to
the docked-ligand centroid), flexibility mean/std, flexibility imputation value. Training: Adam 1e-3, at most 15
epochs, early stopping with patience 5 on validation NLL, random proper rotations of all coordinates and targets
during training only.

Usage: python3 train.py FEATS.pkl OUTDIR ARCH SEED
"""
import sys, os, json, pickle, time
import numpy as np
import torch
from model import PoseCorrector, nll

torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "1")))
EPOCHS, PATIENCE, LR, BATCH = 15, 5, 1e-3, 16


def fit_preprocessing(data):
    tr = [d for d in data if d["split"] == "train"]
    c = float(np.sqrt(np.mean(np.concatenate([d["res_xyz"] for d in tr]) ** 2)))
    flex = np.concatenate([d["res_flex_raw"] for d in tr])
    flex = flex[~np.isnan(flex)]
    cov = [1 - np.isnan(d["res_flex_raw"]).mean() for d in tr]
    fm, fs = (float(flex.mean()), float(flex.std() + 1e-6)) if len(flex) else (0.0, 1.0)
    return {"coord_scale": c, "flex_mean": fm, "flex_std": fs,
            "train_fully_imputed_frac": float(np.mean([x == 0 for x in cov])),
            "train_under_half_coverage_frac": float(np.mean([0 < x < 0.5 for x in cov])),
            "train_misato_qc_counts": {k: int(sum(d.get("misato_qc") == k for d in tr)) for k in ("ok", "failed_registration", "absent")}}


def prepare(d, pp):
    flex = d["res_flex_raw"].copy()
    flex[np.isnan(flex)] = pp["flex_mean"]                       # frozen training-mean imputation
    c = pp["coord_scale"]
    return {"lig": d["lig_feat"], "lig_xyz": d["lig_xyz"] / c, "target": d["target"] / c, "aa": d["res_aa"],
            "res_xyz": d["res_xyz"] / c, "res_sc": d["res_sc"] / c, "deg": d["res_deg"],
            "flex": (flex - pp["flex_mean"]) / pp["flex_std"], "edges": d["edges"], "segments": d["segments"]}


def random_rotation(rng):
    q = rng.normal(size=4); q /= np.linalg.norm(q)
    a, b, c, d = q
    return np.array([[a*a+b*b-c*c-d*d, 2*(b*c-a*d), 2*(b*d+a*c)],
                     [2*(b*c+a*d), a*a-b*b+c*c-d*d, 2*(c*d-a*b)],
                     [2*(b*d-a*c), 2*(c*d+a*b), a*a-b*b-c*c+d*d]], np.float32)


def collate(items, rots=None):
    B = len(items)
    N = max(len(x["lig"]) for x in items); R = max(len(x["aa"]) for x in items)
    S = max(int(x["segments"].max()) + 1 for x in items)
    out = {k: torch.zeros(B, N, s) for k, s in (("lig", 18), ("lig_xyz", 3), ("target", 3))}
    out.update(res=torch.zeros(B, R, 28), res_xyz=torch.zeros(B, R, 3), adj=torch.zeros(B, R, R, dtype=torch.bool),
               incidence=torch.zeros(B, R, S), lig_mask=torch.zeros(B, N, dtype=torch.bool),
               res_mask=torch.zeros(B, R, dtype=torch.bool))
    for i, x in enumerate(items):
        rot = rots[i] if rots is not None else np.eye(3, dtype=np.float32)
        n, r = len(x["lig"]), len(x["aa"])
        lx, tg, rx, sc = x["lig_xyz"] @ rot.T, x["target"] @ rot.T, x["res_xyz"] @ rot.T, x["res_sc"] @ rot.T
        out["lig"][i, :n] = torch.from_numpy(x["lig"]); out["lig_xyz"][i, :n] = torch.from_numpy(lx)
        out["target"][i, :n] = torch.from_numpy(tg); out["lig_mask"][i, :n] = True
        feats = np.concatenate([x["aa"], rx, sc, x["deg"][:, None], x["flex"][:, None]], 1)
        out["res"][i, :r] = torch.from_numpy(feats.astype(np.float32)); out["res_xyz"][i, :r] = torch.from_numpy(rx)
        out["res_mask"][i, :r] = True
        if len(x["edges"]):
            out["adj"][i, x["edges"][:, 0], x["edges"][:, 1]] = True
        out["incidence"][i, np.arange(r), x["segments"]] = 1.0
    return out


def run_epoch(model, items, opt, rng, train):
    order = rng.permutation(len(items)) if train else np.arange(len(items))
    tot, cnt = 0.0, 0
    model.train(train)
    for s in range(0, len(items), BATCH):
        batch = [items[i] for i in order[s:s + BATCH]]
        rots = [random_rotation(rng) for _ in batch] if train else None
        b = collate(batch, rots)
        with torch.set_grad_enabled(train):
            pred, lv = model(b)
            loss = nll(pred, lv, b["target"], b["lig_mask"].float())
        if train:
            opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach()) * len(batch); cnt += len(batch)
    return tot / cnt


@torch.no_grad()
def predict(model, items, pp, rots=None):
    model.eval()
    out = []
    for s in range(0, len(items), BATCH):
        batch = items[s:s + BATCH]
        b = collate(batch, rots[s:s + BATCH] if rots is not None else None)
        pred, lv = model(b)
        for i, x in enumerate(batch):
            n = len(x["lig"])
            out.append({"pred": (pred[i, :n].numpy() * pp["coord_scale"]).astype(np.float32),
                        "logvar": lv[i, :n].numpy().astype(np.float32)})
    return out


def main():
    feats, outdir, arch, seed = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    os.makedirs(outdir, exist_ok=True)
    data = pickle.load(open(feats, "rb"))
    pp = fit_preprocessing(data)
    items = [prepare(d, pp) for d in data]
    idx = {s: [i for i, d in enumerate(data) if d["split"] == s] for s in ("train", "val", "test", "external")}
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    model = PoseCorrector(arch)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    tr, va = [items[i] for i in idx["train"]], [items[i] for i in idx["val"]]
    best, best_state, wait, hist = 1e18, None, 0, []
    t0 = time.time()
    for ep in range(EPOCHS):
        tl = run_epoch(model, tr, opt, rng, True)
        vl = run_epoch(model, va, None, rng, False)
        hist.append({"epoch": ep + 1, "train_nll": tl, "val_nll": vl})
        if vl < best:
            best, best_state, wait = vl, {k: v.clone() for k, v in model.state_dict().items()}, 0
        else:
            wait += 1
            if wait >= PATIENCE:
                break
    model.load_state_dict(best_state)
    preds = {}
    for s, ids in idx.items():
        p = predict(model, [items[i] for i in ids], pp)
        for i, o in zip(ids, p):
            preds[data[i]["pdb"]] = o
    torch.save(model.state_dict(), f"{outdir}/{arch}_s{seed}.pt")
    pickle.dump({"arch": arch, "seed": seed, "preprocessing": pp, "history": hist, "best_val_nll": best,
                 "seconds": time.time() - t0, "predictions": preds}, open(f"{outdir}/{arch}_s{seed}.pkl", "wb"))
    print(arch, seed, "best val nll", round(best, 4), "epochs", len(hist), "time", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
