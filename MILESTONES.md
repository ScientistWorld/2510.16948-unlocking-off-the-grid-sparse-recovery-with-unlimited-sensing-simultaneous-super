# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-31 12:01] - core_claim
- Packaged a scoped US-SRes reproduction around the paper's Fig. 2 low-bit HDR setting.
- Implemented deterministic weak/strong off-grid spike data, a clipped-ADC baseline, the paper's modulo finite-difference recovery path, and method-agnostic scoring.
- Current saved scores show at least 30 dB waveform-MSE gain over the clipped baseline at dynamic-range factors 10, 20, and 30 with 3-bit measurements.
- Full robust SRes-IterSiS rational residue refinement and undistributed hardware ToF experiments remain out of scope for this milestone.

## Stop Justification
- Not stopped; submitting a CPU reproduction job to verify the packaged environment end to end.
