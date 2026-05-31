# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-05-31 00:00] - none
- Continuing from a previous workspace and re-auditing integrity.
- Found a real modulo finite-difference implementation, but also found that
  the previous scoring reference mixed paper-reported targets with local
  invented metrics; fixing this before restoring a milestone.

### [2026-05-31 11:48] - core_claim_plus
- CPU container job `8a2d4851-d38` ran the method and clipped baseline
  end-to-end on three synthetic Fig. 2-style dynamic-range settings.
- US-SRes achieved MSE gains of 30.16 dB, 36.73 dB, and 39.69 dB over the
  conventional clipped baseline for DR 10, 20, and 30 respectively.
- `python validate.py --compare` passed in the job environment.

## Stop Justification
- Completed at milestone `core_claim_plus`.
