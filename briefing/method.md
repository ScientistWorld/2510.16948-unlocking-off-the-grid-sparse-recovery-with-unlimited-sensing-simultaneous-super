# Method (reference: SRes-IterSiS, the paper's Algorithm 1)

The paper proposes Unlimited-Sensing Super-Resolution (US-SRes): sense
`M_lambda(g)` with a modulo ADC so that a low-bit quantizer never clips, then
recover the folding residue and the spikes.  The reference implementation is
`method/us_sres.py`, registered as `scripts/methods/us_sres.sh`.

Model in the first-difference domain (Eq. 32): `Delta y = Delta g - eps`,
where the residue `eps` is a sparse train of multiples of `2 lambda` at the
fold instants.  Robust recovery alternates two sub-problems (Section III):

```
eps_tilde^[0] = -Delta y                          (no signal estimate yet)
for i = 1 .. i_max:
  P1  residue recovery (Eqs. 35-43): fit eps_tilde with a rational model
      P/Q (deg Q = M folds, deg P = M - 1) by the iterative weighted least
      squares of Eq. (38) from several Q^[0] seeds; keep the iterate whose
      lattice-quantized reconstruction (Eq. 43) is closest to eps_tilde.
  g_tilde = anti-difference(Delta y + eps)        (HDR signal up to a constant)
  P2  spike estimation (Eqs. 45-47): s[l] = DFT(g_tilde)[l] / DFT(psi)[l]
      for |l| <= I_psi; a first spectral fit on l >= 1 initialises s[0];
      the remaining constant c0 is the small eigenvalue of the Toeplitz
      matrix of s (rank-K structure); matrix pencil -> tau_k;
      least squares -> Gamma_k.
  eps_tilde = Delta(sum_k Gamma_k psi(n - tau_k)) - Delta y      (Eq. 34)
stop when the residue stops changing; output tau_k and
g[n] = sum_k Gamma_k psi(n - tau_k).
```

Implementation choices (documented departures):

* Eq. (38) is solved in the partial-fraction basis relative to the previous
  denominator `Q^[j-1]` (the same weighted least squares; new poles are the
  zeros of `Q / Q^[j-1]`), with `Q` monic instead of the `<q^[0], q> = 1`
  normalisation.  A degree-30 monomial `Q` whose roots cluster on the pulse
  edges is numerically unusable in double precision.
* Folds are on the sampling grid, where the closed form (39) for the residues
  is 0/0; residues are read on the grid at the pole positions (Eq. 36) and
  quantised (Eq. 43).  The literal `P/Q` evaluation (Eq. 35 + 43) is kept as a
  second candidate in the selection of Algorithm 1, lines 10-12.
* `M` is not given to the method; it is estimated each outer iteration as the
  number of non-zero lattice residues of `eps_tilde`.
* The paper writes `eps_tilde^[0] <- Delta y`; with `eps_tilde = Delta g - Delta y`
  (Eq. 34) and no signal estimate, the seed is `-Delta y`.
* `I_psi` is the largest frequency where `|DFT(psi)|` is at least 5% of its
  peak (9 for this kernel); the Toeplitz order for the DC step is 4.
* At most 6 outer iterations, 3 weighted-LS iterations and 2 seeds per P1.

There is no learned component and no training.
