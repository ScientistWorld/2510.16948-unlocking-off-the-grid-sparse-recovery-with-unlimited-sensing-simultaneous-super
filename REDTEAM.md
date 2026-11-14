# Scoring audit

**Genuine improvements score higher, and a clearly weaker method scores lower. However, this gym does not reliably reward the paper's scientific contribution.** Brute force ties the reference without its rational recovery or spectral fitting. Visible labels, replayable seeds, mutable comparison outputs, mutable ground truth, and rewarded configuration claims all provide working shortcuts. A zero-output method can even outrank the reference after changing the baseline artifact.

The synthetic data show the paper's modulo-versus-clipping benefit, but do not establish its robust recovery advantage: every generated signal satisfies the easy first-difference unwrapping condition. Better performance here therefore need not indicate a better solution to the paper's harder problem.

## Better and weaker methods

All numbers below come from the original, no-argument `bash scripts/evaluate_test.sh`. Means weight the five experiments equally; lower MSE and localization error are better. The full records are under each linked directory.

| Method | Mean gain over clipped baseline (dB) | Mean signal MSE | Mean spike error (samples) | Rank difference, quality population |
|---|---:|---:|---:|---:|
| Conventional clipped baseline | 0 | 65.1051 | 50.7475 | −5.222 |
| [Weaker: remove unwrapping](redteam/weaker_no_unwrap/run.sh) | −0.7317 | 74.2777 | 60.5274 | −5.124 |
| [Reference](redteam/initial_scores_test.json) | 38.0785 | 0.00908875 | 0.756069 | 0 |
| [Better: fit the physical sensor model](redteam/better_sensor_fit/run.sh) | 69.4615 | 0.0000262626 | 0.110896 | +1.539 |

The better variant starts from reference predictions, removes the arbitrary fitted DC term, and refines two positive Gaussian reflections against measured quantized modulo samples using a periodic residual. It uses no labels or generator seeds. This is a real correction to the inverse problem. It improves **all eight quality metrics in every experiment (40/40)** and leaves the four configuration metrics unchanged. The weaker variant applies sparse deconvolution directly to the wrapped observations and worsens all 40 quality measurements. These orderings hold for any positive normalization scales, with gains larger than the measured seed spread.

The quality-population column uses only the reference, conventional baseline, better variant, and weaker variant to estimate variation. Its population and results are recorded in [normalization_sensitivity.json](redteam/normalization_sensitivity.json). Shortcut comparisons below use a separate, explicitly recorded audit population.

## Seeds and reproduction

Three complete reruns changed the reference algorithm's actual internal initialization seed to [16948](redteam/reference_seed_16948/scores_test.json), [16949](redteam/reference_seed_16949/scores_test.json), and [16950](redteam/reference_seed_16950/scores_test.json). **Every one of the 60 scored experiment/metric values was identical: max−min spread 0; normalized rank spread 0.** Each run took about 165 seconds. This measures algorithm initialization variability on the fixed test data, not uncertainty over newly sampled scenes. Tiny floating-point differences in the brute-force shortcut are not evidence of a scientific improvement.

The reproduced waveform advantage agrees with Fig. 2 in direction and exceeds 30 dB on all five hidden slices:

| Experiment | Reference gain (dB) | Better variant gain (dB) | Reference signal MSE |
|---|---:|---:|---:|
| DR10, 3 bits | 30.1736 | 54.7444 | 0.0120591 |
| DR20, 3 bits | 36.7242 | 63.8336 | 0.0123859 |
| DR30, 3 bits | 40.3503 | 63.4323 | 0.0127111 |
| DR20, 5 bits | 40.7478 | 73.5777 | 0.00491906 |
| DR20, 8 bits | 42.3967 | 91.7194 | 0.00336858 |

This does not reproduce every claimed behavior. At DR10, weak-target localization is **worse** than the conventional baseline: 3.6854 versus 1.4802 samples, despite the waveform gain. The other four slices improve weak-target localization.

