# Progress

## What Works

- Implemented deterministic synthetic off-grid ToF-like benchmarks following
  the paper's Fig. 2 setup: `K=2`, weak/strong amplitude ratio 10, 3-bit modulo
  acquisition, and dynamic-range settings of 10, 20, and 30 times the folding
  threshold.
- Implemented the paper's core US-SRes computation: centered modulo sensing,
  nonlinear finite-difference recovery of `Delta g`, anti-difference HDR
  signal recovery, and sparse off-grid spike estimation.
- Added a compact SRes-IterSiS-style refinement for the continuation: rational
  `P/Q` residue fitting in the differentiated folded domain, fold-residue
  quantization to `2 lambda Z`, and matrix-pencil spectral initialization for
  the spike-estimation step.
- Implemented a conventional clipped-ADC sparse recovery baseline and a
  method-agnostic evaluator.
- Split generated datasets into public acquisition files for methods and
  private label files for evaluation, reducing the chance that future methods
  accidentally train or infer from hidden labels.

## Results

- Local validation on 2026-05-31 passed with `python validate.py --compare`.
- CPU job `5ad9d555-3dc` showed that always applying the compact rational
  residue update was unstable on the quantized synthetic benchmark: DR10 gained
  only 4.66 dB, while DR20 and DR30 were worse than the clipped baseline. That
  result is treated as a failed extension, not as a reproduced claim.
- The method now treats the rational `P/Q` residue update as an IterSiS
  candidate and accepts it only if the candidate improves the sparse
  reconstruction residual over the finite-difference theorem path.
- `scripts/run.sh` now includes a quality gate requiring at least 20 dB MSE
  gain over the clipped baseline in every scored dynamic-range setting.
- Official CPU container job `9db3b291-cd4` completed successfully after the
  public/private dataset split and passed `python validate.py --compare`.
- Earlier CPU job `8a2d4851-d38` verified the same scoped reproduction before
  the split.
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

- Verify the repaired adaptive IterSiS/P2 spectral path in the container and
  compare its scores against the existing core-claim results.
- Add bit-depth sweeps for broader coverage of Fig. 2 after the upgraded method
  is confirmed stable.
- Extend the compact residue refinement toward the full hardware-calibrated
  robust IterSiS implementation if additional evidence is needed.
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
  fitting/matrix pencil after residue recovery. The continuation adds this as
  the P2 initializer, but keeps a continuum least-squares fallback because the
  nonperiodic Gaussian substitute can make the plain Fourier quotient
  ill-conditioned.
- Algorithm scope: the continuation adds a compact rational residue-recovery
  loop from Section III, but it is still scaled to the synthetic benchmark and
  lacks the paper's hardware-specific calibration and full initialization
  sweep.
