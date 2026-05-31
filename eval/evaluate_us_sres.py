"""Evaluate saved US-SRes reproduction artifacts."""

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


def match_tau_mae(true_taus: np.ndarray, pred_taus: np.ndarray) -> float:
    errors = []
    for truth, pred in zip(true_taus, pred_taus):
        truth = np.sort(truth)
        pred = np.sort(pred)
        direct = np.mean(np.abs(truth - pred))
        swapped = np.mean(np.abs(truth - pred[::-1]))
        errors.append(min(direct, swapped))
    return float(np.mean(errors))


def evaluate_method(data_path: Path, output_path: Path) -> dict[str, float]:
    data = np.load(data_path, allow_pickle=True)
    output = np.load(output_path, allow_pickle=True)
    config = data["config"][0]
    reconstruction = output["reconstruction"]
    clean = data["clean"]
    tau_mae = match_tau_mae(data["taus"], output["taus"])
    signal_psnr = psnr(clean, reconstruction)
    signal_mse = float(np.mean((clean - reconstruction) ** 2))
    return {
        "psnr_db": signal_psnr,
        "time_mae_samples": tau_mae,
        "signal_mse": signal_mse,
        "dynamic_range_x": float(config["dynamic_range_x"]),
        "quant_bits": float(config["quant_bits"]),
        "amplitude_ratio": float(config["amplitude_ratio"]),
        "mean_fold_count": float(np.mean(data["folds"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/synthetic/us_sres_benchmark.npz")
    parser.add_argument("--method", default="checkpoints/us_sres_outputs.npz")
    parser.add_argument("--baseline", default="checkpoints/conventional_outputs.npz")
    parser.add_argument("--scores", default="scoring/scores.json")
    args = parser.parse_args()

    method_metrics = evaluate_method(Path(args.data), Path(args.method))
    baseline_metrics = evaluate_method(Path(args.data), Path(args.baseline))
    mse_gain_db = 10.0 * np.log10(
        max(baseline_metrics["signal_mse"], 1e-18)
        / max(method_metrics["signal_mse"], 1e-18)
    )
    method_metrics["mse_gain_over_conventional_db"] = float(mse_gain_db)
    baseline_metrics["mse_gain_over_conventional_db"] = 0.0

    scores = {
        "experiments": {
            "synthetic_lowbit_hdr_weak_strong": {
                "results": {
                    "conventional_clip_sres": baseline_metrics,
                    "us_sres": method_metrics,
                }
            }
        }
    }
    scores_path = Path(args.scores)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.write_text(json.dumps(scores, indent=2, sort_keys=True))
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
