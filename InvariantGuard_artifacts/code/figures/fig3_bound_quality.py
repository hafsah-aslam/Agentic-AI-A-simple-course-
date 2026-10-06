# Figure 3 of the paper (fig06_bound_quality.pdf): certified bounds against optimizer estimates over 800 delete predicates (a: predicted vs. true rows, b: tightness CDF).
# Reads results/bound_quality_rows.jsonl; writes figures/fig06_bound_quality.pdf and figures/fig06_bound_quality_300dpi.png.
# Run from anywhere: python3 code/figures/fig3_bound_quality.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullLocator

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig06_bound_quality"
FS = 10.0          # base text size

rows = [json.loads(x) for x in open(ROOT / "results" / "bound_quality_rows.jsonl")]
data = np.array([[r["true"], r["estimate"], r["bound_mf"], r["bound_pv"]] for r in rows], dtype=float)
N = len(data)
true, est, b_mf, b_pv = data.T
under_est = int((est < true).sum()); under_mf = int((b_mf < true).sum()); under_pv = int((b_pv < true).sum())
pos = true > 0
tight_mf = np.sort(b_mf[pos] / true[pos]); tight_pv = np.sort(b_pv[pos] / true[pos])

BLUE, RED, ORANGE, PURPLE, INK = "#1f5fbf", "#b2182b", "#e8710a", "#7b3fa0", "#222222"
mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": FS, "axes.titlesize": FS, "axes.labelsize": FS,
    "xtick.labelsize": FS - 0.5, "ytick.labelsize": FS - 0.5, "legend.fontsize": FS - 1.0,
    "axes.edgecolor": "#666666", "axes.labelcolor": INK, "xtick.color": "#444444", "ytick.color": "#444444",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": True, "axes.spines.bottom": True,
    "axes.grid": True, "grid.color": "#e9e9e9", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
def plain(v, _): return f"{v:g}" if v < 1e4 else f"{v:.0e}".replace("e+0", "e")

fig, (ax, bx) = plt.subplots(2, 1, figsize=(3.5, 3.8), gridspec_kw={"hspace": 0.62})   # stacked, lower than before

# (a) predicted vs. true affected rows (log–log; zeros drawn at 1)
c = lambda a: np.maximum(1, a)
ax.fill_between([1, 3e4], [0.01, 0.01], [1, 3e4], color=RED, alpha=0.06, lw=0, zorder=0)       # under-prediction zone
ax.plot([1, 3e4], [1, 3e4], color=INK, lw=0.9, zorder=1)
ax.scatter(c(true), c(est),  s=10, color=ORANGE, marker="v", alpha=0.75, lw=0, zorder=3, label="optimizer est.")
ax.scatter(c(true), c(b_mf), s=10, color=BLUE,   marker="o", alpha=0.75, lw=0, zorder=3, label="max-freq. bound")
ax.scatter(c(true), c(b_pv), s=10, color=PURPLE, marker="s", alpha=0.75, lw=0, zorder=3, label="per-value bound")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(1, 3e4); ax.set_ylim(0.01, 1e7)          # strip below 1 holds the zone note, band above 1e5 holds the legend; no data in either
for a_ in (ax.xaxis, ax.yaxis):
    a_.set_major_formatter(FuncFormatter(plain)); a_.set_minor_locator(NullLocator())
ax.set_yticks([1, 100, 1e4]); ax.set_xticks([1, 10, 100, 1e3, 1e4])
ax.set_xlabel("true affected rows"); ax.set_ylabel("predicted rows")
ax.set_title("(a) Predicted vs. true affected rows", pad=5, fontweight="bold")
ax.text(2.8e4, 0.013, f"under-prediction zone\nestimate {under_est}/{N}, certified {under_mf + under_pv}/{N}",
        color=RED, fontsize=FS - 1.5, ha="right", va="bottom", linespacing=1.1)
ax.legend(loc="upper left", markerscale=1.6, handletextpad=0.2, labelspacing=0.25, borderaxespad=0.1,
          fontsize=FS - 1.5, handlelength=1.0)        # top-left corner: no data there

# (b) tightness CDF of the certified bounds
y_mf = np.arange(1, len(tight_mf) + 1) / len(tight_mf); y_pv = np.arange(1, len(tight_pv) + 1) / len(tight_pv)
bx.step(tight_mf, y_mf, where="post", color=BLUE, lw=1.7, label="max-frequency certificate")
bx.step(tight_pv, y_pv, where="post", color=PURPLE, lw=1.7, ls="--", label="per-value certificate")
bx.set_xscale("log"); bx.set_xlim(0.9, 160); bx.set_ylim(0, 1.13)
bx.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}×")); bx.xaxis.set_minor_locator(NullLocator())
bx.set_xticks([1, 2, 5, 10, 20, 100]); bx.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
bx.set_xlabel("tightness  u / A  (always ≥ 1)"); bx.set_ylabel("fraction of predicates")
bx.set_title("(b) Tightness of the certified bounds", pad=5, fontweight="bold")
for t, col in ((tight_mf[-1], BLUE), (tight_pv[-1], PURPLE)):
    bx.text(t, 1.035, f"worst {t:.1f}×", ha="center", va="bottom", fontsize=FS - 1.0, color=col)
bx.legend(loc="lower right", handlelength=2.2, labelspacing=0.3, borderaxespad=0.3)

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)

# ---- checks: text overlapping text, text covering data points ----
fig.canvas.draw(); r = fig.canvas.get_renderer()
texts = [t for a in fig.axes for t in [a.title, a.xaxis.label, a.yaxis.label, *a.texts,
         *a.get_xticklabels(), *a.get_yticklabels(), *(a.get_legend().get_texts() if a.get_legend() else [])] if t.get_text()]
boxes = [(t.get_text(), t.get_window_extent(r)) for t in texts]
clash = [(a, b) for i, (a, A) in enumerate(boxes) for b, B in boxes[i + 1:] if A.overlaps(B)]
fb = fig.bbox
out = [t.get_text() for t in texts if t.get_window_extent(r).x0 < fb.x0 - 40 or t.get_window_extent(r).x1 > fb.x1 + 40]
pts = np.vstack([ax.transData.transform(np.c_[c(true), c(v)]) for v in (est, b_mf, b_pv)])
hit = [t.get_text().split(chr(10))[0] for t in [*ax.texts, *ax.get_legend().get_texts()]
       if np.any([t.get_window_extent(r).contains(x, y) for x, y in pts])]
hitb = [t.get_text().split(chr(10))[0] for t in bx.get_legend().get_texts() + bx.texts
        if any(np.any([t.get_window_extent(r).contains(x, y) for x, y in bx.transData.transform(np.c_[tt, yy])]) for tt, yy in ((tight_mf, y_mf), (tight_pv, y_pv)))]
tA, tB = ax.title.get_window_extent(r), bx.title.get_window_extent(r)
print("overlapping labels:", clash or "none")
print("titles overlap:", tA.overlaps(tB))
print("labels covering data points:", (hit + hitb) or "none")
ab=ax.get_window_extent(r); tb=ax.texts[0].get_window_extent(r)
print("note inside panel (a):", tb.x1 <= ab.x1 and tb.x0 >= ab.x0)
near=[(x,y) for x,y in pts if tb.x0-6<=x<=tb.x1+6 and tb.y0-6<=y<=tb.y1+6]
print("data points within 6 px of the note:", len(near))
