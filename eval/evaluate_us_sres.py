"""Evaluate saved US-SRes reproduction artifacts.

The evaluator is intentionally method-agnostic: it reads dataset and output
artifacts written by any implementation that follows the documented npz format.
It does not import or call code from method/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


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


def method_name_from_path(output_path: Path) -> str:
    stem = output_path.stem
    for suffix in ("_dr20_bits8", "_dr20_bits5", "_dr10", "_dr20", "_dr30", "_outputs"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
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
    parser.add_argument("--data", default="data/synthetic/us_sres_benchmark.npz")
    parser.add_argument("--method", default="checkpoints/us_sres_outputs.npz")
    parser.add_argument("--baseline", default="checkpoints/conventional_outputs.npz")
    parser.add_argument("--experiment-name", default="synthetic_lowbit_hdr_dr20")
    parser.add_argument("--manifest")
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
    else:
        experiments.update(
            evaluate_experiment(
                args.experiment_name,
                Path(args.data),
                Path(args.method),
                Path(args.baseline),
                method_name_from_path(Path(args.method)),
            )
        )

    scores = {"experiments": experiments}
    scores_path = Path(args.scores)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.write_text(json.dumps(scores, indent=2, sort_keys=True))
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
