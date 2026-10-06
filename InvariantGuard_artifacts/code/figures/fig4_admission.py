# Figure 4 of the paper (fig04_admission_updown.pdf): admission outcomes (a) and evidence behind each decision (b).
# Reads results/admission.json, results/admission_records.jsonl; writes figures/fig04_admission_updown.pdf and figures/fig04_admission_updown_300dpi.png.
# Run from anywhere: python3 code/figures/fig4_admission.py  (or all at once: python3 code/figures/make_paper_figures.py).
import json
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")                                          # write files only, no window
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.transforms import blended_transform_factory

ROOT = Path(__file__).resolve().parents[2]            # package root: results/ in, figures/ out

mpl.rcdefaults()                                          # start from matplotlib defaults
DPI, OUT, NAME = 300, ROOT / "figures", "fig04_admission_updown"

# ---- data: computed from results/ if present, else the values reported in the paper ----
root = next((d for d in [ROOT] if (d / "results" / "admission.json").exists()), None)
if root:
    adm = json.loads((root / "results" / "admission.json").read_text())
    m, pf = adm["paper"], adm["per_fixture_paper"]
    full = [f for f, x in pf.items() if not x["development"]]
    part = [f for f, x in pf.items() if x["development"]]
    RATES = [(m["contained"], m["unsafe"]), (m["blocked"], m["unsafe"]), (m["safe_escalated"], m["safe"]),
             (sum(pf[f]["safe_escalated"] for f in full), sum(pf[f]["safe"] for f in full)),
             (sum(pf[f]["safe_escalated"] for f in part), sum(pf[f]["safe"] for f in part))]
    recs = [json.loads(x) for x in open(root / "results" / "admission_records.jsonl")]
    EVID = {}
    for cfg in ("paper", "extended"):
        rr = [x for x in recs if x["config"] == cfg]
        st = lambda x: any(e["path"] in ("static", "frame") for e in x["evidence"])
        EVID[cfg] = [sum(x["empty_selection"] for x in rr),
                     sum(not x["empty_selection"] and not x["shadow_used"] for x in rr),
                     sum(not x["empty_selection"] and x["shadow_used"] and st(x) for x in rr),
                     sum(not x["empty_selection"] and x["shadow_used"] and not st(x) for x in rr)]
else:
    RATES = [(114, 114), (101, 114), (200, 341), (0, 103), (200, 238)]
    EVID = {"paper": [200, 0, 0, 255], "extended": [200, 53, 65, 137]}

BLUE, RED, ORANGE, GREEN, PURPLE, INK = "#1f5fbf", "#b2182b", "#e8710a", "#4daf4a", "#7b3fa0", "#222222"
FS = 8.0
mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": FS, "axes.labelsize": FS,
    "xtick.labelsize": FS - 0.5, "ytick.labelsize": FS, "legend.fontsize": FS - 0.5,
    "axes.edgecolor": "#666666", "axes.labelcolor": INK, "xtick.color": "#333333", "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": True, "axes.spines.bottom": True,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})

fig, ax = plt.subplots(figsize=(3.0, 3.4))
hdr = blended_transform_factory(ax.transAxes, ax.transData)   # x in axes units, y in rows

# (a) admission rates: one bar per measure, label "a/n (rate)" at the bar end
YA = np.arange(5)
ORDER = [0, 1, 2, 3, 4]                                  # paper order
RATES = [RATES[i] for i in ORDER]
names = [["Containment", "Decisiveness", "Friction (all)", "Friction (full cov.)", "Friction (partial)"][i] for i in ORDER]
cols = [[BLUE, RED, ORANGE, GREEN, ORANGE][i] for i in ORDER]
VAL = []
for y, (a, n), col in zip(YA, RATES, cols):
    ax.barh(y, a / n, height=0.74, color=col, zorder=2)
    VAL.append(ax.text(a / n - 0.02, y, f"{a}/{n} ({a / n:.1%})", ha="right", va="center",
                       fontsize=FS, color="white", fontweight="bold", zorder=3))
ax.text(0.0, -0.9, "(a) Admission (455 resolved records)", transform=hdr, ha="left", va="center",
        fontsize=FS, fontweight="bold", color=INK)

# separator between the two parts
SEP = 4.7
ax.axhline(SEP, color="#999999", lw=0.8, ls=(0, (4, 3)), zorder=1)

