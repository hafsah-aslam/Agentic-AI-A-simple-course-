#!/bin/bash
# Runs every stage after docking. Paths default to the layout used for the reported run.
#   WORK : large-file work area (structures, docking output, features, model runs)
#   SRC  : downloaded sources (LP-PDBBind clone, MISATO id lists, PoseBusters benchmark)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK=${WORK:-/tmp/claude-0/dock}
SRC=${SRC:-$WORK/src}
MAN=$HERE/manifests/manifest.csv
RES=$HERE/results
PY="python3 $HERE/src"
mkdir -p "$RES" "$WORK/runs"
cd "$HERE/src"

echo "[1] atom matching";        python3 match.py "$MAN" "$WORK/data" "$SRC/pb" "$WORK/docked"
echo "[2] features";             python3 features.py "$MAN" "$WORK/data" "$SRC/pb" "$WORK/docked" "$WORK/feats.pkl" | tee "$RES/features_log.txt"
echo "[3] 4 architectures x 5 seeds"
for a in MLP GNN Hypergraph Transformer; do
  for s in 0 42 123 999 2026; do
    [ -f "$WORK/runs/${a}_s${s}.pkl" ] || echo "$a $s"
  done
done | xargs -P 4 -n 2 sh -c 'python3 train.py '"$WORK"'/feats.pkl '"$WORK"'/runs "$0" "$1"' | tee "$RES/train_log.txt"
echo "[4] selection, gate, RMSD evaluation"; python3 evaluate.py "$WORK/feats.pkl" "$WORK/runs" "$RES"
ARCH=$(python3 -c "import json;print(json.load(open('$RES/eval.json'))['selection']['selected'])")
echo "[5] PoseBusters audit ($ARCH)"
for w in 0 1 2 3; do python3 audit.py "$WORK/feats.pkl" "$WORK/runs" "$ARCH" "$WORK/docked" "$WORK/data" "$SRC/pb" "$WORK/audit_$w.csv" $w 4 > "$WORK/audit_$w.log" 2>&1 & done; wait
python3 -c "import pandas as pd,glob; pd.concat([pd.read_csv(f) for f in sorted(glob.glob('$WORK/audit_[0-9].csv'))]).to_csv('$RES/audit.csv',index=False)"
echo "[6] validity";             python3 validity.py "$WORK/feats.pkl" "$RES/rows_selected.csv" "$RES/audit.csv" "$WORK/docked" "$WORK/runs" "$RES/validity.json"
echo "[7] gap experiments";      python3 gaps.py "$WORK/feats.pkl" "$WORK/runs" "$RES" "$RES/audit.csv" "$MAN" "$SRC/LP-PDBBind/dataset/LP_PDBBind.csv" "$SRC/pb" "$RES/gaps.json"
echo "[8] split variance"
for salt in alt1 alt2 alt3; do
  D=$WORK/split_$salt; mkdir -p "$D/runs" "$D/res"
  python3 resplit.py "$WORK/feats.pkl" "$MAN" "$salt" "$D/feats.pkl" | tee -a "$RES/resplit_log.txt"
  for s in 0 42 123 999 2026; do [ -f "$D/runs/${ARCH}_s${s}.pkl" ] || echo "$s"; done | \
    xargs -P 4 -n 1 sh -c 'python3 train.py '"$D"'/feats.pkl '"$D"'/runs '"$ARCH"' "$0"'
  ONLY_ARCH=$ARCH python3 evaluate.py "$D/feats.pkl" "$D/runs" "$D/res"
  for w in 0 1 2 3; do ONLY_TEST=1 python3 audit.py "$D/feats.pkl" "$D/runs" "$ARCH" "$WORK/docked" "$WORK/data" "$SRC/pb" "$D/audit_$w.csv" $w 4 > /dev/null 2>&1 & done; wait
  python3 -c "import pandas as pd,glob; pd.concat([pd.read_csv(f) for f in sorted(glob.glob('$D/audit_[0-9].csv'))]).to_csv('$D/res/audit.csv',index=False)"
  python3 validity.py "$D/feats.pkl" "$D/res/rows_selected.csv" "$D/res/audit.csv" "$WORK/docked" "$D/runs" "$D/res/validity.json"
  cp "$D/res/eval.json" "$RES/split_${salt}_eval.json"; cp "$D/res/validity.json" "$RES/split_${salt}_validity.json"
done
echo "[9] figures";              python3 figures.py "$RES" "$HERE/figures"
echo done
