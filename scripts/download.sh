#!/bin/bash
# Prepare all data this environment needs.  Idempotent.
#
# Estimated total download size: 0 GB (no external downloads)
# Estimated disk usage after generation: ~3 MB
#
# The paper's hardware ToF tensors are not released, so the benchmark is a
# deterministic synthetic substitute.  This writes the public train slice
# (method inputs and labels) to data/synthetic/.  The hidden test slice is
# never written to disk: eval/test/ builds it at test time.
set -euo pipefail
cd /home/user
mkdir -p data/synthetic
python -m data.us_sres_synthetic --out-dir data/synthetic
