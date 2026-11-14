# Progress

## What Works

- Implemented deterministic synthetic off-grid ToF-like benchmarks following
  the paper's Fig. 2 setup: `K=2`, weak/strong amplitude ratio 10, 3-bit modulo
  acquisition at dynamic-range settings of 10, 20, and 30 times the folding
  threshold, plus DR20 extensions at 5 and 8 bits.
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
- Hardened the public acquisition format so public synthetic datasets no
  longer expose the clean-signal fold count. The method also ignores any
  stale `folds` array if one appears in an input archive and estimates its
  IterSiS residue model degree from its own reconstruction residual.

## Results

- Local validation on 2026-05-31 passed with `python validate.py --compare`.
- CPU job `5ad9d555-3dc` showed that always applying the compact rational
  residue update was unstable on the quantized synthetic benchmark: DR10 gained
  only 4.66 dB, while DR20 and DR30 were worse than the clipped baseline. That
  result is treated as a failed extension, not as a reproduced claim.
- The method now treats the rational `P/Q` residue update as an IterSiS
  candidate and accepts it only if the candidate improves the sparse
  reconstruction residual over the finite-difference theorem path.
- `scripts/run.sh` now includes a quality gate requiring every reference
  experiment to appear in `scores.json` and clear at least 20 dB MSE gain over
  the clipped baseline.
- CPU job `1d35c7b1-6b0` verified the repaired adaptive IterSiS path and
  passed the 20 dB quality gate. The regenerated scores restored 30.16 dB,
  36.73 dB, and 39.69 dB MSE gains at DR10, DR20, and DR30 with 3-bit sensing.
- CPU job `b3e73f92-59e` verified the expanded benchmark with DR20 5-bit and
  8-bit settings. The added settings achieved 42.85 dB and 41.14 dB MSE gain
  over the clipped baseline, respectively.
- Official CPU container job `9db3b291-cd4` completed successfully after the
  public/private dataset split and passed `python validate.py --compare`.
- Continuation audit on 2026-05-31 confirmed the implementation is a
  recognizable US-SRes reproduction rather than a surrogate, while identifying
  benchmark-hygiene cleanup in the main evaluator. Updated
  `eval/evaluate_us_sres.py` so `scores.json` includes the same weak-target,
  folded-region, and wrapped-measurement consistency metrics already computed
  by the train/test evaluators, and made explicit-argument scoring infer the
  submitted method name from artifact paths.
- Final verification completed on 2026-05-31. The standalone default evaluator
  now discovers all method outputs under `checkpoints/`, `scores.json` contains
  the full benefit and constraint metric surface for the five reproduced
  experiments, and `python validate.py --compare` passes.
- A follow-up integrity audit on 2026-05-31 found that per-trial fold counts
  were visible in the public synthetic files and used as IterSiS metadata.
  This has been removed from newly generated public files, and the method was
  hardened to ignore that metadata even if a stale archive contains it.
- CPU job `b9d88f78-5bb` regenerated data, checkpoints, and scores from
  scratch after the metadata hardening. It passed the core-claim quality gate
  and `python validate.py --compare`. Public acquisition archives now contain
  only measurements, kernel arrays, and config; private eval archives retain
  labels and fold counts for scoring.
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
  parameters (`K=2`, `N=501`, amplitude ratio 10, low-bit quantization,
  dynamic ranges 10/20/30, and additional DR20 bit-depth settings).
- Spike-estimation solver: the paper's robust implementation uses spectral
  fitting/matrix pencil after residue recovery. The continuation adds this as
  the P2 initializer, but keeps a continuum least-squares fallback because the
  nonperiodic Gaussian substitute can make the plain Fourier quotient
  ill-conditioned.
- Algorithm scope: the continuation adds a compact rational residue-recovery
  loop from Section III, but it is still scaled to the synthetic benchmark and
  lacks the paper's hardware-specific calibration and full initialization
  sweep.
- Algorithm metadata: the paper's Algorithm 1 accepts the number of folds `M`
  as an input. The benchmark no longer provides the true clean-signal fold
  count to the submitted method; this reproduction estimates the compact
  residue degree from the current reconstruction residual instead.

## Iteration 11 (hardening)

- Rebuilt evaluation around hidden test scenes generated inside `eval/test/`,
  an evaluator-computed conventional baseline, a method registry
  (`scripts/methods/*.sh`) and strict output validation with worst-value
  failures.
- Restored the reference to Algorithm 1 and added Section III sensor noise so
  the robust residue loop is exercised (DR30 3/5/8-bit settings).
- One CPU job (`2af8d91e-d18`) produced the official scores and the audit of
  variants and shortcuts; see `HARDENING.md`.
