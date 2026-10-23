"""Confidence-aware pose-correction model: ligand MLP encoder, one of four pocket encoders, distance-biased
cross-attention fusion, a per-atom coordinate-correction head and a per-atom log-variance head."""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

H = 64
LIG_IN = 18 + 3          # atom chemistry + scaled coordinates
RES_IN = 28              # 20 one-hot + CA (3) + side-chain offset (3) + degree + flexibility


def mlp(i, o, h=H):
    return nn.Sequential(nn.Linear(i, h), nn.SiLU(), nn.Linear(h, o))


def masked_softmax(logits, mask):
    logits = logits.masked_fill(~mask, -1e9)
    return torch.softmax(logits, -1)


class MLPEncoder(nn.Module):
    def __init__(self, layers=2):
        super().__init__()
        self.inp = nn.Linear(RES_IN, H)
        self.layers = nn.ModuleList([mlp(H, H) for _ in range(layers)])

    def forward(self, b):
        h = self.inp(b["res"])
        for l in self.layers:
            h = h + l(F.silu(h))
        return h


class GNNEncoder(nn.Module):
    """Distance-weighted message passing over C-alpha contacts (Gilmer et al.)."""
    def __init__(self, layers=2):
        super().__init__()
        self.inp = nn.Linear(RES_IN, H)
        self.msg = nn.ModuleList([mlp(2 * H + 1, H) for _ in range(layers)])
        self.upd = nn.ModuleList([mlp(2 * H, H) for _ in range(layers)])

    def forward(self, b):
        h = self.inp(b["res"])                                    # B,R,H
        d = torch.cdist(b["res_xyz"], b["res_xyz"])               # B,R,R (scaled units)
        adj = b["adj"].float()
        w = adj * torch.exp(-d)                                   # distance weighting
        R = h.shape[1]
        for msg, upd in zip(self.msg, self.upd):
            hi = h.unsqueeze(2).expand(-1, -1, R, -1)
            hj = h.unsqueeze(1).expand(-1, R, -1, -1)
            m = msg(torch.cat([hi, hj, d.unsqueeze(-1)], -1))     # B,R,R,H
            agg = (w.unsqueeze(-1) * m).sum(2) / (adj.sum(2, keepdim=True) + 1)
            h = h + upd(torch.cat([h, agg], -1))
        return h


class HypergraphEncoder(nn.Module):
    """Residue-incidence hypergraph: chain segments are hyperedges; segment attention weighted by flexibility."""
    def __init__(self, layers=2):
        super().__init__()
        self.inp = nn.Linear(RES_IN, H)
        self.att = nn.ModuleList([nn.Linear(H, 1) for _ in range(layers)])
        self.flex_w = nn.Parameter(torch.zeros(layers))
        self.upd = nn.ModuleList([mlp(2 * H, H) for _ in range(layers)])

    def forward(self, b):
        h = self.inp(b["res"])
        inc = b["incidence"]                                      # B,R,S (residue-in-segment)
        flex = b["res"][..., -1]                                  # B,R
        for k, (att, upd) in enumerate(zip(self.att, self.upd)):
            logit = att(h).squeeze(-1) + self.flex_w[k] * flex    # B,R
            a = masked_softmax(logit.unsqueeze(1).expand(-1, inc.shape[2], -1), inc.transpose(1, 2) > 0)  # B,S,R
            seg = a @ h                                           # B,S,H
            back = (inc @ seg) / inc.sum(2, keepdim=True).clamp(min=1)
            h = h + upd(torch.cat([h, back], -1))
        return h


class TransformerEncoder(nn.Module):
    """Self-attention over pocket residues with a learned coordinate (distance) bias."""
    def __init__(self, layers=2, heads=4):
        super().__init__()
        self.inp = nn.Linear(RES_IN, H)
        self.layers = nn.ModuleList([nn.MultiheadAttention(H, heads, batch_first=True) for _ in range(layers)])
        self.ff = nn.ModuleList([mlp(H, H) for _ in range(layers)])
        self.norm1 = nn.ModuleList([nn.LayerNorm(H) for _ in range(layers)])
        self.norm2 = nn.ModuleList([nn.LayerNorm(H) for _ in range(layers)])
        self.bias = nn.Parameter(torch.ones(layers))
        self.heads = heads

    def forward(self, b):
        h = self.inp(b["res"])
        d = torch.cdist(b["res_xyz"], b["res_xyz"])
        pad = ~b["res_mask"]
        for k, (attn, ff) in enumerate(zip(self.layers, self.ff)):
            bias = (-F.softplus(self.bias[k]) * d).masked_fill(pad.unsqueeze(1), -1e9)
            bias = bias.repeat_interleave(self.heads, 0)
            x = self.norm1[k](h)
            h = h + attn(x, x, x, attn_mask=bias, need_weights=False)[0]
            h = h + ff(self.norm2[k](h))
        return h


ENCODERS = {"MLP": MLPEncoder, "GNN": GNNEncoder, "Hypergraph": HypergraphEncoder, "Transformer": TransformerEncoder}


class PoseCorrector(nn.Module):
    def __init__(self, encoder="MLP"):
        super().__init__()
        self.lig = nn.Sequential(nn.Linear(LIG_IN, H), nn.SiLU(), nn.Linear(H, H), nn.SiLU(), nn.Linear(H, H))
        self.pocket = ENCODERS[encoder]()
        self.q, self.k, self.v = nn.Linear(H, H), nn.Linear(H, H), nn.Linear(H, H)
        self.dist_scale = nn.Parameter(torch.tensor(1.0))
        self.fuse = mlp(2 * H, H)
        self.corr = mlp(H, 3)
        self.logvar = mlp(H, 1)

    def forward(self, b):
        hl = self.lig(torch.cat([b["lig"], b["lig_xyz"]], -1))   # B,N,H
        hp = self.pocket(b)                                       # B,R,H
        d = torch.cdist(b["lig_xyz"], b["res_xyz"])               # distance-biased cross-attention
        logits = (self.q(hl) @ self.k(hp).transpose(1, 2)) / math.sqrt(H) - F.softplus(self.dist_scale) * d
        a = masked_softmax(logits, b["res_mask"].unsqueeze(1))
        ctx = a @ self.v(hp)
        z = hl + self.fuse(torch.cat([hl, ctx], -1))
        return self.corr(z), self.logvar(z).squeeze(-1).clamp(-12, 12)


def nll(pred, logvar, target, mask):
    """Heteroscedastic NLL (Eq. 8): 0.5 * mean_i [3 s_i + ||r_i||^2 / exp(s_i)]."""
    r2 = ((pred - target) ** 2).sum(-1)
    per = 0.5 * (3 * logvar + r2 / torch.exp(logvar))
    return (per * mask).sum() / mask.sum()
