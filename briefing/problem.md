# Problem Definition

Recover an off-grid sparse spike train from low-bit **modulo** samples of a
smooth, filtered high-dynamic-range signal.

Each scene is a continuous-time pair of positive spikes (a strong and a weak
reflection, as in time-of-flight imaging)

`s(t) = Gamma[0] delta(t - tau[0]) + Gamma[1] delta(t - tau[1])`

observed through a known smooth pulse `psi` (a Gaussian with standard
deviation `kernel_sigma` samples) on `N = 501` samples:

`g[n] = sum_k Gamma[k] psi(n - tau[k])`,  `max_n |g[n]| = DR * lambda`.

The analog signal carries additive Gaussian thermal noise `w[n]`
(standard deviation `thermal_noise_std`, in units of `lambda`).  It is
digitised by a modulo ADC with folding threshold `lambda`, input range
`[-lambda, lambda]` and a `B`-bit uniform quantizer:

`y[n] = Q_B( M_lambda(g[n] + w[n]) )`,
`M_lambda(x) = 2 lambda ( frac(x / (2 lambda) + 1/2) - 1/2 )`.

`DR` is 10, 20 or 30 (the signal is 10-30 times larger than the ADC range)
and `B` is 3, 5 or 8 bits.  Scenes vary in spike positions, separation (60-90
samples), weak/strong amplitude ratio (about 7-13) and which spike comes
first.

The goal is to recover, from `y` alone, both

1. the high-dynamic-range waveform `g[n]` (amplitude super-resolution), and
2. the two off-grid spike times `tau[k]` (temporal super-resolution),

including the weak reflection, which coarse quantization tends to bury.

A conventional ADC with the same input range and bit budget clips the signal;
the evaluation compares every method against recovery from such a clipping
ADC.

## What a method receives and returns

A method is an executable entry point `scripts/methods/<name>.sh`, called as

    bash scripts/methods/<name>.sh <input.npz> <output.npz>

`<input.npz>` (load with `allow_pickle=False`) contains:

| array | meaning |
|---|---|
| `modulo_samples` | `(trials, 501)` quantized modulo samples `y` |
| `kernel_grid`, `kernel` | samples of the pulse `psi` on integer offsets `-250..250` |
| `kernel_sigma` | pulse width (samples) |
| `lambda_value` | folding threshold (1.0) |
| `num_spikes` | `K = 2` |
| `quant_bits` | `B` |
| `thermal_noise_std` | std of the analog noise |

`<output.npz>` must contain plain numeric arrays

| array | meaning |
|---|---|
| `reconstruction` | `(trials, 501)` estimate of `g[n]` (absolute level, no free offset) |
| `taus` | `(trials, 2)` spike-time estimates in samples, within `[0, 500]` |

The input carries no labels and no samples from the second (conventional)
ADC.  A visible training slice with labels is written to `data/synthetic/`
by `scripts/download.sh` (`train_<experiment>.npz` holds method inputs,
`train_<experiment>_labels.npz` the clean waveforms, spike times and
amplitudes); `data/us_sres_synthetic.py` is the public generator.  The
scored test scenes are different, hidden, and never written to disk.

The paper's hardware time-of-flight tensors are not released, so the
benchmark is a synthetic substitute that keeps the paper's Fig. 2 signal
model (K = 2, N = 501, weak/strong mixture, DR = 10-30 lambda, 3-8 bits).
