# Method

The paper proposes Unlimited-Sensing Super-Resolution (US-SRes) for recovering
continuous spike locations and amplitudes from modulo-folded, low-bit samples.

Core computation implemented here:

1. Acquire low-dynamic-range samples with the centered modulo map
   `M_lambda(g) = 2 lambda (frac(g/(2 lambda) + 1/2) - 1/2)`.
2. Use smoothness of the filtered spike signal to make finite differences
   small enough that `M_lambda(Delta y) = Delta g`.
3. Recover the high-dynamic-range signal up to an additive constant by
   anti-differencing the recovered `Delta g`.
4. Estimate off-grid spike times and amplitudes from the recovered
   high-dynamic-range waveform.

The robust SRes-IterSiS component is implemented at compact synthetic scale.
It alternates a P1-style rational `P/Q` fold-residue fit in the differentiated
domain, quantization of the residue onto `2 lambda Z`, anti-difference signal
recovery, and a P2 spike-estimation step using matrix-pencil spectral
initialization plus continuous least-squares refinement. The implementation
estimates the residue model degree from its own reconstruction residual rather
than reading the private clean-signal fold count.

This is still scaled down relative to the hardware-calibrated paper algorithm:
it uses deterministic synthetic weak/strong ToF-like waveforms instead of the
undistributed hardware tensors, keeps a small number of IterSiS
initializations, and retains a continuum least-squares fallback for the
nonperiodic Gaussian substitute when the Fourier quotient is ill-conditioned.
