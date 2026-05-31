# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-05-31 00:00] - core_claim
- Implemented and previously verified a scaled Theorem 2-style US-SRes
  reproduction on synthetic weak/strong off-grid spike data.
- Reproduced the central Fig. 2-style low-bit HDR claim across dynamic range
  settings 10, 20, and 30 with at least 30 dB MSE gain over clipped
  conventional sparse recovery.
- Scope is limited to the modulo finite-difference recovery mechanism; the
  full robust SRes-IterSiS rational residue-sieving loop and hardware ToF
  experiments remain unreproduced.

### [2026-05-31 12:00] - core_claim_plus
- Job `9db3b291-cd4` regenerated public method-input datasets and private
  evaluation-label datasets, reran the conventional clipped baseline and
  US-SRes method, and passed `python validate.py --compare`.
- Verified the central low-bit HDR recovery claim on three dynamic-range
  settings (`10`, `20`, and `30` times the folding threshold), which is beyond
  the minimum single-setting core claim.
- The milestone remains below `secondary_claims` because the full robust
  SRes-IterSiS rational residue-recovery loop, bit-depth sweep, K=3 high-order
  imaging, and hardware ToF experiments are not reproduced.
