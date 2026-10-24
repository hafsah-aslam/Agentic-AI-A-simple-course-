# DockingPoseCorrection — independent reproduction and extension

Reproduction of *Confidence-Gated Correction of Molecular Docking Poses: A Geometric and Chemical-Validity Evaluation*
(Mwamughunda, Guohao and Aslam, ICCK Transactions and Journals, 2026), rebuilt end to end from public data, plus eight
new analyses (G1–G8). The manuscript is `paper/main.pdf`.

## Headline results

| | Original | Reproduction |
|---|---|---|
| Pooled MSE reduction, internal / external | 9.75% / 11.35% | 18.2% / 11.3% |
| RMSD < 2 Å success change, ungated | −3.6 pp / n.s. | −16.4 pp / −19.2 pp |
| PoseBusters pass after ungated correction | 31.2% / 59.0% | 0.6% / 0.3% |
| Gate admit rate (validation) | 24.2% | 2.9% |
| External σ vs validation | −32% | +1.1% |

New findings:
- **G8, ligand collapse:** the learned correction shrinks ligands to a median 58% of their docked radius of gyration, and about 96% of each correction is internal deformation.
- **G3, rigid projection:** restricting the correction to a rigid motion keeps validity but removes all of the error reduction.
- **Pooled MSE hides harm:** pooled MSE falls only because badly docked complexes dominate it; for the median complex the error rises.
- **G7, split variance:** the gate fails its own Stage A check on all three alternative splits.
- **G5, sequence leakage:** 17.8% of external complexes are near-identical in sequence to training proteins.

## Layout

```
DockingPoseCorrection/
├── run_pipeline.sh        all stages after docking (matching → features → training → evaluation → audit → analyses → figures)
├── manifests/             frozen manifest (manifest.csv) and eligibility/split log with SHA-256
├── src/
│   ├── prepare_data.py    ID intersection, eligibility, group-aware split, RCSB structures, receptors
│   ├── dock.py            AutoDock Vina docking (20 Å box, exhaustiveness 8, 5 poses, rank 1)
│   ├── match.py           docked/reference atom matching (graph isomorphism, symmetry-aware)
│   ├── misato_flex.py     MISATO trajectory RMSF via HTTP range reads + ligand-graph registration
│   ├── features.py        ligand and 28-feature pocket representation
│   ├── model.py, train.py dual-head model, four pocket encoders, NLL training
│   ├── evaluate.py        selection, three-stage gate, RMSD results, permutation and rotation audits
│   ├── audit.py           PoseBusters (dock config, 22 checks) for all pose variants
│   ├── validity.py        chemical-validity results
│   ├── gaps.py            G1–G6 new analyses
│   ├── resplit.py         G7 alternative splits
│   ├── shrinkage.py       G8 deformation / contraction analysis
│   ├── figures.py         all figures, including the methodology diagram
│   └── make_numbers.py    every number in the paper → paper/numbers.tex
├── results/               JSON/CSV output of every stage
├── figures/               PDF + 300 dpi PNG
└── paper/                 LaTeX source (main.tex, sections/, refs.bib, numbers.tex) and main.pdf
```

## Reproducing

Requirements: Python 3.11 with `vina meeko openbabel-wheel posebusters rdkit gemmi h5py fsspec aiohttp torch pandas scipy
networkx matplotlib`.

1. **Sources:**
   - LP-PDBBind (`git clone https://github.com/THGLab/LP-PDBBind`).
   - The MISATO ID lists (`train_MD.txt`, `val_MD.txt` and `test_MD.txt` from Zenodo record 7711953).
   - The PoseBusters benchmark (`posebusters_paper_data.zip`, Zenodo record 8278563).
2. **Build the manifest and structures:** `python3 src/prepare_data.py DATA LP_CSV MISATO_DIR PB_DIR manifests`, then rerun it with `--rebuild-receptors` as the sixth argument.
3. **Dock:** `python3 src/dock.py manifests/manifest.csv DATA PB_DIR DOCKED 0 1`. Run several workers in parallel; claim files prevent duplicate work.
4. **MISATO flexibility:** `python3 src/misato_flex.py <internal manifest> DATA 0 1`.
5. **Everything else:** `WORK=... SRC=... ./run_pipeline.sh`, then `python3 src/shrinkage.py` and `python3 src/make_numbers.py`.
6. **Paper:** `cd paper && latexmk -pdf main.tex`.

Docking took about 30 CPU-hours (4 cores); everything after docking takes about 6 hours on 4 CPU cores. Seeds are fixed, so
docking, labels and model outputs are deterministic for a given software version.

## Deviations from the original protocol

These are listed in full in Section 3.8 of the paper:
- RCSB structures instead of PDBbind files, so multi-residue ligands are excluded.
- Sequence-identity grouping.
- Vina 1.2.7.
- Meeko pose export.
- Our own MISATO registration.
- Heavy-atom PoseBusters audit.
