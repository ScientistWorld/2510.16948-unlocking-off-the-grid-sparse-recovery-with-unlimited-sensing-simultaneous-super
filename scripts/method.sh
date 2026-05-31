#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

DATA_PATH="${1:-data/synthetic/us_sres_benchmark.npz}"
OUTPUT_PATH="${2:-checkpoints/us_sres_outputs.npz}"

python -m method.us_sres --input "$DATA_PATH" --output "$OUTPUT_PATH"
