#!/bin/bash
set -euo pipefail
cd /home/user
# Bound BLAS threading to avoid oversubscription in these small CPU solves.
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
python -u redteam/audit.py all
