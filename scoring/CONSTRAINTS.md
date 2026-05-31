# Scientist Constraints

Future methods must evaluate on the same saved datasets unless they add a new
named experiment. Standard method scripts consume public files named
`data/synthetic/us_sres_dr*.npz`; evaluation uses corresponding private label
files named `data/synthetic/eval_us_sres_dr*.npz`. For each standard
experiment, hold fixed:

- `K=2` off-grid spikes.
- `N=501` samples.
- Gaussian pulse width from the corresponding public acquisition file.
- The experiment-specific quantization budget (`3`, `5`, or `8` bits).
- The experiment-specific dynamic range (`10`, `20`, or `30` times the folding
  threshold; the 5-bit and 8-bit extensions use `20`).
- Weak/strong amplitude ratio of 10.

Do not improve scores by increasing bit depth, reducing dynamic range, using
the clean signal as input, or changing the evaluator. Submitted methods should
consume only the measurement arrays available to the corresponding acquisition
setting and write the documented output artifact format.

## Compliance Checklist

- [ ] Uses the provided `data/synthetic/us_sres_dr*.npz` datasets for standard
      experiments, including any `_bits*` variants named in the manifest.
- [ ] Does not read `clean`, `taus`, `amplitudes`, or private fold counts from
      the dataset while producing method outputs.
- [ ] Does not increase `quant_bits` or reduce `dynamic_range_x`.
- [ ] Does not modify `eval/` or `scripts/evaluate.sh` to improve scores.
