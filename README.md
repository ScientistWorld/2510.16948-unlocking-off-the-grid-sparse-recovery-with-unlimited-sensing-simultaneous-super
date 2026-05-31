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

# Paper's Method

How the paper approaches the problem, i.e. the paper's core contributions.

## Key Contribution

<!-- What is the paper's main contribution? -->

## Approach

<!-- How does the paper solve the problem? Key ideas, architecture, algorithm. -->

## Main Claims

<!-- What are the paper's central claims? Which are primary vs. secondary? -->
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

The full paper's robust SRes-IterSiS algorithm alternates rational-polynomial
residue recovery in the difference domain with spectral spike estimation. This
compact environment does not implement that full robust loop. It implements
the Theorem 2 nonlinear modulo finite-difference path, which is the core
mechanism behind the digital super-resolution gain, then solves the
spike-estimation subproblem by direct continuum least-squares refinement
against the known pulse shape. That scaled reproduction is intended to support
the central low-bit HDR recovery claim, not the paper's hardware-robust
secondary claims.

---

# Evaluation

`scripts/evaluate.sh` reads private evaluation datasets and saved method
outputs, then writes `scoring/scores.json`. Method scripts consume the matching
public acquisition files, which omit `clean`, `taus`, and `amplitudes`. The
compact reproduction evaluates three low-bit HDR settings with dynamic range
`10`, `20`, and `30` times the folding threshold.

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

- `quant_bits`: ADC bit budget. Improvements must not rely on increasing it.
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


---

# Reproduction Milestones

**Current: core_claim_plus**
