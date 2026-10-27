#!/usr/bin/env python3
"""Run the complete reproduction on your own machine, from the raw datasets to the paper.

Every stage is skipped when its output already exists, so the script can be stopped and restarted at any time.

Simplest use (WSL on Windows, datasets in D:\\data):
    python3 run_all.py --data /mnt/d/data --work ~/dpc_work --workers 28

Full form (Linux / macOS / WSL):
    python3 run_all.py \
        --lp-csv      /data/LP-PDBBind/dataset/LP_PDBBind.csv \
        --misato-ids  /data/misato \            # folder with train_MD.txt, val_MD.txt, test_MD.txt
        --misato-h5   /data/misato/MD.hdf5 \    # optional: local MISATO trajectories (otherwise streamed from Zenodo)
        --pdbbind-dir /data/PDBbind_v2020 \     # optional: local PDBbind (otherwise structures come from the RCSB PDB)
        --posebusters /data/posebusters_paper_data \   # folder that contains posebusters_benchmark_set/
        --work        /data/dpc_work \
        --workers 30            # i9-13900: 32 threads; training uses the GPU automatically
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


LP_URL = "https://raw.githubusercontent.com/THGLab/LP-PDBBind/master/dataset/LP_PDBBind.csv"
PB_URL = "https://zenodo.org/records/8278563/files/posebusters_paper_data.zip?download=1"
MISATO_IDS_URL = "https://zenodo.org/records/7711953/files/{}?download=1"


def download(url, dest, tries=20):
    """Download with progress, resuming a partial .part file after a dropped connection."""
    import urllib.request
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        return dest
    tmp = dest + ".part"
    log(f"   downloading {os.path.basename(dest)}")
    for attempt in range(1, tries + 1):
        have = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if have and r.status != 206:                        # server ignored the range: start again
                    have = 0
                total = have + int(r.headers.get("Content-Length") or 0)
                shown = -1
                with open(tmp, "ab" if have else "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk); have += len(chunk)
                        pct = int(100 * have / total) if total else -1
                        if pct >= 0 and pct // 10 != shown:
                            shown = pct // 10
                            log(f"      {have / 1e6:.0f} / {total / 1e6:.0f} MB ({pct}%)")
            if total and have < total:
                raise OSError(f"connection closed at {have} of {total} bytes")
            os.replace(tmp, dest)
            return dest
        except Exception as e:
            if attempt == tries:
                raise
            log(f"      download interrupted ({e}); resuming in 10 s (attempt {attempt + 1}/{tries})")
            time.sleep(10)


def find_named(root, names, max_depth=3):
    """Find a file (any of names; a name without extension also matches name.csv) up to max_depth folders below root."""
    if not root:
        return None
    wanted = {n.lower() for n in names} | {n.lower() + ".csv" for n in names if "." not in n}
    base = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirs, files in os.walk(root):
        if dirpath.count(os.sep) - base >= max_depth:
            dirs[:] = []
        dirs[:] = [d for d in dirs if d not in ("P-L", "pdbbind")]        # skip the large structure folders
        for f in files:
            if f.lower() in wanted:
                return os.path.join(dirpath, f)
    return None


def resolve_sources(a, W):
    """Fill in every input from --data, from explicit options, or by downloading the small public files."""
    import tarfile, zipfile
    D = os.path.abspath(a.data) if a.data else None
    S = os.path.join(W, "sources"); os.makedirs(S, exist_ok=True)
    find = lambda *names: next((os.path.join(D, n) for n in names if D and os.path.exists(os.path.join(D, n))), None)
    # MISATO trajectories
    a.misato_h5 = a.misato_h5 or find("MD.hdf5")
    # PDBbind: an extracted folder, or P-L.tar / P-L.tar.gz extracted once into the work folder
    if not a.pdbbind_dir:
        folder = find("P-L", "PDBbind_v2020_PL", "v2020-other-PL", "refined-set")
        archive = find("P-L.tar", "P-L.tar.gz", "PDBbind_v2020_PL.tar.gz")
        if folder:
            a.pdbbind_dir = folder
        elif archive:
            target = os.path.join(S, "pdbbind")
            if not os.path.exists(os.path.join(target, ".extracted")):
                log(f"   extracting {os.path.basename(archive)} (once, a few minutes)")
                with tarfile.open(archive) as t:
                    t.extractall(target)
                open(os.path.join(target, ".extracted"), "w").close()
            a.pdbbind_dir = target
    # LP-PDBBind table
    a.lp_csv = a.lp_csv or find_named(D, ("LP_PDBBind.csv", "LP_PDBBind")) or download(LP_URL, os.path.join(S, "LP_PDBBind.csv"))
    # PoseBusters benchmark
    if not a.posebusters:
        a.posebusters = find("posebusters_paper_data")
        zp = find("posebusters_paper_data.zip")
        if not a.posebusters and os.path.exists(os.path.join(S, "posebusters_benchmark_set")):
            a.posebusters = S                                   # extracted earlier (zip without a top folder)
        if not a.posebusters:
            target = os.path.join(S, "posebusters_paper_data")
            if not os.path.exists(os.path.join(target, "posebusters_benchmark_set")):
                zp = zp or download(PB_URL, os.path.join(S, "posebusters_paper_data.zip"))
                log("   extracting PoseBusters benchmark")
                with zipfile.ZipFile(zp) as z:
                    z.extractall(S)
                if not os.path.exists(os.path.join(target, "posebusters_benchmark_set")):   # zip without a top folder
                    target = S
            a.posebusters = target
    # MISATO identifier lists (tiny); fall back to the group names inside a local MD.hdf5
    if not a.misato_ids:
        if find("train_MD.txt"):
            a.misato_ids = D
        else:
            target = os.path.join(S, "misato_ids")
            try:
                for f in ("train_MD.txt", "val_MD.txt", "test_MD.txt"):
                    download(MISATO_IDS_URL.format(f), os.path.join(target, f))
            except Exception as e:
                if not a.misato_h5:
                    sys.exit(f"cannot get the MISATO ID lists ({e}); pass --misato-ids or --misato-h5")
                import h5py
                log("   MISATO ID lists from the groups in MD.hdf5")
                keys = list(h5py.File(a.misato_h5, "r").keys())
                os.makedirs(target, exist_ok=True)
                open(os.path.join(target, "train_MD.txt"), "w").write("\n".join(keys) + "\n")
                for f in ("val_MD.txt", "test_MD.txt"):
                    open(os.path.join(target, f), "w").close()
            a.misato_ids = target
    log("   inputs:")
    for name, val in (("LP-PDBBind table", a.lp_csv), ("MISATO ID lists", a.misato_ids), ("PoseBusters set", a.posebusters),
                      ("MISATO MD.hdf5", a.misato_h5 or "NOT FOUND - trajectories will be streamed from Zenodo (slow)"),
                      ("PDBbind structures", a.pdbbind_dir or "NOT FOUND - structures will be downloaded from the RCSB PDB")):
        log(f"      {name:20s} {val}")
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="your dataset folder, e.g. /mnt/d/data (MD.hdf5, P-L.tar, ...); everything else is found or downloaded")
    ap.add_argument("--work", required=True, help="working folder for structures, docking output and models (~30 GB)")
    ap.add_argument("--lp-csv", help="LP_PDBBind.csv (downloaded from the LP-PDBBind repository if not given)")
    ap.add_argument("--misato-ids", help="folder with MISATO train_MD.txt, val_MD.txt, test_MD.txt (downloaded if not given)")
    ap.add_argument("--posebusters", help="folder containing posebusters_benchmark_set/ (downloaded if not given)")
    ap.add_argument("--misato-h5", help="local MISATO MD.hdf5 (found in --data if present)")
    ap.add_argument("--pdbbind-dir", help="local PDBbind folder (or P-L.tar in --data, extracted automatically)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2),
                    help="CPU processes for docking, MISATO and PoseBusters (default: all threads minus 2)")
    ap.add_argument("--gpu-jobs", type=int, default=4, help="models trained at the same time on the GPU (default 4)")
    ap.add_argument("--cpu-only", action="store_true", help="do not use the GPU for training")
    ap.add_argument("--skip-splits", action="store_true", help="skip the three alternative splits (G7, ~2 h)")
    ap.add_argument("--no-latex", action="store_true", help="do not compile the paper")
    a = ap.parse_args()

    W = os.path.abspath(a.work); os.makedirs(W, exist_ok=True)
    a = resolve_sources(a, W)
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
    log(f"inputs: LP={a.lp_csv} | MISATO ids={misato_dir} | MD.hdf5={a.misato_h5 or 'remote'} | PDBbind={a.pdbbind_dir or 'RCSB'} | PoseBusters={pb}")
    try:
        import torch
        gpu = torch.cuda.is_available() and not a.cpu_only
        gpu_name = torch.cuda.get_device_name(0) if gpu else "none"
    except Exception:
        gpu, gpu_name = False, "none"
    if a.cpu_only:
        env["DPC_DEVICE"] = "cpu"
    n_train = a.gpu_jobs if gpu else a.workers
    log(f"GPU for training: {gpu_name}; {n_train} models in parallel")
    log(f"work folder {W}; {a.workers} workers; PDBbind {'local' if a.pdbbind_dir else 'RCSB'}; MISATO {'local' if a.misato_h5 else 'remote'}")

    # 1 manifest + structures
    mlog = f"{man_dir}/manifest_log.json"
    if not os.path.exists(mlog) or not os.path.exists(f"{data}/internal") or "max_rotatable_bonds" not in json.load(open(mlog)):
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
    if any(not os.path.exists(f"{data}/misato/{p}.npz") and not os.path.exists(f"{data}/misato/{p}.npz.fail")
           for p in m[m.split != "external"].pdb):
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
        parallel(jobs, n_train, env)

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
            parallel([["train.py", f"{D}/feats.pkl", f"{D}/runs", arch, s] for s in SEEDS if not os.path.exists(f"{D}/runs/{arch}_s{s}.pkl")], n_train, env)
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
