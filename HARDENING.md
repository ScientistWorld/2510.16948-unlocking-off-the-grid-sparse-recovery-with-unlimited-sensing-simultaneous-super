# Hardening report (iteration 11)

**Outcome.** Better results now score higher and weaker ones lower, on paired
comparisons well outside the test's noise.  Every shortcut in `REDTEAM.md` is
closed or no longer pays.  This includes the brute force that used to tie the
reference: it now loses 31-33 dB in the three 30-lambda settings.

The reference is now the paper's Algorithm 1. On 200 hidden scenes per setting
it reproduces the paper's at-least-30-dB claim in all five settings (38-61 dB),
and it leaves 7-10 dB of measurable headroom in each.

All numbers below come from one CPU job (`2af8d91e-d18`, 13 minutes on one
core). It ran the final code through the **no-argument**
`scripts/evaluate_{train,test}.sh`, with every audit submission registered as
`scripts/methods/<name>.sh` next to the reference. Records:

- `redteam/hardening/results/` holds the audit score files, the analysis
  (`analysis.md`, `summary.json`) and the logs.
- `redteam/hardening/variants.py` holds every variant and shortcut.
- `scoring/scores_{train,test}.json` and `scores.json` hold the reference-only
  official scores from the same job.

`python validate.py --compare --post-design` passes.

## What changed

### Evaluation integrity

- **Test answers live only in `eval/test/`.** `eval/test/hidden_instances.json`
  holds private seeds for 200 scenes per experiment. The harness writes only
  the method inputs, to a temporary directory outside the workspace. The seed
  file is `chmod 000` while methods run. Answers are rebuilt in memory after
  the methods return.
  - No label, seed or test acquisition is on disk.
  - Train (64 scenes per experiment, public seeds) is exported to
    `data/synthetic/` with labels.
  - `eval/train` and `eval/test` each carry their own copy of the forward model
    and share no code.
- **The method runs on hidden inputs.** The method needs no training. Every
  executable `scripts/methods/<name>.sh` is a method, called as
  `<input.npz> <output.npz>`.
  - The test scores every entry point on disk, with no names hardcoded and no
    registry file. Deleting `scores_train.json` changes nothing.
  - The method input no longer contains conventional-ADC samples (previously a
    second ADC's data was public), the config dict, or the seed.
- **The comparison is fixed by `eval/`.** Each evaluator computes the
  conventional clipping-ADC baseline from the second ADC's samples itself (a
  vectorised version of the previous grid search plus refinement). The
  `checkpoints/conventional_*.npz` files are no longer read. Bit depth, dynamic
  range, noise, K and test size are set by the evaluator's own acquisition.
- **Every scored number is recomputed from raw arrays.** Outputs are loaded with
  `allow_pickle=False`. Only `reconstruction` and `taus` are read; extra fields
  and pre-written score files are ignored.
- **Impossible outputs fail, and failures get the worst values.** Any of the
  following fails the experiment:
  - a non-zero exit, a timeout (2 h), or a missing file;
  - a pickled or unreadable archive;
  - wrong shape or dtype, or NaN/inf values;
  - spike times outside [0, 500];
  - a waveform above 4·DR·λ.

  A failed experiment gets the worst attainable value of **every** metric: the
  gain and PSNR of a maximal-error valid output, and 500 samples for each
  timing error. A crashed method therefore still gets complete rows.
- **Metrics measure the paper's quantities only.** The four configuration
  "metrics" are removed, because they rewarded false metadata. Bits and
  dynamic range are now fixed by construction. Also removed:
  - `signal_mse`, a monotone duplicate of the gain;
  - `hard_fold_signal_mse`, which was redundant;
  - `wrapped_measurement_mae`, which rewards fitting noisy measurements (copying
    the input improved it) and is not a paper quantity;
  - `tau_max_error`.

  Added `separation_error_samples`, the inter-object separation error of
  Sections V-B and VI. Coefficients are now positive, with direction set by
  `higher_is_better`.

  Weights stay 0.2 per experiment. Coefficients are gain 1.0, PSNR 0.45, time
  error 0.45, weak-spike error 0.35, separation 0.25: amplitude
  super-resolution 1.45 against temporal super-resolution 1.05, the paper's
  two claims.

### Reference restored to the paper's method (`method/us_sres.py`)

