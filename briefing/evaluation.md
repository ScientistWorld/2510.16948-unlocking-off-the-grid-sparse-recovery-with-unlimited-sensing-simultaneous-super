# Evaluation

How success is measured. Describe only the metrics, targets, and evaluation procedure — do NOT describe the paper's method or how they achieved these results. Think of this as a general evaluation protocal for other scientists trying to solve the same problem, where they should not see this paper's solution.

## Metrics

<!-- What metrics are used? How are they computed? What does higher/lower mean? -->

## Baselines and Targets

<!-- What performance levels exist as reference points? Include the paper's reported numbers as targets, and any standard baselines. A scientist agent should know what "good" looks like. -->

## Evaluation Protocol

<!-- How should evaluation be run? What data split, what conditions? Any important details about how to compare fairly (e.g., fixed seeds, specific test sets, averaging over runs). -->
# Evaluation

`scripts/evaluate.sh` reads a benchmark dataset and saved method outputs, then
writes `scoring/scores.json`.

Primary metric:

- `mse_gain_over_conventional_db`: reconstruction MSE improvement over the
  conventional clipped-ADC sparse recovery baseline. The paper reports at
  least 30 dB gain in the comparable Fig. 2 low-bit HDR setting.

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
