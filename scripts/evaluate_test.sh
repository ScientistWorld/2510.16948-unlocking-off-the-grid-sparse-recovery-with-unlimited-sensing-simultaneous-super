#!/bin/bash
# Evaluate saved method artifacts on the held-out test slice.
#
# Mirrors scripts/evaluate.sh:
#   ./evaluate_test.sh <data> <method_output> <baseline_output> [experiment_name]
#   ./evaluate_test.sh
#
# The default mode invokes eval/test/ code and scores every method entry already
# present in scoring/scores_train.json. If that file is absent, it falls back to
# the same checkpoint enumeration used by evaluate_train.sh. Results are written
# only to scoring/scores_test.json.

set -e

cd /home/user

mkdir -p scoring
mkdir -p tmp

if [ "$#" -ge 3 ]; then
  DATA_PATH="$1"
  METHOD_OUTPUT="$2"
  BASELINE_OUTPUT="$3"
  EXPERIMENT_NAME="${4:-synthetic_lowbit_hdr_dr20}"
  python -m eval.test.evaluate_us_sres_slice \
    --data "$DATA_PATH" \
    --method "$METHOD_OUTPUT" \
    --baseline "$BASELINE_OUTPUT" \
    --experiment-name "$EXPERIMENT_NAME" \
    --scores scoring/scores_test.json
  exit 0
fi

python -m eval.test.evaluate_us_sres_slice \
  --checkpoint-dir checkpoints \
  --train-scores scoring/scores_train.json \
  --scores scoring/scores_test.json
