# Overview

This paper studies off-grid sparse spike recovery when measurements are both
coarsely sampled and low-bit quantized. Conventional ADCs clip strong signals
or bury weak ones under quantization noise. The proposed US-SRes method uses
modulo sensing to avoid clipping, then recovers the hidden integer residues and
performs spectral super-resolution to estimate spike times and amplitudes.

The reproduction package implements the paper's modulo finite-difference
recovery path on a deterministic synthetic weak/strong ToF-like benchmark.
The hardware ToF data and the full robust SRes-IterSiS loop are not reproduced;
the packaged experiment focuses on the central Fig. 2-style claim that modulo
sensing can retain high-dynamic-range information under a fixed low bit budget
where conventional clipped acquisition fails.

---

# Problem Definition

Recover an off-grid sparse spike train from low-bit samples of a smooth,
filtered signal. Each trial contains a continuous-time sparse scene

`s(t) = sum_k Gamma[k] delta(t - tau[k])`

observed through a known smooth pulse `psi` on a coarse temporal grid:

`g[n] = sum_k Gamma[k] psi(nT - tau[k])`.

The difficult regime is a weak/strong two-spike mixture with high dynamic
range: one reflection is about ten times stronger than the other, and the
signal exceeds the low-bit ADC range. A successful solution must recover both
the high-dynamic-range waveform and the off-grid spike times from the saved
measurements.

The included benchmark is synthetic because the paper's hardware ToF tensors
are not released with the manuscript. It follows the paper's Fig. 2 setting:
`K=2`, `N=501`, weak/strong amplitude ratio `10`, low-bit quantization, and
dynamic range much larger than the ADC range.

---

# Method

The paper proposes Unlimited-Sensing Super-Resolution (US-SRes) for recovering
continuous spike locations and amplitudes from modulo-folded, low-bit samples.

Core computation implemented here:

1. Acquire low-dynamic-range samples with the centered modulo map
   `M_lambda(g) = 2 lambda (frac(g/(2 lambda) + 1/2) - 1/2)`.
2. Use smoothness of the filtered spike signal to make finite differences
   small enough that `M_lambda(Delta y) = Delta g`.
3. Recover the high-dynamic-range signal up to an additive constant by
   anti-differencing the recovered `Delta g`.
4. Estimate off-grid spike times and amplitudes from the recovered
   high-dynamic-range waveform.

The robust SRes-IterSiS component is implemented at compact synthetic scale.
It alternates a P1-style rational `P/Q` fold-residue fit in the differentiated
domain, quantization of the residue onto `2 lambda Z`, anti-difference signal
recovery, and a P2 spike-estimation step using matrix-pencil spectral
initialization plus continuous least-squares refinement. The implementation
estimates the residue model degree from its own reconstruction residual rather
than reading the private clean-signal fold count.

This is still scaled down relative to the hardware-calibrated paper algorithm:
it uses deterministic synthetic weak/strong ToF-like waveforms instead of the
undistributed hardware tensors, keeps a small number of IterSiS
initializations, and retains a continuum least-squares fallback for the
nonperiodic Gaussian substitute when the Fourier quotient is ill-conditioned.

---

# Evaluation

`scripts/evaluate.sh` reads private evaluation datasets and saved method
outputs, then writes `scoring/scores.json`. Method scripts consume the matching
public acquisition files, which omit `clean`, `taus`, and `amplitudes`. The
compact reproduction evaluates three 3-bit HDR settings with dynamic range
`10`, `20`, and `30` times the folding threshold, plus 5-bit and 8-bit
settings at the middle dynamic range.

Primary metric:

- `mse_gain_over_conventional_db`: reconstruction MSE improvement over the
  conventional clipped-ADC sparse recovery baseline. The paper reports at
  least 30 dB gain across the comparable Fig. 2 low-bit HDR settings.

Additional benefit metrics:

- `psnr_db`: waveform reconstruction PSNR after removing the arbitrary DC
  offset left by anti-difference recovery.
- `time_mae_samples`: mean absolute error of the recovered off-grid spike
  locations, in sample units.

Constraint metrics:

- `quant_bits`: ADC bit budget fixed by each named experiment. Improvements
  must not rely on increasing it within an experiment.
- `dynamic_range_x`: input dynamic range in multiples of the folding threshold.
- `amplitude_ratio`: weak/strong mixture severity.
- `mean_fold_count`: average number of modulo folds in the generated signals.

The evaluator is method-agnostic. It imports only `eval/` and reads artifacts
from `checkpoints/*.npz`; it does not import the proposed implementation.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 15m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

<!-- Write your progress here -->

</details>

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 30m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 30m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 30m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 15m | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 17m | **GPU**: 0.0h
- **Jobs**: 5 total (5 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 5 total (5 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 4m | **GPU**: 0.0h
- **Jobs**: 5 total (5 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 10m | **GPU**: 0.0h
- **Jobs**: 7 total (7 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 7m | **GPU**: 0.0h
- **Jobs**: 8 total (8 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

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

</details>


---

# Reproduction Milestones

**Current: secondary_claims**

## Stop Justification
- Completed at milestone `secondary_claims`.
