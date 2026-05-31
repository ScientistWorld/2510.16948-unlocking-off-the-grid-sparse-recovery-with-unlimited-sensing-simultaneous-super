"""Evaluate saved US-SRes reproduction artifacts.

The evaluator is intentionally method-agnostic: it reads dataset and output
artifacts written by any implementation that follows the documented npz format.
It does not import or call code from method/.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


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


def evaluate_method(data_path: Path, output_path: Path) -> dict[str, float]:
    data = np.load(data_path, allow_pickle=True)
    output = np.load(output_path, allow_pickle=True)
    required_labels = {"clean", "taus", "config", "folds", "modulo_samples"}
    missing = required_labels - set(data.files)
    if missing:
        raise ValueError(
            f"evaluation data {data_path} is missing label arrays: {sorted(missing)}"
        )
    required_output = {"reconstruction", "taus"}
    missing_output = required_output - set(output.files)
    if missing_output:
        raise ValueError(
            f"method output {output_path} is missing arrays: {sorted(missing_output)}"
        )
    config = data["config"][0]
    reconstruction = output["reconstruction"]
    clean = data["clean"]
    if reconstruction.shape[0] != clean.shape[0]:
        raise ValueError(
            f"{output_path} has {reconstruction.shape[0]} reconstruction rows, "
            f"but {data_path} has {clean.shape[0]} evaluation trials"
        )
    if output["taus"].shape[0] != clean.shape[0]:
        raise ValueError(
            f"{output_path} has {output['taus'].shape[0]} tau rows, "
            f"but {data_path} has {clean.shape[0]} evaluation trials"
        )

    tau_error = tau_errors(data["taus"], output["taus"])
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
    wrapped_measurement_mae = float(np.mean(np.abs(wrapped - data["modulo_samples"])))
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
        "mean_fold_count": float(np.mean(data["folds"])),
    }


def method_name_from_path(output_path: Path, suffix: str | None = None) -> str:
    stem = output_path.stem
    suffixes = (suffix,) if suffix else (
        "dr20_bits8",
        "dr20_bits5",
        "dr10",
        "dr20",
        "dr30",
        "outputs",
    )
    for token in suffixes:
        suffix_token = f"_{token}"
        if stem.endswith(suffix_token):
            stem = stem[: -len(suffix_token)]
            break
    return "conventional_clip_sres" if stem == "conventional" else stem


def evaluate_experiment(
    name: str,
    data_path: Path,
    method_path: Path,
    baseline_path: Path,
    method_name: str | None = None,
) -> dict[str, dict[str, dict[str, float]]]:
    method_metrics = evaluate_method(data_path, method_path)
    baseline_metrics = evaluate_method(data_path, baseline_path)
    mse_gain_db = 10.0 * np.log10(
        max(baseline_metrics["signal_mse"], 1e-18)
        / max(method_metrics["signal_mse"], 1e-18)
    )
    method_metrics["mse_gain_over_conventional_db"] = float(mse_gain_db)
    baseline_metrics["mse_gain_over_conventional_db"] = 0.0
    method_key = method_name or method_name_from_path(method_path)
    return {
        name: {
            "results": {
                "conventional_clip_sres": baseline_metrics,
                method_key: method_metrics,
            }
        }
    }


def evaluate_methods_for_experiment(
    name: str,
    data_path: Path,
    methods: dict[str, Path],
) -> dict[str, dict[str, dict[str, float]]]:
    if "conventional_clip_sres" not in methods:
        raise ValueError(f"{name} has no conventional baseline output")
    baseline_metrics = evaluate_method(data_path, methods["conventional_clip_sres"])
    baseline_mse = baseline_metrics["signal_mse"]
    results = {"conventional_clip_sres": dict(baseline_metrics)}
    results["conventional_clip_sres"]["mse_gain_over_conventional_db"] = 0.0

    for method_name, method_path in methods.items():
        if method_name == "conventional_clip_sres":
            continue
        method_metrics = evaluate_method(data_path, method_path)
        method_metrics["mse_gain_over_conventional_db"] = float(
            10.0
            * np.log10(
                max(baseline_mse, 1e-18)
                / max(method_metrics["signal_mse"], 1e-18)
            )
        )
        results[method_name] = method_metrics

    return {name: {"results": results}}


def discover_methods(spec: ExperimentSpec, checkpoint_dir: Path) -> dict[str, Path]:
    methods = {"conventional_clip_sres": Path(spec.baseline)}
    suffix_token = f"_{spec.suffix}.npz"
    for path in sorted(checkpoint_dir.glob(f"*{suffix_token}")):
        method_name = method_name_from_path(path, spec.suffix)
        if method_name == "conventional_clip_sres":
            continue
        methods[method_name] = path
    return methods


def load_manifest(path: Path) -> list[dict[str, str]]:
    manifest = json.loads(path.read_text())
    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a list of experiment records")
    required = {"name", "data", "method", "baseline"}
    for idx, record in enumerate(manifest):
        missing = required - set(record)
        if missing:
            raise ValueError(f"Manifest record {idx} missing keys: {sorted(missing)}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data")
    parser.add_argument("--method")
    parser.add_argument("--baseline")
    parser.add_argument("--experiment-name", default="synthetic_lowbit_hdr_dr20")
    parser.add_argument("--manifest")
    parser.add_argument("--checkpoint-dir", default="checkpoints")
    parser.add_argument("--scores", default="scoring/scores.json")
    args = parser.parse_args()

    experiments = {}
    if args.manifest:
        for record in load_manifest(Path(args.manifest)):
            experiments.update(
                evaluate_experiment(
                    record["name"],
                    Path(record["data"]),
                    Path(record["method"]),
                    Path(record["baseline"]),
                    record.get("method_name"),
                )
            )
    elif args.data or args.method or args.baseline:
        if not (args.data and args.method and args.baseline):
            raise ValueError("--data, --method, and --baseline must be provided together")
        experiments.update(
            evaluate_experiment(
                args.experiment_name,
                Path(args.data),
                Path(args.method),
                Path(args.baseline),
                method_name_from_path(Path(args.method)),
            )
        )
    else:
        checkpoint_dir = Path(args.checkpoint_dir)
        for spec in EXPERIMENTS:
            experiments.update(
                evaluate_methods_for_experiment(
                    spec.name,
                    Path(spec.data),
                    discover_methods(spec, checkpoint_dir),
                )
            )

    scores = {"experiments": experiments}
    scores_path = Path(args.scores)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.write_text(json.dumps(scores, indent=2, sort_keys=True))
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