The previous reference always ran an exhaustive pair search with continuous
refinement as a "fallback". In effect it *was* the brute force, which is why
the two tied. It also had extra candidates, a fitted DC offset, a capped
residue degree and a single outer iteration. The new reference is Algorithm 1:

- **Seed.** The residue seed is `ε̃⁰ = −Δy`.
- **P1.** A rational P/Q fit of the residue by the iterative weighted least
  squares of Eq. (38) from two Q⁰ seeds. The iterate is chosen by the
  Algorithm 1 MSE rule. Values are then quantised onto 2λℤ (Eq. 43).
- **Signal.** g̃ = Δ⁻¹(Δy + ε).
- **P2, relaxed problem (45).** The Fourier ratio DFT(g̃)/DFT(ψ) over
  |l| ≤ I_ψ. A spectral fit on l ≥ 1 initialises ŝ[0], and the Toeplitz
  eigenvalue step of Eqs. (46-47) removes the constant c₀. The matrix pencil
  gives τ; least squares gives Γ.
- **Update.** ε̃ = Δ(Σ Γψ) − Δy (Eq. 34). Iterate until the residue stops
  changing. The output waveform is Σ Γψ, with no free offset.

Departures, stated in `briefing/method.md`:

- Eq. (38) is solved in the partial-fraction basis relative to Q^[j−1]. It is
  the same objective, with Q monic instead of ⟨q⁰,q⟩=1. A monomial Q of degree
  about 30 with roots clustered on the pulse edges is numerically unusable,
  which is likely why the earlier rational step "degraded" results.
- Residues are read on the grid at the pole positions, because (39) is 0/0 for
  on-grid folds. The literal (35)+(43) evaluation stays as a second candidate.
- M is estimated from the data rather than supplied.
- I_ψ uses a 5 % spectral threshold, and the Toeplitz order is 4. The paper
  does not specify either.

### Scaling the setup so the test reaches the paper's problem

Previously the scenes satisfied first-difference unwrapping with a wide margin
(max |Δg| = 0.40λ), so the paper's robust machinery was never needed. Now:

- **Thermal noise.** Gaussian noise of std 0.03 λ is added before both ADCs.
  This is Section III's hardware distortion C1, the regime SRes-IterSiS was
  designed for.
- **Narrower pulse.** σ = 20 samples instead of 45, so the support fits in the
  window and the Fourier relaxation (45) is valid. At 30λ the slope reaches
  0.91λ per sample.
- **Bit-depth sweep moved to DR = 30** (`dr30_bits5`, `dr30_bits8`, replacing
  `dr20_bits5/8`). The noise makes naive unwrapping fail there.
- **Scene randomisation.** Positions, separation (60-90 samples), amplitude
  ratio (7-13) and order are randomised, so the generating process is not a
  fixed template.
- **Larger test.** 200 hidden scenes per setting instead of 32.

The calibration (`redteam/hardening/calibrate.py`, `calibration.log`) compared
five (σ, noise) settings.

- **Chosen setting (σ=20, noise 0.03).** Naive unwrapping fails on 100 / 18 /
  12 % of scenes at DR30 3/5/8 bits. The reference fails on 0 %.
- **σ=22, or noise 0.02.** Naive unwrapping almost never fails at 5-8 bits, so
  the brute force would win there.
- **σ=18.** Naive methods fail on every 30λ scene, which leaves no gradation.

## Do better results score higher? (variants, hidden test)

Before (old gym, from `REDTEAM.md`, quality-population ΔR): reference 38.08 dB
mean gain; `better_sensor_fit` 69.46 dB (+1.539); `weaker_no_unwrap` −0.73 dB
(−5.124).

After (mean over the five settings; ΔR uses the honest population
{reference, baseline, both better variants, both weaker variants, brute force,
alternate seed}, with the all-submissions population in brackets):

| method | mean gain dB | mean PSNR dB | time MAE | weak MAE | sep. err | ΔR |
|---|---:|---:|---:|---:|---:|---:|
| **reference `us_sres`** | 50.78 | 64.55 | 0.161 | 0.292 | 0.297 | 0 |
| better: + least-squares solve of P2 (44) | 58.89 | 72.19 | 0.085 | 0.154 | 0.152 | **+0.502** (+0.372) |
| better: + sensor-consistent (wrapped-residual) fit | 59.83 | 72.99 | 0.085 | 0.154 | 0.152 | **+0.560** (+0.415) |
| weaker: no residue sieving (one pass after naive unwrap) | 32.28 | 55.79 | 4.369 | 5.734 | 4.814 | **−1.238** (−0.738) |
| weaker: no unwrapping | −0.67 | 11.39 | 41.74 | 14.03 | 70.21 | **−6.022** (−2.570) |
| conventional clipping ADC (evaluator) | 0 | 12.06 | 11.00 | 9.77 | 5.93 | −4.066 |

