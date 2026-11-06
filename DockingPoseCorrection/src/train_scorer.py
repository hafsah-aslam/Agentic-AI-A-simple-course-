"""RescueDock learned 3D pose scorer (experiment 3): rank Vina's poses by predicted closeness to native.

A rotation/translation-invariant message-passing GNN (SchNet-style continuous-filter convolutions on
interatomic distances) over the protein-pocket + ligand-pose atom graph. For each complex it scores all Vina
poses and is trained, per complex, to put the highest score on the lowest-RMSD pose (listwise softmax toward the
best pose) plus a regression term to the (capped) RMSD. Selection = argmax score. Plain PyTorch only: no
torch-geometric / torch-scatter, so it runs in the existing dpc-diffdock env.

Train on split=train, pick the epoch on val, report test + external with the same Vina/oracle references as the
oracle study. Prints success %, captured headroom, mean/median selected RMSD.

Usage:
  python3 src/train_scorer.py --graphs DPC_WORK/graphs --out DPC_WORK/scorer --epochs 40 [--cpu]
"""
import argparse, glob, os, math, json, random
import numpy as np
import torch
import torch.nn as nn

NELEM = 10            # must match export_graphs.py
CUTOFF = 5.0         # A, edge cutoff
N_RBF = 16


# ---------------- data ----------------
class Complex:
    __slots__ = ("pdb", "split", "poc_xyz", "poc_elem", "lig_xyz", "lig_elem", "rmsd")

    def __init__(self, z):
        self.pdb = str(z["pdb"]); self.split = str(z["split"])
        self.poc_xyz = torch.tensor(z["poc_xyz"], dtype=torch.float32)
        self.poc_elem = torch.tensor(z["poc_elem"].astype(np.int64))
        self.lig_xyz = torch.tensor(z["lig_xyz"], dtype=torch.float32)   # (P,L,3)
        self.lig_elem = torch.tensor(z["lig_elem"].astype(np.int64))
        self.rmsd = torch.tensor(z["rmsd"], dtype=torch.float32)         # (P,)


def load(graphs):
    out = {"train": [], "val": [], "test": [], "external": []}
    for f in sorted(glob.glob(os.path.join(graphs, "*.npz"))):
        z = np.load(f, allow_pickle=True)
        c = Complex(z)
        if torch.isnan(c.rmsd).all() or c.lig_xyz.shape[0] == 0:
            continue
        if c.split in out:
            out[c.split].append(c)
    return out


def build_pose_graph(c, p):
    """Nodes = ligand atoms of pose p + pocket atoms. Returns elem(N), xyz(N,3), is_lig(N), lig_mask indices."""
    lx, le = c.lig_xyz[p], c.lig_elem
    xyz = torch.cat([lx, c.poc_xyz], 0)
    elem = torch.cat([le, c.poc_elem], 0)
    L = lx.shape[0]
    is_lig = torch.zeros(xyz.shape[0]); is_lig[:L] = 1.0
    return elem, xyz, is_lig, L


def edges_within(xyz, cutoff):
    d = torch.cdist(xyz, xyz)
    mask = (d < cutoff) & (d > 1e-6)
    idx = mask.nonzero(as_tuple=False)
    return idx[:, 0], idx[:, 1], d[mask]


def rbf(dist, n=N_RBF, cutoff=CUTOFF):
    centers = torch.linspace(0, cutoff, n, device=dist.device)
    width = cutoff / n
    return torch.exp(-((dist[:, None] - centers[None, :]) ** 2) / (2 * width ** 2))


