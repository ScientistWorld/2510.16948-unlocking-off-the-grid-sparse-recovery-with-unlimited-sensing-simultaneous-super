#!/bin/bash
# End-to-end job (CPU, ~15 minutes on one core):
#   1. public train export,
#   2. hardening audit: better/weaker variants and shortcuts registered next to
#      the reference and scored by the no-argument evaluators (tampering replayed),
#   3. the official reference-only scores (scores_train/test.json, scores.json),
#   4. audit summary and validation.
# The noise/pulse-width calibration that fixed the benchmark constants is a
# separate diagnostic: python redteam/hardening/calibrate.py
set -uo pipefail
cd /home/user
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
JOBS="$(nproc)"
echo "nproc=$JOBS"
python -c "import numpy, scipy; print('numpy', numpy.__version__, 'scipy', scipy.__version__)"

bash scripts/download.sh || exit 1
echo "== audit"
bash redteam/hardening/run_audit.sh "$JOBS"
echo "== official reference scores"
bash scripts/evaluate_train.sh || exit 1
bash scripts/evaluate_test.sh || exit 1
bash scripts/evaluate.sh || exit 1
python -m eval.check_core_claim --scores scoring/scores_test.json
echo "== analysis"
python redteam/hardening/analyze.py 2>&1 | tee redteam/hardening/results/analysis.md
python validate.py --compare --post-design
