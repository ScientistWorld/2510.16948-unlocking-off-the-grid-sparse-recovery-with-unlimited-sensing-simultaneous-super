# Evaluation

`scripts/evaluate.sh` reads the benchmark datasets and saved method outputs,
then writes `scoring/scores.json`. The compact reproduction evaluates three
low-bit HDR settings with dynamic range `10`, `20`, and `30` times the folding
threshold.

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
