#!/bin/bash
# Hardening job (CPU): calibration diagnostics, the audit of better/weaker
# variants and shortcuts through the no-argument evaluators, then the official
# reference-only scores, the audit summary and validation.
set -uo pipefail
cd /home/user
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
JOBS="$(nproc)"
echo "nproc=$JOBS"
python -c "import numpy, scipy; print('numpy', numpy.__version__, 'scipy', scipy.__version__)"
id

bash scripts/download.sh || exit 1
echo "== calibration"
python redteam/hardening/calibrate.py 2>&1 | tee redteam/hardening/calibration.log
echo "== audit"
bash redteam/hardening/run_audit.sh "$JOBS"
echo "== official reference scores"
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
bash scripts/evaluate.sh
python -m eval.check_core_claim --scores scoring/scores_test.json
echo "== analysis"
python redteam/hardening/analyze.py 2>&1 | tee redteam/hardening/results/analysis.md
python validate.py --compare --post-design
