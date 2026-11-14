#!/bin/bash
# Score every registered method on the visible train slice.
#
#   bash scripts/evaluate_train.sh
#
# Runs eval/train/: same protocol as the hidden test (every entry point
# scripts/methods/<name>.sh is run on the train acquisitions and scored from
# raw outputs), on public scenes from the same generator.  Writes
# scoring/scores_train.json.
set -euo pipefail
cd /home/user
mkdir -p scoring
python -m eval.train.evaluate "$@"
