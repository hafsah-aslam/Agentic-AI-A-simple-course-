#!/usr/bin/env python3
"""Run the complete reproduction on your own machine, from the raw datasets to the paper.

Every stage is skipped when its output already exists, so the script can be stopped and restarted at any time.

Example (Linux / macOS / WSL):
    python3 run_all.py \
        --lp-csv      /data/LP-PDBBind/dataset/LP_PDBBind.csv \
        --misato-ids  /data/misato \            # folder with train_MD.txt, val_MD.txt, test_MD.txt
        --misato-h5   /data/misato/MD.hdf5 \    # optional: local MISATO trajectories (otherwise streamed from Zenodo)
        --pdbbind-dir /data/PDBbind_v2020 \     # optional: local PDBbind (otherwise structures come from the RCSB PDB)
        --posebusters /data/posebusters_paper_data \   # folder that contains posebusters_benchmark_set/
        --work        /data/dpc_work \
        --workers 8
"""
import argparse, os, sys, subprocess, json, glob, shutil, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PY = sys.executable
SEEDS = [0, 42, 123, 999, 2026]
ARCHS = ["MLP", "GNN", "Hypergraph", "Transformer"]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(args, env=None, quiet=False):
    """Run one python script from src/ and stop everything if it fails."""
    cmd = [PY, os.path.join(SRC, args[0])] + [str(a) for a in args[1:]]
    r = subprocess.run(cmd, cwd=SRC, env=env, stdout=subprocess.DEVNULL if quiet else None)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd)}")


