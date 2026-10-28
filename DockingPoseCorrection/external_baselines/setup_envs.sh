#!/usr/bin/env bash
# One-time setup of the EquiBind and DiffDock environments (conda or mamba must be installed).
#   EquiBind runs on the CPU: its pinned PyTorch 1.10 / CUDA 10.2 build has no kernels for RTX 40-series GPUs,
#   and EquiBind needs only seconds per complex anyway.
#   DiffDock runs on the GPU (PyTorch 1.13.1 + CUDA 11.7 runs on the RTX 4080).
# Downloads: about 6-8 GB in total (environments, DiffDock models, ESM2 language model). Run it once; rerunning
# skips what is already installed.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
conda_cmd="$(command -v mamba || command -v conda || true)"
[[ -n "$conda_cmd" ]] || { echo "conda or mamba not found; install Miniconda first" >&2; exit 1; }
base="$("$conda_cmd" info --base 2>/dev/null || conda info --base)"

for env in dpc-equibind dpc-diffdock; do
  if [[ -x "$base/envs/$env/bin/python" ]]; then
    echo "$env already installed"
  else
    file="$here/envs/${env#dpc-}.yml"; [[ "$env" == dpc-equibind ]] && file="$here/envs/equibind_cpu.yml"
    echo "creating $env from $file (this takes a while)"
    PIP_DEFAULT_TIMEOUT=120 "$conda_cmd" env create -y -n "$env" -f "$file"
  fi
done

echo "checking the GPU from the DiffDock environment"
"$base/envs/dpc-diffdock/bin/python" -c "import torch; print('CUDA', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"
echo "downloading the ESM2 language model used by DiffDock (2.5 GB, once)"
"$base/envs/dpc-diffdock/bin/python" -c "import esm; esm.pretrained.esm2_t33_650M_UR50D(); print('ESM2 ready')"
"$base/envs/dpc-equibind/bin/python" -c "import torch, dgl; print('EquiBind env ready: torch', torch.__version__, 'dgl', dgl.__version__)"
echo "done. Python paths:"
echo "  EQUIBIND_PYTHON=$base/envs/dpc-equibind/bin/python"
echo "  DIFFDOCK_PYTHON=$base/envs/dpc-diffdock/bin/python"