# ---------------- model ----------------
class Interaction(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.filt = nn.Sequential(nn.Linear(N_RBF, dim), nn.SiLU(), nn.Linear(dim, dim))
        self.pre = nn.Linear(dim, dim)
        self.post = nn.Sequential(nn.Linear(dim, dim), nn.SiLU(), nn.Linear(dim, dim))

    def forward(self, h, src, dst, edge_rbf):
        m = self.pre(h)[src] * self.filt(edge_rbf)          # continuous-filter conv
        agg = torch.zeros_like(h).index_add_(0, dst, m)
        return h + self.post(agg)


class PoseScorer(nn.Module):
    def __init__(self, dim=96, layers=4):
        super().__init__()
        self.embed = nn.Embedding(NELEM, dim)
        self.islig = nn.Linear(1, dim)
        self.inter = nn.ModuleList([Interaction(dim) for _ in range(layers)])
        self.head = nn.Sequential(nn.Linear(dim, dim), nn.SiLU(), nn.Linear(dim, 1))

    def forward(self, elem, xyz, is_lig, L):
        h = self.embed(elem) + self.islig(is_lig[:, None])
        src, dst, dist = edges_within(xyz, CUTOFF)
        er = rbf(dist)
        for layer in self.inter:
            h = layer(h, src, dst, er)
        lig_h = h[:L].mean(0)                                # pool ligand atoms only
        return self.head(lig_h).squeeze(-1)                 # scalar score


# ---------------- train / eval ----------------
def score_complex(model, c, device):
    scores = []
    for p in range(c.lig_xyz.shape[0]):
        if torch.isnan(c.rmsd[p]):
            scores.append(torch.tensor(-1e9, device=device)); continue
        elem, xyz, is_lig, L = build_pose_graph(c, p)
        scores.append(model(elem.to(device), xyz.to(device), is_lig.to(device), L))
    return torch.stack(scores)


def complex_loss(scores, rmsd):
    valid = ~torch.isnan(rmsd)
    s, r = scores[valid], rmsd[valid]
    if s.numel() < 2:
        return None
    target = torch.argmin(r)                                 # best pose
    rank_loss = nn.functional.cross_entropy(s[None, :], target[None].to(s.device))  # listwise softmax
    reg_loss = nn.functional.mse_loss(s, -torch.clamp(r, max=6.0).to(s.device))     # score ~ -rmsd
    return rank_loss + 0.1 * reg_loss


def evaluate(model, data, device):
    model.eval()
    res = {}
    with torch.no_grad():
        for split in ["val", "test", "external"]:
            succ = vina = oracle = n = 0; sels = []
            for c in data[split]:
                r = c.rmsd.numpy()
                valid = ~np.isnan(r)
                if valid.sum() == 0:
                    continue
                s = score_complex(model, c, device).cpu().numpy()
                pick = int(np.nanargmax(np.where(valid, s, -1e9)))
                sel = r[pick]
                sels.append(sel); succ += sel < 2.0
                vina += (r[0] < 2.0) if valid[0] else (r[np.where(valid)[0][0]] < 2.0)
                oracle += np.nanmin(r) < 2.0; n += 1
            cap = 100 * (succ - vina) / (oracle - vina) if oracle > vina else float("nan")
            res[split] = dict(n=n, vina=100 * vina / n, selector=100 * succ / n, oracle=100 * oracle / n,
                              captured=cap, mean_rmsd=float(np.mean(sels)), med_rmsd=float(np.median(sels)))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graphs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--dim", type=int, default=96)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cpu", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    torch.manual_seed(a.seed); np.random.seed(a.seed); random.seed(a.seed)
    device = "cpu" if a.cpu or not torch.cuda.is_available() else "cuda"
    data = load(a.graphs)
    print({k: len(v) for k, v in data.items()}, "device:", device)

    model = PoseScorer(a.dim, a.layers).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr, weight_decay=1e-5)
    best_val, best_state = -1, None
    for ep in range(a.epochs):
        model.train(); random.shuffle(data["train"]); tot = nb = 0
        opt.zero_grad()
        for i, c in enumerate(data["train"]):
            scores = score_complex(model, c, device)
            loss = complex_loss(scores, c.rmsd.to(device))
            if loss is None:
                continue
            (loss / 8).backward(); tot += float(loss.detach()); nb += 1
            if (i + 1) % 8 == 0:                              # gradient accumulation = batch of 8 complexes
                opt.step(); opt.zero_grad()
        opt.step(); opt.zero_grad()
        res = evaluate(model, data, device)
        v = res["val"]["selector"]
        print(f"ep{ep:02d} loss={tot/max(nb,1):.3f} | val sel={v:.1f}% (vina {res['val']['vina']:.1f}, orc {res['val']['oracle']:.1f}) "
              f"| test sel={res['test']['selector']:.1f}% | ext sel={res['external']['selector']:.1f}%")
        if v > best_val:
            best_val = v; best_state = {k: t.cpu().clone() for k, t in model.state_dict().items()}
            torch.save(best_state, os.path.join(a.out, "scorer_best.pt"))
    model.load_state_dict(best_state)
    final = evaluate(model, data, device)
    json.dump(final, open(os.path.join(a.out, "scorer_results.json"), "w"), indent=2)
    print("\n== BEST MODEL (selected on val) ==")
    print(f"{'split':<10}{'n':>5}{'Vina':>9}{'RescueDock':>12}{'Oracle':>9}{'captured':>11}{'mean':>8}{'med':>7}")
    for s in ["val", "test", "external"]:
        d = final[s]
        print(f"{s:<10}{d['n']:>5}{d['vina']:>8.1f}%{d['selector']:>11.1f}%{d['oracle']:>8.1f}%{d['captured']:>10.1f}%{d['mean_rmsd']:>8.2f}{d['med_rmsd']:>7.2f}")


if __name__ == "__main__":
    main()
