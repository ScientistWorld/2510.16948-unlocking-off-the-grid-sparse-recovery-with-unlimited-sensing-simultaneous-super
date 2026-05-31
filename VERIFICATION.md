# Verification Report

## Initial Assessment

The workspace started at `secondary_claims`, with completed container jobs and
saved outputs for five synthetic low-bit HDR experiments. The claimed milestone
is justified: the implementation contains recognizable US-SRes computation,
the clipped baseline is scored through the same evaluator, and the reproduced
results support both dynamic-range and bit-depth robustness on the available
synthetic benchmark.

## Issues Found

- Minor: `scripts/evaluate.sh` defaulted to a single current method manifest,
  which was less reusable for future methods than discovering all compatible
  outputs under `checkpoints/`.
- Minor: the main `scoring/scores.json` was missing several constraint metrics
  that were already computed in the train/test score files.
- Cosmetic: `scoring/DIRECTION.md` named a specific method variant, which was
  unnecessary in a high-level direction file intended for from-scratch agents.

## Fixes Applied

- Updated `eval/evaluate_us_sres.py` and `scripts/evaluate.sh` so the default
  evaluator discovers all per-experiment method artifacts in `checkpoints/`
  while preserving explicit path and manifest evaluation modes.
- Added weak-target localization, max localization error, folded-region MSE,
  and wrapped-measurement consistency metrics to `scoring/scores.json`, using
  the completed train/test evaluator outputs as the source.
- Reworded `scoring/DIRECTION.md` to describe the allowed research family
  without naming the reproduced method.
- Ran `python -m py_compile eval/evaluate_us_sres.py`,
  `git diff --check`, and `python validate.py --compare`; all passed.

## Final Judgment

The workspace is ready to serve as a research gym in both improve and
from-scratch modes. Problem-facing files are method-agnostic, evaluation does
not import from `method/`, scored metrics include both benefit and constraint
quantities, and no wall-clock speed or paper-deviation metric is used.

- Milestone: secondary_claims
- Ready for gym use: yes
- Confidence: medium
- Key limitation: hardware ToF tensors from the paper are unavailable, so the
  gym uses deterministic synthetic low-bit HDR data that preserves the signal
  model and evaluation axes.
