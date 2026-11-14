"""Hidden test-slice evaluator for the low-bit HDR modulo super-resolution gym.

Run with no arguments (``bash scripts/evaluate_test.sh``).  It scores every
method registered on disk and writes ``scoring/scores_test.json``.

1. Private seeds in ``eval/test/hidden_instances.json`` define the hidden test
   scenes.  Only the method inputs (modulo samples, kernel, sensor constants)
   are written, to a fresh temporary directory outside the workspace.
2. Every executable entry point ``scripts/methods/<name>.sh`` is a method.  It
   is called once per experiment as
       bash scripts/methods/<name>.sh <input.npz> <output.npz>
   and must write ``reconstruction`` (trials x N) and ``taus`` (trials x K).
   The seed file is made unreadable while methods run.
3. After the methods return, the answers are rebuilt in memory, the
   conventional clipping-ADC baseline is computed here from the second ADC,
   every output is validated, and every metric is recomputed from raw arrays.
   A missing, crashed or invalid output (wrong shape, non-finite values,
   spike times outside the record, |g| above the physical bound) fails that
   experiment and receives the worst value of every metric.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from eval.test import forward_model as fm
from eval.test.conventional import conventional_recovery

SLICE = "test"
ROOT = Path(__file__).resolve().parents[2]
HIDDEN = Path(__file__).resolve().parent / "hidden_instances.json"
BASELINE_NAME = "conventional_clip_sres"
OUTPUT_BOUND_FACTOR = 4.0  # valid reconstructions satisfy |g| <= 4 * DR * lambda
MSE_FLOOR = 1e-12
DEFAULT_TIMEOUT = 7200.0
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$")
METRICS = (
    "mse_gain_over_conventional_db",
    "psnr_db",
    "time_mae_samples",
    "weak_tau_mae_samples",
    "separation_error_samples",
)


class InvalidOutput(Exception):
    pass


def discover_methods(methods_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not methods_dir.is_dir():
        return found
    for path in sorted(methods_dir.glob("*.sh")):
        name = path.stem
        if not path.is_file() or not NAME_RE.match(name) or name == BASELINE_NAME:
            print(f"[{SLICE}] skipping entry point {path.name}")
            continue
        found[name] = path
    return found


@contextlib.contextmanager
def sealed(path: Path):
    """Make the hidden seed file unreadable while submitted code runs."""

    mode = None
    try:
        mode = path.stat().st_mode & 0o7777
        os.chmod(path, 0)
    except OSError as exc:
        print(f"[{SLICE}] could not seal {path.name}: {exc}")
        mode = None
    try:
        yield
    finally:
        if mode is not None:
            os.chmod(path, mode)


def run_entry(script: Path, inp: Path, out: Path, log: Path, timeout: float) -> str:
    try:
        with open(log, "wb") as handle:
            proc = subprocess.run(
                ["bash", str(script), str(inp), str(out)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        return f"timed out after {timeout:.0f}s"
    except OSError as exc:
        return f"could not start ({exc})"
    return "ok" if proc.returncode == 0 else f"exit status {proc.returncode}"


def load_output(path: Path, trials: int, n: int, k: int, bound: float) -> tuple[np.ndarray, np.ndarray]:
    if not path.is_file():
        raise InvalidOutput("no output file written")
    try:
        archive = np.load(path, allow_pickle=False)
    except Exception as exc:  # noqa: BLE001 - any load failure invalidates the run
        raise InvalidOutput(f"unreadable output ({type(exc).__name__})") from None
    if not hasattr(archive, "files"):
        raise InvalidOutput("output is not an .npz archive")
    try:
        with archive:
            if "reconstruction" not in archive.files or "taus" not in archive.files:
                raise InvalidOutput("archive lacks 'reconstruction' or 'taus'")
            recon = np.asarray(archive["reconstruction"])
            taus = np.asarray(archive["taus"])
    except InvalidOutput:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InvalidOutput(f"unreadable arrays ({type(exc).__name__})") from None
    for label, arr, shape in (("reconstruction", recon, (trials, n)), ("taus", taus, (trials, k))):
        if arr.dtype.kind not in "fiu":
            raise InvalidOutput(f"{label} has dtype {arr.dtype}")
        if arr.shape != shape:
            raise InvalidOutput(f"{label} has shape {arr.shape}, expected {shape}")
    recon = recon.astype(np.float64)
    taus = taus.astype(np.float64)
    if not np.all(np.isfinite(recon)):
        raise InvalidOutput("non-finite reconstruction")
    if not np.all(np.isfinite(taus)):
        raise InvalidOutput("non-finite spike times")
    if np.max(np.abs(recon)) > bound:
        raise InvalidOutput(f"reconstruction exceeds the bound |g| <= {bound:g}")
    if np.min(taus) < 0.0 or np.max(taus) > n - 1:
        raise InvalidOutput(f"spike times outside [0, {n - 1}]")
    return recon, taus


def per_trial_errors(
    clean: np.ndarray,
    true_taus: np.ndarray,
    amplitudes: np.ndarray,
    recon: np.ndarray,
    pred_taus: np.ndarray,
) -> dict[str, np.ndarray]:
    mse = np.mean((recon - clean) ** 2, axis=1)
    peak = np.max(np.abs(clean), axis=1)
    psnr = 10.0 * np.log10(peak**2 / np.maximum(mse, MSE_FLOOR))
    order = np.argsort(true_taus, axis=1)
    truth = np.take_along_axis(true_taus, order, axis=1)
    amps = np.take_along_axis(amplitudes, order, axis=1)
    pred = np.sort(pred_taus, axis=1)
    err = np.abs(pred - truth)  # optimal 1-D matching of sorted locations
    weak = np.argmin(np.abs(amps), axis=1)
    weak_err = err[np.arange(err.shape[0]), weak]
    sep_err = np.mean(np.abs(np.diff(pred, axis=1) - np.diff(truth, axis=1)), axis=1)
    return {"mse": mse, "psnr": psnr, "tau_err": err, "weak_err": weak_err, "sep_err": sep_err}


def summarize(per: dict[str, np.ndarray], conventional_mse: float) -> dict[str, float]:
    pooled = float(np.mean(per["mse"]))
    return {
        "mse_gain_over_conventional_db": float(
            10.0 * np.log10(conventional_mse / max(pooled, MSE_FLOOR))
        ),
        "psnr_db": float(np.mean(per["psnr"])),
        "time_mae_samples": float(np.mean(per["tau_err"])),
        "weak_tau_mae_samples": float(np.mean(per["weak_err"])),
        "separation_error_samples": float(np.mean(per["sep_err"])),
    }


def worst_metrics(dynamic_range_x: float, conventional_mse: float, n: int) -> dict[str, float]:
    """Worst value every metric can take for an output inside the validity bounds."""

    peak = dynamic_range_x * fm.LAMBDA_VALUE
    mse_worst = ((OUTPUT_BOUND_FACTOR + 1.0) * peak) ** 2
    return {
        "mse_gain_over_conventional_db": float(10.0 * np.log10(conventional_mse / mse_worst)),
        "psnr_db": float(10.0 * np.log10(peak**2 / mse_worst)),
        "time_mae_samples": float(n - 1),
        "weak_tau_mae_samples": float(n - 1),
        "separation_error_samples": float(n - 1),
    }


def load_hidden() -> tuple[int, dict[str, int]]:
    if not os.access(HIDDEN, os.R_OK):  # left sealed by an interrupted run
        os.chmod(HIDDEN, 0o644)
    hidden = json.loads(HIDDEN.read_text())
    trials = int(hidden["trials"])
    seeds = {name: int(hidden["seeds"][name]) for name in fm.EXPERIMENTS}
    return trials, seeds


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scores", default=str(ROOT / "scoring" / "scores_test.json"))
    parser.add_argument("--methods-dir", default=str(ROOT / "scripts" / "methods"))
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--jobs", type=int, default=1, help="method runs executed concurrently")
    parser.add_argument(
        "--per-trial-dir",
        default=os.environ.get("US_SRES_EVAL_PER_TRIAL_DIR"),
        help="optional directory for per-trial error dumps (diagnostics only)",
    )
    args = parser.parse_args(argv)

    trials, seeds = load_hidden()
    methods = discover_methods(Path(args.methods_dir))
    print(f"[{SLICE}] {trials} hidden trials per experiment; methods: {sorted(methods) or 'none'}")
    per_trial_dir = Path(args.per_trial_dir) if args.per_trial_dir else None
    if per_trial_dir is not None:
        per_trial_dir.mkdir(parents=True, exist_ok=True)

    n, k = fm.N_SAMPLES, fm.NUM_SPIKES
    status: dict[str, dict[str, str]] = {name: {} for name in fm.EXPERIMENTS}
    experiments: dict[str, dict] = {}
    work = Path(tempfile.mkdtemp(prefix=f"us_sres_{SLICE}_"))
    try:
        (work / "inputs").mkdir()
        (work / "logs").mkdir()
        for name, spec in fm.EXPERIMENTS.items():
            inst = fm.make_instances(spec["dynamic_range_x"], spec["quant_bits"], trials, seeds[name])
            np.savez(work / "inputs" / f"{name}.npz", **fm.public_inputs(inst))
            del inst

        with sealed(HIDDEN):
            for method in methods:
                (work / "outputs" / method).mkdir(parents=True)
            tasks = [(method, name) for method in methods for name in fm.EXPERIMENTS]

            def execute(task: tuple[str, str]) -> None:
                method, name = task
                start = time.time()
                log = work / "logs" / f"{method}__{name}.log"
                state = run_entry(
                    methods[method],
                    work / "inputs" / f"{name}.npz",
                    work / "outputs" / method / f"{name}.npz",
                    log,
                    args.timeout,
                )
                status[name][method] = state
                print(f"[{SLICE}] {method} / {name}: {state} ({time.time() - start:.1f}s)", flush=True)
                if state != "ok":
                    print(log.read_bytes()[-2000:].decode("utf-8", "replace"), flush=True)

            with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
                list(pool.map(execute, tasks))

        for name, spec in fm.EXPERIMENTS.items():
            inst = fm.make_instances(spec["dynamic_range_x"], spec["quant_bits"], trials, seeds[name])
            dr = float(spec["dynamic_range_x"])
            conv_recon, conv_taus = conventional_recovery(inst["conventional_samples"], fm.KERNEL_SIGMA)
            conv_per = per_trial_errors(inst["clean"], inst["taus"], inst["amplitudes"], conv_recon, conv_taus)
            conv_mse = float(np.mean(conv_per["mse"]))
            results = {BASELINE_NAME: summarize(conv_per, conv_mse)}
            if per_trial_dir is not None:
                np.savez(per_trial_dir / f"{BASELINE_NAME}__{name}.npz", **conv_per)
            bound = OUTPUT_BOUND_FACTOR * dr * fm.LAMBDA_VALUE
            for method in methods:
                state = status[name][method]
                if state == "ok":
                    try:
                        recon, taus = load_output(work / "outputs" / method / f"{name}.npz", trials, n, k, bound)
                    except InvalidOutput as exc:
                        state = f"invalid output: {exc}"
                    else:
                        per = per_trial_errors(inst["clean"], inst["taus"], inst["amplitudes"], recon, taus)
                        results[method] = summarize(per, conv_mse)
                        if per_trial_dir is not None:
                            np.savez(per_trial_dir / f"{method}__{name}.npz", **per)
                if state != "ok":
                    results[method] = worst_metrics(dr, conv_mse, n)
                    print(f"[{SLICE}] {method} / {name} FAILED ({state}): worst values assigned")
                status[name][method] = state
            experiments[name] = {
                "results": results,
                "status": {BASELINE_NAME: "computed by the evaluator", **status[name]},
                "config": {
                    "dynamic_range_x": dr,
                    "quant_bits": int(spec["quant_bits"]),
                    "trials": trials,
                    "num_spikes": k,
                    "n_samples": n,
                    "kernel_sigma": fm.KERNEL_SIGMA,
                    "thermal_noise_std": fm.THERMAL_NOISE_STD,
                    "mean_fold_count": float(np.mean(inst["fold_count"])),
                },
            }
            del inst
    finally:
        shutil.rmtree(work, ignore_errors=True)

    scores = {"slice": SLICE, "experiments": experiments}
    path = Path(args.scores)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scores, indent=2, sort_keys=True, allow_nan=False))
    for name, exp in experiments.items():
        for method, metrics in exp["results"].items():
            row = ", ".join(f"{key}={metrics[key]:.4g}" for key in METRICS)
            print(f"[{SLICE}] {name} {method}: {row}")
    print(f"[{SLICE}] wrote {path}")


if __name__ == "__main__":
    main()
