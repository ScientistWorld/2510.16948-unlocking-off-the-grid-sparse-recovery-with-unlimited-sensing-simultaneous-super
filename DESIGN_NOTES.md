# Train/Test Evaluation Design Notes

Checked:

- Read `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. Train invokes `eval/train/` and writes `scoring/scores_train.json`; test invokes `eval/test/` and writes `scoring/scores_test.json`.
- Checked that neither split imports from the other and that both evaluators read saved NPZ artifacts rather than importing or rerunning `method/`.
- Checked that default discovery enumerates checkpoint outputs by experiment suffix instead of hardcoding a single method name.
- Checked for paper-agreement metric names and did not find `deviation_from_paper`, `fit_to_published`, `reproduction_error`, or equivalent scored metrics.
- Confirmed no `scoring/scores_train.json` or `scoring/scores_test.json` stubs are present.
- Ran `bash -n` on both split scripts. I did not run evaluators or experiments.

Changed:

- Added method-dependent triangulation metrics to both `eval/train/` and `eval/test/`:
  - `weak_tau_mae_samples` to expose weak-reflection localization failures that average timing error can hide.
  - `tau_max_error_samples` to penalize recovering only one of the two spikes.
  - `hard_fold_signal_mse` to score reconstruction on the higher-fold half of each slice.
  - `wrapped_measurement_mae` to check that reconstructions remain consistent with the modulo sensor observations.
- Added a top-level `slice` marker to split score artifacts (`train` or `test`) so copy-paste mistakes are easier to detect.
- Updated `scoring/reference.json` so every metric has `higher_is_better`, `coefficient`, and `description`.
- Reduced coefficients on fixed configuration checks (`dynamic_range_x`, `quant_bits`, `amplitude_ratio`, `mean_fold_count`) and shifted more weight to method-dependent benefit/constraint metrics.

Runtime concerns for the next runner iteration:

- I could not run Python/Numpy validation on this login node because NumPy is not installed locally. The runner should verify that the new metrics produce finite values for all five experiments.
- The train/test split still uses complementary rows from the same saved evaluation datasets. That keeps difficulty calibrated and lightweight, but if label files are visible to a future agent, the split is weaker than a truly private held-out dataset.
- `wrapped_measurement_mae` depends on `modulo_samples` and `lambda_value` being present in every evaluation NPZ. The dataset generator writes both, but the runner should confirm existing artifacts match that contract.
