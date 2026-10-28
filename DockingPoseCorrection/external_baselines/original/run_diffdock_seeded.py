#!/usr/bin/env python3
"""Invoke pinned DiffDock with a recorded stochastic seed.

The upstream user-inference entry point has no seed option.  This wrapper sets
all relevant Python, NumPy, and Torch RNGs before importing its main module.
It intentionally leaves DiffDock's model, sampler, and rank ordering intact.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--diffdock-root", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    return parser.parse_known_args()


def main() -> int:
    args, remaining = parse_args()
    root = args.diffdock_root.resolve()
    if not (root / "inference.py").is_file():
        raise SystemExit(f"DiffDock inference.py is missing: {root}")
    os.environ.setdefault("PYTHONHASHSEED", str(args.seed))
    random.seed(args.seed)
    import numpy as np
    import torch

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    sys.path.insert(0, str(root))
    from inference import get_parser, main as diffdock_main

    invocation = get_parser().parse_args(remaining)
    diffdock_main(invocation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