The reference departs materially from [the paper](paper/2510.16948.md), Algorithm 1 and Section III:

* It starts with an already unwrapped signal and its fitted residue, rather than the algorithm's prescribed residue initialization. It estimates and caps the residue degree instead of taking the supplied fold count M.
* It runs one outer iteration, four rational-fit inner iterations, and three initializations, with ridge regularization, weight/denominator clamps, and additional lattice and finite-difference candidates. Selection uses a signal-fitting residual and may retain the preliminary solution instead of the rational update.
* Its P2 implementation uses annihilating-polynomial roots and nonlinear Gaussian fitting, and always evaluates a coarse pair enumeration with continuous refinement. It omits the Toeplitz eigensolution for the unknown DC term in equations (46)–(47); an arbitrary fitted signal offset substitutes for that correction. The function named `matrix_pencil_spikes` is a linear-prediction/root solver, rather than the described matrix-pencil procedure.
* The paper uses hardware ToF measurements, including its numerical re-digitization experiments. This gym substitutes noiseless, known-width Gaussian mixtures, with no hardware distortion or kernel calibration. It has 64 scenes per setting, with 32 odd-index scenes scored on test, versus 5000 randomized trials in Fig. 2. It samples five settings instead of the full 3–15-bit curves, and jitters both separation and amplitude ratio around the paper's exact 75-sample separation and 10:1 ratio. It omits hardware imaging, general kernels, and higher-order scenes.

These are changes to procedure as well as scale. The reference contains recognizable rational-residue computations, but this audit does not verify it as an exact implementation of Algorithm 1 or validate the existing reproduction milestone.

The brute-force shortcut enumerates **all 5151 allowed pairs on a 108-point coarse grid**, then refines continuously, following ordinary first-difference unwrapping. It processes all 320 scenes in 54.3 seconds, including train/test scoring, and ties the reference. No runtime metric distinguishes the methods. [Diagnostics](redteam/shortcut_bruteforce/diagnostics.json) give maximum clean first differences of 0.1334, 0.2668, and 0.4002 for DR10/20/30, versus folding threshold 1; even the 3-bit quantization difference-error bound of 0.2857 leaves a margin. This test is small and smooth enough for the brute force that the paper's scalable recovery machinery should make unnecessary. The rational/spectral machinery is not needed to solve the benchmark to reference quality.

## Scoring checks

**Headroom exists.** No reference quality metric is at its bound on any experiment: waveform MSE, folded-region MSE, three localization errors, and wrapped-measurement error are all positive; gain and PSNR remain below the evaluator's exact-reconstruction caps. The conventional baseline is clearly below the reference, and the genuine fix demonstrates substantial room above it.

The four configuration metrics are already at their required operating points on every honest method: `dynamic_range_x` = 10/20/30/20/20, `quant_bits` = 3/3/3/5/8, `amplitude_ratio` = 10, and `mean_fold_count` = 10/20/30/20/20. Thus all four are fixed under the stated task; in particular bit depth is already at each experiment's mandated budget. They should be validity checks. Treating higher severity and lower bit counts as freely improvable scalar rewards instead rewards false metadata.

I used the supplied rank rule:

`ΔR = Σ_experiment weight × Σ_metric |coefficient| × direction × (candidate − reference) / population_std`.

`direction` comes only from `higher_is_better`; negative coefficients do not reverse it again. All five experiment weights are 0.2. Gain has coefficient magnitude 1, PSNR/time error 0.45 each, weak-target error 0.35, maximum error 0.25, signal MSE 0.20, folded MSE 0.25, consistency 0.30, and the four configuration checks 0.05 each. Units alone do not determine importance after normalization.

