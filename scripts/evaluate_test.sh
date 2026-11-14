#!/bin/bash
# Score every registered method on the hidden test slice.
#
#   bash scripts/evaluate_test.sh
#
# Runs eval/test/: builds the hidden test acquisitions from private seeds,
# calls every entry point scripts/methods/<name>.sh on them, rebuilds the
# answers in memory after the methods return, computes the conventional
# clipping-ADC baseline itself, validates every output and recomputes every
# metric.  Writes scoring/scores_test.json.  Needs no arguments.
set -euo pipefail
cd /home/user
mkdir -p scoring
python -m eval.test.evaluate "$@"
