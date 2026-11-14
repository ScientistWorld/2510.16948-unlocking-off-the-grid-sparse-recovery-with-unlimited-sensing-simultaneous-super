#!/bin/bash
# Run the paper's method (SRes-IterSiS) on the exported train acquisitions and
# save its outputs under checkpoints/ for inspection.  Scoring does not read
# these files: the evaluators run scripts/methods/*.sh themselves.
#
#   bash scripts/method.sh
set -euo pipefail
cd /home/user
mkdir -p checkpoints
for INPUT in data/synthetic/train_synthetic_lowbit_hdr_*.npz; do
  case "$INPUT" in *_labels.npz) continue ;; esac
  NAME="$(basename "$INPUT" .npz)"
  bash scripts/methods/us_sres.sh "$INPUT" "checkpoints/us_sres_${NAME#train_}.npz"
done
