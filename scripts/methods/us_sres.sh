#!/bin/bash
# Registered method: SRes-IterSiS, the paper's Algorithm 1 (method/us_sres.py).
#
# Method contract (every scripts/methods/<name>.sh follows it):
#   bash scripts/methods/<name>.sh <input.npz> <output.npz>
# <input.npz> holds modulo_samples (trials x N), kernel_grid, kernel,
# lambda_value, kernel_sigma, num_spikes, quant_bits, thermal_noise_std.
# <output.npz> must hold reconstruction (trials x N) and taus (trials x K).
# The evaluators call every entry point in this directory; the file name
# (without .sh) is the method's name in the score files.
set -euo pipefail
cd "$(dirname "$0")/../.."
python -m method.us_sres "$1" "$2"
