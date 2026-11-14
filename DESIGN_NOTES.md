# Train/Test Evaluation Design Notes (current, after iteration 11 hardening)

- Methods are executable entry points `scripts/methods/<name>.sh <input.npz> <output.npz>`.
  Both evaluators discover every entry point on disk; no method name is hardcoded.
- `eval/train/` (public seeds, 64 scenes per experiment) and `eval/test/`
  (private seeds in `eval/test/hidden_instances.json`, 200 scenes) each carry
  their own forward model, conventional-baseline solver and harness; they share
  no code and do not import `method/` or `data/`.
- The test harness writes only method inputs (to a temp dir), seals the seed
  file while methods run, rebuilds the answers in memory afterwards, computes
  the clipping-ADC baseline itself, validates outputs (no pickles, exact
  shapes, finite, spike times in the record, |g| <= 4 DR lambda) and assigns
  worst values to every metric of a failed experiment.
- Scored metrics: gain over the conventional ADC (pooled MSE, dB), mean
  per-scene PSNR, spike-time MAE, weak-spike MAE, separation error.
- `scripts/evaluate.sh` scores the train slice into `scoring/scores.json`.
- The audit that checks better/weaker variants and shortcuts lives in
  `redteam/hardening/` (`run_audit.sh`, `variants.py`, `analyze.py`); see
  `HARDENING.md`.