Paired over the same 200 scenes (bootstrap 95 % CI), both better variants beat
the reference in **every setting on every metric (25/25)**:

- gain: +7.65 to +9.88 dB, each CI lower bound ≥ +7.0 dB;
- PSNR: +7.1 to +9.5 dB;
- time error: −0.016 to −0.22 samples, all CIs exclude 0;
- 93-98 % of scenes individually improve.

The no-sieving ablation equals the reference at DR10/20, where unwrapping never
fails. It loses 28-34 dB at DR30 (CI upper bound −25 dB). Train shows the same
ordering (`better_sensor_fit` +0.539, ablation −1.259).

## Seeds, noise, and train vs test

- **Seed.** Changing the reference's random Q⁰ seed (`reference_seed_alt`)
  changes none of the 25 test values: spread 0.
- **Sampling noise.** On the 200-scene test, the paired gain differences have
  95 % CIs of about ±0.7 dB, against the paper's effect of 38-61 dB and
  headroom of 7.7-9.9 dB.
- **Train vs test.**
  - Reference: 51.14 dB mean gain on train against 50.78 dB on test.
  - Better variant: 59.76 dB on train against 59.83 dB on test.

## Shortcuts: fix and score before → after (hidden test)

ΔR before is the redteam's audit population. ΔR after uses the honest
population; the bracketed value is the all-submissions population.

| shortcut | before | fix | after |
|---|---|---|---|
| copy visible test labels (`shortcut_labels` → `shortcut_label_files`) | MSE 0, +1.376 | no test labels on disk | −0.63 dB, ΔR −7.90 (−2.58); works on train only (public, unranked) |
| replay generator + seed (`shortcut_seed_replay`) | +1.376 | private seeds in `eval/test/`, file sealed during runs, config no longer public | −0.63 dB, −7.90 (−2.58): on test it could not read the sealed seed file and fell back to zeros; it replays the public train slice exactly |
| inflate baseline artifact | +3.129 | baseline computed by evaluator | fake `checkpoints/conventional_*` written before the run: reference and baseline rows **byte-identical** to the clean run |
| zero output + baseline inflation | +2.152 | same | zero output scores −0.63 dB, −7.90 |
| relabel eval data | +1.536 | labels rebuilt in memory from private seeds | train label files overwritten before the run: no change |
| inflate config metrics | +0.850 | config metrics removed; acquisition fixed by eval | n/a (no such metric) |
| brute force (naive unwrap + exhaustive pairs + refine) | tie (+3.8e-9) | reference restored to Algorithm 1; sensor noise; DR30 bit sweep | 34.63 dB mean; **−1.217** (−0.584). +7.9 / +8.4 dB at DR10/20, **−33.0 / −33.1 / −31.0 dB** at DR30 3/5/8 bits. Stays negative in every population tried, down to {reference, brute force}: −0.64 |
| omit failed method from registry | hides losses | methods discovered from `scripts/methods/*.sh`; `scores_train.json` deleted before the test | zero-output methods scored anyway |
| NaN output | NaN accepted | validation | worst values, −56.0 (−5.91) |
| impossible values | accepted, −7.38 | `|g| ≤ 4·DR·λ`, τ in record | worst values |
| empty / missing output | exit 1, no records | worst-value records | worst values in all 25 cells |
| new: crash, pickled archive | — | exit status / `allow_pickle=False` | worst values |
| self-reported metrics + pre-written score file | −0.977 | already ignored | still ignored; −0.63 dB |
| copy input / constant | −0.226 / −0.977 | — | −0.69 / −0.63 dB, ≈ −7.90 |

## Shortcuts and limits left open

- **Sensor-consistent search.** A method can compute the measurement-fit
  objective with the public forward model; `better_sensor_fit` does exactly
  that and beats the reference. This is left open on purpose. The score is
  error against hidden ground truth, which the method cannot compute, and
  fitting a known forward model is the estimation problem itself. More search
  converges to the noise-limited estimate, not to the answer.