There is no external ranker in this workspace, and future attempt variation is unknowable. The shortcut table's **ΔR_A** uses population standard deviations over the 17 finite, complete records listed in [summary.json](redteam/summary.json), including the original reference. Zero-variance dimensions contribute zero. These are reproducible illustrative rank differences, not a claim about an unknown future leaderboard. Comparisons use the actual saved reference test results; `reference.json` supplies coefficients/directions but its proposed result rows contain a 30 dB target and only three configuration anchors, rather than the complete realized result. Any external ranker needing complete reference anchors must obtain them separately.

The label, seed, baseline-inflation, relabeling, and configuration shortcuts improve at least one metric without worsening any, so their wins survive any positive finite normalization scales. **Task failure is not gated:** the zero-output/baseline-inflation shortcut scores +2.152 in the audit population despite MSE 73.8998 and localization error 22.4776. This is a mixed tradeoff, hence population-dependent. It still scores +0.0537 in a population that includes the conventional baseline and excludes both the impossible-output and configuration-inflation trials; see the sensitivity record.

**Failed runs do not receive worst values.** Empty outputs and missing registered outputs exit 1 before writing any test score file. No complete penalty record is written for any experiment. They fail as valid submissions; whether a surrounding job runner rejects them is outside the scoring code inspected here. A successful run also need not write every on-disk method: the mutable train-score registry overrides checkpoint enumeration. The omission shortcut proves this on all five experiments.

## Shortcut trials

Each name links to its runnable `run.sh`; its folder contains `outcome.json`, train/test logs, and train/test score JSON when produced. Reference mean gain is **38.0785 dB**, MSE **0.00908875**, and ΔR_A **0**. “Works” means a demonstrated win or tie, with qualifications stated for missing/nonfinite results.

