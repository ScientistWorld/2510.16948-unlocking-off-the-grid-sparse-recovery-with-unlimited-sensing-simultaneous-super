# Progress

## What Works

- Implemented a deterministic synthetic off-grid ToF-like benchmark following
  the paper's Fig. 2 setup: `K=2`, weak/strong amplitude ratio 10, low-bit
  modulo acquisition, and dynamic range above the conventional ADC range.
- Implemented the paper's core US-SRes computation: centered modulo sensing,
  nonlinear finite-difference recovery of `Delta g`, anti-difference HDR
  signal recovery, and sparse off-grid spike estimation.
- Implemented a conventional clipped-ADC sparse recovery baseline and a
  method-agnostic evaluator.

## Results

- Local smoke test before job submission reached the paper's core qualitative
  claim on the synthetic benchmark: US-SRes improved waveform MSE by 36.7 dB
  over the clipped conventional baseline and recovered spike locations with
  about 0.92 sample mean absolute error.
- Paper reference for comparable low-bit HDR recovery: Fig. 2 reports at least
  30 dB MSE gain across dynamic range and quantization settings; Table I
  reports about 40 dB PSNR in 3-bit ToF cases.

## Remaining

- Submit the packaged reproduction as a compute job and record official job
  results in `scoring/scores.json`.
- Add larger matrices of bit-depth/dynamic-range settings for milestones above
  `core_claim`.

## Issues

- The paper's hardware ToF tensors are not included with the manuscript, so the
  first benchmark uses a synthetic substitute preserving the signal model and
  low-bit HDR regime.

## Deviations from Paper

- Data: the paper evaluates on hardware-acquired ToF tensors that are not
  distributed with the manuscript. This workspace substitutes deterministic
  synthetic weak/strong filtered spike signals following the paper's Fig. 2
  parameters (`K=2`, `N=501`, amplitude ratio 10, low-bit quantization, high
  dynamic range).
- Spike-estimation solver: the paper's robust implementation uses spectral
  fitting/matrix pencil after residue recovery. The synthetic benchmark uses a
  direct continuum sparse-deconvolution refinement for the same P2 objective
  because the nonperiodic Gaussian substitute made the plain Fourier ratio
  ill-conditioned. The modulo sensing and nonlinear finite-difference residue
  recovery, which are the paper's central computational steps, are unchanged.
