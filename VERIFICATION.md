# Verification Report

## Initial Assessment

The workspace started at `secondary_claims`. The implementation contains
recognizable US-SRes computation, the clipped baseline is scored through the
same evaluator, and five synthetic low-bit HDR experiments cover the paper's
reported dynamic-range and bit-depth robustness axes.

The claimed milestone was broadly justified, but the final audit found one
integrity issue that needed a verification rerun before signoff.

## Issues Found

- Critical, fixed: stale public synthetic archives still contained per-trial
  fold counts, and the method input path would read them if present. That made
  the benchmark vulnerable to privileged metadata leakage.
- Minor, already fixed before this pass: the standalone evaluator originally
  defaulted to one baked-in method artifact instead of discovering compatible
  outputs under `checkpoints/`.
- Minor, already fixed before this pass: the main score file needed the same
  constraint metrics already present in train/test scoring.

## Fixes Applied

- Hardened `method/us_sres.py` so it ignores any `folds` array in submitted
  public inputs and estimates the residue degree from its own reconstruction
  residual.
- Verified `data/us_sres_synthetic.py` writes public archives with only
  measurement, kernel, and config arrays; private eval archives retain labels
  and fold counts for scoring.
- Ran CPU job `b9d88f78-5bb`, which regenerated data, checkpoints, scores,
  train/test scores, and passed the quality gate and `python validate.py
  --compare`.
- Updated `MILESTONES.md` and `PROGRESS.md` with the final verification
  outcome and removed the obsolete tracked `trajectory/session.json` artifact.

## Final Judgment

The workspace is ready to serve as a research gym in improve and from-scratch
modes. Problem-facing files are method-agnostic, evaluation does not import
from `method/`, scored metrics include benefit and constraint quantities, no
scored metric measures wall-clock speed or deviation from paper values, and
the public data path no longer exposes private fold metadata.

- Milestone: secondary_claims
- Ready for gym use: yes
- Confidence: medium
- Key limitation: hardware ToF tensors from the paper are unavailable, so the
  gym uses deterministic synthetic low-bit HDR data that preserves the signal
  model and evaluation axes.

## Superseded (iteration 11)

The benchmark, evaluators and reference were rebuilt in the hardening
iteration; see `HARDENING.md` for the current verification record.
