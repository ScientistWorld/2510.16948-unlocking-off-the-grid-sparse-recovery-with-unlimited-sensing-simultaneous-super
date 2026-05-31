# Problem Definition

Recover an off-grid sparse spike train from low-bit samples of a smooth,
filtered signal. Each trial contains a continuous-time sparse scene

`s(t) = sum_k Gamma[k] delta(t - tau[k])`

observed through a known smooth pulse `psi` on a coarse temporal grid:

`g[n] = sum_k Gamma[k] psi(nT - tau[k])`.

The difficult regime is a weak/strong two-spike mixture with high dynamic
range: one reflection is about ten times stronger than the other, and the
signal exceeds the low-bit ADC range. A successful solution must recover both
the high-dynamic-range waveform and the off-grid spike times from the saved
measurements.

The included benchmark is synthetic because the paper's hardware ToF tensors
are not released with the manuscript. It follows the paper's Fig. 2 setting:
`K=2`, `N=501`, weak/strong amplitude ratio `10`, low-bit quantization, and
dynamic range much larger than the ADC range.
