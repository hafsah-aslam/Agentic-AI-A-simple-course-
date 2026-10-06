# Figure 5 of the paper (fig10_baselines.pdf): InvariantGuard against the baselines: F1 with 95% CI and errors by type.
# Reads results/admission.json; writes figures/fig10_baselines.pdf and figures/fig10_baselines_300dpi.png.
# Run from anywhere: python3 code/figures/fig5_baselines.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig10_baselines"
FS = 10.0

# ---- data: read results/admission.json if present, else the values reported in the paper ----
p = next((d / "results" / "admission.json" for d in [ROOT]
          if (d / "results" / "admission.json").exists()), None)
if p:
    adm = json.loads(p.read_text()); b = adm["baselines"]
    D = {"ig": adm["paper"], "est": b["estimate_admission"], "abac": b["abac"],
         "kw": b["keyword_guardrail"], "none": b["no_verification"]}
else:
    D = {"ig":   dict(f1=0.9395, f1_ci=[0.9038, 0.9692], admitted_unsafe=0,   safe_blocked=0),
         "est":  dict(f1=0.4056, f1_ci=[0.2937, 0.5029], admitted_unsafe=85,  safe_blocked=0),
         "abac": dict(f1=0.5145, f1_ci=[0.4467, 0.5793], admitted_unsafe=34,  safe_blocked=117),
         "kw":   dict(f1=0.4007, f1_ci=[0.3514, 0.4524], admitted_unsafe=0,   safe_blocked=341),
         "none": dict(f1=0.0,    f1_ci=[0.0, 0.0],       admitted_unsafe=114, safe_blocked=0)}
ROWS = [("ig", "InvariantGuard", "#0348BC"), ("est", "Estimate admission", "#F09837"),
        ("abac", "ABAC", "#7030A0"), ("kw", "Keyword guardrail", "#7CBF33"),
        ("none", "No verification", "#9a9a9a")]
RED, ORANGE, GREY, INK = "#C00000", "#F09837", "#404040", "#222222"

have = {f.name for f in font_manager.fontManager.ttflist}
SERIF = next((f for f in ["Cambria", "Liberation Serif", "Times New Roman", "DejaVu Serif"] if f in have), "serif")
mpl.rcParams.update({
    "font.family": SERIF, "font.size": FS, "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": GREY, "axes.linewidth": 1.0,
    "xtick.color": GREY, "ytick.color": INK, "xtick.labelsize": FS - 1.0, "ytick.labelsize": FS,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "legend.fontsize": FS - 1.0, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})

# one figure, one set of rows; F1 on the left, errors on the right, method names written once
fig, (ax, bx) = plt.subplots(1, 2, figsize=(4.6, 1.9), sharey=True, gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.08})
y = np.arange(len(ROWS))

# left: F1 with 95% bootstrap interval
for i, (k, name, col) in enumerate(ROWS):
    f1 = D[k]["f1"]; lo, hi = D[k]["f1_ci"]
    ax.barh(i, f1, height=0.62, color=col, zorder=2)
    if f1 > 0:
        ax.errorbar(f1, i, xerr=[[f1 - lo], [hi - f1]], fmt="none", ecolor="black", elinewidth=1.0, capsize=2.5, zorder=3)
    ax.text(max(hi, f1) + 0.03, i, f"{f1:.3f}", va="center", ha="left", fontsize=FS - 1.0, color=GREY)
ax.set_yticks(y, [r[1] for r in ROWS]); ax.tick_params(axis="y", length=0)
ax.set_ylim(len(ROWS) - 0.5, -0.5)
ax.set_xlim(0, 1.25); ax.set_xticks([0, 0.5, 1.0], ["0", "0.5", "1"]); ax.grid(axis="y", visible=False)
ax.set_title("F1 (95% CI)", fontsize=FS, pad=4)
ax.get_yticklabels()[0].set_fontweight("bold")

# right: errors by type, two thin bars per method
h = 0.34
ua = [D[k]["admitted_unsafe"] for k, *_ in ROWS]; sb = [D[k]["safe_blocked"] for k, *_ in ROWS]
bx.barh(y - h / 2, ua, height=h, color=RED, zorder=2)
bx.barh(y + h / 2, sb, height=h, color=ORANGE, zorder=2)
for i in range(len(ROWS)):
    if ua[i] == 0 and sb[i] == 0:                         # both zero (InvariantGuard): one label, no stacking
        bx.text(6, i, "0 / 0", va="center", ha="left", fontsize=FS - 2.0, color=GREY)
        continue
    for yy, v in ((i - h / 2, ua[i]), (i + h / 2, sb[i])):
        bx.text(v + 6, yy, f"{v}", va="center", ha="left", fontsize=FS - 2.0, color=GREY)
bx.set_xlim(0, 420); bx.set_xticks([0, 100, 200, 300, 400]); bx.grid(axis="y", visible=False)
bx.tick_params(axis="y", length=0, labelleft=False)
bx.set_title("Errors (records)", fontsize=FS, pad=4)
bx.legend(handles=[Patch(color=RED, label="unsafe admitted"), Patch(color=ORANGE, label="safe blocked")],
          loc="upper right", handlelength=1.0, handleheight=0.8, handletextpad=0.35, borderaxespad=0.1)

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)
print("saved", (OUT / f"{NAME}.pdf").resolve(), "and", (OUT / f"{NAME}_{DPI}dpi.png").resolve())

# ---- check: no two texts overlap, and no number sits on a bar of another series ----
fig.canvas.draw(); r = fig.canvas.get_renderer()
T = [t for a in (ax, bx) for t in [a.title, *a.texts, *a.get_xticklabels(), *a.get_yticklabels()]
     if t.get_text() and t.get_visible()] + list(bx.get_legend().get_texts())
B = [(t.get_text(), t.get_window_extent(r)) for t in T]
clash = [(a, b) for k, (a, A) in enumerate(B) for b, C in B[k + 1:] if A.overlaps(C)]
lb = bx.get_legend().get_window_extent(r)
clash += [("legend", t.get_text()) for t in bx.texts + list(bx.patches) if hasattr(t, "get_text") and t.get_window_extent(r).overlaps(lb)]
clash += [("legend", "bar") for pch in bx.patches if pch.get_width() > 0 and pch.get_window_extent(r).overlaps(lb)]
print("overlapping texts:", clash or "none")
