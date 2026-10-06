# Figure 7 of the paper (fig05_static.pdf): static discharge under the original (a) and extended (b) analyzer.
# Reads results/admission.json; writes figures/fig05_static.pdf and figures/fig05_static_300dpi.png.
# Run from anywhere: python3 code/figures/fig7_static_discharge.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig05_static"
FS = 10.0

# ---- data: read results/admission.json if present, else the values reported in the paper ----
p = next((d / "results" / "admission.json" for d in [ROOT]
          if (d / "results" / "admission.json").exists()), None)
if p:
    adm = json.loads(p.read_text())
    PAPER, EXT = adm["static_breakdown_paper"], adm["static_breakdown_extended"]
else:
    PAPER = {"not-static-class": 260, "scope-containment": 117, "action-scoped": 75}
    EXT = {"point/structural": 194, "cleared": 75, "op-needs-shadow": 66, "threshold": 60,
           "lower-bound": 33, "frame": 23, "cleared-sum": 1}

# labels on one line each (horizontal bars leave room for them)
LAB_A = {"not-static-class": "point / structural", "scope-containment": "scope containment",
         "action-scoped": "action-scoped"}
LAB_B = {"point/structural": "point / structural", "cleared": "bound ≤ θ", "op-needs-shadow": "needs shadow",
         "threshold": "bound > θ", "lower-bound": "lower bound", "frame": "frame rule", "cleared-sum": "summed bound"}
RED, ORANGE, GREEN, PURPLE, INK = "#b2182b", "#e8710a", "#4daf4a", "#7b3fa0", "#222222"
def outcome_colour(k):
    if k in ("cleared", "cleared-sum", "frame"): return GREEN     # decided statically: satisfied
    if k == "lower-bound":                       return PURPLE    # decided statically: violated
    return ORANGE                                                 # needs shadow execution

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": FS, "axes.labelsize": FS,
    "xtick.labelsize": FS - 0.5, "ytick.labelsize": FS - 0.5, "legend.fontsize": FS - 1.0,
    "axes.edgecolor": "#666666", "axes.labelcolor": INK, "xtick.color": "#444444", "ytick.color": "#222222",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": True, "axes.spines.bottom": True,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})

# rows from top to bottom: group header (a), its 3 bars, a gap, group header (b), its 7 bars
A = sorted(PAPER.items(), key=lambda kv: -kv[1]); B = sorted(EXT.items(), key=lambda kv: -kv[1])
rows = [("hdr", "(a) Original analyzer", 0, None)] + [("bar", LAB_A[k], v, RED) for k, v in A] \
     + [("gap", "", 0, None), ("hdr", "(b) Extended analyzer", 0, None)] \
     + [("bar", LAB_B[k], v, outcome_colour(k)) for k, v in B]
y = np.arange(len(rows))

fig, ax = plt.subplots(figsize=(4.2, 3.9))
XMAX = 300
for yy, (kind, lab, v, col) in zip(y, rows):
    if kind == "bar":
        ax.barh(yy, v, height=0.68, color=col, zorder=2)
        ax.text(v + XMAX * 0.012, yy, f"{v}", va="center", ha="left", fontsize=FS - 1.0, color=INK)
    elif kind == "hdr":
        ax.text(-0.02, yy, lab, transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=FS, fontweight="bold", color=INK)
ax.set_yticks([yy for yy, r in zip(y, rows) if r[0] == "bar"], [r[1] for r in rows if r[0] == "bar"])
ax.tick_params(axis="y", length=0, pad=4)
ax.set_ylim(len(rows) - 0.4, -0.6)
ax.set_xlim(0, XMAX); ax.set_xticks([0, 100, 200, 300]); ax.grid(axis="y", visible=False)
ax.set_xlabel("selected pairs (452 per analyzer)")
ax.axhline(y[rows.index(("gap", "", 0, None))], color="#999999", lw=0.6, ls=(0, (3, 2)))   # separates (a) and (b)

leg = fig.legend(handles=[Patch(color=RED, label="not discharged"), Patch(color=GREEN, label="static: satisfied"),
                          Patch(color=PURPLE, label="static: violated"), Patch(color=ORANGE, label="to shadow")],
                 loc="lower center", bbox_to_anchor=(0.5, ax.get_position().y1 + 0.005), ncol=2,
                 handlelength=1.0, handleheight=0.8, handletextpad=0.35, columnspacing=1.0)

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)
print("saved", (OUT / f"{NAME}.pdf").resolve(), "and", (OUT / f"{NAME}_{DPI}dpi.png").resolve())

# ---- check: no two texts overlap ----
fig.canvas.draw(); r = fig.canvas.get_renderer()
T = [t for t in [ax.xaxis.label, *ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels()]
     if t.get_text() and t.get_visible()] + list(leg.get_texts())
Bx = [(t.get_text(), t.get_window_extent(r)) for t in T]
clash = [(a, b) for k, (a, A_) in enumerate(Bx) for b, C in Bx[k + 1:] if A_.overlaps(C)]
lb = leg.get_window_extent(r)
clash += [("legend", t) for t, Bb in Bx if t not in [x.get_text() for x in leg.get_texts()] and Bb.overlaps(lb)]
print("overlapping texts:", clash or "none")
