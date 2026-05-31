# Progress

## What Works

- Implemented deterministic synthetic off-grid ToF-like benchmarks following
  the paper's Fig. 2 setup: `K=2`, weak/strong amplitude ratio 10, 3-bit modulo
  acquisition, and dynamic-range settings of 10, 20, and 30 times the folding
  threshold.
- Implemented the paper's core US-SRes computation: centered modulo sensing,
  nonlinear finite-difference recovery of `Delta g`, anti-difference HDR
  signal recovery, and sparse off-grid spike estimation.
- Implemented a conventional clipped-ADC sparse recovery baseline and a
  method-agnostic evaluator.
- Split generated datasets into public acquisition files for methods and
  private label files for evaluation, reducing the chance that future methods
  accidentally train or infer from hidden labels.

## Results

- Official CPU container job `8a2d4851-d38` completed successfully and passed
  `python validate.py --compare`.
- DR 10: US-SRes improved waveform MSE by 30.16 dB over the clipped
  conventional baseline, with 45.77 dB PSNR and 2.08 sample time MAE.
- DR 20: US-SRes improved waveform MSE by 36.73 dB over the clipped
  conventional baseline, with 52.91 dB PSNR and 0.97 sample time MAE.
- DR 30: US-SRes improved waveform MSE by 39.69 dB over the clipped
  conventional baseline, with 56.84 dB PSNR and 0.62 sample time MAE.
- Paper reference for comparable low-bit HDR recovery: Fig. 2 reports at least
  30 dB MSE gain across dynamic range and quantization settings; Table I
  reports about 40 dB PSNR in 3-bit ToF cases.

## Remaining

- Add bit-depth sweeps for broader coverage of Fig. 2.
- Implement the full robust rational IterSiS residue refinement and
  matrix-pencil spike initializer for closer coverage of Section III.
- Reproduce hardware ToF experiments if the undistributed tensors become
  available.

## Issues

- The paper's hardware ToF tensors are not included with the manuscript, so the
  first benchmark uses a synthetic substitute preserving the signal model and
  low-bit HDR regime.
- The login-node Python environment lacks `numpy`; end-to-end execution was
  verified in the scheduled container where `environment/setup.sh` installs the
  declared dependencies.

## Deviations from Paper

- Data: the paper evaluates on hardware-acquired ToF tensors that are not
  distributed with the manuscript. This workspace substitutes deterministic
  synthetic weak/strong filtered spike signals following the paper's Fig. 2
  parameters (`K=2`, `N=501`, amplitude ratio 10, low-bit quantization, and
  dynamic ranges 10/20/30).
- Spike-estimation solver: the paper's robust implementation uses spectral
  fitting/matrix pencil after residue recovery. The synthetic benchmark uses a
  direct continuum sparse-deconvolution refinement for the same P2 objective
  because the nonperiodic Gaussian substitute made the plain Fourier ratio
  ill-conditioned. The modulo sensing and nonlinear finite-difference residue
  recovery, which are the paper's central computational steps, are unchanged.
- Algorithm scope: the full robust SRes-IterSiS rational residue-recovery loop
  from Section III is not implemented, so the claimed milestone is limited to
  `core_claim`.