def parallel(jobs, n, env=None):
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(lambda a: run(a, env=env, quiet=True), jobs))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lp-csv", required=True, help="LP_PDBBind.csv from the LP-PDBBind repository")
    ap.add_argument("--misato-ids", required=True, help="folder with MISATO train_MD.txt, val_MD.txt, test_MD.txt")
    ap.add_argument("--posebusters", required=True, help="folder containing posebusters_benchmark_set/")
    ap.add_argument("--work", required=True, help="working folder for structures, docking output and models (~30 GB)")
    ap.add_argument("--misato-h5", help="local MISATO MD.hdf5 (recommended if you have it)")
    ap.add_argument("--pdbbind-dir", help="local PDBbind folder (recommended if you have it)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--skip-splits", action="store_true", help="skip the three alternative splits (G7, ~2 h)")
    ap.add_argument("--no-latex", action="store_true", help="do not compile the paper")
    a = ap.parse_args()

    W = os.path.abspath(a.work); os.makedirs(W, exist_ok=True)
    data, docked, runs, res = f"{W}/data", f"{W}/docked", f"{W}/runs", os.path.join(HERE, "results")
    man_dir = os.path.join(HERE, "manifests"); man = f"{man_dir}/manifest.csv"
    for d in (data, docked, runs, res):
        os.makedirs(d, exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    if a.pdbbind_dir:
        env["PDBBIND_DIR"] = os.path.abspath(a.pdbbind_dir)
    if a.misato_h5:
        env["MISATO_H5"] = os.path.abspath(a.misato_h5)
    misato_dir = os.path.abspath(a.misato_ids); pb = os.path.abspath(a.posebusters); a.lp_csv = os.path.abspath(a.lp_csv)
    for p in (a.lp_csv, misato_dir, f"{pb}/posebusters_benchmark_set"):
        if not os.path.exists(p):
            sys.exit(f"not found: {p}")
    log(f"work folder {W}; {a.workers} workers; PDBbind {'local' if a.pdbbind_dir else 'RCSB'}; MISATO {'local' if a.misato_h5 else 'remote'}")

    # 1 manifest + structures
    if not os.path.exists(f"{man_dir}/manifest_log.json") or not os.path.exists(f"{data}/internal"):
        log("1/8 eligibility, frozen manifest and structures")
        run(["prepare_data.py", data, a.lp_csv, misato_dir, pb, man_dir], env=env)
        if not a.pdbbind_dir:
            run(["prepare_data.py", data, a.lp_csv, misato_dir, pb, man_dir, "--rebuild-receptors"], env=env)
    import pandas as pd
    m = pd.read_csv(man)
    internal_csv = f"{W}/internal.csv"
    m[m.split != "external"][["pdb", "split"]].to_csv(internal_csv, index=False)

    # 2 docking (claim files let all workers share one manifest)
    todo = [p for p in m.pdb if not os.path.exists(f"{docked}/{p}/dock.json")]
    if todo:
        for p in todo:                                   # stale claims from an interrupted run
            c = f"{docked}/{p}/claim"
            if os.path.exists(c):
                os.remove(c)
        log(f"2/8 docking {len(todo)} complexes with {a.workers} workers (about 1 CPU-minute each)")
        parallel([["dock.py", man, data, pb, docked, 0, 1] for _ in range(a.workers)], a.workers, env)

    # 3 MISATO flexibility
    if len(glob.glob(f"{data}/misato/*.npz")) + len(glob.glob(f"{data}/misato/*.fail")) < (m.split != "external").sum():
        n = a.workers if a.misato_h5 else min(2, a.workers)   # remote reads are rate limited
        log(f"3/8 MISATO flexibility ({n} workers)")
        parallel([["misato_flex.py", internal_csv, data, w, n] for w in range(n)], n, env)

    # 4 matching, features, training
    log("4/8 atom matching and features")
    run(["match.py", man, data, pb, docked], env=env)
    feats = f"{W}/feats.pkl"
    if not os.path.exists(feats):
        run(["features.py", man, data, pb, docked, feats], env=env)
    jobs = [["train.py", feats, runs, ar, s] for ar in ARCHS for s in SEEDS if not os.path.exists(f"{runs}/{ar}_s{s}.pkl")]
    if jobs:
        log(f"   training {len(jobs)} models")
        parallel(jobs, a.workers, env)

    # 5 evaluation and chemical-validity audit
    if not os.path.exists(f"{res}/eval.json"):
        log("5/8 selection, gate and RMSD evaluation")
        run(["evaluate.py", feats, runs, res], env=env)
    arch = json.load(open(f"{res}/eval.json"))["selection"]["selected"]
    if not os.path.exists(f"{res}/audit.csv"):
        log(f"   PoseBusters audit ({arch})")
        parallel([["audit.py", feats, runs, arch, docked, data, pb, f"{W}/audit_{w}.csv", w, a.workers] for w in range(a.workers)], a.workers, env)
        pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{W}/audit_*.csv"))]).to_csv(f"{res}/audit.csv", index=False)

    # 6 analyses
    log("6/8 validity, gap experiments (G1-G6) and deformation analysis (G8)")
    run(["validity.py", feats, f"{res}/rows_selected.csv", f"{res}/audit.csv", docked, runs, f"{res}/validity.json"], env=env, quiet=True)
    run(["gaps.py", feats, runs, res, f"{res}/audit.csv", man, a.lp_csv, pb, f"{res}/gaps.json"], env=env, quiet=True)
    run(["shrinkage.py", feats, runs, arch, f"{res}/shrinkage.json"], env=env, quiet=True)

    # 7 alternative splits (G7)
    if not a.skip_splits:
        for salt in ("alt1", "alt2", "alt3"):
            if os.path.exists(f"{res}/split_{salt}_validity.json"):
                continue
            log(f"7/8 alternative split {salt}")
            D = f"{W}/split_{salt}"; os.makedirs(f"{D}/runs", exist_ok=True); os.makedirs(f"{D}/res", exist_ok=True)
            run(["resplit.py", feats, man, salt, f"{D}/feats.pkl"], env=env)
            parallel([["train.py", f"{D}/feats.pkl", f"{D}/runs", arch, s] for s in SEEDS if not os.path.exists(f"{D}/runs/{arch}_s{s}.pkl")], a.workers, env)
            run(["evaluate.py", f"{D}/feats.pkl", f"{D}/runs", f"{D}/res"], env=dict(env, ONLY_ARCH=arch), quiet=True)
            e2 = dict(env, ONLY_TEST="1")
            parallel([["audit.py", f"{D}/feats.pkl", f"{D}/runs", arch, docked, data, pb, f"{D}/audit_{w}.csv", w, a.workers] for w in range(a.workers)], a.workers, e2)
            pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{D}/audit_*.csv"))]).to_csv(f"{D}/res/audit.csv", index=False)
            run(["validity.py", f"{D}/feats.pkl", f"{D}/res/rows_selected.csv", f"{D}/res/audit.csv", docked, f"{D}/runs", f"{D}/res/validity.json"], env=env, quiet=True)
            shutil.copy(f"{D}/res/eval.json", f"{res}/split_{salt}_eval.json")
            shutil.copy(f"{D}/res/validity.json", f"{res}/split_{salt}_validity.json")

    # 8 figures, numbers, paper
    log("8/8 figures, numbers and paper")
    run(["figures.py", res, os.path.join(HERE, "figures")], env=env, quiet=True)
    run(["make_numbers.py", res, f"{man_dir}/manifest_log.json", os.path.join(HERE, "paper", "numbers.tex")], env=env)
    if not a.no_latex and shutil.which("latexmk"):
        subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"], cwd=os.path.join(HERE, "paper"),
                       stdout=subprocess.DEVNULL)
        log("paper: paper/main.pdf")
    log("done. Results in results/, figures in figures/.")


if __name__ == "__main__":
    main()
