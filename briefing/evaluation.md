# Evaluation

Scoring runs every registered method (each `scripts/methods/<name>.sh`) on
fresh acquisitions and recomputes every number from the raw output arrays.
Nothing a method writes besides `reconstruction` and `taus` is read.

* `bash scripts/evaluate_train.sh` scores the visible train slice (64 scenes
  per experiment, public seeds) and writes `scoring/scores_train.json`.
  `bash scripts/evaluate.sh` does the same and writes `scoring/scores.json`.
* `bash scripts/evaluate_test.sh` scores the hidden test slice (200 scenes per
  experiment from private seeds in `eval/test/`) and writes
  `scoring/scores_test.json`.  Only this file is ranked.  The test inputs are
  built at test time in a temporary directory; the answers are rebuilt in
  memory after the methods return.

Both slices come from the same generator, so an honest method scores alike on
both.  The comparison row `conventional_clip_sres` is computed by the
evaluator itself from a second, conventional ADC (same input range
`[-lambda, lambda]`, same bit budget, so it clips) followed by a clipping-
unaware sparse least-squares fit.  No file in the workspace can change it.

## Experiments

| experiment | dynamic range | bits |
|---|---|---|
| `synthetic_lowbit_hdr_dr10` | 10 lambda | 3 |
| `synthetic_lowbit_hdr_dr20` | 20 lambda | 3 |
| `synthetic_lowbit_hdr_dr30` | 30 lambda | 3 |
| `synthetic_lowbit_hdr_dr30_bits5` | 30 lambda | 5 |
| `synthetic_lowbit_hdr_dr30_bits8` | 30 lambda | 8 |

All use K = 2, N = 501, pulse width 20 samples and thermal noise std 0.03
lambda.  The bit budget and dynamic range are properties of the acquisition
the evaluator generates; a method cannot change them.

## Metrics (per experiment)

| metric | direction | coefficient | definition |
|---|---|---|---|
| `mse_gain_over_conventional_db` (primary) | higher | 1.0 | `10 log10(MSE_conv / MSE_method)`, waveform MSE pooled over all scenes |
| `psnr_db` | higher | 0.45 | mean over scenes of `10 log10(max|g|^2 / MSE_scene)` |
| `time_mae_samples` | lower | 0.45 | mean absolute error of both spike times (sorted matching) |
| `weak_tau_mae_samples` | lower | 0.35 | spike-time error of the weaker spike only |
| `separation_error_samples` | lower | 0.25 | error of the recovered spike separation |

The waveform is compared at its absolute level; an arbitrary DC offset counts
as error.

## Failures

An experiment fails for a method when its entry point exits non-zero, times
out (2 h per experiment), writes no output, writes an unreadable or pickled
archive, writes arrays of the wrong shape or dtype, writes non-finite values,
spike times outside `[0, 500]`, or a waveform larger than `4 * DR * lambda`.
A failed experiment receives the worst value of every metric: the gain and
PSNR of a maximal-error valid output, and 500 samples for each timing error.

## Ranking

Each metric's improvement over the reference is taken in its better
direction, scaled by its coefficient and by its spread across ranked
attempts, and summed with the experiment weights (0.2 each).
