#!/bin/bash
# The conventional clipping-ADC baseline (conventional_clip_sres) is computed
# by the evaluators themselves (eval/*/conventional.py) from the second ADC's
# samples, so no submitted file can change it.  This script runs the same
# public baseline on the exported train slice for inspection only.
#
#   bash scripts/baseline.sh
set -euo pipefail
cd /home/user
python -m baseline.conventional_sres
