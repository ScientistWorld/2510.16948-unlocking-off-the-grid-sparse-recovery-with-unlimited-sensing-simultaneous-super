#!/bin/bash
# Evaluate saved method artifacts on the visible train slice.
#
# Mirrors scripts/evaluate.sh:
#   ./evaluate_train.sh <data> <method_output> <baseline_output> [experiment_name]
#   ./evaluate_train.sh
#
# The default mode invokes eval/train/ code, enumerates checkpoint NPZ outputs
# by experiment suffix, and writes scoring/scores_train.json.

set -e

cd /home/user

mkdir -p scoring
mkdir -p tmp

if [ "$#" -ge 3 ]; then
  DATA_PATH="$1"
  METHOD_OUTPUT="$2"
  BASELINE_OUTPUT="$3"
  EXPERIMENT_NAME="${4:-synthetic_lowbit_hdr_dr20}"
  python -m eval.train.evaluate_us_sres_slice \
    --data "$DATA_PATH" \
    --method "$METHOD_OUTPUT" \
    --baseline "$BASELINE_OUTPUT" \
    --experiment-name "$EXPERIMENT_NAME" \
    --scores scoring/scores_train.json
  exit 0
fi

python -m eval.train.evaluate_us_sres_slice \
  --checkpoint-dir checkpoints \
  --scores scoring/scores_train.json