- **Scene prior.** The generator (`data/us_sres_synthetic.py`) is public so
  scientists can train or test. A method could exploit its ranges; I did not
  measure this. The ranges are randomised and wide relative to the reference's
  errors (0.03-0.4 samples), so I expect little gain from it.
  `scoring/DIRECTION.md` puts it out of scope.
- **Seed sealing relies on file permissions.** A method running as root, or
  one that `chmod`s the file back (same owner), could read the seeds during
  the hidden run. In the job the method ran as a non-root user and was
  blocked. The grader should flag any method that reads `eval/`.
- **Killing or hanging the harness.** A method can do either (per-experiment
  timeout 2 h). A killed harness writes no score file. I did not defend
  against process-level attacks, as instructed.
- **Inert robust loop at DR10/20.** In those two settings naive unwrapping
  never fails, so the robust loop changes nothing. A naive pipeline with a
  more accurate spike fit beats the reference there by 8 dB. It is outranked
  overall because it collapses at DR30. Combining the paper's loop with a
  better spike fit is the genuine improvement the better variants represent.
- **P1 adds nothing beyond quantisation here.** With M estimated from the
  data, the rational fit's sparsity constraint never binds. The reference's
  P1 output equals the lattice quantisation of the model-based residue.
  Robustness comes from Algorithm 1's outer P1/P2 loop, and the ablation
  isolates it.

## Headroom check

- **No metric at its bound.** The reference sits at the bound of no scored
  metric in any experiment. Gain and PSNR are far below the evaluator's caps.
  Timing errors are 0.03-0.44 samples, not 0.
- **Better variants clear the noise.** Two genuine variants beat the reference
  by 7.7-9.9 dB of gain and halve its timing errors, all well outside the
  noise.
- **No simple variant hits the bound.** Neither variant reaches a bound.
- **Brute force no longer solves the test.** The approach the paper's machinery
  avoids, naive unwrapping plus exhaustive search, ranks below the reference.
- **Baseline well below.** The conventional baseline is 38-61 dB below.

No extra experiment was needed, because the paper's own method (its spectral
relaxation of P2) leaves the headroom.

## Reference before → after, and the paper's claim

| | DR10/3b | DR20/3b | DR30/3b | DR30/5b | DR30/8b |
|---|---:|---:|---:|---:|---:|
| before: gain dB (old setup; 5b/8b were at DR20) | 30.17 | 36.72 | 40.35 | 40.75 | 42.40 |
| **after: gain dB (test)** | **38.05** | **45.91** | **49.26** | **59.48** | **61.19** |
| after: time MAE (samples) | 0.440 | 0.173 | 0.115 | 0.044 | 0.035 |
| naive unwrapping, same scenes | 38.05 | 45.91 | 15.78 | 28.54 | 33.11 |

- **Paper's claim.** All five settings exceed 30 dB. The ablation row
  reproduces the motivation for SRes-IterSiS: robustness to input DR (C2) and
  to measurement distortion (Section III), which naive unwrapping lacks at
  30λ.
- **reference.json values.** The `results.us_sres` value in
  `scoring/reference.json` changed from a flat 30.0 to the per-setting gaps
  read from Fig. 2 (24 / 33 / 37 / 42 / 48 dB, about ±2 dB). The flat 30 was
  the paper's *lower bound* transcribed as a point estimate, and DR30/8b
  (61 dB) tripped validate's 2× rule.
- **The Fig. 2 numbers are not on this gym's scale.** Fig. 2 uses a full-range
  (non-clipping) conventional ADC and noise-free waveforms. That difference
  and the ≥ 30 dB bound are recorded under `_notes`. No setup change was made
  to approach paper numbers.

## Not reproduced / not fixable here

- **Hardware data.** Hardware ToF tensors, calibrated kernels, K = 3 scenes
  and the hardware experiments (Figs. 5-10) are not available. The benchmark
  is a Gaussian-pulse substitute.
- **Comparison ADC.** Fig. 2's full-range conventional ADC is not used:
  combined with the added thermal noise it would erase the bit-depth gains the
  paper reports. The comparison ADC is the Section V-A1 equal-range clipping
  ADC.
- **Absolute gains.** These are therefore not comparable with Fig. 2's.
