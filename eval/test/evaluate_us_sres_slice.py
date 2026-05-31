"""Score saved US-SRes artifacts on the held-out test evaluation slice.

This evaluator is method-agnostic. It reads private evaluation datasets and
saved NPZ outputs produced by any method that follows the benchmark artifact
contract: ``reconstruction`` and ``taus`` arrays with one row per trial.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


SLICE_NAME = "test"
SLICE_OFFSET = 1


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    data: str
    baseline: str
    suffix: str


EXPERIMENTS = (
    ExperimentSpec(
        "synthetic_lowbit_hdr_dr10",
        "data/synthetic/eval_us_sres_dr10.npz",
        "checkpoints/conventional_dr10.npz",
        "dr10",
    ),
    ExperimentSpec(
        "synthetic_lowbit_hdr_dr20",
        "data/synthetic/eval_us_sres_dr20.npz",
        "checkpoints/conventional_dr20.npz",
        "dr20",
    ),
    ExperimentSpec(
        "synthetic_lowbit_hdr_dr30",
        "data/synthetic/eval_us_sres_dr30.npz",
        "checkpoints/conventional_dr30.npz",
        "dr30",
    ),
    ExperimentSpec(
        "synthetic_lowbit_hdr_dr20_bits5",
        "data/synthetic/eval_us_sres_dr20_bits5.npz",
        "checkpoints/conventional_dr20_bits5.npz",
        "dr20_bits5",
    ),
    ExperimentSpec(
        "synthetic_lowbit_hdr_dr20_bits8",
        "data/synthetic/eval_us_sres_dr20_bits8.npz",
        "checkpoints/conventional_dr20_bits8.npz",
        "dr20_bits8",
    ),
)


def psnr(clean: np.ndarray, estimate: np.ndarray) -> float:
    centered_clean = clean - clean.mean(axis=1, keepdims=True)
    centered_estimate = estimate - estimate.mean(axis=1, keepdims=True)
    mse = np.mean((centered_clean - centered_estimate) ** 2)
    peak = np.max(centered_clean) - np.min(centered_clean)
    return float(20.0 * np.log10(peak / np.sqrt(max(mse, 1e-18))))


def modulo(x: np.ndarray, lambda_value: float) -> np.ndarray:
    return 2.0 * lambda_value * (
        np.mod(x / (2.0 * lambda_value) + 0.5, 1.0) - 0.5
    )


def tau_errors(true_taus: np.ndarray, pred_taus: np.ndarray) -> np.ndarray:
    errors = []
    for truth, pred in zip(true_taus, pred_taus):
        truth = np.sort(truth)
        pred = np.sort(pred)
        direct = np.abs(truth - pred)
        swapped = np.abs(truth - pred[::-1])
        errors.append(direct if np.mean(direct) <= np.mean(swapped) else swapped)
    return np.asarray(errors, dtype=np.float64)


def split_indices(num_trials: int) -> np.ndarray:
    indices = np.arange(num_trials)
    return indices[indices % 2 == SLICE_OFFSET]


def load_required_npz(path: Path, required: set[str], kind: str) -> np.lib.npyio.NpzFile:
    arrays = np.load(path, allow_pickle=True)
    missing = required - set(arrays.files)
    if missing:
        raise ValueError(f"{kind} {path} is missing arrays: {sorted(missing)}")
    return arrays


def evaluate_method(data_path: Path, output_path: Path) -> dict[str, float]:
    data = load_required_npz(
        data_path,
        {"clean", "taus", "config", "folds", "modulo_samples"},
        "evaluation data",
    )
    output = load_required_npz(output_path, {"reconstruction", "taus"}, "method output")

    clean_full = data["clean"]
    reconstruction_full = output["reconstruction"]
    output_taus_full = output["taus"]
    if reconstruction_full.shape[0] != clean_full.shape[0]:
        raise ValueError(
            f"{output_path} has {reconstruction_full.shape[0]} reconstruction rows, "
            f"but {data_path} has {clean_full.shape[0]} evaluation trials"
        )
    if output_taus_full.shape[0] != clean_full.shape[0]:
        raise ValueError(
            f"{output_path} has {output_taus_full.shape[0]} tau rows, "
            f"but {data_path} has {clean_full.shape[0]} evaluation trials"
        )

    idx = split_indices(clean_full.shape[0])
    clean = clean_full[idx]
    reconstruction = reconstruction_full[idx]
    true_taus = data["taus"][idx]
    pred_taus = output_taus_full[idx]
    folds = data["folds"][idx]
    modulo_samples = data["modulo_samples"][idx]
    config = data["config"][0]

    tau_error = tau_errors(true_taus, pred_taus)
    tau_mae = float(np.mean(tau_error))
    weak_tau_mae = float(np.mean(tau_error[:, -1]))
    max_tau_error = float(np.mean(np.max(tau_error, axis=1)))
    signal_psnr = psnr(clean, reconstruction)
    signal_mse = float(np.mean((clean - reconstruction) ** 2))
    folded_samples = np.abs(clean) > float(config["lambda_value"])
    if np.any(folded_samples):
        hard_fold_mse = float(
            np.mean((clean[folded_samples] - reconstruction[folded_samples]) ** 2)
        )
    else:
        hard_fold_mse = signal_mse
    wrapped = modulo(reconstruction, float(config["lambda_value"]))
    wrapped_measurement_mae = float(np.mean(np.abs(wrapped - modulo_samples)))
    return {
        "psnr_db": signal_psnr,
        "time_mae_samples": tau_mae,
        "weak_tau_mae_samples": weak_tau_mae,
        "tau_max_error_samples": max_tau_error,
        "signal_mse": signal_mse,
        "hard_fold_signal_mse": hard_fold_mse,
        "wrapped_measurement_mae": wrapped_measurement_mae,
        "dynamic_range_x": float(config["dynamic_range_x"]),
        "quant_bits": float(config["quant_bits"]),
        "amplitude_ratio": float(config["amplitude_ratio"]),
        "mean_fold_count": float(np.mean(folds)),
    }


def method_name_from_path(output_path: Path, suffix: str) -> str:
    stem = output_path.stem
    suffix_token = f"_{suffix}"
    if stem.endswith(suffix_token):
        stem = stem[: -len(suffix_token)]
    return "conventional_clip_sres" if stem == "conventional" else stem


def discover_methods(spec: ExperimentSpec, checkpoint_dir: Path) -> dict[str, Path]:
    methods = {"conventional_clip_sres": Path(spec.baseline)}
    suffix_token = f"_{spec.suffix}.npz"
    for path in sorted(checkpoint_dir.glob(f"*{suffix_token}")):
        name = method_name_from_path(path, spec.suffix)
        if name == "conventional_clip_sres":
            continue
        methods[name] = path
    return methods


def methods_from_train_scores(
    spec: ExperimentSpec, train_scores_path: Path, checkpoint_dir: Path
) -> dict[str, Path]:
    if not train_scores_path.exists():
        return {}
    train_scores = json.loads(train_scores_path.read_text())
    experiment = train_scores.get("experiments", {}).get(spec.name, {})
    names = sorted(experiment.get("results", {}))
    methods: dict[str, Path] = {}
    for name in names:
        if name == "conventional_clip_sres":
            methods[name] = Path(spec.baseline)
        else:
            methods[name] = checkpoint_dir / f"{name}_{spec.suffix}.npz"
    return methods


def evaluate_experiment(
    spec: ExperimentSpec,
    methods: dict[str, Path],
) -> dict[str, dict[str, dict[str, float]]]:
    if "conventional_clip_sres" not in methods:
        raise ValueError(f"{spec.name} has no conventional baseline output")
    baseline_metrics = evaluate_method(Path(spec.data), methods["conventional_clip_sres"])
    baseline_mse = baseline_metrics["signal_mse"]

    results = {"conventional_clip_sres": dict(baseline_metrics)}
    results["conventional_clip_sres"]["mse_gain_over_conventional_db"] = 0.0

    for name, path in methods.items():
        if name == "conventional_clip_sres":
            continue
        if not path.exists():
            raise FileNotFoundError(
                f"train scores include method {name!r} for {spec.name}, "
                f"but held-out scoring could not find {path}"
            )
        method_metrics = evaluate_method(Path(spec.data), path)
        method_mse = method_metrics["signal_mse"]
        method_metrics["mse_gain_over_conventional_db"] = float(
            10.0 * np.log10(max(baseline_mse, 1e-18) / max(method_mse, 1e-18))
        )
        results[name] = method_metrics

    return {spec.name: {"results": results}}


def spec_by_name(name: str) -> ExperimentSpec:
    for spec in EXPERIMENTS:
        if spec.name == name:
            return spec
    raise ValueError(f"unknown experiment name: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data")
    parser.add_argument("--method")
    parser.add_argument("--baseline")
    parser.add_argument("--experiment-name", default="synthetic_lowbit_hdr_dr20")
    parser.add_argument("--checkpoint-dir", default="checkpoints")
    parser.add_argument("--train-scores", default="scoring/scores_train.json")
    parser.add_argument("--scores", default="scoring/scores_test.json")
    args = parser.parse_args()

    experiments = {}
    if args.data or args.method or args.baseline:
        if not (args.data and args.method and args.baseline):
            raise ValueError("--data, --method, and --baseline must be provided together")
        spec = spec_by_name(args.experiment_name)
        method_path = Path(args.method)
        method_name = method_name_from_path(method_path, spec.suffix)
        methods = {
            "conventional_clip_sres": Path(args.baseline),
            method_name: method_path,
        }
        experiments.update(
            evaluate_experiment(
                ExperimentSpec(args.experiment_name, args.data, args.baseline, spec.suffix),
                methods,
            )
        )
    else:
        checkpoint_dir = Path(args.checkpoint_dir)
        train_scores_path = Path(args.train_scores)
        for spec in EXPERIMENTS:
            methods = methods_from_train_scores(spec, train_scores_path, checkpoint_dir)
            if not methods:
                methods = discover_methods(spec, checkpoint_dir)
            experiments.update(evaluate_experiment(spec, methods))

    scores = {"slice": SLICE_NAME, "experiments": experiments}
    scores_path = Path(args.scores)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.write_text(json.dumps(scores, indent=2, sort_keys=True))
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
