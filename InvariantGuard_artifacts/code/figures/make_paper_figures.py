"""Regenerate every data figure of the paper (Figures 3-9) from results/*.json.

Each figN_*.py is self-contained and can also be run on its own. Output goes to
figures/<file name used in the paper>.pdf (vector, fonts embedded) and a 300 dpi PNG.
Figures 1 and 2 are hand-drawn diagrams and are not generated from data.
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["fig3_bound_quality.py", "fig4_admission.py", "fig5_baselines.py", "fig6_ablation_heatmap.py",
           "fig7_static_discharge.py", "fig8_latency.py", "fig9_scale.py"]

for name in SCRIPTS:
    print(f"== {name}", flush=True)
    runpy.run_path(str(HERE / name), run_name="__main__")
print("done: figures written to", HERE.parents[1] / "figures", file=sys.stderr)
