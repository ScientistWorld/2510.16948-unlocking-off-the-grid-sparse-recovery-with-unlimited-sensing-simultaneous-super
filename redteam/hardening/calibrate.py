"""Calibrate the benchmark's sensor noise and pulse width (diagnostic job step).

For several (kernel_sigma, thermal_noise_std) settings this measures, on a
small calibration draw (never the train or test seeds): how often naive
first-difference unwrapping breaks, and the waveform gain / spike-time error
of the reference (SRes-IterSiS), the first-difference + exhaustive-search
shortcut, the least-squares-refined variant and the conventional baseline.
"""

from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data import us_sres_synthetic as gen  # noqa: E402
from eval.test.conventional import conventional_recovery  # noqa: E402
from redteam.hardening import variants  # noqa: E402

CONFIGS = [(20.0, 0.03), (20.0, 0.02), (20.0, 0.045), (22.0, 0.03), (18.0, 0.03)]
TRIALS = int(os.environ.get("CALIB_TRIALS", "40"))
CALIB_SEED = 99


def score(clean, true_taus, amps, recon, taus):
    mse = np.mean((recon - clean) ** 2, axis=1)
    order = np.argsort(true_taus, axis=1)
    truth = np.take_along_axis(true_taus, order, axis=1)
    a = np.take_along_axis(amps, order, axis=1)
    err = np.abs(np.sort(taus, axis=1) - truth)
    weak = err[np.arange(err.shape[0]), np.argmin(a, axis=1)]
    return mse, err, weak


def task(args):
    sigma, noise, name = args
    spec = gen.EXPERIMENTS[name]
    inst = gen.make_instances(spec["dynamic_range_x"], spec["quant_bits"], TRIALS, CALIB_SEED, sigma, noise)
    inputs = gen.public_inputs(inst)
    lam = gen.LAMBDA_VALUE
    itoh = np.array(
        [np.concatenate([[0.0], np.cumsum(gen.modulo(np.diff(y), lam))]) + y[0] for y in inst["modulo_samples"]]
    )
    itoh_fail = float(np.mean(np.max(np.abs(itoh - inst["clean"]), axis=1) > lam))
    row = {"kernel_sigma": sigma, "noise_std": noise, "experiment": name, "itoh_failure_rate": itoh_fail}
    conv_recon, conv_taus = conventional_recovery(inst["conventional_samples"], sigma)
    conv_mse, _, _ = score(inst["clean"], inst["taus"], inst["amplitudes"], conv_recon, conv_taus)
    conv_pooled = float(np.mean(conv_mse))
    methods = {
        "us_sres": lambda: variants._reference_runs(inputs),
        "shortcut_bruteforce": lambda: variants.shortcut_bruteforce(inputs),
        "better_ls_refine": lambda: variants.better_ls_refine(inputs),
        "weaker_no_itersis": lambda: variants.weaker_no_itersis(inputs),
    }
    for mname, fn in methods.items():
        start = time.time()
        out = fn()
        if mname == "us_sres":
            recon = np.asarray([r["reconstruction"] for r in out])
            taus = np.asarray([r["taus"] for r in out])
            row["us_sres_mean_iterations"] = float(np.mean([r["iterations"] for r in out]))
        else:
            recon, taus = out
        mse, err, weak = score(inst["clean"], inst["taus"], inst["amplitudes"], recon, taus)
        row[f"{mname}_gain_db"] = float(10 * np.log10(conv_pooled / max(np.mean(mse), 1e-12)))
        row[f"{mname}_median_trial_mse"] = float(np.median(mse))
        row[f"{mname}_bad_trials"] = float(np.mean(mse > 0.05))
        row[f"{mname}_tau_mae"] = float(np.mean(err))
        row[f"{mname}_weak_mae"] = float(np.mean(weak))
        row[f"{mname}_sec_per_trial"] = (time.time() - start) / TRIALS
    return row


def main() -> None:
    tasks = [(s, w, name) for s, w in CONFIGS for name in gen.EXPERIMENTS]
    workers = max(1, min(len(tasks), os.cpu_count() or 1))
    print(f"calibration: {len(tasks)} tasks, {TRIALS} trials each, {workers} workers", flush=True)
    with Pool(workers) as pool:
        rows = pool.map(task, tasks)
    out = ROOT / "redteam" / "hardening" / "calibration.json"
    out.write_text(json.dumps(rows, indent=1))
    keys = ["itoh_failure_rate"] + [
        f"{m}_{s}"
        for m in ("us_sres", "shortcut_bruteforce", "better_ls_refine", "weaker_no_itersis")
        for s in ("gain_db", "bad_trials", "tau_mae", "weak_mae")
    ]
    for r in rows:
        vals = " ".join(f"{k}={r[k]:.3g}" for k in keys)
        print(f"sigma={r['kernel_sigma']} noise={r['noise_std']} {r['experiment']}: {vals}", flush=True)


if __name__ == "__main__":
    main()
