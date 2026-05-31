# Evaluation Targets

The standard benchmark contains three dynamic-range experiments and two
additional bit-depth experiments:

- `synthetic_lowbit_hdr_dr10`
- `synthetic_lowbit_hdr_dr20`
- `synthetic_lowbit_hdr_dr30`
- `synthetic_lowbit_hdr_dr20_bits5`
- `synthetic_lowbit_hdr_dr20_bits8`

Primary target:

- Increase `mse_gain_over_conventional_db` over the clipped conventional
  sparse-recovery baseline.

Constraint targets:

- Keep `quant_bits` fixed to each experiment's specified value.
- Preserve the experiment's specified high dynamic range.
- Preserve the weak/strong amplitude ratio (`amplitude_ratio = 10`).
- Report `mean_fold_count` to confirm that the measurement stream actually
  contains modulo folds.

All targets above appear in both `scoring/reference.json` and
`scoring/scores.json`.
