#!/bin/bash
# Standard evaluation: score every registered method (scripts/methods/*.sh)
# on the visible train slice and write scoring/scores.json.
#
#   bash scripts/evaluate.sh
#
# Uses only eval/ code; it never imports method/.  The hidden test slice is
# scored by scripts/evaluate_test.sh with the same protocol.
set -euo pipefail
cd /home/user
mkdir -p scoring
python -m eval.train.evaluate --scores scoring/scores.json "$@"
