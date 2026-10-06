# Figure 6 of the paper (fig04_ablation_heatmap.pdf): cascade ablation, reintroduced defects, and tau_b sweep (heat-map table).
# Reads results/admission.json; writes figures/fig04_ablation_heatmap.pdf and figures/fig04_ablation_heatmap_300dpi.png.
# Run from anywhere: python3 code/figures/fig6_ablation_heatmap.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json, sys
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig04_ablation_heatmap"
VAL_FS, DELTA_FS, LABEL_FS, HEAD_FS, NOTE_FS = 11.0, 9.0, 10.5, 9.8, 8.5
FIG_W, FIG_H = 4.3, 2.75                                  # wider and a little shorter than before (3.4 x 2.95)

CFGS = [("paper", r"Full system ($\tau_b$ = 70)"),
        ("ablation_no_cascade", "No cascade closure"),
        ("defect_statement_scope", "Statement-scope decl."),
        ("defect_cross_relation", "Cross-relation bounds"),
        ("defect_no_vacuity", "No vacuity rule"),
        ("defect_all", "All four defects"),
        ("tau80", r"Block threshold $\tau_b$ = 80"),
        ("tau90", r"Block threshold $\tau_b$ = 90")]
GROUP_BREAK = 6                                           # dashed line between defect rows and threshold rows
METRICS = [("containment", "Containment", "Blues"), ("decisiveness", "Decisiveness", "Reds"),
           ("friction", "Friction", "Oranges")]

# ---- data: read results/admission.json if present, else the values reported in the paper ----
p = next((d / "results" / "admission.json" for d in [ROOT]
          if (d / "results" / "admission.json").exists()), None)
if p:
    adm = json.loads(p.read_text())
    adm["tau80"], adm["tau90"] = adm["tau_sweep"]["80"], adm["tau_sweep"]["90"]
    V = {c: {m: adm[c][m] for m, *_ in METRICS} for c, _ in CFGS}
else:
    V = {"paper":                  dict(containment=1.000, decisiveness=0.886, friction=0.587),
         "ablation_no_cascade":    dict(containment=0.991, decisiveness=0.649, friction=0.645),
         "defect_statement_scope": dict(containment=0.921, decisiveness=0.807, friction=0.587),
         "defect_cross_relation":  dict(containment=0.868, decisiveness=0.754, friction=0.587),
         "defect_no_vacuity":      dict(containment=1.000, decisiveness=0.886, friction=0.000),
         "defect_all":             dict(containment=0.658, decisiveness=0.544, friction=0.000),
         "tau80":                  dict(containment=1.000, decisiveness=0.860, friction=0.587),
         "tau90":                  dict(containment=1.000, decisiveness=0.772, friction=0.587)}

INK = "#222222"
mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": LABEL_FS, "pdf.fonttype": 42, "ps.fonttype": 42,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.02})

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
nr, nc = len(CFGS), len(METRICS)
for j, (m, title, cmap) in enumerate(METRICS):
    cm = mpl.colormaps[cmap]
    full = V["paper"][m]
    for i, (c, _) in enumerate(CFGS):
        v = V[c][m]
        face = cm(0.12 + 0.68 * v)                          # same 0–1 scale in every column
        ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=face, edgecolor="white", lw=2))
        lum = 0.2126 * face[0] + 0.7152 * face[1] + 0.0722 * face[2]
        txt = "white" if lum < 0.5 else INK
        if i == 0:                                          # reference row: value only, centred and bold
            ax.text(j + 0.5, i + 0.52, f"{v:.2f}", ha="center", va="center", fontsize=VAL_FS, color=txt, fontweight="bold")
        else:                                               # value on the left, change on the right
            d = v - full
            ax.text(j + 0.47, i + 0.52, f"{v:.2f}", ha="right", va="center", fontsize=VAL_FS, color=txt)
            ax.text(j + 0.55, i + 0.54, "±0.00" if abs(d) < 0.005 else f"{d:+.2f}", ha="left", va="center",
                    fontsize=DELTA_FS, color=txt, alpha=0.9)
ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
ax.set_xticks(np.arange(nc) + 0.5, [t for _, t, _ in METRICS], fontsize=HEAD_FS, fontweight="bold")
ax.xaxis.tick_top(); ax.tick_params(length=0, pad=3)
ax.set_yticks(np.arange(nr) + 0.5, [n for _, n in CFGS], fontsize=LABEL_FS)
ax.get_yticklabels()[0].set_fontweight("bold")
for s in ax.spines.values(): s.set_visible(False)
ax.axhline(1, color=INK, lw=0.8)                            # separates the reference row
ax.axhline(GROUP_BREAK, color="#888888", lw=0.6, ls=(0, (3, 2)))
ax.text(0, nr + 0.12, "small numbers: change against the full system", fontsize=NOTE_FS, color="#555555", va="top")

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)
print("saved", (OUT / f"{NAME}.pdf").resolve(), "and", (OUT / f"{NAME}_{DPI}dpi.png").resolve())

# ---- check: no two texts overlap, and every number stays inside its box ----
fig.canvas.draw(); r = fig.canvas.get_renderer()
T = [t for t in [*ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels()] if t.get_text()]
B = [(t.get_text(), t.get_window_extent(r)) for t in T]
def ov(A, C):
    w = min(A.x1, C.x1) - max(A.x0, C.x0); h = min(A.y1, C.y1) - max(A.y0, C.y0)
    return min(w, h) * 72 / fig.dpi if w > 0 and h > 0 else 0
clash = [(a, b, round(ov(A, C), 2)) for k, (a, A) in enumerate(B) for b, C in B[k + 1:] if ov(A, C) > 0]
spill = []
for t in ax.texts[:-1]:
    x, y = t.get_position(); j, i = int(x), int(y)
    cell = ax.transData.transform([(j + 0.04, i + 0.96), (j + 0.96, i + 0.04)])
    bb = t.get_window_extent(r)
    if bb.x0 < cell[0][0] or bb.x1 > cell[1][0]: spill.append(t.get_text())
print("overlapping texts:", clash or "none")
print("numbers spilling out of their box:", spill or "none")
