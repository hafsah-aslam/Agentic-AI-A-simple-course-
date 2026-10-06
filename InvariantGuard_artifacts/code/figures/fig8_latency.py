# Figure 8 of the paper (fig09_latency.pdf): median admission latency under concurrency.
# Reads results/concurrency.json; writes figures/fig09_latency.pdf and figures/fig09_latency_300dpi.png.
# Run from anywhere: python3 code/figures/fig8_latency.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json
from pathlib import Path
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig09_latency"

# ---- data: read results/concurrency.json if present, else the values reported in the paper ----
p = next((d / "results" / "concurrency.json" for d in [ROOT]
          if (d / "results" / "concurrency.json").exists()), None)
if p:
    cc = json.loads(p.read_text())
    LAT = {d: [cc["latency"][f"{d}|{k}"]["p50_ms"] for k in (1, 2, 4, 8, 16)] for d in ("separate", "serializable", "witness")}
else:
    LAT = {"separate":     [18.06, 28.26, 36.37, 51.13, 69.00],
           "serializable": [15.65, 18.00, 26.58, 37.34, 67.24],
           "witness":      [17.12, 31.43, 57.00, 120.10, 331.37]}
CLIENTS = [1, 2, 4, 8, 16]

# ---- style ----
mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.labelsize": 7.5,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.8,
    "axes.edgecolor": "#666666", "axes.labelcolor": "#222222", "xtick.color": "#444444", "ytick.color": "#444444",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": True, "axes.spines.bottom": True,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})
STYLE = {  # label, colour, marker, line style
    "separate":     ("separate transactions",       "#1f5fbf", "o", "-"),
    "serializable": ("serializable-through-commit", "#b2182b", "s", "--"),
    "witness":      ("witness-and-revalidate",      "#7b3fa0", "^", "-."),
}

fig, ax = plt.subplots(figsize=(3.4, 1.75))
for d, (lab, col, mk, ls) in STYLE.items():
    ax.plot(CLIENTS, LAT[d], color=col, marker=mk, ls=ls, lw=1.4, ms=3.5, label=lab)
ax.set_xscale("log", base=2); ax.set_xticks(CLIENTS, [str(c) for c in CLIENTS]); ax.minorticks_off()
ax.set_ylim(0, 350); ax.set_yticks([0, 100, 200, 300])
ax.set_xlabel("concurrent agent clients"); ax.set_ylabel("median latency (ms)", labelpad=2)
ax.legend(loc="upper left", handlelength=2.0, handletextpad=0.4, labelspacing=0.35, borderaxespad=0.3)

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)
print("saved", (OUT / f"{NAME}.pdf").resolve(), "and", (OUT / f"{NAME}_{DPI}dpi.png").resolve())
