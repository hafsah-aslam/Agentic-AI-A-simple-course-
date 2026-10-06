# Figure 9 of the paper (fig13_scale.pdf): scalability: snapshot construction time and admission latency.
# Reads results/scale.json; writes figures/fig13_scale.pdf and figures/fig13_scale_300dpi.png.
# Run from anywhere: python3 code/figures/fig9_scale.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, NullLocator

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig13_scale"
FS = 10.0

# ---- data: read results/scale.json if present, else the values reported in the paper ----
p = next((d / "results" / "scale.json" for d in [ROOT]
          if (d / "results" / "scale.json").exists()), None)
WL = {"delta": "delta-only (DELETE transaction by key)", "multi": "multi-statement (2 transaction deletes)",
      "mixed": "mixed (DELETE account, cascades)"}
if p:
    pts = json.loads(p.read_text())["points"]
    ROWS = [q["rows"] for q in pts]
    SNAP = [q["snapshot_s"] for q in pts]
    LAT = {(k, mode): [q[f"{mode}|{w}|p50_ms"] for q in pts] for k, w in WL.items() for mode in ("extended", "off")}
else:
    ROWS = [9008, 96008, 1020008, 4080008]
    SNAP = [0.0232, 0.1214, 1.3769, 5.8202]
    LAT = {("delta", "extended"): [0.432, 0.488, 0.414, 0.393], ("delta", "off"): [1.374, 5.626, 30.28, 100.31],
           ("multi", "extended"): [0.412, 0.491, 0.443, 0.445], ("multi", "off"): [1.621, 5.411, 30.26, 100.86],
           ("mixed", "extended"): [5.544, 25.23, 245.15, 877.62], ("mixed", "off"): [4.366, 25.63, 248.13, 935.72]}
SNAP_MS = [s * 1000 for s in SNAP]                         # snapshot time in ms, so everything shares one axis

INK, BLUE, PURPLE, GREEN, GREY = "#222222", "#1f5fbf", "#7b3fa0", "#4daf4a", "#555555"
mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": FS, "axes.labelsize": FS,
    "xtick.labelsize": FS - 0.5, "ytick.labelsize": FS - 0.5, "legend.fontsize": FS - 1.5,
    "axes.edgecolor": "#666666", "axes.labelcolor": INK, "xtick.color": "#444444", "ytick.color": "#444444",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": True, "axes.spines.bottom": True,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
def rows_label(r):  return f"{r/1e6:.1f}M" if r >= 1e6 else f"{r/1e3:.0f}k"
def plain(v, _):    return f"{v:g}"

fig, ax = plt.subplots(figsize=(4.2, 3.0))

# snapshot construction (one-off cost): black dash-dot line with diamonds
ax.plot(ROWS, SNAP_MS, color=INK, marker="D", ms=4.5, lw=1.6, ls="-.", zorder=3)
for r_, s_ in zip(ROWS, SNAP):                            # snapshot times written above each point, in seconds
    ax.annotate(f"{s_:.2f} s", (r_, s_ * 1000), xytext=(0, 9), textcoords="offset points",
                ha="center", va="bottom", fontsize=FS - 1.0, color=INK)
# admission latency: colour = workload, solid = static path (extended analyzer), dotted = shadow only
style = {"delta": (BLUE, "o", 5.0, "full"), "multi": (PURPLE, "s", 4.0, "none"), "mixed": (GREEN, "^", 4.5, "full")}
for k, (col, mk, ms, fill) in style.items():
    kw = dict(color=col, marker=mk, ms=ms, fillstyle=fill, mew=1.1, zorder=3)
    ax.plot(ROWS, LAT[(k, "extended")], ls="-", lw=1.6, **kw)
    ax.plot(ROWS, LAT[(k, "off")], ls=(0, (1.2, 1.4)), lw=1.6, **kw)

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_ylim(0.2, 30000); ax.set_yticks([1, 10, 100, 1000, 10000])
ax.yaxis.set_major_formatter(FuncFormatter(plain)); ax.yaxis.set_minor_locator(NullLocator())
ax.set_ylabel("time (ms)")
ax.set_xlim(ROWS[0] / 1.6, ROWS[-1] * 3.2)
ax.set_xticks(ROWS, [rows_label(r) for r in ROWS]); ax.xaxis.set_minor_locator(NullLocator())
ax.set_xlabel("database rows")

# speed-up at the largest size (delta-only: shadow only vs static path)
r_last = ROWS[-1]; s_fast, s_slow = LAT[("delta", "extended")][-1], LAT[("delta", "off")][-1]
ax.annotate("", xy=(r_last * 1.3, s_fast), xytext=(r_last * 1.3, s_slow), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.8))
ax.text(r_last * 1.45, (s_fast * s_slow) ** 0.5, f"≈{s_slow / s_fast:.0f}×", va="center", fontsize=FS - 0.5, color=INK)

# legend: colours = what is measured, line style = verification path
handles = [Line2D([], [], color=INK, marker="D", ms=4.5, lw=1.6, ls="-.", label="snapshot build"),
           Line2D([], [], color=BLUE, marker="o", ms=5, lw=1.6, label="delta-only"),
           Line2D([], [], color=PURPLE, marker="s", ms=4, fillstyle="none", mew=1.1, lw=1.6, label="multi-statement"),
           Line2D([], [], color=GREEN, marker="^", ms=4.5, lw=1.6, label="mixed (cascades)"),
           Line2D([], [], color=GREY, lw=1.6, ls="-", label="static path"),
           Line2D([], [], color=GREY, lw=1.6, ls=(0, (1.2, 1.4)), label="shadow only")]
leg = fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.55, ax.get_position().y1 + 0.01), ncol=3,
                 handlelength=2.0, handletextpad=0.4, columnspacing=0.9)

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)
print("saved", (OUT / f"{NAME}.pdf").resolve(), "and", (OUT / f"{NAME}_{DPI}dpi.png").resolve())

# ---- checks: text overlapping text, text covering the plotted points ----
fig.canvas.draw(); r = fig.canvas.get_renderer()
texts = [t for t in [ax.xaxis.label, ax.yaxis.label, *ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels()]
         if t.get_text() and t.get_visible() and ax.get_window_extent(r).expanded(1.3, 1.3).overlaps(t.get_window_extent(r))] + list(leg.get_texts())
boxes = [(t.get_text(), t.get_window_extent(r)) for t in texts]
clash = [(a, b) for i, (a, A) in enumerate(boxes) for b, B in boxes[i + 1:] if A.overlaps(B)]
P = np.vstack([ax.transData.transform(np.c_[l.get_xdata(), l.get_ydata()]) for l in ax.get_lines() if len(l.get_xdata())])
hit = [t.get_text() for t in ax.texts if np.any([t.get_window_extent(r).contains(x, y) for x, y in P])]
print("overlapping labels:", clash or "none")
print("labels covering data points:", hit or "none")