# (b) evidence behind each decision: each analyzer's 455 records as one stacked bar (share of records)
ax.text(0.0, SEP + 0.55, "(b) Evidence behind each decision", transform=hdr, ha="left", va="center",
        fontsize=FS, fontweight="bold", color=INK)
parts = [("empty selection → escalate", ORANGE), ("static / frame only", BLUE),
         ("static + shadow", PURPLE), ("shadow only", GREEN)]
YB = np.array([SEP + 1.35, SEP + 2.4])
tot = {c: sum(EVID[c]) for c in ("paper", "extended")}
left = np.zeros(2)
for k, (lab, col) in enumerate(parts):
    cnt = np.array([EVID["paper"][k], EVID["extended"][k]])
    w = cnt / np.array([tot["paper"], tot["extended"]])
    ax.barh(YB, w, left=left, color=col, height=0.74, edgecolor="white", linewidth=1.0, zorder=2)
    for i, (vv, ww) in enumerate(zip(cnt, w)):
        if vv >= 12:
            ax.text(left[i] + ww / 2, YB[i], str(vv), ha="center", va="center", color="white",
                    fontsize=FS, fontweight="bold", zorder=3)
    left += w

ax.set_yticks(list(YA) + list(YB), names + ["Original", "Extended"])
ax.tick_params(axis="y", length=0)
ax.set_ylim(YB[-1] + 0.55, -1.35)
ax.set_xlim(0, 1.0); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0", ".25", ".5", ".75", "1"])
ax.grid(axis="y", visible=False)
ax.set_xlabel("rate (a) / share of records (b)", labelpad=2)
ax.spines["bottom"].set_bounds(0, 1.0)

# value labels sit inside the bar end (white); a bar too short for its label gets it outside (dark)
fig.canvas.draw(); r0 = fig.canvas.get_renderer()
for t, (a, n) in zip(VAL, RATES):
    bar_px = ax.transData.transform((a / n, 0))[0] - ax.transData.transform((0, 0))[0]
    if t.get_window_extent(r0).width + 6 > bar_px:
        t.set_x(a / n + 0.02); t.set_ha("left"); t.set_color(INK); t.set_fontweight("normal")

# legend for (b): 2 x 2 on top, centred over the whole figure
fig.canvas.draw(); r0 = fig.canvas.get_renderer()
full0 = fig.get_tightbbox(r0).transformed(fig.dpi_scale_trans).transformed(fig.transFigure.inverted())
leg = fig.legend(handles=[Patch(color=c, label=l) for l, c in parts], loc="lower center", ncol=2,
                 bbox_to_anchor=(0.5 * (full0.x0 + full0.x1), ax.get_position().y1 + 0.005), borderaxespad=0.0,
                 fontsize=FS, handlelength=0.9, handleheight=0.8, handletextpad=0.3, columnspacing=1.0, labelspacing=0.25)

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"{NAME}.pdf", dpi=DPI)
fig.savefig(OUT / f"{NAME}_{DPI}dpi.png", dpi=DPI)
print("saved", (OUT / f"{NAME}.pdf").resolve(), "and", (OUT / f"{NAME}_{DPI}dpi.png").resolve())

# ---- check: no two texts overlap, no label runs off a bar it sits in, legend clear of the axes ----
fig.canvas.draw(); r = fig.canvas.get_renderer()
T = [t for t in [*ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels(), ax.xaxis.label] if t.get_text() and t.get_visible()]
B = [(t.get_text(), t.get_window_extent(r)) for t in T]
clash = [(a, b) for k, (a, A) in enumerate(B) for b, C in B[k + 1:] if A.overlaps(C)]
L = leg.get_window_extent(r)
clash += [("legend", a) for a, A in B if A.overlaps(L)]
clash += [("legend", "bar") for p in ax.patches if p.get_width() > 0 and p.get_window_extent(r).overlaps(L)]
clash += [(t.get_text(), "bar") for t in ax.texts if t.get_color() == INK and not t.get_text().startswith("(")
          and any(p.get_window_extent(r).overlaps(t.get_window_extent(r)) for p in ax.patches if p.get_width() > 0)]
clash += [(t.get_text(), "outside its bar") for t in VAL if t.get_color() == "white"
          and t.get_window_extent(r).x0 < ax.transData.transform((0, 0))[0]]
full = fig.get_tightbbox(r)
W = full.width * 72
print(f"PDF {W:.0f} x {full.height * 72:.0f} pt -> at \\columnwidth the text prints at ~{FS * 241 / W:.1f} pt")
print("overlapping texts:", clash or "none")
