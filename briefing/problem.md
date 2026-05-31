# Problem Definition

What problem does this paper address? Write this so that someone with no knowledge of the paper can understand what needs to be solved and how success is measured.

Do NOT describe the paper's method or solution here — only the problem itself. Think about if a future scientist agent try to solve this problem from scratch without knowing what approach the paper took. If you leak the solution, you compromise the benchmark.

## Research Question

<!-- What problem or challenge does this paper tackle? What gap in existing work does it address? -->

## Why It Matters

<!-- Why is this problem important? What would a good solution enable? Make it short -->

## Success Criteria

<!-- What would a successful solution look like? What properties should it have? This is about the goal, not the paper's specific approach. Make it short -->
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
