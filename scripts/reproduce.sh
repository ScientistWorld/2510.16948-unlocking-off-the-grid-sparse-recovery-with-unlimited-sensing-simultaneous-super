#!/bin/bash
# Reproduce the gym's reference results end to end (CPU only, ~20 minutes).
#
# The evaluators run every registered method (scripts/methods/*.sh, here the
# paper's SRes-IterSiS) and compute the conventional baseline themselves.
set -euo pipefail
cd /home/user
bash scripts/download.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
bash scripts/evaluate.sh
python -m eval.check_core_claim --scores scoring/scores_test.json
