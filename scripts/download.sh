#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: <1 MB
#
# This reproduction uses deterministic synthetic data generated locally, so
# there are no external dataset or model downloads.

set -e

cd /home/user

mkdir -p data/synthetic
for DR in 10 20 30; do
  EVAL_OUT="data/synthetic/eval_us_sres_dr${DR}.npz"
  PUBLIC_OUT="data/synthetic/us_sres_dr${DR}.npz"
  if [ ! -e "$EVAL_OUT" ] || [ ! -e "$PUBLIC_OUT" ]; then
    python -m data.us_sres_synthetic \
      --output "$EVAL_OUT" \
      --public-output "$PUBLIC_OUT" \
      --trials 64 \
      --bits 3 \
      --dynamic-range-x "$DR" \
      --seed "$((16948 + DR))"
  fi
done
for BITS in 5 8; do
  EVAL_OUT="data/synthetic/eval_us_sres_dr20_bits${BITS}.npz"
  PUBLIC_OUT="data/synthetic/us_sres_dr20_bits${BITS}.npz"
  if [ ! -e "$EVAL_OUT" ] || [ ! -e "$PUBLIC_OUT" ]; then
    python -m data.us_sres_synthetic \
      --output "$EVAL_OUT" \
      --public-output "$PUBLIC_OUT" \
      --trials 64 \
      --bits "$BITS" \
      --dynamic-range-x 20 \
      --seed "$((16948 + 20 + BITS))"
  fi
done

# Compatibility path for scripts that evaluate the paper's middle DR setting.
if [ ! -e data/synthetic/us_sres_benchmark.npz ]; then
  cp data/synthetic/us_sres_dr20.npz data/synthetic/us_sres_benchmark.npz
fi
if [ ! -e data/synthetic/eval_us_sres_benchmark.npz ]; then
  cp data/synthetic/eval_us_sres_dr20.npz data/synthetic/eval_us_sres_benchmark.npz
fi
