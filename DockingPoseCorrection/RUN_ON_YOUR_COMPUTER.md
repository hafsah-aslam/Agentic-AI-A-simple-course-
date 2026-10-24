# Running the reproduction on your own computer

One command runs everything, from the raw datasets to the paper PDF. If it stops (power cut, Ctrl+C), run the same
command again and it continues where it left off.

## 1. What you need

| | Notes |
|---|---|
| **Operating system** | Linux or macOS. On Windows, use **WSL2 (Ubuntu)**: AutoDock Vina and Open Babel install most reliably there. |
| **Python** | 3.10 or 3.11 |
| **CPU** | The more cores the better. Docking is about 1 CPU-minute per complex: 2,428 complexes is about 40 CPU-hours, so roughly 5 h on 8 cores or 2.5 h on 16. A GPU is not needed. |
| **Disk** | About 30 GB free for the work folder, plus your datasets. |
| **RAM** | 8 GB is enough; 16 GB is comfortable. |
| **LaTeX** *(optional)* | `latexmk` + TeX Live, to rebuild the paper PDF automatically. |

## 2. Install

```bash
python3 -m venv dpc && source dpc/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu      # or the CUDA wheel if you prefer
pip install -r requirements.txt
```

Check that everything imports:
```bash
python3 -c "import vina, meeko, rdkit, posebusters, gemmi, h5py, torch; print('ok')"
obabel -V
```

## 3. Your datasets

| Dataset | What the script needs | Required? |
|---|---|---|
| **LP-PDBBind** | `LP_PDBBind.csv` (from `github.com/THGLab/LP-PDBBind`, folder `dataset/`) | yes |
| **MISATO ID lists** | a folder containing `train_MD.txt`, `val_MD.txt`, `test_MD.txt` | yes |
| **PoseBusters benchmark** | the unzipped `posebusters_paper_data` folder (it contains `posebusters_benchmark_set/`) | yes |
| **MISATO `MD.hdf5`** | the 133 GB trajectory file | optional, but recommended. Without it, trajectories are streamed from Zenodo, which is slow. |
| **PDBbind (v2020)** | the folder with `<pdb>/<pdb>_protein.pdb` and `<pdb>_ligand.sdf` or `.mol2` (any sub-folder layout works) | optional, but recommended. Without it, structures are downloaded from the RCSB PDB. |

Using your local PDBbind makes the run **closer to the original study** than the reported reproduction:
- it uses PDBbind's prepared proteins and ligands;
- peptide and multi-residue ligands are kept (the reported run had to drop 357 of them);
- the internal docking baseline should come out closer to the original 55.6%.


## Settings for an i9-13900 + RTX 4080 (12 GB)

```bash
python3 run_all.py ... --workers 28 --gpu-jobs 4
```

| Stage | Uses | Expected time on this machine |
|---|---|---|
| Docking (2,428 complexes) | CPU, 28 parallel Vina processes | ~1.5–2 h |
| MISATO flexibility (local `MD.hdf5`) | CPU, 28 processes | ~15–30 min (disk-bound; faster on an SSD) |
| Training (20 models + 15 for the splits) | **GPU**, 4 models at once | ~10–20 min |
| PoseBusters audit and analyses | CPU | ~30–45 min |

- **The docking stays on the CPU on purpose.** AutoDock Vina has no GPU mode. GPU docking programs such as Vina-GPU and Uni-Dock are different engines, so they would change the protocol compared with the original study.
- **Memory:** each Vina or audit process needs about 0.3–0.5 GB. If you have 32 GB of RAM, use `--workers 24`. With 64 GB or more, `--workers 30` is fine.
- **GPU on Windows:** run everything inside WSL2 (Ubuntu). Install the current NVIDIA driver on Windows (it provides CUDA to WSL). In WSL, install the CUDA build of PyTorch:
  ```bash
  pip install torch --index-url https://download.pytorch.org/whl/cu124
  python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
  ```
  The run log prints `GPU for training: NVIDIA GeForce RTX 4080 ...` when it is used. Use `--cpu-only` to train on the CPU instead.
- **GPU and CPU results:** they agree to within floating-point noise. The hyperparameters are identical on both devices; only the speed differs.

## 4. Run

```bash
python3 run_all.py \
    --lp-csv      /path/to/LP-PDBBind/dataset/LP_PDBBind.csv \
    --misato-ids  /path/to/misato \
    --misato-h5   /path/to/misato/MD.hdf5 \
    --pdbbind-dir /path/to/PDBbind_v2020 \
    --posebusters /path/to/posebusters_paper_data \
    --work        /path/to/dpc_work \
    --workers 8
```

- `--workers`: the number of CPU cores to use (default: all but one).
- `--skip-splits`: skip the three alternative splits (G7), which saves about 2 hours.
- `--no-latex`: don't compile the paper.

The run prints one line per stage:
```
1/8 eligibility, frozen manifest and structures
2/8 docking ...
3/8 MISATO flexibility
4/8 atom matching and features   (then: training 20 models)
5/8 selection, gate and RMSD evaluation   (then: PoseBusters audit)
6/8 validity, gap experiments (G1-G6) and deformation analysis (G8)
7/8 alternative split alt1 / alt2 / alt3
8/8 figures, numbers and paper
```

## 5. Results

| Where | What |
|---|---|
| `results/eval.json` | architecture selection, gate, RMSD results, permutation and rotation tests |
| `results/validity.json` | PoseBusters pass rates, newly invalid rates, per-check failures |
| `results/gaps.json` | new analyses G1–G6 |
| `results/shrinkage.json` | G8: ligand contraction and rigid/internal decomposition |
| `results/split_alt*_*.json` | G7: alternative splits |
| `figures/` | every figure (PDF + 300 dpi PNG), including the methodology diagram |
| `paper/numbers.tex`, `paper/main.pdf` | the paper rebuilt with **your** numbers |
| `results_reference/` | the results of the reported run, for comparison |

Every number in the paper text comes from `paper/numbers.tex`, so the PDF always matches your results. If your numbers
differ from the reported run (for example, because you used local PDBbind), **read the text again before submitting**.
Some sentences describe the direction of a result ("not reproduced", "fails on all three splits"), and those may need
changing.

## 6. Common problems

| Problem | Fix |
|---|---|
| `obabel: command not found` | `pip install openbabel-wheel` inside the same environment, or `conda install -c conda-forge openbabel` |
| `vina` fails to install | Use Linux/WSL2 and `pip install vina`, or `conda install -c conda-forge vina` |
| A step failed and the run stopped | Fix the cause and run the same command again; finished stages are skipped |
| You want to redo one stage | Delete its output (e.g. `results/eval.json`, or `work/feats.pkl` for features) and run again |
| Zenodo answers 429 (too many requests) | Only happens without `--misato-h5`; the script waits and retries. Using the local file avoids it. |
| A receptor cannot be read by PoseBusters | Handled automatically: a polymer-only copy (`protein_pb.pdb`) is used if you create one, as in the reported run (3 complexes) |

## 7. Quick test first (optional, about 20 minutes)

To check that the installation works before the long run, make a small manifest with the `DPC_TARGET` setting (training,
validation and test sizes):
```bash
DPC_TARGET=30,10,10 python3 run_all.py ... --work /tmp/dpc_test --skip-splits --no-latex
```
This test overwrites `manifests/`, `results/` and `figures/` with test outputs. Before the real run, either run it on a
separate copy of the folder or delete `manifests/manifest_log.json`, `results/*` and the test work folder.