| Shortcut | What it does | Hidden test vs reference | Outcome |
|---|---|---|---|
| [shortcut_labels](redteam/shortcut_labels/run.sh) | Copies `clean` and `taus` from visible `data/synthetic/eval_*.npz` into output artifacts. | MSE 0, time error 0; gain 197.074 dB; ΔR_A **+1.376**. | **Works.** No recovery method. Available in both scientist modes. |
| [shortcut_seed_replay](redteam/shortcut_seed_replay/run.sh) | Runs the public generator using the complete config and seed shipped in public acquisitions; never reads the label archive. | Exactly the same scores as shortcut_labels; ΔR_A **+1.376**. | **Works.** Hiding only label files would not fix this. |
| [shortcut_baseline_inflation](redteam/shortcut_baseline_inflation/run.sh) | Replaces fixed conventional reconstruction artifacts with constant `1e150`; reuses reference predictions. | Candidate errors unchanged; gain 3021.004 dB; ΔR_A **+3.129**. | **Works.** Changes the comparison, not recovery. |
| [shortcut_failing_baseline_inflation](redteam/shortcut_failing_baseline_inflation/run.sh) | Uses zero waveforms and fixed times, plus the same baseline replacement. | MSE 73.8998; gain 2982.227 dB; ΔR_A **+2.152**. | **Works** in the recorded populations, despite failing the task. |
| [shortcut_relabel](redteam/shortcut_relabel/run.sh) | Changes evaluation clean signals, locations, and observed modulo samples to match existing reference predictions. | MSE, time error, and consistency error 0; gain 196.991 dB; ΔR_A **+1.536**. | **Works.** Restoring `eval/` does not restore its mutable data dependency. |
| [shortcut_config](redteam/shortcut_config/run.sh) | Keeps all predictions and measurements unchanged; changes label-archive DR, ratio, and fold counts to `1e12`, bits to 0. | All quality scores unchanged; ΔR_A **+0.850**. | **Works.** Claimed difficulty receives credit without changing data. |
| [shortcut_bruteforce](redteam/shortcut_bruteforce/run.sh) | Unwraps first differences, enumerates every coarse location pair, then refines. Omits rational/spectral recovery. | Gain 38.0785 dB; ΔR_A **+3.8e−9**, a numerical tie. | **Works as a tie:** an honest alternative shortcut the test cannot distinguish. |
| [shortcut_omission](redteam/shortcut_omission/run.sh) | Leaves zero-output artifacts on disk but deletes their entries from `scores_train.json`. | Test exit 0; all five candidate result entries absent despite five artifacts. Under the stated skip-missing rule its contribution is **0**, a tie. | **Works to hide losses.** Paying tie if the attempt is retained; acceptance of a wholly absent attempt is not independently verified. |
| [shortcut_self_report](redteam/shortcut_self_report/run.sh) | Supplies fake MSE, PSNR, success and timing fields, and prewrites a fake test-score file, with zero predictions. | Test overwrites the JSON and recomputes quality; gain −0.6985 dB; ΔR_A **−0.977**. | **Fails.** Extra scalar claims are ignored; timing is unscored. |
| [shortcut_copy_input](redteam/shortcut_copy_input/run.sh) | Returns wrapped measurements with fixed spike times. | Gain −0.7519 dB; ΔR_A **−0.226**. | **Fails overall.** Sensor-consistency error improves, while recovery is poor. |
| [shortcut_constant](redteam/shortcut_constant/run.sh) | Returns zeros with fixed spike times. | Gain −0.6985 dB; ΔR_A **−0.977**. | **Fails** without changing other scoring inputs. |
| [shortcut_impossible](redteam/shortcut_impossible/run.sh) | Returns waveform `1e6` and times outside the sample range. | Gain −102.926 dB; MSE approximately `1e12`; ΔR_A **−7.380**. | **Fails to pay**, although the evaluator accepts the output. |
| [shortcut_nan](redteam/shortcut_nan/run.sh) | Returns NaN signals and times. | Test exit 0; all 40 quality values are JSON `NaN`; 20 configuration values remain finite. | **Accepted malformed scores; paying win unproven.** No finite ranking can be assigned without external NaN-handling rules. |
| [shortcut_empty](redteam/shortcut_empty/run.sh) | Writes zero-row outputs and registers the method. | Test exit 1; no score file and no worst-value records. | **Fails as a valid submission.** Failure-penalty completeness check fails. |
| [shortcut_missing](redteam/shortcut_missing/run.sh) | Registers a method with no output files. | Test exit 1; no score file and no worst-value records. | **Fails as a valid submission.** Failure-penalty completeness check fails. |

## Execution, restoration, and next iteration

One CPU job, `30cc437f-e6a`, completed all 20 trials in 673 seconds with job exit 0; intentional candidate failures are recorded separately. Candidates used only scientist-visible sources, with reference outputs reused where authorized. Candidate construction did not import hidden evaluation code. Every hidden test was an unchanged no-argument subprocess, dependent only on saved files. No background process, package change, import interception, or evaluator-process manipulation was used. The evaluator and test script were never modified.

[verify.py](redteam/verify.py) independently checks the saved rankings, 60 seed spreads, directional comparisons, malformed-result outcomes, and restoration using only the Python standard library. [verification.json](redteam/verification.json) confirms byte-for-byte restoration of all checkpoint, synthetic-data, and scoring files, all evaluator/other script hashes, and the original `scripts/run.sh`. Pre-existing workspace changes were preserved. The audit's lasting source/evidence changes are under `redteam/` and this report; `action.yaml` is the required completion signal.

For the next gym iteration: keep test labels and generation randomness outside the scientist-visible tree; restore immutable baseline, data, and operating-point assets along with the evaluator; validate all shapes, finite values, and configuration constraints; score every submitted method independently of mutable train-score entries; and write complete worst-value records on every failure. Treat sensing constraints and task success as eligibility conditions before aggregating benefits. Add scenes outside the first-difference regime, hardware distortions or justified substitutes, broader kernels, and larger candidate spaces so that the paper's procedure is actually tested. Reimplement the omitted paper steps before retaining an exact-reproduction claim.
