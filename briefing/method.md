# Paper's Method

How the paper approaches the problem, i.e. the paper's core contributions.

## Key Contribution

<!-- What is the paper's main contribution? -->

## Approach

<!-- How does the paper solve the problem? Key ideas, architecture, algorithm. -->

## Main Claims

<!-- What are the paper's central claims? Which are primary vs. secondary? -->
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
4. Divide Fourier coefficients of the recovered signal by the known pulse
   response to obtain a sum-of-sinusoids sequence.
5. Estimate off-grid spike times using an annihilating-filter / matrix-pencil
   spectral fit, then estimate amplitudes by least squares.

The full paper's robust SRes-IterSiS algorithm alternates residue recovery in
the difference domain with spike estimation. The first benchmark uses the
exact nonlinear filtering path from Theorem 2, which is the core algorithmic
mechanism behind the reported digital super-resolution gain.
