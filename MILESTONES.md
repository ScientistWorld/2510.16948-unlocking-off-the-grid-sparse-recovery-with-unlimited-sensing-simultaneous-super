# Reproduction Milestones

**Current: secondary_claims**

## Progress Log

### [2026-05-31 12:01] - core_claim
- Packaged a scoped US-SRes reproduction around the paper's Fig. 2 low-bit HDR setting.
- Implemented deterministic weak/strong off-grid spike data, a clipped-ADC baseline, the paper's modulo finite-difference recovery path, and method-agnostic scoring.
- Current saved scores show at least 30 dB waveform-MSE gain over the clipped baseline at dynamic-range factors 10, 20, and 30 with 3-bit measurements.
- Full robust SRes-IterSiS rational residue refinement and undistributed hardware ToF experiments remain out of scope for this milestone.

### [2026-05-31 12:01] - core_claim
- Continuation audit found the prior implementation was a real core-claim reproduction but too scoped to restore `core_claim_plus`.
- Added a compact Section III-style residue-sieving path: rational `P/Q` weighted least-squares fold-residue recovery, `2 lambda Z` residue quantization, and P2 matrix-pencil spectral initialization with continuous least-squares refinement.
- Submitting a CPU job to regenerate method outputs and scores with the upgraded algorithm before claiming a higher milestone.

### [2026-05-31 12:14] - core_claim
- CPU job `5ad9d555-3dc` completed, but the forced IterSiS residue update degraded DR20/DR30 below the clipped baseline, so it does not support a milestone increase.
- Fixed the method to keep rational `P/Q` residue recovery as a Section III candidate and accept it only when the resulting signal has lower sparse-model residual than the finite-difference recovery path.
- Added a job quality gate requiring at least 20 dB MSE gain for every scored dynamic-range setting before a reproduction job can pass silently.

### [2026-05-31 12:21] - core_claim_plus
- CPU job `1d35c7b1-6b0` verified the repaired adaptive IterSiS path end to end.
- Restored 30.16/36.73/39.69 dB MSE gains over the clipped baseline at DR10/DR20/DR30 with 3-bit sensing.
- Expanded the planned benchmark with DR20 5-bit and 8-bit experiments to cover an additional Fig. 2 axis before attempting a higher milestone.

### [2026-05-31 12:28] - secondary_claims
- CPU job `b3e73f92-59e` verified the expanded five-experiment benchmark end to end.
- Reproduced Fig. 2's dynamic-range robustness claim at DR10/DR20/DR30 and its bit-depth robustness claim at DR20 with 3/5/8-bit sensing.
- The expanded scores all clear the quality gate: 30.16, 36.73, 39.69, 42.85, and 41.14 dB MSE gain over the clipped baseline.

### [2026-05-31 12:49] - secondary_claims
- Independent audits confirmed the method implements recognizable US-SRes computations and that eval/data do not import from `method/`.
- Added richer constraint metrics to the main reusable evaluator so `scores.json` can report weak-target localization, folded-region MSE, and modulo measurement consistency in addition to the primary MSE-gain metric.
- Submitting a CPU verification job to regenerate all score files and validate the updated schema.

### [2026-05-31 12:55] - secondary_claims
- Final verification found the claimed milestone justified: the workspace reproduces the dynamic-range and bit-depth robustness claims on the synthetic low-bit HDR benchmark.
- Repaired the standalone evaluator default so it discovers all method outputs under `checkpoints/` instead of scoring only a baked-in method artifact.
- Filled the main `scores.json` with the same constraint metrics already present in the train/test evaluator outputs and reran `python validate.py --compare` successfully.

### [2026-05-31 13:05] - secondary_claims
- Integrity audit found that public synthetic datasets exposed per-trial fold counts, which the compact IterSiS path used as privileged metadata.
- Removed fold counts from public acquisition files and changed the method to estimate its residue degree from its own reconstruction residual.
- Updated `scripts/run.sh` to regenerate synthetic data, baseline outputs, method outputs, and scores before validating, so the next job does not depend on ignored checkpoint artifacts.

### [2026-05-31 13:10] - secondary_claims
- CPU job `b9d88f78-5bb` completed the hardened end-to-end reproduction after the method was changed to ignore fold-count metadata even if a stale public archive contains it.
- Verified public acquisition archives now contain only measurements, kernel, and config arrays; private eval archives retain labels and fold counts only for scoring.
- `python validate.py --compare` passed, and all five experiments still clear the 20 dB MSE-gain quality gate with reproduced gains of 30.16, 36.73, 42.85, 41.14, and 39.69 dB.

## Stop Justification
- Final verification confirms milestone `secondary_claims`: the workspace reproduces the dynamic-range and bit-depth robustness claims on the scoped synthetic low-bit HDR benchmark, with method-agnostic evaluation and no privileged public fold-count metadata.
