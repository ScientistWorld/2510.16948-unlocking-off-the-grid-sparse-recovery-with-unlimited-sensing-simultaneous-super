# Evaluation Targets

Five scored experiments (weight 0.2 each), all on hidden test scenes:
`synthetic_lowbit_hdr_dr10`, `synthetic_lowbit_hdr_dr20`,
`synthetic_lowbit_hdr_dr30`, `synthetic_lowbit_hdr_dr30_bits5`,
`synthetic_lowbit_hdr_dr30_bits8`.

Benefit targets (amplitude super-resolution):

- `mse_gain_over_conventional_db` (primary, coefficient 1.0): waveform MSE
  improvement over the evaluator's conventional clipping-ADC recovery.  The
  paper reports at least 30 dB across dynamic ranges and bit depths.
- `psnr_db` (0.45): mean per-scene waveform PSNR.

Timing targets (temporal super-resolution, which the paper claims is achieved
without giving up amplitude fidelity):

- `time_mae_samples` (0.45): error of both spike times.
- `weak_tau_mae_samples` (0.35): error of the weak reflection, which coarse
  quantization buries.
- `separation_error_samples` (0.25): error of the inter-spike separation.

Constraints (enforced by construction, not scored): the bit budget, dynamic
range, sensor noise and number of spikes are set by the evaluator's
acquisition; methods only see modulo samples; outputs must be finite, of the
right shape, with spike times inside the record and waveform magnitude below
`4 * DR * lambda`, or the experiment fails with worst values.

Every target above appears in `scoring/reference.json` and in the score files.
