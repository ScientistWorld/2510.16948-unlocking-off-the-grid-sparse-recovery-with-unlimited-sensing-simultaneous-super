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

The full paper's robust SRes-IterSiS algorithm alternates rational-polynomial
residue recovery in the difference domain with spectral spike estimation. This
compact environment does not implement that full robust loop. It implements
the Theorem 2 nonlinear modulo finite-difference path, which is the core
mechanism behind the digital super-resolution gain, then solves the
spike-estimation subproblem by direct continuum least-squares refinement
against the known pulse shape. That scaled reproduction is intended to support
the central low-bit HDR recovery claim, not the paper's hardware-robust
secondary claims.
