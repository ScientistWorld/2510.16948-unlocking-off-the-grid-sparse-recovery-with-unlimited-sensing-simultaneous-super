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
python -m data.us_sres_synthetic \
  --output data/synthetic/us_sres_benchmark.npz \
  --trials 64 \
  --bits 3 \
  --dynamic-range-x 20
