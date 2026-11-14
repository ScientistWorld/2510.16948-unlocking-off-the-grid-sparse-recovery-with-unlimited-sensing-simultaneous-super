# Scientist Constraints

A method is an entry point `scripts/methods/<name>.sh <input.npz> <output.npz>`
(see `briefing/problem.md`).  The evaluators call every entry point in that
directory on acquisitions they generate, so the sensing setup cannot be
changed by a method.  Hold fixed:

- `K = 2` off-grid spikes, `N = 501` samples, the Gaussian pulse given in the
  input.
- The experiment's bit budget (3, 5 or 8 bits) and dynamic range (10, 20 or 30
  times the folding threshold), and the sensor noise.
- Input: only the arrays in `<input.npz>` (modulo samples and sensor
  constants).  Do not read labels, evaluator files (`eval/`), or the score
  files while producing outputs, and do not try to identify scenes.
- Output: plain numeric `reconstruction` `(trials, 501)` and `taus`
  `(trials, 2)` arrays.  The waveform is scored at its absolute level.

Do not modify `eval/` or the evaluation scripts.  A method that crashes, times
out or writes an invalid output receives the worst value of every metric in
that experiment.

## Compliance Checklist

- [ ] Method registered as `scripts/methods/<name>.sh` and runnable offline.
- [ ] Reads only its `<input.npz>`; never labels, `eval/` or `scoring/`.
- [ ] Writes finite outputs of the documented shape for every scene.
- [ ] Does not modify `eval/` or `scripts/evaluate*.sh`.
